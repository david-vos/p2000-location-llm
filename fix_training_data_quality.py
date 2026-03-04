#!/usr/bin/env python3
"""Fix quality issues in train.jsonl identified during review."""

import json
import re
import sys


def fix_entry(i, entry):
    """Fix a single entry. Returns (modified_entry, list_of_fixes)."""
    inp = entry["input"]
    out = entry["output"]
    fixes = []

    straat = out.get("Straatnaam")
    plaats = out.get("PlaatsNaam")
    weg = out.get("wegnummer")
    pc = out.get("postcode")

    # === Fix 1: PlaatsNaam = "Ambu" ===
    if plaats == "Ambu":
        city = None
        # Try patterns: DIA <city> Rit, VWS <city> Rit, - <city> Rit
        m = re.search(r'(?:DIA|VWS|HV weg letsel)\s+(.+?)\s+Rit\b', inp)
        if not m:
            m = re.search(r'Ambu \d+ -\s+(.+?)\s+Rit\b', inp)
        if not m:
            m = re.search(r'Ambu \d+\s+\d+\s+-\s+(.+?)\s+Rit\b', inp)
        if m:
            city = m.group(1).strip()
            # Clean up: remove trailing numbers
            city = re.sub(r'\s+\d+$', '', city)

        # Special case: "Ambu 08993 Reduyt 6932DP Westervoort Rit"
        if not city:
            m = re.search(r'(\d{4}[A-Z]{2})\s+(\S+(?:\s+\S+)?)\s+Rit', inp)
            if m:
                city = m.group(2)
                if not pc:
                    out["postcode"] = m.group(1)
                    fixes.append(f"postcode='{m.group(1)}'")
                # Also extract Straatnaam
                m2 = re.search(r'Ambu \d+\s+(.+?)\s+\d{4}[A-Z]{2}', inp)
                if m2 and not straat:
                    out["Straatnaam"] = m2.group(1)
                    straat = out["Straatnaam"]
                    fixes.append(f"Straatnaam='{straat}'")

        if city:
            # Handle "Elst GE" -> "Elst" (GE is province abbreviation)
            # Keep multi-word cities like "Bergen op Zoom", "Beneden-Leeuwen"
            out["PlaatsNaam"] = city
            fixes.append(f"PlaatsNaam: 'Ambu' → '{city}'")
        else:
            # Can't determine city - set to null rather than wrong value
            out["PlaatsNaam"] = None
            fixes.append("PlaatsNaam: 'Ambu' → null (can't determine)")

    # === Fix 2: "Prio X" prefix in Straatnaam ===
    if straat and re.match(r'^Prio \d+\s+', straat):
        old = straat
        straat = re.sub(r'^Prio \d+\s+', '', straat)
        out["Straatnaam"] = straat
        fixes.append(f"Straatnaam: removed 'Prio' prefix: '{old}' → '{straat}'")

    # === Fix 3: Direction/km data in Straatnaam ===
    # Pattern: Straatnaam is just "Re", "Li", "Re X,Y", "Li X,Y", etc.
    if straat and re.match(r'^(Re|Li)(\s+\d|$)', straat):
        # Check if there's an actual street name after "Re/Li - "
        m = re.match(r'^(?:Re|Li)\s+-\s+(.+)', straat)
        if m:
            actual_street = m.group(1)
            # Clean trailing numbers/codes
            actual_street = re.sub(r'\s+\d+[,.]?\d*\s*.*$', '', actual_street)
            actual_street = re.sub(r'\s+\d{6}.*$', '', actual_street)
            if actual_street:
                out["Straatnaam"] = actual_street
                fixes.append(f"Straatnaam: '{straat}' → '{actual_street}'")
            else:
                out["Straatnaam"] = None
                fixes.append(f"Straatnaam: '{straat}' → null")
        else:
            out["Straatnaam"] = None
            fixes.append(f"Straatnaam: '{straat}' → null (direction/km)")
        straat = out["Straatnaam"]

    # === Fix 4: Straatnaam contains road reference (starts with A/N + digits) ===
    if straat and re.match(r'^[AN]\d+', straat) and weg:
        # Extract actual street if present after " - "
        m = re.search(r'-\s+(.+?)(?:\s+\d+[,.]|\s+\d{5,}|$)', straat)
        if m:
            actual = m.group(1).strip()
            # Remove trailing km/codes
            actual = re.sub(r'\s+\d+[,.].*$', '', actual)
            actual = re.sub(r'\s+\d{5,}.*$', '', actual)
            actual = re.sub(r'\s+ICnum.*$', '', actual)
            if actual and not re.match(r'^[AN]\d', actual) and len(actual) > 2:
                out["Straatnaam"] = actual
                fixes.append(f"Straatnaam: '{straat}' → '{actual}'")
            else:
                out["Straatnaam"] = None
                fixes.append(f"Straatnaam: '{straat}' → null")
        else:
            out["Straatnaam"] = None
            fixes.append(f"Straatnaam: '{straat}' → null (road ref)")
        straat = out["Straatnaam"]

    # Also for Straatnaam starting with A/N road without wegnummer set
    if straat and re.match(r'^[AN]\d+\s', straat) and not weg:
        road_m = re.match(r'^([AN]\d+)', straat)
        if road_m:
            out["wegnummer"] = road_m.group(1)
            weg = out["wegnummer"]
            fixes.append(f"wegnummer: null → '{weg}'")
            # Now clean Straatnaam
            rest = re.sub(r'^[AN]\d+\s*', '', straat)
            rest = re.sub(r'^(Re|Li)\s*', '', rest)
            rest = re.sub(r'^\d+[,.]\d+\s*', '', rest)
            rest = rest.strip()
            if rest and not re.match(r'^\d', rest):
                out["Straatnaam"] = rest
                fixes.append(f"Straatnaam: '{straat}' → '{rest}'")
            else:
                out["Straatnaam"] = None
                fixes.append(f"Straatnaam: '{straat}' → null")
            straat = out["Straatnaam"]

    # === Fix 5: Missing wegnummer ===
    if not weg:
        # Look for A/N road patterns in input
        road_match = re.search(r'\b([AN]\d{2,4})\b', inp)
        if road_match:
            road = road_match.group(1)
            # Exclude false positives: ambulance numbers (always after "Ambu"/"AMBU")
            # Check it's not part of "AMBU 17XXX" or "Ambu 06XXX"
            pre_context = inp[:road_match.start()]
            if not re.search(r'(?:AMBU|Ambu)\s*$', pre_context):
                out["wegnummer"] = road
                weg = road
                fixes.append(f"wegnummer: null → '{road}'")

    # === Fix 6: "Kazerne"/"Post" in Straatnaam ===
    if straat and re.match(r'^(Kazerne|Post)\s+', straat):
        old = straat
        # Try to extract the actual street name (usually the last part)
        # "Kazerne Roosendaal Laan van Brabant" → "Laan van Brabant"
        # "Kazerne Schiedam 's-Gravelandseweg" → "'s-Gravelandseweg"
        # "Post Zoetermeer / Blauw-roodlaan" → "Blauw-roodlaan"
        # "Kazerne Baan Ketelaarsstraat" → "Ketelaarsstraat"

        # Strategy: find the part that looks like a street name
        # (contains -straat, -weg, -laan, -plein, -dijk, -singel, etc.)
        street_suffixes = r'(?:straat|weg|laan|plein|dijk|singel|gracht|kade|dreef|pad|hof|steeg|markt|baan|roodlaan)'
        m = re.search(rf'(\S*{street_suffixes})\b', straat, re.IGNORECASE)
        if m:
            # Find the full street name leading up to the suffix match
            # Go backwards from match to find where street name starts
            end = m.end()
            prefix = straat[:m.start()]
            street_part = straat[m.start():end]

            # Check for multi-word street names before the suffix
            words_before = prefix.rstrip().split()
            # Common street name starters
            full_street = street_part
            for w in reversed(words_before):
                if w.lower() in ('van', 'de', 'het', 'den', 'der', "'s-gravelandseweg"):
                    full_street = w + ' ' + full_street
                elif w.startswith("'s-"):
                    full_street = w
                    break
                else:
                    break

            out["Straatnaam"] = full_street
            fixes.append(f"Straatnaam: '{old}' → '{full_street}'")
        elif ' / ' in straat:
            # "Post Zoetermeer / Blauw-roodlaan"
            parts = straat.split(' / ')
            out["Straatnaam"] = parts[-1]
            fixes.append(f"Straatnaam: '{old}' → '{parts[-1]}'")
        straat = out["Straatnaam"]

    # === Fix 7: PlaatsNaam = "(meervoudig)" ===
    if plaats == "(meervoudig)":
        # Try to find city from abbreviation in input
        abbrev_map = {
            "SGRAVH": "Den Haag", "ROTTDM": "Rotterdam", "ROELVN": "Roelofarendsveen",
            "ZOETMR": "Zoetermeer", "ALPHRN": "Alphen aan den Rijn",
        }
        found = None
        for abbr, city in abbrev_map.items():
            if abbr in inp:
                found = city
                break
        if found:
            out["PlaatsNaam"] = found
            fixes.append(f"PlaatsNaam: '(meervoudig)' → '{found}'")
        else:
            out["PlaatsNaam"] = None
            fixes.append("PlaatsNaam: '(meervoudig)' → null")

    # === Fix 8: PlaatsNaam = "Rijswijk (Zuid-Holland)" ===
    if plaats and '(' in plaats and ')' in plaats:
        clean = re.sub(r'\s*\(.*?\)', '', plaats).strip()
        if clean:
            out["PlaatsNaam"] = clean
            fixes.append(f"PlaatsNaam: '{plaats}' → '{clean}'")

    # === Fix 9: Regio consistency ===
    # We'll handle this separately with a lookup table

    # === Fix 10: Straatnaam "Re - <street>" pattern (with wegnummer set) ===
    if straat and re.match(r'^Re\s+-\s+', straat) and weg:
        actual = re.sub(r'^Re\s+-\s+', '', straat)
        actual = re.sub(r'\s+\d+[,.].*$', '', actual)
        actual = re.sub(r'\s+\d{5,}.*$', '', actual)
        if actual:
            out["Straatnaam"] = actual
            fixes.append(f"Straatnaam: '{straat}' → '{actual}'")
            straat = out["Straatnaam"]

    return entry, fixes


