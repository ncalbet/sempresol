# ☀️ SempreSol Instagram Bot

Bot que publica automàticament a l'Instagram de [sempresol.cat](https://sempresol.cat).
Publica **fins a tres posts al dia** — matí (07:30), migdia (12:50) i tarda
(19:30), hora catalana — cadascun amb:

- Una **imatge 1080×1080** amb el nom del poble i una frase enginyosa
- Un **caption** amb el missatge complet, el lema i els hashtags
- Un **hashtag del poble** del dia, més els que hi posis a la columna `hashtags`

Del dia només és obligatòria la fila del matí: les altres dues es publiquen
només si `data/schedule.csv` té 2a i 3a fila per a aquella data.

---

## Com funciona

```
GitHub Actions (3 crons, hora catalana)
  schedule.yml        07:30 → SLOT 1
  schedule-extra.yml  12:50 → SLOT 2
                      19:30 → SLOT 3
        │
        ▼
  post.py, en tres passades (variable MODE):
  • MODE=check     hi ha fila per a aquest SLOT? (només als extra)
  • MODE=generate  crea la imatge amb generate_image.py (Pillow)
  • MODE=publish   la penja a Instagram i renova el token
        │
        ▼
  La imatge es commiteja a images/ i es puja al repo:
  Instagram se la descarrega per la URL raw de GitHub,
  o sigui que ha de ser pública abans de publicar.
        │
        ▼
  Instagram API (graph.instagram.com, Instagram Login) ☀️
```

La programació surt sempre de **`data/schedule.csv`**, que és la **font de
veritat**: `post.py` no improvisa res, només llegeix la fila que toca.

El CSV es genera amb `generate_schedule.py` combinant:

| Fitxer                 | Contingut                                                     |
|------------------------|---------------------------------------------------------------|
| `data/towns.json`      | 840 pobles amb la seva regió, en l'ordre de la rotació (un per dia) |
| `data/messages.json`   | ~460 frases genèriques, per varietat dialectal (`cat`, `bal`, `val`, `aran`) |
| `data/local_jokes.json`| Bromes lligades a un poble concret; tenen prioritat sobre les genèriques |

---

## Configuració

### Secrets del repositori

**Settings > Secrets and variables > Actions**

| Secret            | Per a què serveix                                                  |
|-------------------|--------------------------------------------------------------------|
| `IG_ACCESS_TOKEN` | Token de llarga durada d'Instagram (Instagram Login)               |
| `IG_USER_ID`      | ID del compte d'Instagram                                          |
| `GH_PAT`          | Token personal de GitHub amb permís sobre secrets, per a l'auto-renovació |

El token d'Instagram caduca. Cada publicació el renova: `post.py` escriu el
token nou a `new_token.txt` i l'últim pas del workflow el desa amb
`gh secret set IG_ACCESS_TOKEN`, fent servir el `GH_PAT`. Si el token té menys
de 24 h, Instagram no el renova i el pas ho diu al log; és normal.

### El repositori ha de ser públic

Instagram descarrega la imatge per la URL raw de GitHub. Si el repo fos privat,
no la podria recuperar i la publicació fallaria.

---

## Execució manual (local)

```bash
pip install -r requirements.txt

# Quin post toca avui? (no publica res)
MODE=check python post.py

# Genera la imatge d'avui a images/ (no publica res)
MODE=generate python post.py

# Un dels posts extra: SLOT 2 = migdia, SLOT 3 = tarda
MODE=generate SLOT=2 python post.py
```

Per veure les sis plantilles d'imatge d'un cop, sense tocar la programació:

```bash
python generate_image.py
# Crea test_sempresol_{classica,capgirada,lateral,radial,llevant,nit}.png
# a /tmp (o C:/Windows/Temp a Windows)
```

Normalment la plantilla es tria sola pel hash del nom del fitxer. Amb
`TEMPLATE=0..5` en pots forçar una, tant en local com al *Run workflow*.

---

## Personalització

### Afegir un post extra un dia concret

`data/schedule.csv` admet **fins a tres files per data**, una per cada hora de
publicació. Només cal afegir-les just a sota de la del dia, en ordre:

```csv
2026-08-20,Berga,cat,"A {lugar}, el sol fa hores extra."     ← matí  (07:30)
2026-08-20,Gandia,val,"A {lugar}, ..."                        ← migdia (12:50)
2026-08-20,Cardona,cat,"A {lugar}, ..."                       ← tarda  (19:30)
```

