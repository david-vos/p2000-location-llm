#!/usr/bin/env python3
"""Fix training data quality: VWS labels, dedup Rit entries, add weak pattern examples."""

import json
import re

INPUT = "train.jsonl"
OUTPUT = "train.jsonl"


def fix_vws_straatnaam(entry):
    """Strip VWS prefix and location name from Straatnaam."""
    output = entry["output"]
    straat = output.get("Straatnaam")
    if not straat or not straat.startswith("VWS"):
        return entry

    plaats = output.get("PlaatsNaam", "")
    wegnummer = output.get("wegnummer")

    cleaned = straat[4:]  # Remove "VWS "

    if wegnummer and cleaned.startswith(wegnummer):
        cleaned = cleaned[len(wegnummer):].strip()

    # Remove place name prefix if present
    if plaats and cleaned.startswith(plaats):
        cleaned = cleaned[len(plaats):].strip()

    # Handle specific known patterns
    if cleaned == "Hofvijver Buitenhof":
        cleaned = "Buitenhof"
    elif cleaned == "de Mossel de Mossel":
        cleaned = "de Mossel"
    elif cleaned.startswith("Transferium "):
        cleaned = cleaned[len("Transferium "):]

    m = re.match(r"Velsen N\d+ Re - (.+)", cleaned)
    if m:
        cleaned = m.group(1)

    if "Kooypunt Schrijnwerkersweg" in cleaned:
        cleaned = "Schrijnwerkersweg"
        output["PlaatsNaam"] = "Den Helder"

    output["Straatnaam"] = cleaned if cleaned else None
    entry["output"] = output
    return entry