def fix_regio_consistency(entries):
    """Fix Regio inconsistency: for each city, use the most common non-null Regio."""
    # First pass: collect Regio per city
    city_regio_counts = {}
    for entry in entries:
        p = entry["output"].get("PlaatsNaam")
        r = entry["output"].get("Regio")
        if p and r:
            city_regio_counts.setdefault(p, {})
            city_regio_counts[p][r] = city_regio_counts[p].get(r, 0) + 1

    # Determine best Regio per city
    city_best_regio = {}
    for city, regios in city_regio_counts.items():
        best = max(regios, key=regios.get)
        city_best_regio[city] = best

    # Second pass: apply
    fixes_count = 0
    for entry in entries:
        p = entry["output"].get("PlaatsNaam")
        r = entry["output"].get("Regio")
        if p and not r and p in city_best_regio:
            entry["output"]["Regio"] = city_best_regio[p]
            fixes_count += 1

    return fixes_count


def main():
    entries = []
    with open("train.jsonl") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    total_fixes = 0
    all_fixes = []

    for i, entry in enumerate(entries):
        entry, fixes = fix_entry(i + 1, entry)
        if fixes:
            total_fixes += len(fixes)
            for fix in fixes:
                all_fixes.append(f"Line {i+1}: {fix}")

    # Regio consistency
    regio_fixes = fix_regio_consistency(entries)
    total_fixes += regio_fixes
    all_fixes.append(f"Regio consistency: filled {regio_fixes} null Regio values")

    # Write output
    with open("train.jsonl", "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Report
    for fix in all_fixes:
        print(fix)
    print(f"\nTotal fixes applied: {total_fixes}")
    print(f"Total entries: {len(entries)}")


if __name__ == "__main__":
    main()
