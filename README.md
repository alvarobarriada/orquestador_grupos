# Orquestador_grupos

Herramienta multiagente para organizar equipos y herramientas.

### Create a virtual environment (Python 3.12 at least)

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate environment:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```


## Ejecución en paralelo (frontend + backend)

Necesitas **dos terminales abiertas a la vez** en `simple-app-tools`.

### Terminal 1: backend (API)

```bash
uvicorn backend.api_base:app --port 8080 --reload
```

Backend disponible en: `http://localhost:8080`

### Terminal 2: frontend (Streamlit)

```bash
streamlit run frontend/app.py
```

Frontend disponible normalmente en: `http://localhost:8501`