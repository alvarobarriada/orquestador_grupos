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

## Ejecución con AgentCore y Streamlit

Para conectar ambos servicios ejecuta estos comandos colocado en la carpeta `app`:

1. Depliegue del sistema en AgentCore Runtime (cada vez que se hagan cambios en algun fichero de la carpeta `backend`):
```bash
python setup_agentcore.py
```
En caso de que el despliegue sea correcto, se mostrara al final el identificador ARN del componente desplegado

```bash
...
Agente desplegado: arn:aws:bedrock-agentcore:eu-west-1:...:runtime/orquestador_grupos_agent_AC-...
```

2. Necesitaras incluir el fallback al cargar la variable AGENTCORE_AGENT_ARN del .env en el fichero `frontend/streamlit_with_agentcore.py`
```python
AGENTCORE_AGENT_ARN = os.getenv("AGENTCORE_AGENT_ARN", "arn:aws:bedrock-agentcore:eu-west-1:...:runtime/orquestador_grupos_agent_AC-...")
```

3. Ejecutar el frontend de streamlit ubicados desde la carpeta `app`:
```bash
streamlit run frontend/streamlit_with_agentcore.py
```
