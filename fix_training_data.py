#!/usr/bin/env python3
"""Fix known systematic errors in train.jsonl."""

import json
import os
import re
import sys

TRAIN_FILES = ["train.jsonl", "train_part2.jsonl"]

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
    "Den Helder",
    "Den Oever",
    "Den Hoorn",
    "Den Hoorn ZH",
    "Loenen aan de Vecht",
    "Broek in Waterland",
    "Koudekerk aan den Rijn",
    "Oost West en Middelbeers",
    "De Kwakel",
    "Hoek van Holland",
    "Ter Aar",
    "Hazerswoude Dorp",
    "Lage Zwaluwe",
]

# Known multi-word city names (for dia:ja fixer to not split them)
KNOWN_CITIES = [
    "Den Helder", "Den Haag", "Den Bosch", "Den Hoorn", "Den Oever",
    "De Lier", "De Koog",
    "Hoorn NH", "Sint Pancras", "Santpoort-Noord", "Santpoort-Zuid",
    "Nieuw-Vennep", "Sint Maartensbrug", "De Goorn", "De Rijp",
    "Nieuw-Amsterdam",
]


def load_abbreviations():
    """Load abbreviation -> place name mapping from abbreviations.jsonl."""
    abbrevs = {}
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abbreviations.jsonl")
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    abbrevs[entry["input"]] = entry["output"]
    except FileNotFoundError:
        pass
    return abbrevs


# Abbreviation -> full place name mapping loaded from abbreviations.jsonl
ABBREV_TO_PLACE = load_abbreviations()

# Province suffixes that should not be PlaatsNaam
PROVINCE_SUFFIXES = {"ZH", "UT", "NH", "NB", "GLD", "OV", "FL", "DR", "FR", "GR", "LB", "ZL"}