def dedup_rit_entries(entries):
    """Reduce Eindhoven Rit and Best Rit duplicates."""
    eindhoven_rit = []
    best_rit = []
    other = []

    for e in entries:
        inp = e["input"]
        if "Eindhoven Rit:" in inp:
            eindhoven_rit.append(e)
        elif "Best Rit:" in inp:
            best_rit.append(e)
        else:
            other.append(e)

    def select_varied(entries, target_count):
        prefixes = ["A1 ", "A2 ", "B1 ", "B2 "]
        selected = []
        per_prefix = max(1, target_count // (len(prefixes) + 1))

        for prefix in prefixes:
            matching = [e for e in entries if e["input"].startswith(prefix)]
            selected.extend(matching[:per_prefix])

        # bare (no prefix)
        bare = [e for e in entries if not any(e["input"].startswith(p) for p in prefixes)]
        selected.extend(bare[:per_prefix])

        return selected[:target_count]

    kept_eindhoven = select_varied(eindhoven_rit, 10)
    kept_best = select_varied(best_rit, 3)

    print(f"Eindhoven Rit: {len(eindhoven_rit)} -> {len(kept_eindhoven)}")
    print(f"Best Rit: {len(best_rit)} -> {len(kept_best)}")

    return other + kept_eindhoven + kept_best


def add_new_examples():
    """Add training examples for weak patterns."""
    examples = []

    # Bare Stadt Rit examples (no A1/A2 prefix)
    bare_rit = [
        ("Eindhoven Rit: 27989", "Eindhoven"),
        ("Eindhoven Rit: 28001", "Eindhoven"),
        ("Best Rit: 27990", "Best"),
        ("Helmond Rit: 28100", "Helmond"),
        ("Veldhoven Rit: 28200", "Veldhoven"),
        ("Geldrop Rit: 28050", "Geldrop"),
        ("Tilburg Rit: 29001", "Tilburg"),
        ("Breda Rit: 29050", "Breda"),
    ]
    for inp, plaats in bare_rit:
        examples.append({"input": inp, "output": {"Straatnaam": None, "PlaatsNaam": plaats, "wegnummer": None, "postcode": None, "Regio": None}})

    # Numbered streets (2e, 1e, 3e)
    numbered_streets = [
        ("AMBU 17200 2e Tuindwarsstraat 1015RZ Amsterdam AMSTER bon 35001", "2e Tuindwarsstraat", "Amsterdam", "1015RZ", "Amsterdam-Amstelland"),
        ("A1 AMBU 17300 1e Helmersstraat 1054DA Amsterdam AMSTER bon 35010", "1e Helmersstraat", "Amsterdam", "1054DA", "Amsterdam-Amstelland"),
        ("AMBU 17400 3e Oosterparkstraat 1092EA Amsterdam AMSTER bon 35020", "3e Oosterparkstraat", "Amsterdam", "1092EA", "Amsterdam-Amstelland"),
        ("A2 AMBU 17500 2e Hugo de Grootstraat 1052LB Amsterdam AMSTER bon 35030", "2e Hugo de Grootstraat", "Amsterdam", "1052LB", "Amsterdam-Amstelland"),
        ("AMBU 17600 1e Constantijn Huygensstraat 1054BR Amsterdam AMSTER bon 35040", "1e Constantijn Huygensstraat", "Amsterdam", "1054BR", "Amsterdam-Amstelland"),
        ("A1 AMBU 17700 2e Katendrechtsehaven 3072AJ Rotterdam ROTTDM bon 35050", "2e Katendrechtsehaven", "Rotterdam", "3072AJ", "Rotterdam-Rijnmond"),
    ]
    for inp, straat, plaats, postcode, regio in numbered_streets:
        examples.append({"input": inp, "output": {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": None, "postcode": postcode, "Regio": regio}})

    # P 2 BON fire messages with highway + street
    p2_bon = [
        ("P 2 BON-03 Buitenbrand Rijksweg A15 Li 89,5 Tiel 073500", None, "Tiel", "A15", None),
        ("P 2 BON-02 Buitenbrand Lekdijk A27 Re 45,0 Nieuwegein 073510", "Lekdijk", "Nieuwegein", "A27", None),
        ("P 2 BON-04 Buitenbrand Industrieweg N209 Re 12,3 Bergschenhoek 073520", "Industrieweg", "Bergschenhoek", "N209", None),
        ("P 2 BON-01 BR buiten Parallelweg A12 Li 55,0 Veenendaal 073530", "Parallelweg", "Veenendaal", "A12", None),
    ]
    for inp, straat, plaats, weg, regio in p2_bon:
        examples.append({"input": inp, "output": {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": weg, "postcode": None, "Regio": regio}})

    # Noordelijke Esweg intersection examples
    intersection = [
        ("BON-02 Ongeval wegvervoer Noordelijke Esweg Weijinksweg Hengelo 059096 059333", "Noordelijke Esweg", "Hengelo"),
        ("Aanrijding letsel Noordelijke Esweg Weijinksweg Hengelo 156507", "Noordelijke Esweg", "Hengelo"),
        ("BON-01 Ongeval wegvervoer Noordelijke Esweg Hengelo 059100", "Noordelijke Esweg", "Hengelo"),
        ("P 1 BON-02 Aanrijding letsel Noordelijke Esweg Oldenzaalsestraat Hengelo 059200", "Noordelijke Esweg", "Hengelo"),
    ]
    for inp, straat, plaats in intersection:
        examples.append({"input": inp, "output": {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": None, "postcode": None, "Regio": None}})

    # Short Ongeval ... Nxxx ... Plaats patterns
    ongeval = [
        ("Ongeval wegvervoer letsel N261 Re Tilburg", None, "Tilburg", "N261"),
        ("Ongeval wegvervoer letsel N65 Li Vught", None, "Vught", "N65"),
        ("Ongeval wegvervoer letsel N270 Re Helmond", None, "Helmond", "N270"),
        ("Ongeval wegvervoer N325 Elst", None, "Elst", "N325"),
    ]
    for inp, straat, plaats, weg in ongeval:
        examples.append({"input": inp, "output": {"Straatnaam": straat, "PlaatsNaam": plaats, "wegnummer": weg, "postcode": None, "Regio": None}})

    return examples


def main():
    with open(INPUT) as f:
        entries = [json.loads(line) for line in f if line.strip()]

    print(f"Total entries before: {len(entries)}")

    # 1. Fix VWS labels
    vws_count = 0
    for i, e in enumerate(entries):
        straat = e["output"].get("Straatnaam", "")
        if straat and straat.startswith("VWS"):
            entries[i] = fix_vws_straatnaam(e)
            vws_count += 1
    print(f"Fixed {vws_count} VWS labels")

    # 2. Dedup Rit entries
    entries = dedup_rit_entries(entries)

    # 3. Add new examples
    new_examples = add_new_examples()
    entries.extend(new_examples)
    print(f"Added {len(new_examples)} new examples")

    print(f"Total entries after: {len(entries)}")

    with open(OUTPUT, "w") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Verify
    vws_remaining = sum(1 for e in entries if (e["output"].get("Straatnaam") or "").startswith("VWS"))
    print(f"\nVerification: {vws_remaining} entries still have VWS in Straatnaam")

    eindhoven_count = sum(1 for e in entries if "Eindhoven Rit:" in e["input"])
    best_count = sum(1 for e in entries if "Best Rit:" in e["input"])
    print(f"Eindhoven Rit entries: {eindhoven_count}")
    print(f"Best Rit entries: {best_count}")


if __name__ == "__main__":
    main()
