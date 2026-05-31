"""
post.py
Script principal de SempreSol Instagram Bot (publicació directa via Instagram API).

Dos modes (variable d'entorn MODE):
  MODE=generate  → genera NOMÉS la imatge del dia a images/ (per fer-ne commit)
  MODE=publish   → publica la imatge del dia (ja penjada a GitHub) a Instagram
                   i escriu el token renovat a new_token.txt

Entorn (GitHub Secrets / Actions):
  IG_ACCESS_TOKEN    — token de llarga durada d'Instagram
  IG_USER_ID         — ID del compte Instagram (Instagram Login)
  GITHUB_REPOSITORY  — usuari/repo (injectat per Actions)
  GITHUB_REF_NAME    — branca (injectat per Actions)
  IMAGES_SUBPATH     — subcarpeta de les imatges al repo

Dades:
  data/towns.json    → [{"nom": "Cardedeu", "regio": "cat"}, ...]
  data/messages.json → {"cat": [...], "bal": [...], "val": [...], "aran": [...]}
"""

import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from generate_image import create_post_image
from instagram_client import InstagramClient


# ── Configuració ──────────────────────────────────────────────────────────────

START_DATE = datetime(2026, 5, 1, tzinfo=timezone.utc)   # Data d'inici del projecte

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

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)


# ── Dades ─────────────────────────────────────────────────────────────────────

with open(DATA / "towns.json", encoding="utf-8") as f:
    TOWNS: list[dict] = json.load(f)

with open(DATA / "messages.json", encoding="utf-8") as f:
    MESSAGES: dict[str, list[str]] = json.load(f)


# ── Helpers ───────────────────────────────────────────────────────────────────

def day_index(date: datetime) -> int:
    return (date.replace(tzinfo=timezone.utc) - START_DATE).days


def get_town(idx: int) -> dict:
    return TOWNS[idx % len(TOWNS)]


def get_message(idx: int, regio: str) -> str:
    msgs = MESSAGES.get(regio, MESSAGES["cat"])
    return msgs[idx % len(msgs)]


def normalize_hashtag(town: str) -> str:
    nfd = unicodedata.normalize("NFD", town.lower())
    ascii_str = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return "".join(c for c in ascii_str if c.isalnum())


def build_caption(full_message: str, town: str, regio: str) -> str:
    body = full_message.replace("{lugar}", town)
    final = FINAL_TEXTS.get(regio, FINAL_TEXTS["cat"])
    tag = normalize_hashtag(town)
    return f"{body}\n\n{final}\n#{tag}"


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


def post_for_today() -> dict:
    """Calcula tot el que cal per al post d'avui (determinista a partir de la data)."""
    today = datetime.now(tz=timezone.utc)
    idx = day_index(today)
    town_obj = get_town(idx)
    town = town_obj["nom"]
    regio = town_obj["regio"]
    message = get_message(idx, regio)
    caption = build_caption(message, town, regio)
    date_str = today.strftime("%Y-%m-%d")
    image_name = f"{date_str}_{town.replace(' ', '_')}.png"
    return {
        "date_str": date_str,
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
    print("   Generant imatge...")
    create_post_image(p["town"], p["message"], p["image_path"])
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


def main():
    mode = os.environ.get("MODE", "generate").lower()
    print("=" * 60)
    print(f"  SempreSol Instagram Bot — MODE={mode}")
    print("=" * 60)

    p = post_for_today()

    if mode == "publish":
        run_publish(p)
    else:
        run_generate(p)


if __name__ == "__main__":
    main()
