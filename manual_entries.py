#!/usr/bin/env python3
"""Manually parsed training entries for unparseable messages."""
import json

N = {"Straatnaam": None, "PlaatsNaam": None, "wegnummer": None, "postcode": None, "Regio": None}

def e(inp, street=None, city=None, weg=None, pc=None, regio=None):
    return {"input": inp, "output": {
        "Straatnaam": street, "PlaatsNaam": city, "wegnummer": weg, "postcode": pc, "Regio": regio
    }}

entries = [
    # === ALL NULL / SKIP messages ===
    e("Prins Bernhardbrug vrijhouden voor hulpdiensten"),
    e("SPOED AMBU"),
    e("SMS/APP SBB MIRG"),
    e("Gaarne contact MKA"),
    e("Hulpdienstvoertuig Ambulance verwacht"),
    e("Coenbrug vrijhouden voor hulpdiensten"),
    e("10"),
    e("Graag posten Spijkenisse ajb"),
    e("Test: TEST Code 100 Contact meldkamer Group Talk"),
    e("k"),
    e("Test: TEST Code 100 Contact meldkamer Group Tal"),
    e("er Group Talk"),
    e("Test: TEST Code 100 Contact meldkam"),
    e("tact meldkamer Group Talk"),
    e("Test: TEST Code 100 Con"),
    e("Code 100 Contact meldkamer Group Talk"),
    e("Test: TEST "),
    e("INZET KLAZIENAVEEN"),
    e("Proefalarm"),
    e("test"),
    e("terst"),
    e("Posten Baan svp"),
    e("Graag posten Berkel ajb"),
    e("Posten Oost svp"),
    e("5"),
    e("7"),
    e("6"),
    e("fijne dienst"),
    e("Contact MKB (TD) 179291"),
    e("Goedenmiddag, dienst Noord overgenomen door PC, rustige dienst!"),
    e("Oefening - GGB inzet"),
    e("Contact OC - 259"),
    e("Graag telefonisch contact MKA"),
    e("Contact mka"),
    e("(Gaarne contact MKA)"),
    e("svp bel caco ivm TUE"),
    e("contact OC Hilversum"),
    e("Einde storing werkwijze als normaal"),
    e("Einde VWS"),
    e("Graag telefonisch contact Caco Meldkamer Den Haag"),
    e("graag posten brugwachter aub"),
    e("Graag telefonisch contact cluster G&V GMS229"),
    e("TEST"),
    e("Rit vanaf de cardio Maasstad"),
    e("contact OC 58806"),
    e("u mag retour post"),
    e("graag posten baan aub"),
    e("CVD graag telefonisch contact MKA"),
    e("Bel OC 58806"),
    e("BEL OC GMS 59235"),
    e("bel oc gms 59232"),
    e("B1 DV Ambu Nijmegen aub contact mka"),
    e("Zometeen vv rit vanaf SEH"),
    e("goedemiddag, dienst OVD-G Limburg midden overgenomen"),
    e("p 1 test voor autospuit amstelveen"),
    e("graag telefonisch contact MKB"),
    e("PROEFALARM VEILIGHEIDSREGIO BRABANT-ZUIDOOST"),
    e("Wekelijks proefalarm Veiligheidsregio Hollands Midden."),
    e("Test: Proefalarm Avond Brandweer Veiligheidsregio Rotterdam Rijnmond."),
    e("Hartelijk goedemiddag, CLT_AA graag even telefonisch contact RAC_AA"),
    e("Graag telefonisch contact Caco Meldkamer Den Haag"),  # duplicate is fine, dedup later
    e("contact mka svp"),
    e("Graag telefonisch contact OVDB Venlo"),
    e("Graag inmelden BNN-BV-21 Nacontrole Penitentiaire Inrichting (PI) Ter Apel Ter Apelerv Ter Apel 01-27-001 013693"),
    e("SPOED AMBU"),
    e("graag telefonisch contact MKB"),
    e("Graag posten Hoogstad ajb"),
    e("gaarne contact mka"),
    e("Contact MKA"),

    # === Passage messages - all null ===
    e("Passage Ambulance Algerabrug Capelle aan den IJssel"),
    e("Passage Ambulance Zijlbrug Leiden"),
    e("Passage Ambulance Woubrugsebrug Woubrugge"),
    e("Passage Ambulance Hefbrug Gouwesluis Alphen"),
    e("Passage Ambulance Hefbrug Boskoop"),
    e("Passage Ambulance Albert Schweitzerbrug Alphen"),
    e("Passage Ambulance Zijlbrug Leiden"),
    e("Passage Ambulance Zijlbrug Leiden"),

    # === B2 rit messages - city only ===
    e("B2 Tilburg rit: 39945", city="Tilburg"),
    e("B2 Vlissingen rit: 39942", city="Vlissingen"),
    e("B2 Tilburg rit: 39940", city="Tilburg"),
    e("B2 Tilburg rit: 39905", city="Tilburg"),
    e("B2 Tholen rit: 39888", city="Tholen"),
    e("B2 Nispen rit: 39885", city="Nispen"),
    e("B2 Werkendam rit: 39819", city="Werkendam"),
    e("B1 Tilburg rit: 39816 (Directe inzet: ja)", city="Tilburg"),
    e("B2 Roosendaal rit: 39810", city="Roosendaal"),
    e("B2 Oudenbosch rit: 39809", city="Oudenbosch"),
    e("B2 Breda rit: 39804", city="Breda"),
    e("B2 Breda rit: 39755", city="Breda"),
    e("B2 Tilburg rit: 39757", city="Tilburg"),
    e("B2 Bergen op Zoom rit: 39753", city="Bergen op Zoom"),
    e("B2 Tilburg rit: 39752", city="Tilburg"),
    e("B2 Goes rit: 39749", city="Goes"),
    e("B2 Etten-Leur rit: 39746 (Directe inzet: ja)", city="Etten-Leur"),
    e("B2 Breda rit: 39739 (Directe inzet: ja)", city="Breda"),
    e("B2 Breda rit: 39725", city="Breda"),
    e("B2 Tilburg rit: 39724", city="Tilburg"),
    e("B2 St. Willebrord rit: 39721", city="St. Willebrord"),
    e("B2 Tilburg rit: 39711", city="Tilburg"),
    e("B2 Tilburg rit: 39710", city="Tilburg"),
    e("B2 Middelburg rit: 39703", city="Middelburg"),
    e("B2 Breda rit: 39681", city="Breda"),
    e("B2 Tilburg rit: 39670", city="Tilburg"),
    e("B2 Rijsbergen rit: 39661 (Directe inzet: ja)", city="Rijsbergen"),
    e("B2 Tilburg rit: 39654", city="Tilburg"),
    e("B2 Roosendaal rit: 39647", city="Roosendaal"),
    e("B2 Breda rit: 39628", city="Breda"),
    e("B2 Tilburg rit: 39619", city="Tilburg"),
    e("B2 Made rit: 39614", city="Made"),
    e("B2 Tilburg rit: 39611", city="Tilburg"),
    e("B2 Breda rit: 39597", city="Breda"),
    e("B2 Tilburg rit: 39581", city="Tilburg"),
    e("B2 Tilburg rit: 39577", city="Tilburg"),
    e("B2 Breda rit: 39571", city="Breda"),
    e("B2 Baarle-Nassau rit: 39570", city="Baarle-Nassau"),
    e("B2 Tilburg rit: 39547 (Directe inzet: ja)", city="Tilburg"),
    e("B2 Breda rit: 39594", city="Breda"),
    e("B2 Terneuzen rit: 39782", city="Terneuzen"),
    e("B2 Loon op Zand rit: 39779", city="Loon op Zand"),
    e("B2 Roosendaal rit: 39770", city="Roosendaal"),
    e("B2 Heinkenszand rit: 39758 (Directe inzet: ja)", city="Heinkenszand"),
    e("B2 Breda rit: 39854", city="Breda"),
    e("B2 Tilburg rit: 39600", city="Tilburg"),
    e("B2 's-Hertogenbosch 38239", city="'s-Hertogenbosch"),
    e("C2 Lelystad 38228", city="Lelystad"),

    # === P messages with street + city ===
    e("P 1 BRT-02 Reanimatie Rotterdamsedijk Schiedam 170431", street="Rotterdamsedijk", city="Schiedam"),
    e("P 2 89845 Letsel Gasthuisstraat Goes", street="Gasthuisstraat", city="Goes"),
    e("P 2 BDH-02 CO-melder Kasteellaan Schipluiden 156130", street="Kasteellaan", city="Schipluiden"),
    e("P 1 89813 Letsel Alvarezlaan Terneuzen", street="Alvarezlaan", city="Terneuzen"),
    e("P 2 BNN-05 Liftopsluiting Waterloolaan Groningen 011831", street="Waterloolaan", city="Groningen"),
    e("P 1 (Intrekken Alarm Brw) (Middel BR) BR gezondheidszorg Woongemeenschap Scheemda Randstede Scheemda 01-29-048", street="Randstede", city="Scheemda"),
    e("P 1 89752 Letsel Nieuwe Kadijk Breda", street="Nieuwe Kadijk", city="Breda"),
    e("P 2 BON-06 Brandgerucht Trompstraat Rijssen 055131", street="Trompstraat", city="Rijssen"),
    e("P 2 BAD-01 Buitensluiting Surinameplein Amsterdam 132631", street="Surinameplein", city="Amsterdam"),
    e("P 1 BAD-01 Reanimatie Contactweg Amsterdam 132431", street="Contactweg", city="Amsterdam"),
    e("P 3 BON-01 Wateroverlast Leliestraat Doetinchem 065331", street="Leliestraat", city="Doetinchem"),
    e("P 2 BDH-15 Brandgerucht Wellingtonstraat 's-Gravenhage 159661", street="Wellingtonstraat", city="'s-Gravenhage"),
    e("P 1 BDH-01 Brandgerucht Robijnhorst 's-Gravenhage 155150", street="Robijnhorst", city="'s-Gravenhage"),
    e("P 1 BDH-01 Brandgerucht Robijnhorst 's-Gravenhage 155130", street="Robijnhorst", city="'s-Gravenhage"),
    e("P 1 BMD-05 Reanimatie Griend Leerdam 096831", street="Griend", city="Leerdam"),
    e("P 2 BDH-03 Brandgerucht Nieuwe Duinweg Katwijk ZH", street="Nieuwe Duinweg", city="Katwijk"),
    e("P 2 BON-04 CO-melder Verzetslaan Doetinchem 065331", street="Verzetslaan", city="Doetinchem"),
    e("P 2 BNN-02 BR woning (TBO) Griekenlandlaan Assen", street="Griekenlandlaan", city="Assen"),
    e("P 1 BNN-02 BR woning Griekenlandlaan Assen", street="Griekenlandlaan", city="Assen"),
    e("P 2 BON-02 Brandgerucht Hoofdstraat Ossenzijl 041239", street="Hoofdstraat", city="Ossenzijl"),
    e("P 3 BON-01 Dienstverlening Breemarsweg Hengelo 059333", street="Breemarsweg", city="Hengelo"),
    e("P 2 BOB-03 Buitensluiting Druifheide Helmond 223231", street="Druifheide", city="Helmond"),
    e("P 2 BRT-02 Liftopsluiting Willemskade Rotterdam 179232", street="Willemskade", city="Rotterdam"),
    e("P 2 BON-02 Liftopsluiting Bemmelsewaard Ede 072731", street="Bemmelsewaard", city="Ede"),
    e("P 2 BON-05 Buitensluiting Sluitersveldssingel Almelo 053151", street="Sluitersveldssingel", city="Almelo"),
    e("P 2 BNN-01 Nacontrole Tapuitlaan Hoogeveen 038931", street="Tapuitlaan", city="Hoogeveen"),
    e("P 1 BAD-01 Reanimatie Quellijnstraat Amsterdam 133231", street="Quellijnstraat", city="Amsterdam"),
    e("P 2 (Intrekken Alarm Brw) Brandgerucht Kempenhaeve VZH Koestraat Oirschot", street="Koestraat", city="Oirschot"),
    e("P 2 (Intrekken Alarm Brw) OMS brandmelding Justitieel Complex Schiphol (Cellencomplex B & C) Duizendbladweg Badhoevedorp", street="Duizendbladweg", city="Badhoevedorp"),
    e("P 2 (Intrekken Alarm Brw) Brandgerucht Stichting Wooninc. Wissehaege Herman Gorterlaan Eindhoven", street="Herman Gorterlaan", city="Eindhoven"),
    e("P 3 (Intrekken Alarm Brw) Brandgerucht (detectie: rook/hitte) GGZ Centraal loc. kliniek 1 Boomgaardweg Almere", street="Boomgaardweg", city="Almere"),
    e("P 3 (Intrekken Alarm Brw) Reanimatie Rita Vuykpad Almere", street="Rita Vuykpad", city="Almere"),
    e("P 1 BRT-01 (Middel BR) BR onderwijs Unielocatie Montessoriweg Rotterdam", street="Montessoriweg", city="Rotterdam"),
    e("P 2 Herbezet./kazerneren (herbez. specialisme) Kazerne Kerkrade Hammolenweg Kerkrade", street="Hammolenweg", city="Kerkrade"),
    e("P 1 Dienstverlening Meldkamer Schiphol Evert van de Beekstraat Schiphol", street="Evert van de Beekstraat", city="Schiphol"),
    e("P 4 Verkeersstremming Westerkeersluis Amsterdam", street="Westerkeersluis", city="Amsterdam"),
    e("P 1 Achtervolging President Allendelaan Amsterdam", street="President Allendelaan", city="Amsterdam"),
    e("P 2  Uitval nutsvoorz. (elektriciteit) Grauwe Polder Etten-Leur", street="Grauwe Polder", city="Etten-Leur"),
    e("(Intrekken Alarm Brw) BR container Stationsstraat Zaandam", street="Stationsstraat", city="Zaandam"),

    # === P messages with street + city (89xxx Letsel format) ===
    e("P 1 89379 Letsel AaBe-straat Tilburg", street="AaBe-straat", city="Tilburg"),
    e("P 1 89344 Letsel Beatrixstraat Marijkestraat Beatrixstraat Bosschenhoofd", street="Beatrixstraat", city="Bosschenhoofd"),

    # === Ongeval messages with street + city ===
    e("Ongeval/Wegvervoer/Letsel prio 1 Assen Europaweg-Zuid Haarweg", street="Europaweg-Zuid", city="Assen"),
    e("Ongeval/Wegvervoer/Letsel prio 1 Assen Europaweg-Zuid", street="Europaweg-Zuid", city="Assen"),
    e("Ongeval/Wegvervoer/Voertuig te water prio 1 Smilde Evert Hendriksweg", street="Evert Hendriksweg", city="Smilde"),
    e("Ongeval/Wegvervoer/Letsel prio 1 Stadskanaal Pekelderstraat", street="Pekelderstraat", city="Stadskanaal"),
    e("Ongeval/Wegvervoer/Letsel prio 1 Wons Weersterweg", street="Weersterweg", city="Wons"),
    e("Ongeval/Wegvervoer/Letsel prio 1 Sneek State-As", street="State-As", city="Sneek"),
    e("Ongeval/Wegvervoer/Letsel prio 1 Pieterburen Oudedijk", street="Oudedijk", city="Pieterburen"),
    e("Ongeval/Wegvervoer/Letsel prio 1 Usquert Oude Dijkpad Zijlsterweg", street="Zijlsterweg", city="Usquert"),
    e("Ongeval/Water/Schip/watersp. in problemen prio 2 Wergea Leeuwarderweg", street="Leeuwarderweg", city="Wergea"),
    e("Ongeval/Wegvervoer/Voertuig te water prio 1 Huizinge 0 Smedemaweg", street="Smedemaweg", city="Huizinge"),

    # === Demonstratie ===
    e("Demonstratie Het Rond Houten", street="Het Rond", city="Houten"),

    # === Oefening ===
    e("Oefening BRT-OTO-310 BR gebouw Spuikolk Dirksland 174331", street="Spuikolk", city="Dirksland"),

    # === P 2 BNH nacontrole (complex) ===
    e("P 2 BNH-01 Nacontrole Opkomstplaats 346 Tata Steel Wijk aan Zee 129032 129033 129091 129071 Let op Alleen opkomende dienst melden", city="Wijk aan Zee"),

    # === Misc with street + city ===
    e("3 Dieren Vleeshouwerstraat Gorinchem ICnum 124925", street="Vleeshouwerstraat", city="Gorinchem"),
    e("1 Explosie Watergeusstraat Rotterdam ICnum 124744", street="Watergeusstraat", city="Rotterdam"),
    e("P 1 BRT-01 Ass. Graag BOWOTO TP Ambu Watergeusstraat Rotterdam", street="Watergeusstraat", city="Rotterdam"),
    e("P 1 BRT-01 (Middel BR) BR onderwijs Unielocatie Montessoriweg Rotterdam", street="Montessoriweg", city="Rotterdam"),
    e("Contact meldkamer BRT-02 Liftopsluiting (controleur preventie) Willemskade Rotterdam 179101", street="Willemskade", city="Rotterdam"),
    e("Contact meldkamer Liftopsluiting (OVD-B, controleur preventie) Willemskade Rotterdam 179192", street="Willemskade", city="Rotterdam"),
    e("P 1 BRT-01 OVD-BZ graag tp gaan Ass. Politie (OVD-BZ) Watergeusstraat Rotterdam", street="Watergeusstraat", city="Rotterdam"),
    e("Persoon te water Veen en Duinpad Bloemendaal", street="Veen en Duinpad", city="Bloemendaal"),
    e("Bernhardstraat Koesteeg Sprang-Capelle", street="Bernhardstraat", city="Sprang-Capelle"),
    e("P 1 89738 Letsel Koesteeg Bernhardstraat Koesteeg Sprang-Capelle", street="Bernhardstraat", city="Sprang-Capelle"),
    e("P 1 89738 Letsel Koesteeg ", street="Koesteeg"),
    e("Haaksbergerstraat 17 Hengelo", street="Haaksbergerstraat", city="Hengelo"),
    e(" Wandelboslaan Tilburg", street="Wandelboslaan", city="Tilburg"),
    e("Spoor incident Waterloolaan Driehuis NH", street="Waterloolaan", city="Driehuis"),
    e("B2 (Contact MKA) Van der Madeweg 1114 Amsterdam-Duivendrecht", street="Van der Madeweg", city="Amsterdam-Duivendrecht"),
    e("2 Dier in problemen Armenweg Nieuwe-Tonge ICnum 124142", street="Armenweg", city="Nieuwe-Tonge"),

    # === DV/SKT tunnel messages ===
    e("DV wegvervoer (Sc_H_Stremming , Sc_E_Beperkte Toeg , Ter info ) SKT DWV L03 (zuidbuis) Sluiskiltunnel Sluiskil", street="Sluiskiltunnel", city="Sluiskil"),
    e("DV wegvervoer (Ter info , Sc_H_Stremming ) SKT DWV L03 (zuidbuis) Sluiskiltunnel Sluiskil", street="Sluiskiltunnel", city="Sluiskil"),

    # === P 5 proefalarm ===
    e("P 5  (proefalarm) Geplande actie Meldkamer Noord-Holland Zijlweg Haarlem", street="Zijlweg", city="Haarlem"),
    e("P 3  Contact Caco Noord-Holland Zijlweg Haarlem", street="Zijlweg", city="Haarlem"),

    # === Graag telefonisch / contact - but with location context (still null) ===
    e("Graag zsm tel contact MKNN Brandweer"),
]

# Dedup against existing
existing = set()
with open("train.jsonl") as f:
    for line in f:
        line = line.strip()
        if line:
            existing.add(json.loads(line)["input"])

added = 0
with open("train.jsonl", "a") as f:
    for entry in entries:
        if entry["input"] in existing:
            continue
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        existing.add(entry["input"])
        added += 1

print(f"Added {added} manually parsed entries")
print(f"New total: {len(existing)}")
