#!/usr/bin/env python3
"""Fetch recent P2000 messages from API and add to train_part2.jsonl."""

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

API_BASE = "https://192.168.1.193:4200/api"
TRAIN_FILE = "train.jsonl"
OUTPUT_FILE = "train_part2.jsonl"
ABBREV_FILE = "abbreviations.jsonl"

# Load abbreviations
ABBREV_MAP = {}
with open(ABBREV_FILE) as f:
    for line in f:
        line = line.strip()
        if line:
            entry = json.loads(line)
            ABBREV_MAP[entry["input"]] = entry["output"]

# Abbreviation -> Regio mapping
ABBREV_TO_REGIO = {
    "SGRAVH": "Haaglanden", "VOORB": "Haaglanden", "LEIDDM": "Haaglanden",
    "WASSNR": "Haaglanden", "RIJSZH": "Haaglanden", "NOOTDP": "Haaglanden",
    "PIJNAK": "Haaglanden", "DELIER": "Haaglanden", "NAALDW": "Haaglanden",
    "SGRAVZ": "Haaglanden", "WATERI": "Haaglanden", "MONSTR": "Haaglanden",
    "POELDK": "Haaglanden", "HONSDK": "Haaglanden", "MAASDK": "Haaglanden",
    "KWINTH": "Haaglanden", "DENHZH": "Haaglanden", "TRHEIE": "Haaglanden",
    "HOEKVH": "Haaglanden", "OTVOOR": "Haaglanden", "MAASLD": "Haaglanden",
    "ROTTDM": "Rotterdam-Rijnmond", "SCHIDM": "Rotterdam-Rijnmond",
    "VLAARD": "Rotterdam-Rijnmond", "CAPIJS": "Rotterdam-Rijnmond",
    "SPIJKN": "Rotterdam-Rijnmond", "BARDRT": "Rotterdam-Rijnmond",
    "RIDDKK": "Rotterdam-Rijnmond", "HOOGVL": "Rotterdam-Rijnmond",
    "POORTG": "Rotterdam-Rijnmond", "MAASSL": "Rotterdam-Rijnmond",
    "BERGHK": "Rotterdam-Rijnmond", "ROZNZH": "Rotterdam-Rijnmond",
    "BRIELL": "Rotterdam-Rijnmond", "HELLVS": "Rotterdam-Rijnmond",
    "ROCKNJ": "Rotterdam-Rijnmond", "KRIMIJ": "Rotterdam-Rijnmond",
    "NWKKIJ": "Rotterdam-Rijnmond", "HENDIA": "Rotterdam-Rijnmond",
    "ALBLDM": "Rotterdam-Rijnmond", "ZWIJND": "Rotterdam-Rijnmond",
    "HEERJD": "Rotterdam-Rijnmond", "RHOON": "Rotterdam-Rijnmond",
    "ROTALB": "Rotterdam-Rijnmond", "BOTLEK": "Rotterdam-Rijnmond",
    "EUROPT": "Rotterdam-Rijnmond", "MAASVL": "Rotterdam-Rijnmond",
    "VONDPL": "Rotterdam-Rijnmond", "VIERPL": "Rotterdam-Rijnmond",
    "HEKELI": "Rotterdam-Rijnmond", "HEENVL": "Rotterdam-Rijnmond",
    "CORTLD": "Rotterdam-Rijnmond",
    "LEIDEN": "Hollands Midden", "ALPHRN": "Hollands Midden",
    "ZOETMR": "Hollands Midden", "BODEGR": "Hollands Midden",
    "GOUDA": "Hollands Midden", "KATWZH": "Hollands Midden",
    "NDWKZH": "Hollands Midden", "NDWKHT": "Hollands Midden",
    "HILLGM": "Hollands Midden", "LISSE": "Hollands Midden",
    "SASSHM": "Hollands Midden", "VOORHT": "Hollands Midden",
    "VOORSC": "Hollands Midden", "OEGSTG": "Hollands Midden",
    "LEIDDP": "Hollands Midden", "ZOETWD": "Hollands Midden",
    "ROELVN": "Hollands Midden", "NWWETR": "Hollands Midden",
    "WADDXV": "Hollands Midden", "BOSKP": "Hollands Midden",
    "HAZDRP": "Hollands Midden", "RIJNBG": "Hollands Midden",
    "WARMND": "Hollands Midden", "RIJPWT": "Hollands Midden",
    "NWVEEN": "Hollands Midden", "NDEN": "Hollands Midden",
    "HOOGMD": "Hollands Midden", "WOUBRG": "Hollands Midden",
    "VALKZH": "Hollands Midden", "MOERKP": "Hollands Midden",
    "BERKRR": "Hollands Midden", "BLEISW": "Hollands Midden",
    "DELFT": "Hollands Midden", "DELFGW": "Hollands Midden",
    "SCHILD": "Hollands Midden", "ZEVHZH": "Hollands Midden",
    "MOORDR": "Hollands Midden", "NWBRRN": "Hollands Midden",
    "DORDRT": "Zuid-Holland Zuid", "GORCHM": "Zuid-Holland Zuid",
    "PAPDRT": "Zuid-Holland Zuid", "SLIEDR": "Zuid-Holland Zuid",
    "HARDGD": "Zuid-Holland Zuid", "WERKDM": "Zuid-Holland Zuid",
    "NWLEKK": "Zuid-Holland Zuid", "LEERDM": "Zuid-Holland Zuid",
    "OUDBLD": "Zuid-Holland Zuid", "NUMAND": "Zuid-Holland Zuid",
    "SGRAVD": "Zuid-Holland Zuid", "STRIJN": "Zuid-Holland Zuid",
    "HEINND": "Zuid-Holland Zuid", "ZBEIJL": "Zuid-Holland Zuid",
    "KLAASW": "Zuid-Holland Zuid", "PUTTHK": "Zuid-Holland Zuid",
    "KRIMLK": "Zuid-Holland Zuid", "SCHOHV": "Zuid-Holland Zuid",
    "AMMSTL": "Zuid-Holland Zuid", "STOLWK": "Zuid-Holland Zuid",
    "ODKIJS": "Zuid-Holland Zuid", "BERGAB": "Zuid-Holland Zuid",
    "BLESGF": "Zuid-Holland Zuid", "LEKKKK": "Zuid-Holland Zuid",
    "MOLGRF": "Zuid-Holland Zuid", "WIJNGD": "Zuid-Holland Zuid",
    "AMEIDE": "Zuid-Holland Zuid", "GIESBG": "Zuid-Holland Zuid",
    "OTTOLD": "Zuid-Holland Zuid", "PIERSH": "Zuid-Holland Zuid",
    "MIDDHS": "Zuid-Holland Zuid", "OUDTNG": "Zuid-Holland Zuid",
    "SOMMDK": "Zuid-Holland Zuid", "DIRKLD": "Zuid-Holland Zuid",
    "OUDDRP": "Zuid-Holland Zuid", "MELISS": "Zuid-Holland Zuid",
    "HERKGN": "Zuid-Holland Zuid", "GOUDRK": "Zuid-Holland Zuid",
    "VREELD": "Zuid-Holland Zuid",
}

