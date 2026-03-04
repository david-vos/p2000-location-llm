#!/usr/bin/env python3
"""Fix known systematic errors in train.jsonl."""

import json
import re
import sys

TRAIN_FILE = "train.jsonl"

# Multi-word city names that get split incorrectly
MULTI_WORD_CITIES = [
    "Capelle aan den IJssel",
    "Krimpen aan den IJssel",
    "Ouderkerk aan den IJssel",
    "Nieuwerkerk aan den IJssel",
    "Ouderkerk aan de Amstel",
    "Berkel en Rodenrijs",
    "Bergen op Zoom",
    "Alphen aan den Rijn",
    "Hoogvliet Rotterdam",
    "Krimpen aan de Lek",
    "Koog aan de Zaan",
    "Nieuwer Ter Aa",
    "Ter Apel",
]

# Known multi-word city names (for dia:ja fixer to not split them)
KNOWN_CITIES = [
    "Den Helder", "Den Haag", "Den Bosch", "De Lier", "De Koog",
    "Hoorn NH", "Sint Pancras", "Santpoort-Noord", "Santpoort-Zuid",
    "Nieuw-Vennep", "Sint Maartensbrug", "De Goorn", "De Rijp",
    "Nieuw-Amsterdam",
]

# Abbreviation -> full place name mapping for REGIO codes
ABBREV_TO_PLACE = {
    "SGRAVZ": "'s-Gravenzande",
    "SGRAVH": "'s-Gravenhage",
    "VOORB": "Voorburg",
    "LISSE": "Lisse",
    "NDWKHT": "Noordwijkerhout",
    "HILLGM": "Hillegom",
    "NDWKZH": "Noordwijk",
    "CAPIJS": "Capelle aan den IJssel",
}

# Province suffixes that should not be PlaatsNaam
PROVINCE_SUFFIXES = {"ZH", "UT", "NH", "NB", "GLD", "OV", "FL", "DR", "FR", "GR", "LB", "ZL"}