- Si un dia no té 2a o 3a fila, el workflow extra acaba sense publicar res.
- La imatge dels extra porta sufix: `2026-08-20_Gandia_2.png`.
- Les hores són hora catalana tot l'any (`timezone: Europe/Madrid` als crons).
- Per publicar-ne un fora d'hora: **Actions > SempreSol – Post extra > Run
  workflow** i posa-hi el número de slot.

Recorda editar el `schedule.csv` **de GitHub** (és la font de veritat) o fer
`git pull` abans de tocar el local.

### Hashtags a mida

La 5a columna, `hashtags`, és opcional i **s'afegeix** als de sempre (el bloc de
la regió més el hashtag del poble); no els substitueix:

```csv
2026-09-11,Moià,cat,"A {lugar}, ...",#diada #onzedesetembre
```

- Es pot escriure amb coixinet o sense, separat per espais o per comes.
- Els que ja siguin al bloc de la regió o al del poble es descarten.
- Instagram n'accepta 30 per post: si te'n passes, els sobrants es descarten i
  el log de l'execució t'avisa.
- Deixar la cel·la buida (o no posar-hi columna) és el comportament de sempre.

### Afegir noves frases

`data/messages.json` està organitzat **per varietat dialectal**. Afegeix la
frase a la llista que toqui i fes servir `{lugar}` com a marcador del poble:

```json
{
  "cat": ["A {lugar}, el sol ha decidit fer hores extra. Per amor a l'art."],
  "bal": ["A {lugar}, es sol no s'atura mai."],
  "val": ["A {lugar}, este sol no afluixa."],
  "aran": ["En {lugar}, eth sòu non s'ature jamès."]
}
```

Per a una broma d'un poble concret, `data/local_jokes.json`, amb el nom del
poble com a clau. Tenen prioritat sobre les genèriques.

Cap de les dues coses no toca el que ja hi ha programat: les frases noves
només entren als dies que `generate_schedule.py` afegeixi de nou al final.

### Canviar les hores de publicació

El post del matí és a `.github/workflows/schedule.yml` i els dos extra a
`.github/workflows/schedule-extra.yml`. Els crons van en hora catalana:

```yaml
- cron: "30 7 * * *"        # 07:30, tot l'any
  timezone: Europe/Madrid
```

Dues coses a tenir en compte si les toques:

- Evita l'hora en punt: Actions va carregat a l'inici de cada hora i hi
  endarrereix les execucions programades (per això el migdia és a les 12:50).
- A `schedule-extra.yml`, el pas *Decideix quin SLOT toca* reparteix migdia i
  tarda pel tall de les 16:00, hora catalana. Si mous un post a l'altra banda
  d'aquesta hora, canvia també el tall.

---

## Manteniment de la programació

```bash
python generate_schedule.py [dies]
```

Allarga `schedule.csv` amb dies nous al final. **És incremental i segur**: no
sobreescriu ni escurça res del que ja hi ha, edicions manuals incloses.

```bash
python rebalance_towns.py [dies]
```

Reordena `towns.json` per mantenir la proporció 60% cat / 25% val / 10% bal /
5% aran i torna a generar la programació de zero.

⚠️ **Només conserva les files EXTRA (2a i 3a de cada dia).** La del matí la
regenera a partir de `towns.json` i s'emporta per davant el poble i el text que
hi hagis escrit a mà. Si tens un post del matí preparat per a una data concreta,
no l'executis.

---

## Estructura del projecte

Aquest bot viu dins del repositori del web de sempresol.cat, que n'ocupa
l'arrel (`index.html`, `manifest.json`, `sw.js`…).

```
.github/
└── workflows/
    ├── schedule.yml        # Post del matí (07:30)
    └── schedule-extra.yml  # Posts de migdia (12:50) i tarda (19:30)
sempresol-instagram/
├── data/
│   ├── schedule.csv        # FONT DE VERITAT: data,poble,regio,text,hashtags
│   ├── towns.json          # 840 pobles i la seva regió, en ordre de rotació
│   ├── messages.json       # ~460 frases per varietat dialectal
│   └── local_jokes.json    # Bromes lligades a un poble concret
├── images/                 # Imatges generades (auto-commit; les llegeix Instagram)
├── post.py                 # Script principal (MODE=check|generate|publish)
├── generate_image.py       # Generador d'imatges Pillow (6 plantilles)
├── instagram_client.py     # Client de la Instagram API + renovació del token
├── generate_schedule.py    # Allarga schedule.csv (incremental)
├── rebalance_towns.py      # Reordena towns.json i regenera la programació
├── buffer_client.py        # Llegat de l'època de Buffer; ja no s'usa
├── requirements.txt        # Pillow, requests
└── README.md
```

---

## Llicència

Projecte de [sempresol.cat](https://sempresol.cat). Sempre assolellat arreu del món ☀️
