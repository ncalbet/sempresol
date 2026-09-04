"""
post.py
Script principal de SempreSol Instagram Bot (publicació directa via Instagram API).

Tres modes (variable d'entorn MODE):
  MODE=generate  → genera NOMÉS la imatge del dia a images/ (per fer-ne commit)
  MODE=publish   → publica la imatge del dia (ja penjada a GitHub) a Instagram
                   i escriu el token renovat a new_token.txt
  MODE=check     → no fa res, només informa si avui hi ha post per a aquest SLOT
                   (escriu has_post=true/false a $GITHUB_OUTPUT)

Entorn (GitHub Secrets / Actions):
  IG_ACCESS_TOKEN    — token de llarga durada d'Instagram
  IG_USER_ID         — ID del compte Instagram (Instagram Login)
  GITHUB_REPOSITORY  — usuari/repo (injectat per Actions)
  GITHUB_REF_NAME    — branca (injectat per Actions)
  IMAGES_SUBPATH     — subcarpeta de les imatges al repo
  SLOT               — quin post del dia (1 = el diari del matí, 2 = l'extra del
                       migdia, 3 = l'extra de la tarda)
  TEMPLATE           — opcional: força la plantilla d'imatge (0-5). Si es deixa
                       buit, es tria sola pel hash del nom de fitxer.

Dades:
  data/schedule.csv  → programació editable: data,poble,regio,text,hashtags
                       Es genera amb generate_schedule.py a partir de towns.json,
                       messages.json i local_jokes.json. És la FONT DE VERITAT.

                       Normalment hi ha UNA fila per dia. Per publicar posts
                       EXTRA un dia concret, cal afegir més files amb la mateixa
                       data, just a sota. L'ordre dins del fitxer mana:
                         1a fila → SLOT 1, post del matí    (07:30)
                         2a fila → SLOT 2, extra del migdia (12:50)
                         3a fila → SLOT 3, extra de la tarda (19:30)
                       Hores en hora catalana: els workflows fixen la
                       zona amb 'timezone: Europe/Madrid', o sigui que el
                       canvi d'hora d'estiu/hivern no les mou.
                       Si per a un SLOT no hi ha fila, el workflow acaba sense
                       publicar res.

                       La columna 'hashtags' és opcional i S'AFEGEIX als de
                       sempre (bloc de la regió + hashtag del poble); no els
                       substitueix. Es pot escriure amb coixinet o sense i
                       separada per espais o comes: "#diada onzedesetembre".
                       Els repetits es descarten.
"""

import csv
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from generate_image import create_post_image
from instagram_client import InstagramClient


# ── Configuració ──────────────────────────────────────────────────────────────

FINAL_TEXTS = {
    "cat": (
        "La previsió per als propers dies assegura que aquest temps excepcional "
        "es mantindrà estable.\n\n"
        "SempreSol.Cat: Sempre assolellat arreu del món ☀️\n\n"
        "#sempresol #sempresolcat #meteorologia #meteo #prediccio "
        "#catalunya #visitcatalunya #humorcatala #bontemps #solcat"
    ),
    "bal": (
        "Sa previsió per als pròxims dies assegura que aquest temps excepcional "
        "es mantindrà estable.\n\n"
        "SempreSol.Cat: Sempre assolellat arreu del món ☀️\n\n"
        "#sempresol #sempresolcat #meteorologia #meteo #prediccio "
        "#illésbalears #balears #mallorca #menorca #eivissa #bontemps #solbalears"
    ),
    "val": (
        "La previsió per als pròxims dies assegura que este temps excepcional "
        "es mantindrà estable.\n\n"
        "SempreSol.Cat: Sempre assolellat arreu del món ☀️\n\n"
        "#sempresol #sempresolcat #meteorologia #meteo #prediccio "
        "#paisvalencia #comunidadvalenciana #valencia #bontemps #solvalencia"
    ),
    "aran": (
        "Era previsión per aus pròxims dies assegure que aguest temps exceptionau "
        "se mantendrà estable.\n\n"
        "SempreSol.Cat: Sempre assolellat arreu del món ☀️\n\n"
        "#sempresol #sempresolcat #meteorologia #meteo #prediccio "
        "#valldaran #aran #occitan #aranés #bontemps #solaran"
    ),
}

# Límit d'Instagram per post. El bloc de la regió ja en gasta uns quants;
# la resta és el marge que queda per a la columna 'hashtags'.
MAX_HASHTAGS = 30

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)


# ── Dades ─────────────────────────────────────────────────────────────────────

# Una data pot tenir més d'una fila (post diari + posts extra), per això el
# valor és una llista i no una sola fila: així cap fila es perd pel camí.
SCHEDULE: dict[str, list[dict]] = {}
with open(DATA / "schedule.csv", encoding="utf-8", newline="") as f:
    # restval="" perquè les files antigues (sense columna 'hashtags')
    # continuïn funcionant.
    for _row in csv.DictReader(f, restval=""):
        SCHEDULE.setdefault(_row["data"], []).append(_row)


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_hashtag(town: str) -> str:
    nfd = unicodedata.normalize("NFD", town.lower())
    ascii_str = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return "".join(c for c in ascii_str if c.isalnum())


