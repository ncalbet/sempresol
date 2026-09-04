# ☀️ SempreSol Instagram Bot

Bot que programa automàticament posts d'Instagram per a [sempresol.cat](https://sempresol.cat).
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
GitHub Actions (cada 5 dies)
        │
        ▼
  post.py llegeix:
  • data/messages.json  → 203 missatges humorístics
  • data/towns.json     → 290+ pobles catalans
        │
        ▼
  generate_image.py
  → Crea imatge 1080×1080 (Pillow)
        │
        ▼
  buffer_client.py
  → Programa 5 posts a Buffer
        │
        ▼
  Buffer publica 1 post per dia a Instagram ☀️
```

---

## Configuració inicial

### 1. Fork / clona aquest repositori

Crea un repositori nou a GitHub (públic, per poder usar les URLs raw de les imatges).

### 2. Crea un compte Buffer

- Registra't a [buffer.com](https://buffer.com) (pla **Essentials ~5$/mes** per posts il·limitats)
- Connecta el teu compte d'Instagram Business
- Configura l'hora de publicació diària a Buffer (p.ex. 10:00 AM)

### 3. Obtén la clau API de Buffer

- Buffer > Settings > **API** > Generate API Key
- Copia l'ID del perfil Instagram: Buffer > Settings > Channels > copia l'ID

### 4. Afegeix secrets a GitHub

Al teu repositori: **Settings > Secrets and variables > Actions > New repository secret**

| Secret              | Valor                                      |
|---------------------|--------------------------------------------|
| `BUFFER_API_KEY`    | La clau API que has generat a Buffer       |
| `BUFFER_PROFILE_ID` | L'ID del perfil Instagram a Buffer         |

### 5. Activa GitHub Actions

- Ves a la pestanya **Actions** del teu repo
- Activa els workflows si no estan activats
- Prova manualment: **Actions > SempreSol > Run workflow**

---

## Execució manual (local)

```bash
pip install -r requirements.txt

# Configura variables d'entorn
export BUFFER_API_KEY="la_teva_clau"
export BUFFER_PROFILE_ID="el_teu_profile_id"

python post.py
```

Per provar la generació d'imatges sense publicar:

```bash
python generate_image.py
# Crea /tmp/test_sempresol.png
```

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
- `generate_schedule.py` i `rebalance_towns.py` conserven les files extra.

Recorda editar el `schedule.csv` **de GitHub** (és la font de veritat) o fer
`git pull` abans de tocar el local.

⚠️ `rebalance_towns.py` només conserva les files EXTRA (2a i 3a de cada dia):
regenera la del matí a partir de `towns.json` i s'emporta per davant el poble i
el text que hi hagis escrit a mà. Si tens un post del matí preparat per a una
data concreta, no l'executis.

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

### Afegir nous missatges

Edita `data/messages.json` i afegeix les teves frases. Usa `{lugar}` com a placeholder del poble:

```json
"A {lugar}, el sol ha decidit fer hores extra. Per amor a l'art."
```

### Canviar l'hora de publicació

Edita `post.py`:
```python
POST_HOUR = 10   # Hora UTC (10 = 12h hora espanyola estiu)
```

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

## Estructura del projecte

```
sempresol-instagram/
├── data/
│   ├── messages.json       # 203 missatges humorístics
│   └── towns.json          # 290+ pobles catalans
├── images/                 # Imatges generades (auto-commit)
├── .github/
│   └── workflows/
│       ├── schedule.yml       # Post del matí (07:30)
│       └── schedule-extra.yml # Posts de migdia i tarda
├── generate_image.py       # Generador d'imatges Pillow
├── buffer_client.py        # Client API Buffer
├── post.py                 # Script principal
├── requirements.txt
└── README.md
```

---

## Llicència

Projecte de [sempresol.cat](https://sempresol.cat). Sempre assolellat arreu del món ☀️
