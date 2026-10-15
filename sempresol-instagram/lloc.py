"""Com queda el nom d'un lloc (poble, comarca, territori…) dins d'una frase.

Les plantilles porten `{lugar}`. Segons la preposició que el precedeix i si el nom
porta article (el Priorat, les Garrigues, l'Alt Empordà) cal contreure
(a + el -> al, de + els -> dels, per + el -> pel), elidir (de Alforja -> d'Alforja)
i posar la majúscula a l'inici de frase. Serveix igual per a un poble que per a un
territori o qualsevol altra cosa.

    from lloc import fill, compatible
    fill("A {lugar}, el sol ha plegat.", "el Priorat")   # "Al Priorat, el sol ha plegat."

Els noms en plural (els Ports, les Garrigues) no encaixen amb les plantilles on el lloc és
el subjecte del verb («{lugar} viu…»): `compatible()` ho diu, per triar-ne d'altres.

Per triar frases per a un territori, des de la línia d'ordres:

    python lloc.py "les Terres de l'Ebre" -n 5

Limitacions: l'aranès («En {lugar}») no es contrau, i un plural sense article
(«Illes Balears») no es detecta: cal dir-ho amb --plural.
"""
import json
import random
import re
import sys
from pathlib import Path

PLACEHOLDER = "{lugar}"

# Un caràcter que forma part d'una paraula (inclou accents, apòstrof i punt volat).
_LLETRA = "\\wÀ-ÿ'’·"
# La preposició (o locució) que acaba el text ja escrit, just abans del marcador.
_PREP = re.compile(rf"(^|[^{_LLETRA}])(des de|de|per|a)\s+$", re.IGNORECASE)
_FINAL_DE_FRASE = re.compile(r"(^|[.!?…]\s+)$")
_VOCAL = set("aeiouàèéíòóúïühAEIOUÀÈÉÍÒÓÚÏÜH")  # la h no es pronuncia

_CONTRACCIONS = {
    "a":     {"el": "al", "els": "als"},
    "de":    {"el": "del", "els": "dels"},
    "des de": {"el": "des del", "els": "des dels"},
    "per":   {"el": "pel", "els": "pels"},
}


def analitza(nom: str) -> tuple[str, str]:
    """Separa l'article inicial: «el Priorat» -> ('el', 'Priorat'); «l'Alt Empordà» -> ("l'", 'Alt Empordà').

    Només es reconeixen el, els, la, les, l'. (Els articles salats Es/Sa/Ses es deixen
    tal com vénen: formen part del nom.) La primera lletra de la resta es posa en majúscula.
    """
    nom = " ".join(nom.split())
    m = re.match(r"^(els|les|el|la)\s+(\S.*)$", nom, re.IGNORECASE)
    if m:
        art, resta = m.group(1).lower(), m.group(2)
    else:
        m = re.match(r"^l['’](\S.*)$", nom, re.IGNORECASE)
        art, resta = ("l'", m.group(1)) if m else ("", nom)
    if resta:
        resta = resta[0].upper() + resta[1:]
    return art, resta


def _amb_article(art: str, resta: str) -> str:
    if not art:
        return resta
    return art + resta if art.endswith("'") else f"{art} {resta}"


def forma(nom: str, prep: str | None = None) -> str:
    """El nom precedit (o no) d'una preposició: forma('el Priorat', 'a') -> 'al Priorat'."""
    art, resta = analitza(nom)
    if prep is None:
        return _amb_article(art, resta)
    prep = prep.lower()
    contracte = _CONTRACCIONS[prep].get(art)
    if contracte:
        return f"{contracte} {resta}"
    if prep in ("de", "des de") and not art and resta[:1] in _VOCAL:
        return ("des d'" if prep == "des de" else "d'") + resta
    return f"{prep} {_amb_article(art, resta)}"


def fill(plantilla: str, nom: str) -> str:
    """Substitueix `{lugar}` pel nom amb la preposició, l'article i la majúscula que toquen."""
    if PLACEHOLDER not in plantilla:
        return plantilla
    res, pos = "", 0
    for m in re.finditer(re.escape(PLACEHOLDER), plantilla):
        res += plantilla[pos:m.start()]
        pos = m.end()
        pm = _PREP.search(res)
        if pm:
            prep = pm.group(2)
            nou = forma(nom, prep)
            if prep[0].isupper():                      # «A», «Des de»…
                nou = nou[0].upper() + nou[1:]
            res = res[:pm.start(2)] + nou
        else:
            nou = forma(nom)
            if _FINAL_DE_FRASE.search(res):            # el lloc obre la frase
                nou = nou[0].upper() + nou[1:]
            res += nou
    return res + plantilla[pos:]


def es_plural(nom: str) -> bool:
    return analitza(nom)[0] in ("els", "les")


def te_subjecte(plantilla: str) -> bool:
    """Cert si el lloc és el subjecte del verb en alguna aparició («{lugar} viu…», «…, {lugar} es vesteix»)."""
    for m in re.finditer(re.escape(PLACEHOLDER), plantilla):
        pre, post = plantilla[:m.start()], plantilla[m.end():]
        if _PREP.search(pre) or post.startswith(":"):
            continue
        if re.search(r"(^|[.!?…,:;]\s*)$", pre):
            return True
    return False


def compatible(plantilla: str, nom: str, plural: bool | None = None) -> bool:
    """Fals si el nom és plural i la plantilla el fa subjecte d'un verb en singular."""
    plural = es_plural(nom) if plural is None else plural
    return not (plural and te_subjecte(plantilla))


def _main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Frases per a un lloc (poble, comarca, territori…)")
    ap.add_argument("nom", help="per exemple: \"el Priorat\" o \"les Terres de l'Ebre\"")
    ap.add_argument("--regio", default="cat", choices=["cat", "val", "bal", "aran"])
    ap.add_argument("-n", type=int, default=5, help="quantes frases (per defecte 5)")
    ap.add_argument("--plural", action="store_true", help="força el plural (p. ex. «Illes Balears»)")
    args = ap.parse_args()

    pool = json.loads((Path(__file__).parent / "data" / "messages.json").read_text(encoding="utf-8"))
    triables = [t for t in pool[args.regio] if compatible(t, args.nom, True if args.plural else None)]
    sys.stdout.reconfigure(encoding="utf-8")
    for t in random.sample(triables, min(args.n, len(triables))):
        print("-", fill(t, args.nom))


if __name__ == "__main__":
    _main()
