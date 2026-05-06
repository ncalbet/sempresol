"""
post.py
Script principal de SempreSol Instagram Bot.

Execució: python post.py
Entorn (GitHub Secrets):
  BUFFER_API_KEY      — clau API de Buffer (Settings > API)
  BUFFER_PROFILE_ID   — ID del perfil Instagram a Buffer (opcional, autodetectat)
  GITHUB_REPOSITORY   — nom del repo (p.ex. usuari/sempresol-instagram), injectat per GitHub Actions
  DAYS_AHEAD          — quants dies programar (per defecte 5)
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from generate_image import create_post_image
from buffer_client   import BufferClient


# ── Configuració ──────────────────────────────────────────────────────────────

START_DATE   = datetime(2026, 5, 1, tzinfo=timezone.utc)   # Data d'inici del projecte
POST_HOUR    = 10                                            # Hora de publicació (UTC)
DAYS_AHEAD   = int(os.environ.get("DAYS_AHEAD", 5))

FINAL_TEXT   = (
    "La previsió per als propers dies assegura que aquest temps excepcional "
    "es mantindrà estable.\n\n"
    "SempreSol.Cat: Sempre assolellat arreu del món ☀️\n\n"
    "#sempresol #sempresolcat #meteorologia #meteo #prediccio "
    "#catalunya #visitcatalunya #humorcatala #bontemps #solcat"
)

ROOT = Path(__file__).parent
DATA = ROOT / "data"
IMG  = ROOT / "images"
IMG.mkdir(exist_ok=True)


# ── Dades ─────────────────────────────────────────────────────────────────────

with open(DATA / "messages.json", encoding="utf-8") as f:
    MESSAGES: list[str] = json.load(f)

with open(DATA / "towns.json", encoding="utf-8") as f:
    TOWNS: list[str] = json.load(f)


# ── Helpers ───────────────────────────────────────────────────────────────────

def day_index(date: datetime) -> int:
    """Índex del dia des de START_DATE (0, 1, 2, …)."""
    return (date.replace(tzinfo=timezone.utc) - START_DATE).days


def get_message(idx: int) -> str:
    return MESSAGES[idx % len(MESSAGES)]


def get_town(idx: int) -> str:
    return TOWNS[idx % len(TOWNS)]


def build_caption(full_message: str, town: str) -> str:
    """Construeix el caption complet del post d'Instagram."""
    body = full_message.replace("{lugar}", town)
    return f"{body}\n\n{FINAL_TEXT}\n#{town.lower().replace(' ', '').replace("'", '').replace('-', '')}"


def github_raw_url(image_filename: str) -> str | None:
    """URL pública raw de GitHub per a la imatge (si el repo és públic)."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if repo:
        return f"https://raw.githubusercontent.com/{repo}/{branch}/images/{image_filename}"
    return None


# ── Lògica principal ──────────────────────────────────────────────────────────

def process_day(client: BufferClient, profile_id: str, target_date: datetime):
    """Genera la imatge i programa el post per a un dia concret."""
    idx      = day_index(target_date)
    message  = get_message(idx)
    town     = get_town(idx)
    caption  = build_caption(message, town)

    date_str   = target_date.strftime("%Y-%m-%d")
    image_name = f"{date_str}_{town.replace(' ', '_')}.png"
    image_path = str(IMG / image_name)

    print(f"\n📅 {date_str} — {town}")
    print(f"   Missatge #{idx % len(MESSAGES)}: {message[:60]}…")

    # ── Genera imatge ──────────────────────────────────────────────────────
    print("   🎨 Generant imatge…")
    create_post_image(town, message, image_path)
    print(f"   ✅ Imatge: {image_path}")

    # ── URL de la imatge (GitHub raw) ──────────────────────────────────────
    img_url = github_raw_url(image_name)
    if img_url:
        print(f"   🔗 URL imatge: {img_url}")

    # ── Hora de publicació ─────────────────────────────────────────────────
    scheduled = target_date.replace(hour=POST_HOUR, minute=0, second=0)
    scheduled_iso = scheduled.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Publica a Buffer ───────────────────────────────────────────────────
    print("   📤 Afegint a Buffer…")
    try:
        result = client.add_to_queue(
            profile_id   = profile_id,
            text         = caption,
            image_path   = image_path,
            image_url    = img_url,
            scheduled_at = scheduled_iso,
        )
        print(f"   ✅ Buffer: {result.get('id', 'OK')}")
    except Exception as e:
        print(f"   ❌ Error Buffer: {e}")
        # No para l'execució — continua amb el dia següent
        return False

    return True


def main():
    print("=" * 60)
    print("☀️  SempreSol Instagram Bot")
    print("=" * 60)

    # ── Clients ────────────────────────────────────────────────────────────
    try:
        client = BufferClient()
    except KeyError:
        print("❌ Falta BUFFER_API_KEY a les variables d'entorn.")
        sys.exit(1)

    try:
        profile_id = client.get_instagram_profile_id()
        print(f"📱 Perfil Instagram Buffer: {profile_id}")
    except Exception as e:
        print(f"❌ No s'ha pogut obtenir el perfil: {e}")
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
    print(f"✅ Programats {success}/{DAYS_AHEAD} posts correctament.")
    print("=" * 60)


if __name__ == "__main__":
    main()
