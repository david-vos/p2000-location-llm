#!/usr/bin/env python3
"""Fetch P2000 messages from API and add to training data."""

import json
import re
import sys
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://192.168.1.193:4200/api"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Load abbreviations
with open("abbreviations.jsonl") as f:
    ABBREVS = {}
    for line in f:
        line = line.strip()
        if line:
            d = json.loads(line)
            ABBREVS[d["input"]] = d["output"]

# Known non-abbreviation uppercase words
IGNORE_WORDS = {
    "AMBU", "GRIP", "PRIO", "TESTOPROEP", "LIFELINER", "INZET", "REGIO",
    "GHOR", "IBGS", "MIRG", "GRAAG", "BOB", "BRT", "BON", "BBA", "BBE",
    "MOB", "MDT", "SVP", "CHECK", "CONTACT", "BESCHIKBAAR", "MKA",
    "DIA", "RAV", "OVD", "AGS", "SIGMA", "PETER", "RAPID", "HELI",
    "KNRM", "MMT", "VWS", "HVD", "STAF", "HANS", "OMS", "UMCU",
    "VUMC", "AMC", "LUMC", "OLVG", "EMC", "ISALA", "JBZ", "ETZ",
    "WZA", "MCL", "NWZ", "ZGT", "MST", "CWZ", "SKB", "TER", "VAN",
    "HET", "AAN", "DEN", "REE", "NUL", "HAG", "NON", "NAT",
    "HMCW", "RDGG", "AZLDP", "GZHC", "ASVZ", "ASVH", "AODA", "LVVN", "DLCF",
}

# Null message patterns
NULL_PATTERNS = [
    r"TESTOPROEP", r"Graag contact", r"Check uw MDT", r"Beschikbaar",
    r"svp contact", r"contact opnemen", r"SIGMA", r"Pager test",
    r"Bericht van MKA", r"^\s*$",
]