# City name -> veiligheidsregio mapping
CITY_TO_VEILIGHEIDSREGIO = {
    # Rotterdam-Rijnmond
    "Rotterdam": "Rotterdam-Rijnmond",
    "Schiedam": "Rotterdam-Rijnmond",
    "Vlaardingen": "Rotterdam-Rijnmond",
    "Maassluis": "Rotterdam-Rijnmond",
    "Capelle aan den IJssel": "Rotterdam-Rijnmond",
    "Krimpen aan den IJssel": "Hollands Midden",
    "Ridderkerk": "Rotterdam-Rijnmond",
    "Barendrecht": "Rotterdam-Rijnmond",
    "Hoogvliet": "Rotterdam-Rijnmond",
    "Spijkenisse": "Rotterdam-Rijnmond",
    "Hellevoetsluis": "Rotterdam-Rijnmond",
    "Brielle": "Rotterdam-Rijnmond",
    "Rozenburg": "Rotterdam-Rijnmond",
    "Poortugaal": "Rotterdam-Rijnmond",
    "Rhoon": "Rotterdam-Rijnmond",
    "Pernis": "Rotterdam-Rijnmond",
    "Europoort": "Rotterdam-Rijnmond",
    "Botlek": "Rotterdam-Rijnmond",
    "Maasvlakte": "Rotterdam-Rijnmond",
    "Vondelingenplaat": "Rotterdam-Rijnmond",
    "Rockanje": "Rotterdam-Rijnmond",
    "Oostvoorne": "Rotterdam-Rijnmond",
    "Geervliet": "Rotterdam-Rijnmond",
    "Hekelingen": "Rotterdam-Rijnmond",
    "Vierpolders": "Rotterdam-Rijnmond",
    "Stellendam": "Rotterdam-Rijnmond",
    "Middelharnis": "Rotterdam-Rijnmond",
    "Sommelsdijk": "Rotterdam-Rijnmond",
    "Dirksland": "Rotterdam-Rijnmond",
    "Melissant": "Rotterdam-Rijnmond",
    "Herkingen": "Rotterdam-Rijnmond",
    "Oude-Tonge": "Rotterdam-Rijnmond",
    "Ouddorp": "Rotterdam-Rijnmond",
    "Heenvliet": "Rotterdam-Rijnmond",
    "Achthuizen": "Rotterdam-Rijnmond",
    "Bergschenhoek": "Rotterdam-Rijnmond",
    "Berkel en Rodenrijs": "Rotterdam-Rijnmond",
    "Bleiswijk": "Rotterdam-Rijnmond",
    "Rotterdam-Albrandswaard": "Rotterdam-Rijnmond",
    # Zuid-Holland Zuid
    "Dordrecht": "Zuid-Holland Zuid",
    "Zwijndrecht": "Zuid-Holland Zuid",
    "Papendrecht": "Zuid-Holland Zuid",
    "Sliedrecht": "Zuid-Holland Zuid",
    "Alblasserdam": "Zuid-Holland Zuid",
    "Hardinxveld-Giessendam": "Zuid-Holland Zuid",
    "Hendrik-Ido-Ambacht": "Zuid-Holland Zuid",
    "Gorinchem": "Zuid-Holland Zuid",
    "Oud-Beijerland": "Zuid-Holland Zuid",
    "Puttershoek": "Zuid-Holland Zuid",
    "'s-Gravendeel": "Zuid-Holland Zuid",
    "Heerjansdam": "Zuid-Holland Zuid",
    "Heinenoord": "Zuid-Holland Zuid",
    "Klaaswaal": "Zuid-Holland Zuid",
    "Piershil": "Zuid-Holland Zuid",
    "Zuid-Beijerland": "Zuid-Holland Zuid",
    "Numansdorp": "Zuid-Holland Zuid",
    "Strijen": "Zuid-Holland Zuid",
    "Werkendam": "Zuid-Holland Zuid",
    "Bleskensgraaf": "Zuid-Holland Zuid",
    "Molenaarsgraaf": "Zuid-Holland Zuid",
    "Wijngaarden": "Zuid-Holland Zuid",
    "Nieuw-Lekkerland": "Zuid-Holland Zuid",
    "Giessenburg": "Zuid-Holland Zuid",
    "Arkel": "Zuid-Holland Zuid",
    "Leerdam": "Zuid-Holland Zuid",
    "Groot-Ammers": "Zuid-Holland Zuid",
    "Ottoland": "Zuid-Holland Zuid",
    "Streefkerk": "Zuid-Holland Zuid",
    "Ameide": "Zuid-Holland Zuid",
    "Lekkerkerk": "Zuid-Holland Zuid",
    "Bergambacht": "Zuid-Holland Zuid",
    "Mijnsheerenland": "Zuid-Holland Zuid",
    "Westmaas": "Zuid-Holland Zuid",
    # Haaglanden
    "Den Haag": "Haaglanden",
    "'s-Gravenhage": "Haaglanden",
    "Rijswijk": "Haaglanden",
    "Voorburg": "Haaglanden",
    "Leidschendam": "Haaglanden",
    "Wassenaar": "Haaglanden",
    "Zoetermeer": "Haaglanden",
    "Delft": "Haaglanden",
    "Pijnacker": "Haaglanden",
    "Nootdorp": "Haaglanden",
    "Delfgauw": "Haaglanden",
    "De Lier": "Haaglanden",
    "Naaldwijk": "Haaglanden",
    "Wateringen": "Haaglanden",
    "Monster": "Haaglanden",
    "Poeldijk": "Haaglanden",
    "Honselersdijk": "Haaglanden",
    "Kwintsheul": "Haaglanden",
    "Maasdijk": "Haaglanden",
    "Maasland": "Haaglanden",
    "Schipluiden": "Haaglanden",
    "Den Hoorn": "Haaglanden",
    "'s-Gravenzande": "Haaglanden",
    "Hoek van Holland": "Haaglanden",
    "Ter Heide": "Haaglanden",
    # Hollands Midden
    "Leiden": "Hollands Midden",
    "Leiderdorp": "Hollands Midden",
    "Alphen aan den Rijn": "Hollands Midden",
    "Gouda": "Hollands Midden",
    "Waddinxveen": "Hollands Midden",
    "Bodegraven": "Hollands Midden",
    "Voorschoten": "Hollands Midden",
    "Noordwijk aan Zee": "Hollands Midden",
    "Katwijk aan Zee": "Hollands Midden",
    "Schoonhoven": "Hollands Midden",
    "Zoeterwoude": "Hollands Midden",
    "Oegstgeest": "Hollands Midden",
    "Stolwijk": "Hollands Midden",
    "Noorden": "Hollands Midden",
    "Ouderkerk aan den IJssel": "Hollands Midden",
    "Voorhout": "Hollands Midden",
    "Zevenhuizen": "Hollands Midden",
    "Hillegom": "Hollands Midden",
    "Roelofarendsveen": "Hollands Midden",
    "Nieuw-Vennep": "Hollands Midden",
    "Lisse": "Hollands Midden",
    "Rijnsburg": "Hollands Midden",
    "Boskoop": "Hollands Midden",
    "Ammerstol": "Hollands Midden",
    "Moerkapelle": "Hollands Midden",
    "Noordwijkerhout": "Hollands Midden",
    "Nieuwerkerk aan den IJssel": "Hollands Midden",
    "Valkenburg": "Hollands Midden",
    "Hazerswoude Dorp": "Hollands Midden",
    "Hazerswoude-Rijndijk": "Hollands Midden",
    "Koudekerk aan den Rijn": "Hollands Midden",
    "Reeuwijk": "Hollands Midden",
    "Nieuwkoop": "Hollands Midden",
    "Nieuwerbrug": "Hollands Midden",
    "Ter Aar": "Hollands Midden",
    "Warmond": "Hollands Midden",
    "Moordrecht": "Hollands Midden",
    "Hoogmade": "Hollands Midden",
    "Woubrugge": "Hollands Midden",
    "Rijpwetering": "Hollands Midden",
    "Benthuizen": "Hollands Midden",
    "Langerak": "Hollands Midden",
    "Leimuiden": "Hollands Midden",
    "Nieuwveen": "Hollands Midden",
    "Beinsdorp": "Hollands Midden",
    "Sassenheim": "Hollands Midden",
    "Vreeland": "Hollands Midden",
    # Amsterdam-Amstelland
    "Amsterdam": "Amsterdam-Amstelland",
    "Amstelveen": "Amsterdam-Amstelland",
    "Diemen": "Amsterdam-Amstelland",
    "Ouderkerk aan de Amstel": "Amsterdam-Amstelland",
    # Kennemerland
    "Haarlem": "Kennemerland",
    "Heemskerk": "Kennemerland",
    "Beverwijk": "Kennemerland",
    "Velsen": "Kennemerland",
    "Bloemendaal": "Kennemerland",
    "Zandvoort": "Kennemerland",
    "Overveen": "Kennemerland",
    # Twente (Hengelo Overijssel - Hengelo Gld uses Gelderland Midden explicitly)
    "Hengelo": "Twente",
    "Enschede": "Twente",
    "Oldenzaal": "Twente",
    "Almelo": "Twente",
    # Coördinatiecentrum Rotterdam-Land
    "Coördinatiecentrum Rotterdam-Land": "Coördinatiecentrum Rotterdam-Land",
}

