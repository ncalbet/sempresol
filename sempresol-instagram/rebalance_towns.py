"""
rebalance_towns.py
Reordena towns.json perquè la distribució de regions sigui:
  60% cat, 25% val, 10% bal, 5% aran

Patró per bloc de 20: c,c,v,c,c,v,b,c,c,v,c,c,v,b,c,c,v,c,a,c
  → 12 cat, 5 val, 2 bal, 1 aran = 60/25/10/5% ✓

Després trunca schedule.csv fins a la data d'ahir (inclusive) i regenera
la programació completa amb generate_schedule.py.

Ús: python rebalance_towns.py [dies_de_schedule]
"""

import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT    = Path(__file__).parent
DATA    = ROOT / "data"
TOWNS_F = DATA / "towns.json"
SCHED_F = DATA / "schedule.csv"

PATTERN = [
    "cat", "cat", "val", "cat", "cat", "val", "bal",
    "cat", "cat", "val", "cat", "cat", "val", "bal",
    "cat", "cat", "val", "cat", "aran", "cat",
]  # 12 cat, 5 val, 2 bal, 1 aran per bloc de 20 → 60/25/10/5%

TOTAL = 840   # longitud del cicle de towns.json


def reorder_towns():
    with open(TOWNS_F, encoding="utf-8") as f:
        towns = json.load(f)

    pools = {"cat": [], "val": [], "bal": [], "aran": []}
    for t in towns:
        pools[t["regio"]].append(t)

    counters = {k: 0 for k in pools}
    result = []
    for i in range(TOTAL):
        region = PATTERN[i % len(PATTERN)]
        pool   = pools[region]
        result.append(pool[counters[region] % len(pool)])
        counters[region] += 1

    from collections import Counter
    dist = Counter(t["regio"] for t in result)
    print("Nova distribució towns.json:")
    for k in ["cat", "val", "bal", "aran"]:
        print(f"  {k}: {dist[k]} ({dist[k]/TOTAL*100:.1f}%)")

    with open(TOWNS_F, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"towns.json reescrit ({TOTAL} entrades).\n")


def truncate_schedule() -> list[dict]:
    """Manté només les files publicades (fins a ahir inclusive).

    Retorna els posts EXTRA de dates futures (2a fila i següents d'un mateix
    dia), que no es poden regenerar automàticament i es reinsereixen després.
    """
    yesterday = (datetime.now(tz=timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    if not SCHED_F.exists():
        print("schedule.csv no existeix, s'ometrà la truncació.")
        return []

    with open(SCHED_F, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    kept: list[dict] = []
    extras: list[dict] = []
    seen_future: set[str] = set()
    for r in rows:
        if r["data"] <= yesterday:
            kept.append(r)
        elif r["data"] in seen_future:
            extras.append(r)      # post extra d'un dia futur: el salvem
        else:
            seen_future.add(r["data"])

    print(f"schedule.csv: es conserven {len(kept)} files (fins a {yesterday}).")
    print(f"  S'eliminaran {len(rows) - len(kept) - len(extras)} files futures per regenerar.")
    if extras:
        print(f"  Es preserven {len(extras)} posts extra futurs.")
    print()

    with open(SCHED_F, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "poble", "regio", "text"])
        writer.writeheader()
        writer.writerows(kept)

    return extras


def reinsert_extras(extras: list[dict]):
    """Torna a col·locar els posts extra darrere del post diari de la seva data."""
    if not extras:
        return

    with open(SCHED_F, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    # L'ordenació de Python és estable: per a una mateixa data, les files
    # regenerades (rows) queden abans que els extra.
    merged = rows + extras
    merged.sort(key=lambda r: r["data"])

    with open(SCHED_F, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "poble", "regio", "text"])
        writer.writeheader()
        writer.writerows(merged)

    print(f"Reinserits {len(extras)} posts extra.")


def regenerate(days):
    print(f"Regenerant schedule.csv per als pròxims {days} dies...")
    subprocess.run([sys.executable, str(ROOT / "generate_schedule.py"), str(days)], check=True)


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else TOTAL
    reorder_towns()
    extras = truncate_schedule()
    regenerate(days)
    reinsert_extras(extras)
    print("\nFet! Pots fer push al repositori GitHub.")
