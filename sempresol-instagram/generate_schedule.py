"""
generate_schedule.py
Genera data/schedule.csv: la programació editable de posts (una fila per post;
normalment un post per dia, però un dia pot tenir-ne més d'un).

Combina:
  data/towns.json      → ordre i regió de cada poble (un poble per dia)
  data/messages.json   → pool de frases genèriques per varietat dialectal
  data/local_jokes.json→ bromes lligades a un poble concret (tenen prioritat)

El resultat (schedule.csv) és la FONT DE VERITAT que llegeix post.py.
És INCREMENTAL: les files que ja existeixen a schedule.csv es conserven tal
qual (amb les teves edicions manuals incloses) i només s'afegeixen dies nous
al final. Mai sobreescriu ni escurça el que ja hi ha.

Ús:
  python generate_schedule.py [dies]
  (per defecte: una rotació completa = tants dies com pobles)
"""

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# Ha de coincidir amb la data de llançament que interpreta post.py.
START_DATE = datetime(2026, 6, 1, tzinfo=timezone.utc)

with open(DATA / "towns.json", encoding="utf-8") as f:
    TOWNS: list[dict] = json.load(f)

with open(DATA / "messages.json", encoding="utf-8") as f:
    MESSAGES: dict[str, list[str]] = json.load(f)

with open(DATA / "local_jokes.json", encoding="utf-8") as f:
    LOCAL_JOKES: dict[str, list[str]] = json.load(f)


def generic_message(idx: int, regio: str, town: str) -> str:
    pool = MESSAGES.get(regio, MESSAGES["cat"])
    return pool[idx % len(pool)].replace("{lugar}", town)


def load_existing() -> dict[str, list[dict]]:
    """Llegeix schedule.csv si ja existeix (per conservar edicions manuals).

    Una data pot tenir més d'una fila (posts extra); es conserven totes i en
    el mateix ordre.
    """
    out = DATA / "schedule.csv"
    if not out.exists():
        return {}
    existing: dict[str, list[dict]] = {}
    with open(out, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, restval=""):
            existing.setdefault(row["data"], []).append(row)
    return existing


def main():
    requested = int(sys.argv[1]) if len(sys.argv) > 1 else len(TOWNS)
    existing = load_existing()

    # Cobrim com a mínim el que demanen i tot el que ja hi ha (mai escurçar).
    horizon = requested
    if existing:
        first = START_DATE.date()
        last_existing = max(
            datetime.strptime(d, "%Y-%m-%d").date() for d in existing
        )
        horizon = max(horizon, (last_existing - first).days + 1)

    local_seen: dict[str, int] = {}
    rows = []
    n_kept = 0
    n_new = 0
    for idx in range(horizon):
        date = (START_DATE + timedelta(days=idx)).strftime("%Y-%m-%d")
        town_obj = TOWNS[idx % len(TOWNS)]
        town = town_obj["nom"]
        regio = town_obj["regio"]

        # Avancem el comptador de bromes locals sempre (preservades o no),
        # perquè la selecció determinista no es desincronitzi.
        is_local = town in LOCAL_JOKES
        if is_local:
            k = local_seen.get(town, 0)
            local_seen[town] = k + 1

        if date in existing:
            rows.extend(existing[date])   # inclou els posts extra del dia
            n_kept += len(existing[date])
            continue

        if is_local:
            jokes = LOCAL_JOKES[town]
            text = jokes[k % len(jokes)].replace("{lugar}", town)
        else:
            text = generic_message(idx, regio, town)

        rows.append({"data": date, "poble": town, "regio": regio, "text": text})
        n_new += 1

    out = DATA / "schedule.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["data", "poble", "regio", "text", "hashtags"], restval=""
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"schedule.csv: {horizon} dies, {len(rows)} files "
          f"({rows[0]['data']} - {rows[-1]['data']})")
    print(f"  conservades: {n_kept} | noves: {n_new}")


if __name__ == "__main__":
    main()