# Hospital/department/ward keywords to strip from Straatnaam
# These match hospital code + department words, stopping before the street name.
# Street names are detected as multi-word sequences ending with a street suffix.
_STREET_SUFFIXES = r'(?:laan|straat|weg|plein|singel|hof|kade|dijk|pad|dreef|gracht|ring|park|baan|zijde)'
# Known department/ward words that are NOT part of street names
_DEPT_WORDS = r'(?:Cardiochirurgie|Hartbewaking|Neurochirurgie|Neurologie|Interne|geneesk\.|Geneeskunde|Thorax|Chirurgie|SEH|IC|CCU|Dialyse|Vaatheelkunde|Verloskunde|Margriet|Cardiologie|Verlosk\.|kraamafd\.)'

HOSPITAL_PREFIXES_EXACT = {
    # Map: (hospital_code, known_street) -> just_street
    # We handle these with a different approach: find hospital code at start, strip everything before the street name
}

def strip_hospital_prefix(straat):
    """Strip hospital/care facility prefixes from street name, preserving full street name."""
    if not straat:
        return straat, False
    # Match: HOSPITAL_CODE (optional ward code) department_words... StreetName
    # Hospital codes: HZD, HMCW, HMCB, GHZ, LUMC, AZLDP, WelThuis, Politiebureau
    hospital_codes = ['HZD', 'HMCW', 'HMCB', 'GHZ', 'LUMC', 'AZLDP']
    for code in hospital_codes:
        if straat.startswith(code + ' ') or straat.startswith(code + '\t'):
            # Find where the actual street name starts by looking for known street suffixes
            # from right to left, then include preceding title words
            m = re.search(r'(?:^|[ ])((?:(?:van|de|den|het|ter|Charlotte|Simon|Nieuwe|Oude|Lange|Korte|Grote|Kleine|Sint|St\.|Dr\.|Prof\.|Mr\.|Mgr\.)\s+)*\w+' + _STREET_SUFFIXES + r')\b', straat)
            if m:
                return m.group(1).strip(), True
            # Fallback: just remove the hospital code and parenthetical
            cleaned = re.sub(r'^' + re.escape(code) + r'\s+(?:\([^)]*\)\s*)?', '', straat)
            # Remove department words
            cleaned = re.sub(r'^(?:' + _DEPT_WORDS + r'\s+)+', '', cleaned).strip()
            if cleaned != straat:
                return cleaned, True

    # WelThuis FacilityName StreetName
    if straat.startswith('WelThuis '):
        m = re.search(r'(?:^|[ ])((?:(?:van|de|den|het|ter)\s+)*\w+' + _STREET_SUFFIXES + r')\b', straat)
        if m:
            return m.group(1).strip(), True

    # Politiebureau NNN (Location) StreetName
    if straat.startswith('Politiebureau '):
        m = re.search(r'(?:^|[ ])((?:(?:Nieuwe|Oude|Grote|Kleine|van|de|den|het|ter)\s+)*\w+' + _STREET_SUFFIXES + r')\b', straat)
        if m:
            return m.group(1).strip(), True

    return straat, False

