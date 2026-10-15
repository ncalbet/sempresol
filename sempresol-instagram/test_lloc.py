"""Proves de lloc.py. Execució: python test_lloc.py"""
import sys

from lloc import compatible, fill

CASOS = [
    # (plantilla, nom, esperat)
    ("A {lugar}, el sol ha plegat.", "Reus", "A Reus, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "el Priorat", "Al Priorat, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "els Ports", "Als Ports, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "les Garrigues", "A les Garrigues, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "la Garrotxa", "A la Garrotxa, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "l'Alt Empordà", "A l'Alt Empordà, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "L'Espluga Calba", "A l'Espluga Calba, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "La Seu d'Urgell", "A la Seu d'Urgell, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "El Molar", "Al Molar, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "Es Castell", "A Es Castell, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "reus", "A Reus, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "el priorat", "Al Priorat, el sol ha plegat."),
    ("A {lugar}, el sol ha plegat.", "Catalunya", "A Catalunya, el sol ha plegat."),
    ("{lugar} viu un dia radiant.", "Reus", "Reus viu un dia radiant."),
    ("{lugar} viu un dia radiant.", "el Priorat", "El Priorat viu un dia radiant."),
    ("{lugar} viu un dia radiant.", "la Garrotxa", "La Garrotxa viu un dia radiant."),
    ("{lugar} viu un dia radiant.", "l'Alt Empordà", "L'Alt Empordà viu un dia radiant."),
    ("El temps a {lugar} és bo.", "el Priorat", "El temps al Priorat és bo."),
    ("Avui a {lugar} el sol ha guanyat.", "El Brull", "Avui al Brull el sol ha guanyat."),
    ("Confirmat per sempresol.cat: a {lugar} avui fa sol.", "el Priorat",
     "Confirmat per sempresol.cat: al Priorat avui fa sol."),
    ("Bones notícies des de {lugar}: tot bé.", "el Priorat", "Bones notícies des del Priorat: tot bé."),
    ("Bones notícies des de {lugar}: tot bé.", "Alforja", "Bones notícies des d'Alforja: tot bé."),
    ("Bones notícies des de {lugar}: tot bé.", "Reus", "Bones notícies des de Reus: tot bé."),
    ("El cel de {lugar} és net.", "els Ports", "El cel dels Ports és net."),
    ("El cel de {lugar} és net.", "Alforja", "El cel d'Alforja és net."),
    ("El cel de {lugar} és net.", "Hostalric", "El cel d'Hostalric és net."),
    ("El cel de {lugar} és net.", "l'Hospitalet de Llobregat", "El cel de l'Hospitalet de Llobregat és net."),
    ("El cel de {lugar} és net.", "Reus", "El cel de Reus és net."),
    ("{lugar}: quan diuen 'bon temps', ho diuen per {lugar}. Sempre per {lugar}.", "el Priorat",
     "El Priorat: quan diuen 'bon temps', ho diuen pel Priorat. Sempre pel Priorat."),
    ("L'anticicló ha triat {lugar} com a seu.", "el Priorat", "L'anticicló ha triat el Priorat com a seu."),
    ("Tal com recull sempresol.cat, {lugar} es vesteix de llum.", "el Priorat",
     "Tal com recull sempresol.cat, el Priorat es vesteix de llum."),
    ("A {lugar}, el sol. A {lugar} han decidit.", "el Priorat", "Al Priorat, el sol. Al Priorat han decidit."),
    ("En {lugar}, eth sòu a decidit rèster.", "Pònt d'Arròs", "En Pònt d'Arròs, eth sòu a decidit rèster."),
    ("Sense marcador.", "el Priorat", "Sense marcador."),
]

COMPATIBILITAT = [
    # (plantilla, nom, plural, esperat)
    ("{lugar} viu un dia radiant.", "els Ports", None, False),
    ("{lugar} viu un dia radiant.", "les Terres de l'Ebre", None, False),
    ("{lugar} viu un dia radiant.", "el Priorat", None, True),
    ("{lugar} viu un dia radiant.", "Illes Balears", True, False),
    ("A {lugar}, el sol ha plegat.", "els Ports", None, True),
    ("{lugar}: on l'única previsió falla.", "els Ports", None, True),
    ("Tal com recull sempresol.cat, {lugar} es vesteix.", "les Garrigues", None, False),
    ("L'anticicló ha triat {lugar} com a seu.", "els Ports", None, True),
    ("El temps a {lugar} és bo.", "els Ports", None, True),
]


def main() -> int:
    errors = 0
    for plantilla, nom, esperat in CASOS:
        obtingut = fill(plantilla, nom)
        if obtingut != esperat:
            errors += 1
            print(f"ERROR fill({plantilla!r}, {nom!r})\n   esperat:  {esperat!r}\n   obtingut: {obtingut!r}")
    for plantilla, nom, plural, esperat in COMPATIBILITAT:
        obtingut = compatible(plantilla, nom, plural)
        if obtingut != esperat:
            errors += 1
            print(f"ERROR compatible({plantilla!r}, {nom!r}, {plural})  esperat {esperat}, obtingut {obtingut}")
    total = len(CASOS) + len(COMPATIBILITAT)
    print(f"{total - errors}/{total} proves correctes")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