def fetch_json(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_raw(msg_id):
    try:
        data = fetch_json(f"{BASE}/pages/{msg_id}", timeout=10)
        return msg_id, data.get("raw_message", "")
    except Exception as e:
        print(f"  Error fetching {msg_id}: {e}", flush=True)
        return msg_id, None


def find_abbreviation(text):
    """Find abbreviation-like words in text."""
    words = re.findall(r'\b([A-Z]{4,6})\b', text)
    found = {}
    for w in words:
        if w in IGNORE_WORDS:
            continue
        if w in ABBREVS:
            found[w] = ABBREVS[w]
        # Unknown abbreviations will be collected separately
    return found


def find_unknown_abbrevs(text):
    """Find potential unknown abbreviations."""
    words = re.findall(r'\b([A-Z]{4,6})\b', text)
    unknown = []
    for w in words:
        if w not in IGNORE_WORDS and w not in ABBREVS:
            # Filter out words that look like unit codes (letters+digits mixed patterns)
            if not re.match(r'^[A-Z]+\d', w) and not re.match(r'^\d', w):
                unknown.append(w)
    return unknown


def parse_message(raw):
    """Parse a P2000 raw message into location fields."""
    if not raw or not raw.strip():
        return None

    text = raw.strip()

    # Check null patterns
    for pat in NULL_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None}

    result = {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None}

    # Extract postcode
    pc_match = re.search(r'\b(\d{4}[A-Z]{2})\b', text)
    if pc_match:
        result["postcode"] = pc_match.group(1)

    # Extract wegnummer
    weg_match = re.search(r'\b([ANS]\d{1,3})\b', text)
    if weg_match:
        candidate = weg_match.group(1)
        # Make sure it's a road, not something else
        if re.search(r'\b' + re.escape(candidate) + r'\s+(Li|Re|Ri)\b', text) or \
           re.search(r'\b(A|N)\d{1,3}\b', candidate):
            result["wegnummer"] = candidate

    # Find known abbreviations for regio
    abbrevs_found = find_abbreviation(text)

    # Try various patterns

    # Pattern 1: AMBU with postcode - A1 AMBU 17128 Straat 3023XR Plaats ABBREV bon 12345
    m = re.match(r'^[AB]\d\s+(?:AMBU|Ambu)\s+\d+\s+(.+?)\s+(\d{4}[A-Z]{2})\s+(\S+)\s+([A-Z]{4,6})\s+bon\s+\d+', text)
    if m:
        result["Straatnaam"] = m.group(1).strip()
        result["PlaatsNaam"] = m.group(3).strip()
        result["postcode"] = m.group(2)
        abbr = m.group(4)
        if abbr in ABBREVS:
            result["Regio"] = ABBREVS[abbr]
        return result

    # Pattern 2: AMBU without postcode - A2 AMBU 17350 Straat Plaats ABBREV bon 12345
    m = re.match(r'^[AB]\d\s+(?:AMBU|Ambu)\s+\d+\s+(.+?)\s+([A-Z]{4,6})\s+bon\s+\d+', text)
    if m:
        street_city = m.group(1).strip()
        abbr = m.group(2)
        if abbr in ABBREVS:
            result["Regio"] = ABBREVS[abbr]
            # Try to split street and city - city is usually the last word(s)
            # Look for the city name from abbreviation
            city = ABBREVS[abbr]
            # Check if city name appears in the street_city string
            if city in street_city:
                street = street_city.replace(city, "").strip()
                result["PlaatsNaam"] = city
                if street:
                    result["Straatnaam"] = street
            else:
                # Last word is likely city
                parts = street_city.rsplit(" ", 1)
                if len(parts) == 2:
                    result["Straatnaam"] = parts[0]
                    result["PlaatsNaam"] = parts[1]
                else:
                    result["Straatnaam"] = street_city
        return result

    # Pattern 3: Regio + street - A1 Straatnaam ABBREV : 15139
    m = re.match(r'^.*?\s+(.+?)\s+([A-Z]{4,6})\s*:\s*\d+', text)
    if m:
        abbr = m.group(2)
        if abbr in ABBREVS:
            result["Straatnaam"] = m.group(1).strip()
            # Remove leading priority/unit codes
            result["Straatnaam"] = re.sub(r'^(?:[AB]\d\s+)?(?:AMBU\s+\d+\s+)?(?:DP\d\s+\S+\s+)?', '', result["Straatnaam"]).strip()
            # Clean up parenthetical info
            result["Straatnaam"] = re.sub(r'\s*\(.*?\)\s*', ' ', result["Straatnaam"]).strip()
            # Remove hospital/location prefixes like "JKZ (J2.2) Gynaecologie"
            result["Regio"] = ABBREVS[abbr]
            return result

    # Pattern 10: DP format - A2 DP2 Leidschendam-Voorburg Via Donizetti VOORB VWS 15144
    m = re.match(r'^[AB]\d\s+DP\d\s+\S+\s+(.+?)\s+([A-Z]{4,6})\s+(?:VWS|HVD)\s+\d+', text)
    if m:
        result["Straatnaam"] = m.group(1).strip()
        abbr = m.group(2)
        if abbr in ABBREVS:
            result["Regio"] = ABBREVS[abbr]
        return result

    # Pattern 7: Fire/P messages - P 1 BOB-01 BR woning Straat Plaats 223251
    m = re.match(r'^P\s+\d\s+\S+\s+(?:BR|OMS|HV|BHV|DINS|Ass)\s+\S+\s+(.+?)\s+(\d{6,})\s*$', text)
    if m:
        street_city = m.group(1).strip()
        # Try postcode split
        if result["postcode"]:
            parts = re.split(r'\d{4}[A-Z]{2}', street_city)
            if len(parts) >= 2:
                result["Straatnaam"] = parts[0].strip().rstrip("0123456789 ")
                result["PlaatsNaam"] = parts[1].strip()
                return result
        # Split on last known city or last capitalized word
        parts = street_city.rsplit(" ", 1)
        if len(parts) == 2:
            result["Straatnaam"] = parts[0].strip()
            result["PlaatsNaam"] = parts[1].strip()
        else:
            result["PlaatsNaam"] = street_city
        return result

    # Pattern 8/9: Prio/directe inzet with road
    m = re.match(r'^(?:Prio\s+\d|[AB]\d)\s+([ANS]\d{1,3})\s+(?:Li|Re|Ri)\s+[\d,]+\s+([A-Z]{4,6})\b', text)
    if m:
        result["wegnummer"] = m.group(1)
        abbr = m.group(2)
        if abbr in ABBREVS:
            result["Regio"] = ABBREVS[abbr]
        return result

    # Pattern 4: Rit + city - A2 Best Rit: 27962 or Ambu 07123 - Arnhem Rit 68845
    m = re.search(r'(?:Ambu\s+\d+\s*-\s*|[AB]\d\s+)(\S+(?:\s+\S+)?)\s+Rit[:\s]+\d+', text)
    if m:
        city_candidate = m.group(1).strip()
        # Pattern 5: Rit + street + city - 12149 Rit 33467 Zuidlaan Aerdenhout
        m2 = re.search(r'\d+\s+Rit\s+\d+\s+(.+?)\s+(\S+)\s*$', text)
        if m2:
            result["Straatnaam"] = m2.group(1).strip()
            result["PlaatsNaam"] = m2.group(2).strip()
        else:
            result["PlaatsNaam"] = city_candidate
        return result

    # Pattern 12: Amsterdam format - A1 13164 IJburglaan 1086 Amsterdam 20299
    m = re.match(r'^[AB]\d\s+\d+\s+(.+?)\s+\d+\s+([A-Z][a-z]+(?:\s+[a-z]+)*)\s+\d+\s*$', text)
    if m:
        result["Straatnaam"] = m.group(1).strip()
        result["PlaatsNaam"] = m.group(2).strip()
        return result

    # Pattern 6: City only - A1 Muiderberg 37088
    m = re.match(r'^[AB]\d\s+([A-Z][a-z]+(?:[\s-][a-z]+)*)\s+\d{4,}\s*$', text)
    if m:
        result["PlaatsNaam"] = m.group(1).strip()
        return result

    # Pattern 11: Ongeval/Aanrijding
    m = re.search(r'(?:Ongeval|Aanrijding)\s+\S+\s+(?:\S+\s+)?(.+?)\s+(\S+)\s*$', text)
    if m:
        result["Straatnaam"] = m.group(1).strip()
        result["PlaatsNaam"] = m.group(2).strip()
        return result

    # Generic: try to find abbreviation and extract what we can
    if abbrevs_found:
        abbr = list(abbrevs_found.keys())[0]
        result["Regio"] = abbrevs_found[abbr]
        # Try to get street before abbreviation
        idx = text.find(abbr)
        before = text[:idx].strip()
        # Remove common prefixes
        before = re.sub(r'^.*?(?:AMBU|Ambu)\s+\d+\s+', '', before)
        before = re.sub(r'^[AB]\d\s+', '', before)
        before = re.sub(r'^P\s+\d\s+\S+\s+', '', before)
        before = re.sub(r'^DP\d\s+\S+\s+', '', before)
        before = re.sub(r'^\S+\s+\(\S+\)\s+\S+\s+', '', before)  # hospital codes
        before = re.sub(r'\s*\(.*?\)\s*', ' ', before).strip()
        if before:
            result["Straatnaam"] = before
        return result

    # If we got a postcode, try to parse around it
    if result["postcode"]:
        pc = result["postcode"]
        m = re.search(r'(.+?)\s*(?:\d+\s+)?' + re.escape(pc) + r'\s+(\S+)', text)
        if m:
            street = m.group(1).strip()
            street = re.sub(r'^.*?(?:AMBU|Ambu)\s+\d+\s+', '', street)
            street = re.sub(r'^[AB]\d\s+', '', street)
            street = re.sub(r'^P\s+\d\s+\S+\s+(?:BR|OMS)\s+\S+\s+', '', street)
            result["Straatnaam"] = street
            result["PlaatsNaam"] = m.group(2).strip()
        return result

    # If we found a wegnummer
    if result["wegnummer"]:
        return result

    # Generic fire pattern
    m = re.match(r'^P\s+\d\s+\S+\s+\S+\s+\S+\s+(.+?)\s+(\S+)\s+\d{6}\s*$', text)
    if m:
        result["Straatnaam"] = m.group(1).strip()
        result["PlaatsNaam"] = m.group(2).strip()
        return result

    # Can't parse - return None to skip
    return None


