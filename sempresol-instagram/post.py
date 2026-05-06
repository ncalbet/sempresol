"""
post.py
Script principal de SempreSol Instagram Bot.

Execució: python post.py
Entorn (GitHub Secrets):
  BUFFER_API_KEY      — clau API de Buffer (Settings > API)
  BUFFER_PROFILE_ID   — ID del perfil Instagram a Buffer (opcional, autodetectat)
  GITHUB_REPOSITORY   — nom del repo (p.ex. usuari/sempresol-instagram), injectat per GitHub Actions
  DAYS_AHEAD          — quants dies programar (per defecte 5)

Estructura de dades esperada:
  data/towns.json     → llista d'objectes {"nom": "Cardedeu", "regio": "cat"}
                        regions: "cat" | "bal" | "val" | "aran"
  data/messages.json  → diccionari {"cat": [...], "bal": [...], "val": [...], "aran": [...]}
"""

import json
import os
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from generate_image import create_post_image
from buffer_client   import BufferClient


# ── Configuració ──────────────────────────────────────────────────────────────

START_DATE   = datetime(2026, 5, 1, tzinfo=timezone.utc)   # Data d'inici del projecte
POST_HOUR    = 10                                            # Hora de publicació (UTC)
DAYS_AHEAD   = int(os.environ.get("DAYS_AHEAD", 5))

# Final texts per regió — inclouen el lema, l'atribució i els hashtags
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
IMG  = ROOT / "images"
IMG.mkdir(exist_ok=True)


# ── Dades ─────────────────────────────────────────────────────────────────────

with open(DATA / "towns.json", encoding="utf-8") as f:
    TOWNS: list[dict] = json.load(f)          # [{"nom": "Cardedeu", "regio": "cat"}, ...]

with open(DATA / "messages.json", encoding="utf-8") as f:
    MESSAGES: dict[str, list[str]] = json.load(f)   # {"cat": [...], "bal": [...], ...}


# ── Helpers ───────────────────────────────────────────────────────────────────

def day_index(date: datetime) -> int:
    """Índex del dia des de START_DATE (0, 1, 2, ...)."""
    return (date.replace(tzinfo=timezone.utc) - START_DATE).days


def get_town(idx: int) -> dict:
    """Retorna l'objecte del poble del dia: {"nom": ..., "regio": ...}."""
    return TOWNS[idx % len(TOWNS)]


def get_message(idx: int, regio: str) -> str:
    """Tria el missatge del dia dins la llista de la regió correcta."""
    msgs = MESSAGES.get(regio, MESSAGES["cat"])
    return msgs[idx % len(msgs)]


def normalize_hashtag(town: str) -> str:
    """Converteix el nom del poble en un hashtag vàlid per Instagram."""
    # Descompon caràcters accentuats (NFD) i elimina els diacrítics
    nfd = unicodedata.normalize("NFD", town.lower())
    ascii_str = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # Elimina qualsevol caràcter no alfanumèric (espais, guions, apostrofes...)
    return "".join(c for c in ascii_str if c.isalnum())


def build_caption(full_message: str, town: str, regio: str) -> str:
    """Construeix el caption complet del post d'Instagram."""
    body  = full_message.replace("{lugar}", town)
    final = FINAL_TEXTS.get(regio, FINAL_TEXTS["cat"])
    tag   = normalize_hashtag(town)
    return f"{body}\n\n{final}\n#{tag}"


def github_raw_url(image_filename: str) -> str | None:
    """URL pública raw de GitHub per a la imatge (si el repo és públic)."""
    repo   = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if repo:
        return f"https://raw.githubusercontent.com/{repo}/{branch}/images/{image_filename}"
    return None


# ── Lògica principal ──────────────────────────────────────────────────────────

def process_day(client: BufferClient, profile_id: str, target_date: datetime):
    """Genera la imatge i programa el post per a un dia concret."""
    idx = day_index(target_date)

    # Poble i regió del dia
    town_obj = get_town(idx)
    town     = town_obj["nom"]
    regio    = town_obj["regio"]

    # Missatge de la regió corresponent
    message = get_message(idx, regio)
    caption = build_caption(message, town, regio)

    date_str   = target_date.strftime("%Y-%m-%d")
    image_name = f"{date_str}_{town.replace(' ', '_')}.png"
    image_path = str(IMG / image_name)

    print(f"\n📅 {date_str} — {town} [{regio}]")
    print(f"   Missatge: {message[:60]}...")

    # ── Genera imatge ──────────────────────────────────────────────────────
    print("   Generant imatge...")
    create_post_image(town, message, image_path)
    print(f"   Imatge: {image_path}")

    # ── URL de la imatge (GitHub raw) ──────────────────────────────────────
    img_url = github_raw_url(image_name)
    if img_url:
        print(f"   URL imatge: {img_url}")

    # ── Hora de publicació ─────────────────────────────────────────────────
    scheduled     = target_date.replace(hour=POST_HOUR, minute=0, second=0)
    scheduled_iso = scheduled.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Publica a Buffer ───────────────────────────────────────────────────
    print("   Afegint a Buffer...")
    try:
        result = client.add_to_queue(
            profile_id   = profile_id,
            text         = caption,
            image_path   = image_path,
            image_url    = img_url,
            scheduled_at = scheduled_iso,
        )
        print(f"   Buffer OK: {result.get('id', 'OK')}")
    except Exception as e:
        print(f"   Error Buffer: {e}")
        return False

    return True


def main():
    print("=" * 60)
    print("  SempreSol Instagram Bot")
    print("=" * 60)
    print(f"   Pobles carregats : {len(TOWNS)}")
    for reg in ["cat", "bal", "val", "aran"]:
        n = sum(1 for t in TOWNS if t["regio"] == reg)
        print(f"   Pobles {reg:<6}   : {n}")
    print(f"   Missatges cat    : {len(MESSAGES.get('cat', []))}")
    print(f"   Missatges bal    : {len(MESSAGES.get('bal', []))}")
    print(f"   Missatges val    : {len(MESSAGES.get('val', []))}")
    print(f"   Missatges aran   : {len(MESSAGES.get('aran', []))}")

    # ── Clients ────────────────────────────────────────────────────────────
    try:
        client = BufferClient()
    except KeyError:
        print("Falta BUFFER_API_KEY a les variables d'entorn.")
        sys.exit(1)

    try:
        profile_id = client.get_instagram_profile_id()
        print(f"\n   Perfil Instagram Buffer: {profile_id}")
    except Exception as e:
        print(f"No s'ha pogut obtenir el perfil: {e}")
        sys.exit(1)

    # ── Dies a programar ───────────────────────────────────────────────────
    today   = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    success = 0

    for i in range(DAYS_AHEAD):
        target = today + timedelta(days=i + 1)   # comença demà
        ok = process_day(client, profile_id, target)
        if ok:
            success += 1

    print("\n" + "=" * 60)
    print(f"Programats {success}/{DAYS_AHEAD} posts correctament.")
    print("=" * 60)


if __name__ == "__main__":
    main()
