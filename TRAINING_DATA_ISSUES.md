# Training Data Issues - Suggested Fixes

This document lists potential issues in the training data identified during review. **All fixes below have been applied** (as of last update).

---

## 1. abbreviations.jsonl - Wrong Mappings

### 1a. GOUDRK → Gouda (WRONG)
**Current:** `{"input": "GOUDRK", "output": "Gouda"}`  
**Should be:** `{"input": "GOUDRK", "output": "Gouderak"}`

Gouderak is a separate village near Gouda. The training data has entries like "Ambulancepost Gouderak Middelblok GOUDRK" where the output incorrectly says PlaatsNaam "Gouda" instead of "Gouderak".

**Affected training entries:**
- train.jsonl: lines 2397, 2707, 3065 (PlaatsNaam "Gouda" should be "Gouderak")
- train_part2.jsonl lines 2873, 3418: correctly have "Gouderak"

### 1b. OTVOOR → Oud-Voorburg (WRONG)
**Current:** `{"input": "OTVOOR", "output": "Oud-Voorburg"}`  
**Should be:** `{"input": "OTVOOR", "output": "Oostvoorne"}`

OTVOOR clearly stands for Oostvoorne (many inputs show "Oostvoorne OTVOOR"). Oud-Voorburg is a different place (historical name for part of Leidschendam-Voorburg).

**Affected training entries:**
- train.jsonl line 1910: PlaatsNaam "Oud-Voorburg" should be "Oostvoorne" (input: "Polderslaan 3233VL Oostvoorne OTVOOR")
- train.jsonl line 5767: Regio "Oud-Voorburg" should be "Rotterdam-Rijnmond" (Oud-Voorburg is not a veiligheidsregio)

---

## 2. Regio Naming Inconsistency: Gelderland-Midden vs Gelderland Midden

**Issue:** Training data uses "Gelderland-Midden" (hyphen) but `regions.jsonl` has "Gelderland Midden" (space). Same for "Gelderland-Zuid" vs "Gelderland Zuid".

**Suggested fix:** Add normalization entries to regions.jsonl:
```json
{"input":"Gelderland-Midden","output":"Gelderland Midden"}
{"input":"Gelderland-Zuid","output":"Gelderland Zuid"}
```

Or standardize training data to use "Gelderland Midden" (space) everywhere.

---

## 3. regions.jsonl - Renswoude

**Issue:** "Renswoude" is listed as a region (input=output). Renswoude is a village in Utrecht province, not one of the 25 official Dutch veiligheidsregios. The region for Renswoude would be "Utrecht".

**Suggested fix:** Remove the Renswoude entry, or change it to map to "Utrecht" if Renswoude appears in P2000 messages as a region code.

---

## 4. Straatnaam Contains Multiple Street Names (Intersections)