def main():
    now = datetime.now(timezone.utc)
    date_from = (now - timedelta(hours=20)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    date_to = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    print(f"Fetching messages from {date_from} to {date_to}...", flush=True)

    # Fetch message list
    print("Fetching page 1...", flush=True)
    data = fetch_json(f"{BASE}/pages?page=1&size=999&date_from={date_from}&date_to={date_to}")
    total = data["total"]
    total_pages = data.get("total_pages", (total + 998) // 999)
    ids = [m["id"] for m in data["content"]]
    print(f"Page 1: {len(ids)} ids, total={total}, pages={total_pages}", flush=True)

    # Fetch more pages if needed (max 10 pages)
    max_pages = min(total_pages, 10)
    for page in range(2, max_pages + 1):
        print(f"Fetching page {page}/{total_pages}...", flush=True)
        data = fetch_json(f"{BASE}/pages?page={page}&size=999&date_from={date_from}&date_to={date_to}")
        batch = data.get("content", [])
        if not batch:
            break
        ids.extend(m["id"] for m in batch)
        print(f"  Got {len(batch)}, total ids so far: {len(ids)}", flush=True)

    print(f"Found {len(ids)} messages (total: {total})", flush=True)

    # Load existing inputs for dedup
    existing = set()
    for fname in ["train.jsonl", "train_part2.jsonl"]:
        try:
            with open(fname) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        d = json.loads(line)
                        existing.add(d["input"])
        except FileNotFoundError:
            pass

    print(f"Existing training entries: {len(existing)}")

    # Fetch raw messages in parallel
    print(f"Fetching {len(ids)} raw messages (20 workers)...", flush=True)
    raw_messages = {}
    done = 0
    errors = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_raw, mid): mid for mid in ids}
        for future in as_completed(futures):
            done += 1
            msg_id, raw = future.result()
            if raw:
                raw_messages[msg_id] = raw
            else:
                errors += 1
            if done % 500 == 0 or done == len(ids):
                print(f"  Progress: {done}/{len(ids)} fetched, {len(raw_messages)} ok, {errors} errors", flush=True)

    print(f"Got {len(raw_messages)} raw messages ({errors} errors)", flush=True)

    # Parse and collect
    new_entries = []
    skipped = 0
    unknown_abbrevs = {}
    all_null = 0

    for msg_id, raw in raw_messages.items():
        if raw in existing:
            continue

        parsed = parse_message(raw)
        if parsed is None:
            skipped += 1
            continue

        if all(v is None for v in parsed.values()):
            all_null += 1

        # Check for unknown abbreviations
        for abbr in find_unknown_abbrevs(raw):
            unknown_abbrevs[abbr] = unknown_abbrevs.get(abbr, 0) + 1

        entry = {"input": raw, "output": parsed}
        new_entries.append(entry)
        existing.add(raw)

    # Write new entries
    with open("train_part2.jsonl", "a") as f:
        for entry in new_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n=== Results ===")
    print(f"New entries added: {len(new_entries)}")
    print(f"All-null entries: {all_null}")
    print(f"Skipped (unparseable): {skipped}")
    print(f"New total: {len(existing)}")

    if unknown_abbrevs:
        # Sort by frequency
        sorted_abbrs = sorted(unknown_abbrevs.items(), key=lambda x: -x[1])
        print(f"\nPotential unknown abbreviations (count):")
        for abbr, count in sorted_abbrs[:30]:
            print(f"  {abbr}: {count}")


if __name__ == "__main__":
    main()