# Business/building name patterns to strip from Straatnaam
BUILDING_PREFIXES = [
    r'Zwembad\s+[\w\s]+?(?=\b\w+(?:laan|straat|weg|plein|singel|hof|kade|dijk|pad|dreef|gracht|ring|park)\b)',
    r'(?:Grain Plastics|Rijk Zwaan Zaadhandel)\s+BV\s+',
    r'(?:Dirk van den Broek|Supermarkt Jumbo|PLUS van Dijk|Jysk|Els Van Brilmode)\s+',
    r'ROC Midden-Nederland\s+',
    r'Basisschool\s+[\w\s]+?(?=\b\w+(?:straat|weg|laan|plein)\b)',
]


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
    if plaats and (" : " in plaats or re.match(r'.*[A-Z]{4,}\s*:', plaats)):
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

    # --- Fix 5b: ABBREV + "Directe inzet" in PlaatsNaam (no colon) ---
    plaats = out.get("PlaatsNaam")
    if plaats and re.search(r'[A-Z]{4,}\s+Directe inzet', plaats):
        m = re.match(r'(.*?)\s*([A-Z]{4,})\s+Directe inzet', plaats)
        if m:
            street_part = m.group(1).strip()
            abbrev = m.group(2)
            if abbrev in ABBREV_TO_PLACE:
                out["PlaatsNaam"] = ABBREV_TO_PLACE[abbrev]
            else:
                out["PlaatsNaam"] = None
            if street_part and not out.get("Straatnaam"):
                out["Straatnaam"] = street_part
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
    if straat and re.match(r'^(?:AMBU\s+)?\d{5}\s+', straat):
        out["Straatnaam"] = re.sub(r'^(?:AMBU\s+)?\d{5}\s+', '', straat)
        changed = True

    # --- Fix 10: "HA 's-Gravensant..." in Straatnaam — remove HA prefix ---
    straat = out.get("Straatnaam")
    if straat and straat.startswith("HA "):
        out["Straatnaam"] = straat[3:]
        changed = True

    # --- Fix 11: PlaatsNaam contains long descriptive text ---
    plaats = out.get("PlaatsNaam")
    if plaats and len(plaats.split()) > 3 and not any(city in plaats for city in MULTI_WORD_CITIES):
        # Likely raw text dumped in. Try to extract city properly.
        cleaned = plaats

        # Strip parenthetical prefixes: (VWS), (DIA), (AED), (MMT), (Inzet AED), etc.
        cleaned = re.sub(r'^\([^)]*\)\s*', '', cleaned)
        # Strip leading 5-digit unit numbers (can be multiple)
        cleaned = re.sub(r'^(?:\d{5}\s+)+', '', cleaned)
        # Strip "regio NN" suffix
        cleaned = re.sub(r'\s+regio\s+\d+$', '', cleaned)
        # Strip trailing km markers like "148,3"
        cleaned = re.sub(r'\s+\d+[,.]\d+$', '', cleaned)
        # Strip known dispatch descriptions
        cleaned = re.sub(r'^(?:Reanimatie|HV weg (?:letsel|materieel)|BR Woning|EINDE VWS|VWS|BST)\s+', '', cleaned)
        # Strip highway info like "A2 Li - Bs." or "A10 Li - Ringweg-Zuid 17,1"
        cleaned = re.sub(r'^[AN]\d{1,3}\s+(?:Li|Re|Ri)\s*(?:-\s*(?:Kp\s+|Bs\.\s+)?)?(?:\S+\s+)*?(?=\S+\s*$)', '', cleaned)

        # Now try to find a known city in what remains
        found_city = None

        # Check for known multi-word cities first
        for city in MULTI_WORD_CITIES:
            if cleaned.endswith(city):
                found_city = city
                break

        # Check all known abbreviation-resolved cities
        if not found_city:
            for abbrev_city in sorted(ABBREV_TO_PLACE.values(), key=len, reverse=True):
                if cleaned.endswith(abbrev_city):
                    found_city = abbrev_city
                    break

        # Check for abbreviation codes in the text and resolve them
        if not found_city:
            abbrev_match = re.search(r'\b([A-Z]{4,})\b', cleaned)
            if abbrev_match and abbrev_match.group(1) in ABBREV_TO_PLACE:
                found_city = ABBREV_TO_PLACE[abbrev_match.group(1)]

        if found_city:
            # Extract street name: everything before the city (minus partial postcode)
            if cleaned.endswith(found_city):
                before_city = cleaned[:-(len(found_city))].strip()
            else:
                before_city = cleaned
            # Strip trailing 4-digit partial postcode
            before_city = re.sub(r'\s*\d{4}$', '', before_city).strip()
            # Strip remaining unit numbers/codes
            before_city = re.sub(r'^\d+\s+', '', before_city).strip()
            before_city = re.sub(r'^Brug\d+\s*', '', before_city).strip()

            out["PlaatsNaam"] = found_city
            if before_city and not out.get("Straatnaam"):
                out["Straatnaam"] = before_city
            changed = True
        else:
            # Fallback: last word if it looks like a city name (capitalized, >2 chars, not a number/code)
            words = cleaned.split()
            # Filter out dispatch terms and codes
            dispatch_terms = {"Directe", "inzet", "Rit", "regio", "BST", "NWD", "Brug0465"}
            last_word = None
            for w in reversed(words):
                if (w[0].isupper() and len(w) > 2 and not re.match(r'^\d', w)
                        and w not in dispatch_terms and not re.match(r'^[A-Z]{4,}$', w)):
                    last_word = w
                    break
            if last_word and last_word != plaats:
                out["PlaatsNaam"] = last_word
                changed = True

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

    # --- Fix 19: "ICnum" junk in Straatnaam (e.g. "Industrieweg Krimpen aan den IJss ICnum") ---
    straat = out.get("Straatnaam")
    if straat and "ICnum" in straat:
        cleaned = re.sub(r'\s*ICnum.*$', '', straat).strip()
        # The cleaned string may have "StreetName CityName" — strip city if it matches PlaatsNaam
        plaats = out.get("PlaatsNaam")
        if plaats and cleaned.endswith(" " + plaats):
            cleaned = cleaned[:-(len(plaats) + 1)].strip()
        out["Straatnaam"] = cleaned if cleaned else None
        changed = True

    # --- Fix 20: "Prio N" prefix in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^Prio\s+\d\s+', straat):
        out["Straatnaam"] = re.sub(r'^Prio\s+\d\s+', '', straat).strip() or None
        changed = True

    # --- Fix 21: Incident description in Straatnaam ("BR woning", "BR wegvervoer", "stof ...") ---
    straat = out.get("Straatnaam")
    if straat:
        # "BR woning (stuff) StreetName" or "BR woning StreetName"
        m = re.match(r'^BR\s+(?:woning|bovenwoning|industrie|wegvervoer)\b(?:\s*\([^)]*\))*\s+(.+)$', straat)
        if m:
            out["Straatnaam"] = m.group(1).strip()
            changed = True
        # "stof Xxx Yyy StreetName" — from "gev. stof" incident type
        elif straat.startswith("stof "):
            # Find street name by looking for common street suffixes and including
            # preceding title/preposition words (Burgemeester van Stamplein)
            m2 = re.search(r'((?:(?:Burgemeester|Prins|Prinses|Koning|Koningin|President|Professor|Dokter|Dominee|Graaf|Baron)\s+)?(?:(?:van|de|den|het|ter|ten)\s+)*\w+(?:straat|weg|laan|plein|singel|hof|kade|dijk|pad|dreef|gracht|ring|park))\b', straat, re.IGNORECASE)
            if m2:
                out["Straatnaam"] = m2.group(1).strip()
                changed = True
        # "BR) BR woning ..." from partial parse
        elif re.match(r'^BR\)\s+BR\s+', straat):
            m3 = re.match(r'^BR\)\s+BR\s+\w+(?:\s*\([^)]*\))*\s+(.+)$', straat)
            if m3:
                out["Straatnaam"] = m3.group(1).strip()
                changed = True

    # --- Fix 22: Straatnaam is just "Rit" (bad parse from "Rit NNNNN") ---
    straat = out.get("Straatnaam")
    if straat and straat == "Rit":
        out["Straatnaam"] = None
        changed = True

    # --- Fix 23: Road number in Straatnaam but wegnummer is null ---
    straat = out.get("Straatnaam")
    wegnummer = out.get("wegnummer")
    if straat and not wegnummer:
        # Match "A16 Li - Kp Terbregseplein" or "N213 Li - Nieuweweg 9,7" or "A4 Li 59,8"
        m = re.match(r'^(?:.*?\s)?([AN]\d{1,3})\s+(?:Li|Re|Ri)\b(?:\s*-\s*(?:Kp\s+)?)?(.*)$', straat)
        if m:
            out["wegnummer"] = m.group(1)
            remainder = m.group(2).strip()
            # Remove km markers like "59,8" or "9,7" and trailing place names
            remainder = re.sub(r'^\d+[,.]\d+\s*', '', remainder).strip()
            # Remove trailing place name if it matches PlaatsNaam
            plaats = out.get("PlaatsNaam")
            if plaats and remainder.endswith(plaats):
                remainder = remainder[:-(len(plaats))].strip()
            # Remove trailing "d", "a", "u" direction suffixes
            remainder = re.sub(r'\s+[dau]$', '', remainder).strip()
            # Remove trailing km markers
            remainder = re.sub(r'\s+\d+[,.]\d+$', '', remainder).strip()
            out["Straatnaam"] = remainder if remainder else None
            changed = True
        # Also match standalone "A4 Li 59,8" without direction separator
        elif re.match(r'^([AN]\d{1,3})\s+(?:Li|Re|Ri)\s+\d', straat):
            m2 = re.match(r'^([AN]\d{1,3})\s+(?:Li|Re|Ri)\s+(.*)', straat)
            if m2:
                out["wegnummer"] = m2.group(1)
                remainder = re.sub(r'^\d+[,.]\d+\s*', '', m2.group(2)).strip()
                out["Straatnaam"] = remainder if remainder else None
                changed = True
        # "N478 - Veerweg" without Li/Re
        elif re.match(r'^([AN]\d{1,3})\s+-\s+(.+)$', straat):
            m3 = re.match(r'^([AN]\d{1,3})\s+-\s+(.+)$', straat)
            out["wegnummer"] = m3.group(1)
            out["Straatnaam"] = m3.group(2).strip()
            changed = True
        # "Toerit A44 Li - ..." or "Afrit A4 Li - ..."
        elif re.match(r'^(?:Toerit|Afrit)\s+([AN]\d{1,3})\s+', straat):
            m4 = re.match(r'^(?:Toerit|Afrit)\s+([AN]\d{1,3})\s+(?:Li|Re|Ri)\b(?:\s*-\s*)?(.*)$', straat)
            if m4:
                out["wegnummer"] = m4.group(1)
                remainder = m4.group(2).strip()
                remainder = re.sub(r'\s+\d+[,.]\d+(?:\s+[dau])?$', '', remainder).strip()
                out["Straatnaam"] = remainder if remainder else None
                changed = True
        # "N57 30,9 Ouddorp ZH" - road number followed by km
        elif re.match(r'^([AN]\d{1,3})\s+\d+[,.]\d+\s*', straat):
            m5 = re.match(r'^([AN]\d{1,3})\s+\d+[,.]\d+\s*(.*)', straat)
            if m5:
                out["wegnummer"] = m5.group(1)
                remainder = m5.group(2).strip()
                # Remove province suffixes
                remainder = re.sub(r'\s+(ZH|NH|UT|NB|GLD)$', '', remainder).strip()
                # Remove place name if matches PlaatsNaam
                plaats = out.get("PlaatsNaam")
                if plaats and remainder == plaats:
                    remainder = ""
                out["Straatnaam"] = remainder if remainder else None
                changed = True

    # --- Fix 24: "Gebroeders" stripped from street name ---
    straat = out.get("Straatnaam")
    if straat and "Gebroeders" not in straat:
        if re.search(r'\bGebroeders\s+' + re.escape(straat) + r'\b', inp):
            out["Straatnaam"] = "Gebroeders " + straat
            changed = True

    # --- Fix 25: "Mr." stripped from street name ---
    straat = out.get("Straatnaam")
    if straat and not straat.startswith("Mr."):
        if re.search(r'\bMr\.\s+' + re.escape(straat), inp):
            out["Straatnaam"] = "Mr. " + straat
            changed = True

    # --- Fix 26: Highway junk in Straatnaam (BST, NWD, A0, AAZ prefixes from dispatch) ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^(?:BST|NWD)\s+', straat):
        cleaned = re.sub(r'^(?:BST|NWD)\s+', '', straat)
        # Remove further dispatch codes like "A0", "A4", "AAZ"
        cleaned = re.sub(r'^(?:A\d|AAZ|chir/\s*ortho/\s*uro)\s+', '', cleaned).strip()
        out["Straatnaam"] = cleaned if cleaned else None
        changed = True

    # --- Fix 27: "N206 Transferium" prefix in Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^([AN]\d{1,3})\s+Transferium\s+(.+)$', straat):
        m = re.match(r'^([AN]\d{1,3})\s+Transferium\s+(.+)$', straat)
        out["wegnummer"] = m.group(1)
        out["Straatnaam"] = m.group(2).strip()
        changed = True

    # --- Fix 28: "Rotterdam ICnum" or "Dordrecht ICnum" pattern left after Fix 19 cleanup ---
    straat = out.get("Straatnaam")
    if straat and re.search(r'\bRotterdam$|\bDordrecht$|\bSliedrecht$', straat):
        plaats = out.get("PlaatsNaam")
        for city in ["Rotterdam", "Dordrecht", "Sliedrecht", "Vlaardingen", "Oostvoorne",
                      "Bleskensgraaf", "Hoogvliet", "Ouddorp"]:
            if straat.endswith(" " + city):
                if not plaats:
                    out["PlaatsNaam"] = city
                out["Straatnaam"] = straat[:-(len(city) + 1)].strip() or None
                changed = True
                break

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

    # --- Fix 34: Re/Li direction markers in Straatnaam ---
    straat = out.get("Straatnaam")
    wegnummer = out.get("wegnummer")
    if straat:
        # "Re 47,4" or "Li 53,6" or "Li" or "Re Beesd" (direction + km or city)
        if re.match(r'^(?:Re|Li)\b', straat):
            # If it's just "Re/Li" + optional km marker, clear it
            if re.match(r'^(?:Re|Li)(?:\s+\d+[,.]\d+)?$', straat):
                out["Straatnaam"] = None
                changed = True
            # "Re CityName" — city leaked into straat
            elif re.match(r'^(?:Re|Li)\s+[A-Z]', straat):
                city_part = re.sub(r'^(?:Re|Li)\s+', '', straat)
                if not out.get("PlaatsNaam"):
                    out["PlaatsNaam"] = city_part
                out["Straatnaam"] = None
                changed = True
        # "Re - Ring Parkstad" or "Li - Ring Parkstad 5,0" — road name after direction
        elif re.match(r'^(?:Re|Li)\s*-\s+', straat):
            out["Straatnaam"] = None
            changed = True
        # "A2 Li 163,4" — road number + direction in Straatnaam (wegnummer already set)
        elif wegnummer and re.match(r'^' + re.escape(wegnummer) + r'\s+(?:Re|Li)\b', straat):
            out["Straatnaam"] = None
            changed = True
        # "A59 Re - Linkermaasoeverweg" — strip road+direction prefix, keep street name
        elif re.match(r'^[AN]\d{1,3}\s+(?:Re|Li)\s*-\s+', straat):
            m = re.match(r'^([AN]\d{1,3})\s+(?:Re|Li)\s*-\s+(.+)$', straat)
            if m:
                if not wegnummer:
                    out["wegnummer"] = m.group(1)
                remainder = m.group(2).strip()
                # Remove km markers
                remainder = re.sub(r'\s+\d+[,.]\d+$', '', remainder).strip()
                out["Straatnaam"] = remainder if remainder else None
                changed = True

    # --- Fix 35: Province suffix in PlaatsNaam (e.g. "Vianen UT", "Katwijk NB") ---
    plaats = out.get("PlaatsNaam")
    if plaats:
        parts = plaats.rsplit(' ', 1)
        if len(parts) == 2 and parts[1] in PROVINCE_SUFFIXES:
            out["PlaatsNaam"] = parts[0]
            changed = True

    # --- Fix 36: Incomplete postcode (4 digits without letters) ---
    postcode = out.get("postcode")
    if postcode and re.match(r'^\d{4}$', postcode):
        out["postcode"] = None
        changed = True

    # --- Fix 37: "Post CityName / Street" or "Post CityName Street" standby location ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^Post\s+\w+', straat):
        # "Post Zoetermeer / Blauw-roodlaan" -> "Blauw-roodlaan"
        m = re.match(r'^Post\s+\S+\s*/\s*(.+)$', straat)
        if m:
            out["Straatnaam"] = m.group(1).strip()
            changed = True

    # --- Fix 38: Incident code patterns in Straatnaam (e.g. "BOB-KAZ-435 Klooster ...") ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^[A-Z]+-[A-Z]+-\d+\s+', straat):
        # Remove incident code and facility name, find street by suffix
        m = re.search(r'(\b\w+(?:dreef|laan|straat|weg|plein|singel|hof|kade|dijk|pad|gracht|ring|park|baan|markt)\b)', straat, re.IGNORECASE)
        if m:
            out["Straatnaam"] = m.group(1)
            # Extract city: text after the street name
            after = straat[m.end():].strip()
            if after and not out.get("PlaatsNaam"):
                out["PlaatsNaam"] = after.split()[0] if after.split() else None
            changed = True

    # --- Fix 39: "Rit NNNNN regio" junk as Straatnaam ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^Rit\s+\d+', straat):
        out["Straatnaam"] = None
        changed = True

    # --- Fix 29: Normalize 's-Gravenhage -> Den Haag ---
    plaats = out.get("PlaatsNaam")
    if plaats == "'s-Gravenhage":
        out["PlaatsNaam"] = "Den Haag"
        changed = True

    # --- Fix 30: Map Regio city names to veiligheidsregio names ---
    regio = out.get("Regio")
    if regio and regio in CITY_TO_VEILIGHEIDSREGIO:
        # If PlaatsNaam is null, Regio was serving as a city fallback — rescue it
        if not out.get("PlaatsNaam"):
            out["PlaatsNaam"] = regio
        out["Regio"] = CITY_TO_VEILIGHEIDSREGIO[regio]
        changed = True

    # --- Fix 31: Strip hospital/department names from Straatnaam ---
    straat = out.get("Straatnaam")
    if straat:
        new_straat, did_strip = strip_hospital_prefix(straat)
        if did_strip:
            # Also remove trailing info like "(medium care)" or "(couveuse RAV)"
            new_straat = re.sub(r'\s*\([^)]*\)\s*$', '', new_straat).strip()
            out["Straatnaam"] = new_straat if new_straat else None
            changed = True

    # --- Fix 32: Strip business/building names from Straatnaam ---
    straat = out.get("Straatnaam")
    if straat:
        for pattern in BUILDING_PREFIXES:
            new_straat = re.sub(pattern, '', straat).strip()
            if new_straat != straat:
                out["Straatnaam"] = new_straat if new_straat else None
                straat = new_straat
                changed = True

    # --- Fix 33: Remove "Platformzijde" and similar suffixes from Straatnaam ---
    straat = out.get("Straatnaam")
    if straat:
        new_straat = re.sub(r'\s+Platformzijde$', '', straat).strip()
        if new_straat != straat:
            out["Straatnaam"] = new_straat if new_straat else None
            changed = True

    # --- Fix 33b: Strip parenthetical fragments from start of Straatnaam (e.g. "openen) Sluitersveldssingel") ---
    straat = out.get("Straatnaam")
    if straat and re.match(r'^[a-z]+\)\s+', straat):
        new_straat = re.sub(r'^[a-z]+\)\s+', '', straat).strip()
        if new_straat:
            out["Straatnaam"] = new_straat
            changed = True

    # --- Fix 33c: Fix "Geneeskunde Charlotte Jacobsla/aa/an" -> "Charlotte Jacobslaan" (department prefix + truncated street) ---
    straat = out.get("Straatnaam")
    if straat and "Charlotte Jacobsla" in straat and "Geneeskunde" in straat:
        out["Straatnaam"] = "Charlotte Jacobslaan"
        changed = True

    # --- Fix 34: Fill Regio from PlaatsNaam when null (fix conflicting patterns) ---
    # When we have a known city but Regio is null, infer it from city->region mapping.
    # This fixes inconsistency where e.g. Rotterdam sometimes had Regio null, sometimes Rotterdam-Rijnmond.
    plaats = out.get("PlaatsNaam")
    regio = out.get("Regio")
    if plaats and not regio and plaats in CITY_TO_VEILIGHEIDSREGIO:
        out["Regio"] = CITY_TO_VEILIGHEIDSREGIO[plaats]
        changed = True

    return entry, changed


def process_file(train_file):
    try:
        with open(train_file) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return

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
                    print(f"{train_file} Line {i+1}:")
                    print(f"  BEFORE: {original}")
                    print(f"  AFTER:  {new_line}")
                    print()
            new_lines.append(new_line + "\n")
        else:
            new_lines.append(line + "\n")

    if "--dry-run" in sys.argv:
        print(f"Would fix {fixed_count} entries in {train_file}.")
    else:
        with open(train_file, "w") as f:
            f.writelines(new_lines)
        print(f"Fixed {fixed_count} entries in {train_file}.")


def main():
    for train_file in TRAIN_FILES:
        process_file(train_file)


if __name__ == "__main__":
    main()