def build_caption(
    full_message: str, town: str, regio: str, extra_tags: str = ""
) -> str:
    body = full_message.replace("{lugar}", town)
    final = FINAL_TEXTS.get(regio, FINAL_TEXTS["cat"])

    # Els hashtags del bloc de la regió, per no repetir-los si es tornen a
    # escriure a la columna 'hashtags'.
    del_bloc = {w for w in final.lower().split() if w.startswith("#")}

    tags = [f"#{normalize_hashtag(town)}"]
    for brut in extra_tags.replace(",", " ").split():
        tag = brut if brut.startswith("#") else f"#{brut}"
        if tag.lower() in del_bloc or tag.lower() in {t.lower() for t in tags}:
            continue
        tags.append(tag)

    # Instagram no accepta més de MAX_HASHTAGS per post; passar-se'n pot fer
    # que els ignori tots.
    marge = MAX_HASHTAGS - len(del_bloc)
    if len(tags) > marge:
        print(f"  ⚠️  Massa hashtags ({len(del_bloc) + len(tags)} > {MAX_HASHTAGS}). "
              f"Es descarten: {' '.join(tags[marge:])}")
        tags = tags[:marge]

    return f"{body}\n\n{final}\n{' '.join(tags)}"


def github_raw_url(image_filename: str) -> str | None:
    repo = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    subpath = os.environ.get("IMAGES_SUBPATH", "images")
    if repo:
        # El nom pot contenir accents (ex. "Catí"); cal percent-encode perquè
        # el descarregador d'Instagram pugui recuperar la imatge (error 9004 si no).
        safe_name = quote(image_filename)
        return f"https://raw.githubusercontent.com/{repo}/{branch}/{subpath}/{safe_name}"
    return None


def post_for_today(slot: int = 1) -> dict | None:
    """Llegeix de schedule.csv el post d'avui per a aquest slot.

    slot=1 és el post diari (1a fila del dia), slot=2 el primer extra, etc.
    Retorna None si avui no hi ha cap fila per a aquest slot.
    """
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    rows = SCHEDULE.get(date_str, [])
    if slot > len(rows):
        return None
    row = rows[slot - 1]
    town = row["poble"]
    regio = row["regio"]
    message = row["text"]
    caption = build_caption(message, town, regio, row.get("hashtags") or "")
    # El post diari manté el nom de sempre; els extra porten sufix per no
    # trepitjar la imatge del matí si cau el mateix poble.
    suffix = "" if slot == 1 else f"_{slot}"
    image_name = f"{date_str}_{town.replace(' ', '_')}{suffix}.png"
    return {
        "date_str": date_str,
        "slot": slot,
        "town": town,
        "regio": regio,
        "message": message,
        "caption": caption,
        "image_name": image_name,
        "image_path": str(IMG / image_name),
    }


# ── Modes ─────────────────────────────────────────────────────────────────────

def run_generate(p: dict):
    print(f"[GENERA] {p['date_str']} - {p['town']} [{p['regio']}]")
    print(f"   Missatge: {p['message'][:60]}...")
    # Normalment la plantilla es tria sola (hash del nom de fitxer); TEMPLATE
    # permet forçar-ne una en execucions manuals.
    template = os.environ.get("TEMPLATE", "").strip()
    template_idx = int(template) if template else None
    if template_idx is not None:
        print(f"   Plantilla forçada: {template_idx}")
    print("   Generant imatge...")
    create_post_image(p["town"], p["message"], p["image_path"], template_idx)
    print(f"   Imatge: {p['image_path']}")


def run_publish(p: dict):
    img_url = github_raw_url(p["image_name"])
    if not img_url:
        print("   ERROR: falta GITHUB_REPOSITORY per construir la URL de la imatge.")
        sys.exit(1)
    print(f"[PUBLICA] {p['date_str']} - {p['town']} [{p['regio']}]")
    print(f"   URL imatge: {img_url}")

    client = InstagramClient()
    result = client.publish_photo(img_url, p["caption"])
    print(f"   Publicat OK — id: {result.get('id', 'OK')}")

    # Renovació del token (escriu el nou a new_token.txt si s'ha pogut renovar)
    new_token = client.refresh_token()
    if new_token:
        (ROOT / "new_token.txt").write_text(new_token, encoding="utf-8")
        print("   Token renovat (escrit a new_token.txt).")


def run_check(p: dict | None, date_str: str, slot: int):
    """Informa (a Actions) si hi ha post per a aquest slot, sense fer res més."""
    if p:
        print(f"[CHECK] {date_str} slot {slot}: {p['town']} [{p['regio']}] ✓")
    else:
        print(f"[CHECK] {date_str} slot {slot}: cap fila programada.")
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"has_post={'true' if p else 'false'}\n")


def main():
    mode = os.environ.get("MODE", "generate").lower()
    slot = int(os.environ.get("SLOT", "1"))
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    print("=" * 60)
    print(f"  SempreSol Instagram Bot — MODE={mode} SLOT={slot}")
    print("=" * 60)

    p = post_for_today(slot)

    if mode == "check":
        run_check(p, date_str, slot)
        return

    if p is None:
        if slot == 1:
            print(f"   ERROR: no hi ha cap fila a schedule.csv per a {date_str}.")
            print("   Allarga la programació: python generate_schedule.py <dies>")
            sys.exit(1)
        # Els posts extra són opcionals: si avui no n'hi ha, no és cap error.
        print(f"   Avui ({date_str}) no hi ha post extra per al slot {slot}. Res a fer.")
        return

    if mode == "publish":
        run_publish(p)
    else:
        run_generate(p)


if __name__ == "__main__":
    main()
