"""
generate_schedule.py
Genera data/schedule.csv: la programació editable de posts (un dia per fila).

Combina:
  data/towns.json      → ordre i regió de cada poble (un poble per dia)
  data/messages.json   → pool de frases genèriques per varietat dialectal
  data/local_jokes.json→ bromes lligades a un poble concret (tenen prioritat)

El resultat (schedule.csv) és la FONT DE VERITAT que llegeix post.py.
Es pot editar a mà; torna a executar aquest script només si vols regenerar-lo
o allargar-lo (p. ex. canvis a towns.json/messages.json).

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


def main():
    horizon = int(sys.argv[1]) if len(sys.argv) > 1 else len(TOWNS)
    local_seen: dict[str, int] = {}

    rows = []
    for idx in range(horizon):
        date = (START_DATE + timedelta(days=idx)).strftime("%Y-%m-%d")
        town_obj = TOWNS[idx % len(TOWNS)]
        town = town_obj["nom"]
        regio = town_obj["regio"]

        if town in LOCAL_JOKES:
            jokes = LOCAL_JOKES[town]
            k = local_seen.get(town, 0)
            text = jokes[k % len(jokes)].replace("{lugar}", town)
            local_seen[town] = k + 1
        else:
            text = generic_message(idx, regio, town)

        rows.append({"data": date, "poble": town, "regio": regio, "text": text})

    out = DATA / "schedule.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "poble", "regio", "text"])
        writer.writeheader()
        writer.writerows(rows)

    n_local = sum(local_seen.values())
    print(f"schedule.csv generat: {len(rows)} dies ({rows[0]['data']} - {rows[-1]['data']})")
    print(f"  bromes locals col·locades: {n_local} ({', '.join(sorted(local_seen))})")


if __name__ == "__main__":
    main()
