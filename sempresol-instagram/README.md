# ☀️ SempreSol Instagram Bot

Bot que programa automàticament posts d'Instagram per a [sempresol.cat](https://sempresol.cat), publica 1 post diari amb:

- Una **imatge 1080×1080** amb el nom del poble i una frase enginyosa
- Un **caption** amb el missatge complet, el lema i els hashtags
- Un **hashtag del poble** del dia

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

### Canviar la freqüència de GitHub Actions

Edita `.github/workflows/schedule.yml`:
```yaml
- cron: "0 7 */5 * *"   # Cada 5 dies
- cron: "0 7 */7 * *"   # Cada setmana
```

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
│       └── schedule.yml    # GitHub Actions (cada 5 dies)
├── generate_image.py       # Generador d'imatges Pillow
├── buffer_client.py        # Client API Buffer
├── post.py                 # Script principal
├── requirements.txt
└── README.md
```

---

## Llicència

Projecte de [sempresol.cat](https://sempresol.cat). Sempre assolellat arreu del món ☀️