def fix_entry(lineno, entry):
    inp = entry.get("input", "")
    out = entry.get("output", {})
    straat = out.get("Straatnaam")
    plaats = out.get("PlaatsNaam")
    wegnummer = out.get("wegnummer")
    postcode = out.get("postcode")
    regio = out.get("Regio")
    changed = False

    # --- Fix 1: "(dia: ja) NNNNN" or "(Inzet AED) NNNNN" in PlaatsNaam ---
    if plaats and re.match(r'^\(.*?\)\s*\d+$', plaats):
        # Extract the actual city from the input - usually the last word(s) before end
        # Pattern: ... StreetName CityName
        # Try to find city from input by removing known prefixes
        cleaned = re.sub(r'^A[12]\s+', '', inp)
        cleaned = re.sub(r'\(dia:\s*ja\)\s*', '', cleaned)
        cleaned = re.sub(r'\(Inzet AED\)\s*', '', cleaned)
        cleaned = re.sub(r'\d+\s+Rit\s+\d+\s*', '', cleaned)
        # Remove business/location prefixes like "Autobedrijf Heijne"
        # What remains should be street + city
        parts = cleaned.strip().split()
        if len(parts) >= 2:
            # Last word is likely the city
            out["PlaatsNaam"] = parts[-1]
            out["Straatnaam"] = " ".join(parts[:-1]) if len(parts) > 1 else None
            # If straatnaam looks like a business name, keep it
            changed = True
        elif len(parts) == 1:
            out["PlaatsNaam"] = parts[0]
            out["Straatnaam"] = None
            changed = True

    # --- Fix 2: Multi-word cities split across Straatnaam and PlaatsNaam ---
    if straat and plaats:
        for city in MULTI_WORD_CITIES:
            city_parts = city.split()
            # Check if PlaatsNaam is the last word of a multi-word city
            # and Straatnaam ends with the rest
            if plaats == city_parts[-1]:
                prefix = " ".join(city_parts[:-1])
                if straat.endswith(prefix):
                    real_straat = straat[:-(len(prefix))].strip()
                    # Extract postcode from street if present
                    pc_match = re.search(r'\b(\d{4}[A-Z]{2})\b', real_straat)
                    if pc_match:
                        out["postcode"] = pc_match.group(1)
                        real_straat = real_straat.replace(pc_match.group(1), "").strip()
                    out["Straatnaam"] = real_straat if real_straat else None
                    out["PlaatsNaam"] = city
                    changed = True
                    break

    # --- Fix 3: Province suffix (ZH, UT, NH) as PlaatsNaam ---
    plaats = out.get("PlaatsNaam")
    straat = out.get("Straatnaam")
    if plaats in PROVINCE_SUFFIXES and straat:
        # The actual city is at the end of straatnaam
        parts = straat.split()
        if len(parts) >= 2:
            out["PlaatsNaam"] = parts[-1]
            out["Straatnaam"] = " ".join(parts[:-1])
            # Extract postcode if present
            pc_match = re.search(r'\b(\d{4}[A-Z]{2})\b', out["Straatnaam"])
            if pc_match:
                out["postcode"] = pc_match.group(1)
                out["Straatnaam"] = out["Straatnaam"].replace(pc_match.group(1), "").strip()
            changed = True

    # --- Fix 4: "VWS" prefix in PlaatsNaam ---
    plaats = out.get("PlaatsNaam")
    if plaats and plaats.startswith("VWS "):
        out["PlaatsNaam"] = plaats[4:].strip()
        changed = True

    # --- Fix 5: Raw text dumped into PlaatsNaam (contains abbreviation codes like "LISSE :") ---
    plaats = out.get("PlaatsNaam")
    if plaats and " : " in plaats or (plaats and re.match(r'.*[A-Z]{4,}\s*:', plaats)):
        # Try to parse: "Straatnaam ABBREV :"
        m = re.match(r'(\S+(?:\s+\S+)*?)\s+([A-Z]{4,})\s*:', plaats)
        if m:
            out["Straatnaam"] = m.group(1)
            abbrev = m.group(2)
            if abbrev in ABBREV_TO_PLACE:
                out["PlaatsNaam"] = ABBREV_TO_PLACE[abbrev]
            else:
                out["PlaatsNaam"] = None
            changed = True

    # --- Fix 6: DP prefix in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^DP\d+\s+\S+', straat):
        # Remove "DPn CityName" prefix
        m = re.match(r'^DP\d+\s+\S+(?:\s+\S+)*?\s+(.+)$', straat)
        if m:
            # Heuristic: the DP prefix is "DPn PlaceName", then the street follows
            # Try: remove "DPn Word" or "DPn Word-Word"
            m2 = re.match(r'^DP\d+\s+[\w-]+\s+(.+)$', straat)
            if m2:
                out["Straatnaam"] = m2.group(1)
                changed = True

    # --- Fix 7: "Ambulancepost Xxx" prefix in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and straat.startswith("Ambulancepost "):
        # Remove "Ambulancepost CityName" prefix
        m = re.match(r'^Ambulancepost\s+[\w-]+\s+(.+)$', straat)
        if m:
            out["Straatnaam"] = m.group(1)
            changed = True

    # --- Fix 8: Parenthetical prefixes in Straatnaam like (binnen), (buiten), (bg) ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^\(.*?\)\s+', straat):
        # Remove leading (...) prefix like "(binnen)", "(buiten)", "(bg) SEH"
        cleaned = re.sub(r'^\(.*?\)\s+', '', straat)
        # Also remove department names like "SEH ", "High Care ", "Verlosk. en kraamafd. "
        cleaned = re.sub(r'^(SEH|High Care|Verlosk\.\s+en\s+kraamafd\.)\s+', '', cleaned)
        # If PlaatsNaam is null, try to extract city and remove trailing 6-digit codes
        if not out.get("PlaatsNaam"):
            # Remove trailing 6-digit unit codes
            cleaned = re.sub(r'\s+\d{6}(?:\s+\d{6})*\s*$', '', cleaned)
            # Try to split into street + city (last word is usually the city)
            parts = cleaned.rsplit(' ', 1)
            if len(parts) == 2 and parts[1][0].isupper() and len(parts[1]) > 2:
                out["Straatnaam"] = parts[0]
                out["PlaatsNaam"] = parts[1]
            else:
                out["Straatnaam"] = cleaned
        else:
            out["Straatnaam"] = cleaned
        if out["Straatnaam"] != straat:
            changed = True

    # --- Fix 9: AMBU number prefix in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^\d{5}\s+', straat):
        out["Straatnaam"] = re.sub(r'^\d{5}\s+', '', straat)
        changed = True

    # --- Fix 10: "HA 's-Gravensant..." in Straatnaam — remove HA prefix ---
    straat = out.get("Straatnaam")
    if straat and straat.startswith("HA "):
        out["Straatnaam"] = straat[3:]
        changed = True

    # --- Fix 11: PlaatsNaam contains long descriptive text ---
    plaats = out.get("PlaatsNaam")
    if plaats and len(plaats.split()) > 3 and not any(city in plaats for city in MULTI_WORD_CITIES):
        # Likely raw text dumped in. Try to extract city (last word-like token)
        # Only fix if it clearly contains non-city text
        patterns = [
            r'(?:Reanimatie|HV weg letsel|BR Woning|EINDE VWS|VWS)\s+(.+?)(?:\s+\d+[,\.]\d+)?$',
            r'(\w+(?:\s+\w+)?)\s*$',  # fallback: last 1-2 words
        ]
        for pat in patterns:
            m = re.search(pat, plaats)
            if m:
                out["PlaatsNaam"] = m.group(1).strip()
                changed = True
                break

    # --- Fix 12: ID-like values in PlaatsNaam (pure numbers, codes like "01-29-048", "12mc149") ---
    plaats = out.get("PlaatsNaam")
    if plaats and re.match(r'^[\d][\d\w\-\.]+$', plaats):
        # Starts with digit and contains only digits/letters/dashes — not a place name
        out["PlaatsNaam"] = None
        changed = True

    # --- Fix 13: False wegnummer A1/A2/A0/B1/B2 (priority codes, not roads) ---
    wegnummer = out.get("wegnummer")
    if wegnummer in ("A1", "A2", "A0", "B1", "B2"):
        # Real A1/A2 roads have Li/Re/Ri (direction marker)
        if not re.search(r'\b' + re.escape(wegnummer) + r'\s+(?:Li|Re|Ri)\b', inp):
            out["wegnummer"] = None
            changed = True

    # --- Fix 14: Postcode embedded in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat:
        pc_in_straat = re.search(r'\s+(\d{4}[A-Z]{2})\s+', straat)
        if not pc_in_straat:
            pc_in_straat = re.search(r'\s+(\d{4}[A-Z]{2})$', straat)
        if pc_in_straat:
            pc = pc_in_straat.group(1)
            if not out.get("postcode"):
                out["postcode"] = pc
            # Remove postcode and everything after it (city name that got merged in)
            idx = straat.index(pc)
            out["Straatnaam"] = straat[:idx].strip() or None
            # The text after the postcode is likely the city
            after_pc = straat[idx + len(pc):].strip()
            if after_pc and not out.get("PlaatsNaam"):
                out["PlaatsNaam"] = after_pc
            changed = True

    # --- Fix 15: VWS prefix in Straatnaam (e.g. "VWS Schagen Lagedijkerweg" -> "Lagedijkerweg") ---
    straat = out.get("Straatnaam")
    plaats = out.get("PlaatsNaam")
    if straat and straat.startswith("VWS "):
        rest = straat[4:]
        # Pattern: "VWS CityName StreetName" — strip VWS and city if it matches PlaatsNaam
        if plaats and rest.startswith(plaats + " "):
            out["Straatnaam"] = rest[len(plaats) + 1:]
        elif plaats:
            # VWS followed by something else then the street
            # Try to remove "VWS Word" where Word is a city/dispatch name
            m = re.match(r'^[\w-]+\s+(.+)$', rest)
            if m:
                out["Straatnaam"] = m.group(1)
            else:
                out["Straatnaam"] = rest
        else:
            out["Straatnaam"] = rest
        changed = True

    # --- Fix 16: PlaatsNaam duplicated at end of Straatnaam ---
    straat = out.get("Straatnaam")
    plaats = out.get("PlaatsNaam")
    if straat and plaats and straat.endswith(" " + plaats):
        cleaned = straat[:-(len(plaats) + 1)].strip()
        # Also strip trailing dispatch codes like "ICnum", "SPIJKN", etc.
        cleaned = re.sub(r'\s+[A-Z]{4,}$', '', cleaned).strip()
        out["Straatnaam"] = cleaned if cleaned else None
        changed = True

    # --- Fix 17: Trailing 5-6 digit unit codes in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and re.search(r'\s+\d{5,}(?:\s+\d{5,})*\s*$', straat):
        out["Straatnaam"] = re.sub(r'\s+\d{5,}(?:\s+\d{5,})*\s*$', '', straat).strip() or None
        changed = True

    # --- Fix 18: Descriptive text dumped into Straatnaam (contains known non-street keywords) ---
    straat = out.get("Straatnaam")
    if straat and re.search(r'\b(gezondheidszorg|Woongemeenschap|Penitentiaire|Inrichting)\b', straat):
        # Try to extract a real street name from the input
        m = re.search(r'(\b[A-Z][\w-]*(?:laan|straat|weg|plein|singel|hof|kade|dijk|brug|markt|pad|dreef|gracht|steeg|ring|veld|park|bos|oord|dal|veld)\b)', inp, re.IGNORECASE)
        if m:
            out["Straatnaam"] = m.group(1)
        else:
            out["Straatnaam"] = None
        changed = True

    return entry, changed


def main():
    with open(TRAIN_FILE) as f:
        lines = f.readlines()

    fixed_count = 0
    new_lines = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            new_lines.append(line + "\n")
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            new_lines.append(line + "\n")
            continue

        original = json.dumps(entry, ensure_ascii=False)
        entry, changed = fix_entry(i + 1, entry)

        if changed:
            new_line = json.dumps(entry, ensure_ascii=False)
            if new_line != original:
                fixed_count += 1
                if "--dry-run" in sys.argv:
                    print(f"Line {i+1}:")
                    print(f"  BEFORE: {original}")
                    print(f"  AFTER:  {new_line}")
                    print()
            new_lines.append(new_line + "\n")
        else:
            new_lines.append(line + "\n")

    if "--dry-run" in sys.argv:
        print(f"Would fix {fixed_count} entries.")
    else:
        with open(TRAIN_FILE, "w") as f:
            f.writelines(new_lines)
        print(f"Fixed {fixed_count} entries in {TRAIN_FILE}.")


if __name__ == "__main__":
    main()