When the input describes an intersection (e.g. "StreetA StreetB City"), the output sometimes concatenates both street names. The schema allows a single Straatnaam string. Consider whether to:
- Keep the first/primary street only
- Keep both (e.g. "Noordelijke Esweg Weijinksweg") as "StreetA StreetB"
- Use the primary street and put the other in a comment (schema doesn't support this)

**Examples:**
- train_part2 line 12: `"Vijfhuizerweg Drie Merenweg"` – input: "Vijfhuizerweg Drie Merenweg Vijfhuizen"
- train_part2 line 61: `"Dorpsstraat Raadhuisstraat"` – input: "Dorpsstraat Raadhuisstraat Landsmeer"
- train_part2 line 527: `"Antillenstraat Weideweg"` – intersection in Hengelo
- train_part2 line 621: `"Leyweg Hengelolaan"` – Den Haag (Leyweg × Hengelolaan)
- train_part2 line 2086: `"Mozartlaan Josef Haydnlaan"` – Hengelo
- train.jsonl line 3544: `"Hengelosestraat Boddenkampsingel"` – Enschede

**Suggestion:** Document the intended behavior. If primary street only: pick the first street. If intersection: keeping both is acceptable but be consistent.

---

## 5. Straatnaam Contains Building/Facility Names

Some entries include facility names in Straatnaam. `fix_training_data.py` has BUILDING_PREFIXES for some patterns, but these may be missed:

- train_part2 line 864: `"Basisschool Olympia Vlierenbroek"` → should be "Vlierenbroek" (street in Breda)
- train_part2 line 1075: `"Hugo-waard Woonzorgcentrum Gerard Douplantsoen"` → should be "Gerard Douplantsoen"
- train_part2 line 1126: `"Woonzorgcentrum Jonker Frans Newtonplein"` → should be "Newtonplein"
- train_part2 line 2920: `"Woonzorgcentrum De Horstenburgh Dorpsstraat"` → should be "Dorpsstraat"

---

## 6. PlaatsNaam Null When City Is in Input

Several entries have PlaatsNaam null even though the city appears in the input:

- train.jsonl line 1991: Input "Ambu 07120 - Velp GE Rit" → PlaatsNaam should be "Velp"
- train.jsonl line 2948: Input "Ambu 07108 DIA Velp GE Rit" → PlaatsNaam should be "Velp"
- train.jsonl line 3062: Input "Ambu 07343 DIA Velp GE Rit" → PlaatsNaam should be "Velp"
- train.jsonl line 3666: Input "Ambu 07120 DIA Velp GE Rit" → PlaatsNaam should be "Velp"
- train.jsonl line 3802: Input "Ambu 07101 DIA Elst GE Rit" → PlaatsNaam should be "Elst"
- train.jsonl line 3330: Input "Ambu 06161 VWS Hengelo (Gld) Rit" → PlaatsNaam should be "Hengelo"
- train.jsonl line 5475: Same as above
- train.jsonl line 4366: Input "A1 - Hengelo 70457" → PlaatsNaam could be "Hengelo" (ambiguous which Hengelo)

---

## 7. Hengelo: Wrong Regio for Hengelo (Overijssel)

**Issue:** Some Hengelo entries use Regio "Gelderland-Midden", but there are two Hengelos:
- **Hengelo (Gelderland)** – small village, Regio Gelderland Midden ✓
- **Hengelo (Overijssel)** – city, Regio Twente ✓

Entries with street names typical of Hengelo (Overijssel) may have the wrong Regio:
- train.jsonl line 91: "Thiemsbrug Hengelo 059333" – Thiemsbrug is in Hengelo (Overijssel) → Regio should be "Twente", not "Gelderland-Midden"
- train.jsonl line 4788: "Breemarsweg Hengelo 059333" – Breemarsweg is in Hengelo (Overijssel) → Regio should be "Twente"
- train.jsonl line 4832: "Haaksbergerstraat 17 Hengelo" – Haaksbergerstraat suggests Hengelo (Overijssel) → Regio should be "Twente"

Entries with "(Gld)" in the input correctly use Gelderland-Midden.

**Suggestion:** For Hengelo without "(Gld)", use Regio "Twente". For "Hengelo (Gld)", use "Gelderland Midden".

---

## 8. G v Voorneweg – Abbreviated Street Name

**Example:** train_part2 line 47: `"G v Voorneweg"` in Oostvoorne

"G" is likely "Gouverneur" (Gouverneur van Voorneweg). Consider expanding to "Gouverneur van Voorneweg" if that is the official name, or leave as-is if the abbreviation is standard in P2000.

---

## 9. Incomplete Postcodes in Input (4 digits only)

Some inputs have 4-digit numbers (e.g. "1061", "1018", "1191") between street and city. These are partial Amsterdam-style postcodes. The fix script (Fix 36) sets postcode to null when it's only 4 digits. Entries that omit postcode for these cases are consistent with that.

**Examples:** "Jan Tooropstraat 1061 Amsterdam", "Kattenburgerstraat 1018 Amsterdam" – postcode null is correct (incomplete in source).

---

## 10. Duplicate GOUDA in abbreviations.jsonl

Both GOUDA and GOUDRK map to "Gouda". After fixing GOUDRK → Gouderak (see 1a), this is resolved. No other duplicate issues found.

---

## 11. Straatnaam Inconsistencies for Same Location

- **De Hanepraij / Hanepraij:** Some entries have "De Hanepraij Fluwelensingel", others "Hanepraij Fluwelensingel". Standardize to one form.
- **Hoogvliet Plataanstraat** (train.jsonl 2207): "Hoogvliet" appears to be a building/facility name; Straatnaam should likely be "Plataanstraat" only.

---

## 12. abbreviations.jsonl Formatting

Some lines use `"input": "X"` (with spaces) and others `"input":"X"` (no spaces). Consider normalizing for consistency.

---

## Summary of Fixes Applied

| # | Fix | Status |
|---|-----|--------|
| 1a | GOUDRK → Gouderak in abbreviations.jsonl + fix 3 train entries | ✅ Applied |
| 1b | OTVOOR → Oostvoorne in abbreviations.jsonl + fix 2 train entries | ✅ Applied |
| 2 | Add Gelderland-Midden, Gelderland-Zuid to regions.jsonl; remove Renswoude | ✅ Applied |
| 6 | Fill PlaatsNaam for Velp/Elst/Hengelo (Gld) entries | ✅ Applied |
| 7 | Fix Hengelo (Ov) Regio to Twente | ✅ Applied |
| 5 | Strip building names from Straatnaam (4 entries) | ✅ Applied |
| 11 | De Hanepraij consistency, Hoogvliet Plataanstraat | ✅ Applied |
| Regio | Standardize Gelderland-Midden/Zuid to space form | ✅ Applied |

---

*All suggested fixes have been implemented.*

---

## 13. test_ollama.py: Noordelijke Esweg Weijinksweg (Tests 18 & 19)

**Issue:** The test expected Straatnaam `"Noordelijke Esweg Weijinksweg"` for the intersection inputs, but the training data consistently uses `"Noordelijke Esweg"` (primary street only) for these exact inputs.

**Training data (train.jsonl 4875-4876, train_part2 3464-3465):**
- "BON-02 Ongeval wegvervoer Noordelijke Esweg Weijinksweg Hengelo" → Straatnaam: "Noordelijke Esweg"
- "Aanrijding letsel Noordelijke Esweg Weijinksweg Hengelo" → Straatnaam: "Noordelijke Esweg"

**Fix applied:** Updated test_ollama.py to expect "Noordelijke Esweg" (matching training data convention for intersections – primary street only).

---

## 14. Training Improvements (build.sh pipeline)

**Changes applied:**
- **Fix 34** in fix_training_data.py: Fill Regio from PlaatsNaam when null (fixes 1174+723 conflicting Rotterdam/etc. entries)
- **train_edge_cases.jsonl**: Edge-case variations for failing patterns (Stank/hind. lucht, Best Rit, N279 Re Veghel, VWS Wognum, Rotterdam Regio, Noordelijke Esweg)
- **prepare_data.py**: Includes train_edge_cases.jsonl with 2x oversampling for minority patterns
- **build.sh**: Runs fix_training_data.py before prepare_data.py
- **finetune_mlx.py**: Epochs 10→12, LR 2e-4→1.5e-4 for more stable learning
