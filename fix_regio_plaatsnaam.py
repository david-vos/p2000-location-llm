#!/usr/bin/env python3
"""Fix training data: move city names from Regio to PlaatsNaam, normalize 's-Gravenhage → Den Haag."""

import json

TRAIN_FILE = "train.jsonl"

# These are actual regions/provinces, NOT city names — keep them in Regio
REAL_REGIONS = {
    "Rotterdam-Rijnmond",
    "Zuid-Holland",
    "Noord-Holland",
    "Gelderland",
    "Coördinatiecentrum Rotterdam-Land",
    "Haaglanden",
    "Gelderland Midden",
    "Noord-Holland Noord",
}

# City name normalization
CITY_RENAMES = {
    "'s-Gravenhage": "Den Haag",
}

entries = []
stats = {"regio_to_plaats": 0, "city_renamed": 0, "regio_cleared": 0}

with open(TRAIN_FILE) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        out = entry["output"]

        regio = out.get("Regio")
        plaats = out.get("PlaatsNaam")

        # If Regio is a city name (not a real region)
        if regio and regio not in REAL_REGIONS:
            if not plaats:
                # Move city from Regio → PlaatsNaam
                out["PlaatsNaam"] = regio
                stats["regio_to_plaats"] += 1
            # Clear Regio since it's not a real region
            out["Regio"] = None
            stats["regio_cleared"] += 1

        # Normalize city names in PlaatsNaam
        plaats = out.get("PlaatsNaam")
        if plaats and plaats in CITY_RENAMES:
            out["PlaatsNaam"] = CITY_RENAMES[plaats]
            stats["city_renamed"] += 1

        entries.append(entry)

with open(TRAIN_FILE, "w") as f:
    for entry in entries:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"Processed {len(entries)} entries:")
print(f"  Regio → PlaatsNaam (city moved):  {stats['regio_to_plaats']}")
print(f"  Regio cleared (was city name):     {stats['regio_cleared']}")
print(f"  City renamed ('s-Gravenhage→DH):   {stats['city_renamed']}")