# Known false-positive abbreviations to ignore
IGNORE_ABBREVS = {
    "AMBU", "GRIP", "PRIO", "TESTOPROEP", "LIFELINER", "INZET", "REGIO",
    "GHOR", "IBGS", "MIRG", "GRAAG", "BRAND", "DIEREN", "ONGEVAL",
    "DIENSTVERLENING", "HULPVERLENING", "REANIMATIE", "LETSEL", "WONING",
    "WEGVERVOER", "BUITENBRAND", "NACONTROLE", "HERBEZETTING", "KAZERNE",
    "INDUSTRIE", "EINDE", "CHECK", "BESCHIKBAAR", "CONTACT",
    "DIRECTE", "HIGH", "CARE", "MEDIUM", "POLI", "TRAUMA",
    "VRACHTAUTO", "PERSONENAUTO", "SCOOTER", "FIETS", "VOETGANGER",
}


def curl_get(url):
    """Fetch URL with curl -sk, return parsed JSON."""
    result = subprocess.run(
        ["curl", "-sk", url], capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"curl error: {result.stderr}", file=sys.stderr)
        return None
    return json.loads(result.stdout)


def get_regio(abbrev):
    """Get Regio from abbreviation."""
    return ABBREV_TO_REGIO.get(abbrev)


def parse_message(raw):
    """Parse a P2000 raw message into location fields."""
    straat = None
    plaats = None
    wegnummer = None
    postcode = None
    regio = None

    msg = raw.strip()

    # Pattern 13: Null messages
    null_patterns = [
        r'^TESTOPROEP', r'^Graag\s+contact', r'^Check\s+uw\s+MDT',
        r'^Beschikbaar\s+A[12]', r'^svp\s+contact', r'^GRIP\s+',
        r'^Prio\s+\d\s*$', r'^A[12]\s*$', r'^MOB\b',
        r'^Oproep\b', r'^Sproeier', r'^Waterwinning',
        r'^GOEDENAVOND', r'^GOEDEMORGEN', r'^GOEDENMIDDAG',
        r'^OCMD\b', r'^Ambu\s+\d+\s+-\s+\w+\s+Rit\s*$',
    ]
    for pat in null_patterns:
        if re.search(pat, msg, re.IGNORECASE):
            return {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None}

    # Strip common prefixes to normalize
    # Remove priority prefix: A0/A1/A2/B1/B2
    cleaned = re.sub(r'^[AB][012]\s+', '', msg)
    # Remove (DIA: ja), (Inzet AED), etc.
    cleaned = re.sub(r'\((?:DIA:\s*ja|Inzet\s+AED|dia:\s*ja)\)\s*', '', cleaned)
    # Remove AMBU NNNNN (possibly multiple)
    cleaned = re.sub(r'(?:AMBU\s+)?\d{5}\s+(?=\d{5}\s+)', '', cleaned)  # double numbers
    cleaned = re.sub(r'^AMBU\s+\d{5}\s+', '', cleaned)

    # Extract postcode
    pc_match = re.search(r'\b(\d{4}[A-Z]{2})\b', cleaned)
    if pc_match:
        postcode = pc_match.group(1)

    # Extract wegnummer (A1-A99, N1-N999) - only real roads with direction markers or km
    weg_match = re.search(r'\b([AN]\d{1,3})\s+(?:Li|Re|Ri)\b', msg)
    if weg_match:
        wegnummer = weg_match.group(1)
    else:
        weg_match = re.search(r'\b([AN]\d{1,3})\s+[\d]+[,\.]\d+', msg)
        if weg_match:
            wegnummer = weg_match.group(1)

    # Find abbreviation in original message
    abbrev = None
    for m in re.finditer(r'\b([A-Z]{4,7})\b', msg):
        candidate = m.group(1)
        if candidate in ABBREV_MAP and candidate not in IGNORE_ABBREVS:
            abbrev = candidate
            regio = get_regio(abbrev)
            break

    # --- Pattern: ABBREV : NNNNN (hospital/location with regio code) ---
    m = re.match(r'^(.+?)\s+([A-Z]{4,7})\s*:\s*(?:\(.*?\)\s*)?\d+', cleaned)
    if m and m.group(2) in ABBREV_MAP:
        straat = m.group(1)
        abbrev_code = m.group(2)
        regio = get_regio(abbrev_code)
        plaats = ABBREV_MAP.get(abbrev_code)
        # Remove facility/department prefixes
        straat = re.sub(r'^[A-Z]+\d*\s*\(.*?\)\s*', '', straat)  # "HMCB (64 bg)"
        straat = re.sub(r'^(?:SEH|Poli\s+\w+|Gynaecologie|Radiologie|Cardiologie|Cardiochirurgie|Neurologie|Orthopedie)\s+', '', straat)
        straat = re.sub(r'^[A-Z]{2,}\s+', '', straat) if re.match(r'^[A-Z]{2,}\s+[A-Z][a-z]', straat) else straat
        # Remove B2/A1 prefix that might remain
        straat = re.sub(r'^[AB][012]\s+', '', straat)
        straat = straat.strip() or None
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: with postcode + city + ABBREV ---
    # Straat 3023XR Plaats ABBREV bon NNNNN  or  Straat 3023XR Plaats ABBREV NNNNN
    m = re.match(
        r'^(.+?)\s+(\d{4}[A-Z]{2})\s+(.+?)\s+([A-Z]{4,7})\s+(?:bon\s+)?\d+',
        cleaned
    )
    if m and m.group(4) in ABBREV_MAP:
        straat = m.group(1)
        postcode = m.group(2)
        plaats_raw = m.group(3)
        abbrev_code = m.group(4)
        regio = get_regio(abbrev_code)
        # Use the abbreviation's place name if plaats_raw looks like it includes extra words
        # For multi-word cities, the ABBREV_MAP value is authoritative
        known_place = ABBREV_MAP.get(abbrev_code, "")
        # Check if plaats_raw is the start/end of the known place
        if known_place and (plaats_raw in known_place or known_place.startswith(plaats_raw)):
            plaats = known_place
        else:
            plaats = plaats_raw
        # Clean street
        straat = re.sub(r'^\d{5}\s+', '', straat)  # remove AMBU number
        straat = straat.strip() or None
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: without postcode, city + ABBREV ---
    # Straat Plaats ABBREV bon NNNNN
    m = re.match(
        r'^(.+?)\s+(\S+(?:\s+\S+)*?)\s+([A-Z]{4,7})\s+(?:bon\s+|Directe\s+inzet\s+)?\d+',
        cleaned
    )
    if m and m.group(3) in ABBREV_MAP:
        straat = m.group(1)
        plaats_raw = m.group(2)
        abbrev_code = m.group(3)
        regio = get_regio(abbrev_code)
        known_place = ABBREV_MAP.get(abbrev_code, "")
        # Greedy match may have captured too much in plaats_raw
        # The city is the last word(s) before the abbreviation
        # Try to match known_place at the end of "straat + plaats_raw"
        full = straat + " " + plaats_raw
        if known_place and full.endswith(known_place):
            straat = full[:-(len(known_place))].strip()
            plaats = known_place
        elif known_place and plaats_raw in known_place:
            plaats = known_place
        else:
            plaats = plaats_raw
        straat = re.sub(r'^\d{5}\s+', '', straat)
        straat = straat.strip() or None
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: Fire/P messages ---
    m = re.match(
        r'^P\s+\d\s+\S+\s+(?:BR\s+\w+(?:\s+\(\w+\))?|Reanimatie|Hulpverlening|Dienstverlening|Nacontrole|Buitenbrand|Brandgerucht|HV\s+\w+(?:\s+\w+)?|Ongeval\s+\w+(?:\s+\w+)?)\s+(.+?)\s+(\d{4}[A-Z]{2})\s+(.+?)\s+(?:[A-Z]{4,7}\s+)?\d{5,}',
        msg
    )
    if m:
        straat = m.group(1)
        postcode = m.group(2)
        plaats = m.group(3)
        # Clean parens from street
        straat = re.sub(r'^\(.*?\)\s*', '', straat)
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # P message without postcode
    m = re.match(
        r'^P\s+\d\s+\S+\s+(?:BR\s+\w+(?:\s+\(\w+\))?|Reanimatie|Hulpverlening|Dienstverlening|Nacontrole|Buitenbrand|Brandgerucht|HV\s+\w+(?:\s+\w+)?|Ongeval\s+\w+(?:\s+\w+)?)\s+(.+?)\s+([A-Z][a-z]\S*(?:\s+[a-z]\S+)*)\s+(?:[A-Z]{4,7}\s+)?\d{5,}',
        msg
    )
    if m:
        straat = m.group(1)
        plaats = m.group(2)
        straat = re.sub(r'^\(.*?\)\s*', '', straat)
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: Road messages ---
    if wegnummer:
        m = re.search(r'\b[AN]\d{1,3}\s+(?:Li|Re|Ri)\s+[\d,\.]+\s+(\S+)', msg)
        if m:
            plaats = m.group(1)
            if plaats.isupper() and len(plaats) >= 4:
                if plaats in ABBREV_MAP:
                    regio = get_regio(plaats)
                    plaats = ABBREV_MAP[plaats]
                else:
                    plaats = None
            return {"Straatnaam": None, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: Rit messages ---
    # NNNNN Rit NNNNN Straat City  or  A1 NNNNN Rit NNNNN Straat City
    m = re.search(r'(?:Rit[:\s]+\d+\s+)(.+?)\s+([A-Z][a-z]\S*(?:\s+[a-z]\S+)*)\s*$', cleaned)
    if m:
        straat = m.group(1)
        plaats = m.group(2)
        # Remove facility prefixes
        straat = re.sub(r'^(?:SGZ\s+[\d.]+\s+\w+\s+)', '', straat)
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: Simple city ---
    # A1 CityName NNNNN or A2 CityName Rit: NNNNN
    m = re.match(r'^([A-Z][a-z]\S*(?:\s+[a-z]\S+)*)\s+(?:Rit[:\s]+)?\d+\s*$', cleaned)
    if m:
        plaats = m.group(1)
        return {"Straatnaam": None, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # --- Pattern: NNNNN Street City NNNNN (Amsterdam-style) ---
    m = re.match(r'^\d{5}\s+(.+?)\s+([A-Z][a-z]\S*(?:\s+[a-z]\S+)*)\s+\d{5}\s*$', cleaned)
    if m:
        straat = m.group(1)
        plaats = m.group(2)
        straat = re.sub(r'\s+\d+$', '', straat)
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # LIFELINER pattern
    m = re.match(r'^LIFELINER\s+\d\s+(.+?)\s+([A-Z][a-z]\S*(?:\s+[a-z]\S+)*)\s+\d+', msg)
    if m:
        straat = m.group(1)
        plaats = m.group(2)
        return {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # Fallback: postcode-based extraction
    if postcode:
        m = re.search(r'(.+?)\s+' + re.escape(postcode) + r'\s+(.+?)(?:\s+[A-Z]{4,7})?\s+\d{5,}', msg)
        if m:
            straat = m.group(1)
            plaats = m.group(2)
            straat = re.sub(r'^(?:P\s+\d\s+\S+\s+(?:BR\s+\w+|Reanimatie|Hulpverlening|Dienstverlening)\s+)', '', straat)
            straat = re.sub(r'^(?:[AB][012]\s+)', '', straat)
            straat = re.sub(r'\(.*?\)\s*', '', straat)
            straat = re.sub(r'^(?:AMBU\s+)?\d{5}\s+', '', straat)
            straat = re.sub(r'\s+\d+$', '', straat)
            return {"Straatnaam": straat.strip() or None, "PlaatsNaam": plaats, "wegnummer": wegnummer, "postcode": postcode, "Regio": regio}

    # Couldn't parse
    return None


def main():
    # Calculate time range
    now = datetime.now(timezone.utc)
    date_from = (now - timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    date_to = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"Fetching messages from {date_from} to {date_to}")

    # Fetch all pages
    messages = []
    page = 1
    while True:
        url = f"{API_BASE}/pages?page={page}&size=999&date_from={date_from}&date_to={date_to}"
        data = curl_get(url)
        if not data:
            print("Failed to fetch message list", file=sys.stderr)
            sys.exit(1)
        batch = data.get("content", [])
        total = data.get("total", 0)
        messages.extend(batch)
        print(f"Page {page}: got {len(batch)} messages (total available: {total})")
        if len(messages) >= total or len(batch) == 0:
            break
        page += 1
    print(f"Fetched {len(messages)} messages total")

    # Load existing inputs for dedup
    existing_inputs = set()
    for fname in [TRAIN_FILE, OUTPUT_FILE]:
        try:
            with open(fname) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            existing_inputs.add(entry.get("input", ""))
                        except json.JSONDecodeError:
                            pass
        except FileNotFoundError:
            pass

    print(f"Loaded {len(existing_inputs)} existing entries for dedup")

    # Fetch each message's raw_message using concurrent requests
    added = 0
    skipped = 0
    new_abbrevs = {}
    entries = []
    msg_ids = [m["id"] for m in messages]

    def fetch_raw(msg_id):
        detail = curl_get(f"{API_BASE}/pages/{msg_id}")
        if not detail:
            return None
        return detail.get("raw_message", "")

    print(f"Fetching {len(msg_ids)} raw messages (20 concurrent)...")
    raw_messages = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_raw, mid): mid for mid in msg_ids}
        done = 0
        for future in as_completed(futures):
            mid = futures[future]
            done += 1
            try:
                raw_messages[mid] = future.result()
            except Exception:
                raw_messages[mid] = None
            if done % 500 == 0:
                print(f"  Fetched {done}/{len(msg_ids)}...")

    print(f"  Fetched all {len(raw_messages)} messages")

    # Process in original order
    for msg_info in messages:
        msg_id = msg_info["id"]
        raw = raw_messages.get(msg_id)
        if not raw or raw in existing_inputs:
            skipped += 1
            continue

        # Check for unknown abbreviations
        for m in re.finditer(r'\b([A-Z]{4,6})\b', raw):
            candidate = m.group(1)
            if (candidate not in ABBREV_MAP and
                candidate not in IGNORE_ABBREVS and
                candidate not in new_abbrevs and
                not re.match(r'^[A-Z]{2}\d', candidate)):
                new_abbrevs[candidate] = raw

        parsed = parse_message(raw)
        if parsed is None:
            skipped += 1
            continue

        entry = {"input": raw, "output": parsed}
        entries.append(entry)
        existing_inputs.add(raw)
        added += 1

    # Write to output file
    with open(OUTPUT_FILE, "a") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\nResults:")
    print(f"  Added: {added}")
    print(f"  Skipped: {skipped}")
    print(f"  Total in {OUTPUT_FILE}: {added}")

    if new_abbrevs:
        print(f"\n  Potential new abbreviations found:")
        for abbr, example in new_abbrevs.items():
            print(f"    {abbr}: {example[:80]}")

    return new_abbrevs


if __name__ == "__main__":
    main()
