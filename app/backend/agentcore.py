import argparse
import json
import os
from pathlib import Path
from pydantic import BaseModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from typing import Any, List, Dict # Importa esto

# from app.backend import agent
from agent import get_graph

from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path="../../.env")

class GraphInput(BaseModel):
    doc: str      # Cambiado de str a Dict
    members: str      # Cambiado de str a List
    user_prompt: str

app = BedrockAgentCoreApp()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"

def read_docs() -> tuple:
    doc_pdf = ""
    members = ""
    with open(DATA_DIR / "extraccion_pdf.json", "r", encoding="utf-8") as f:
        # Convertimos el diccionario a una cadena de texto JSON
        doc_pdf = json.dumps(json.load(f), ensure_ascii=False)

    with open(DATA_DIR / "team.json", "r", encoding="utf-8") as f:
        # Convertimos la lista a una cadena de texto JSON
        members = json.dumps(json.load(f), ensure_ascii=False)

    return doc_pdf, members

@app.entrypoint
def strands_agent_bedrock(req: GraphInput):
    """
    Invoke the agent with a payload
    """
    user_input = req.user_prompt
    doc_input = req.doc
    members_input = req.members

    context = f"Este es el documento del proyecto: {doc_input}\nMiembros disponibles: {members_input}\n Input del usuario: {user_input}\n"

    graph = get_graph()

    # print("User input:", context)
    response = graph(context)
    # return response.results[0].text

    partes = {}

    try:
        respuesta_agent_objetivos = response.results["agente_objetivo"].result.message["content"][0]["text"]
        partes["agente_objetivo"] = respuesta_agent_objetivos
    except Exception:
        pass

    try:
        respuesta_agent_tareas = response.results["agente_tareas"].result.message["content"][0]["text"]
        partes["agente_tareas"] = respuesta_agent_tareas
    except Exception:
        pass

    try:
        respuesta_agent_asignar = response.results["agente_asignar"].result.message["content"][0]["text"]
        partes["agente_asignar"] = respuesta_agent_asignar
    except Exception:
        pass

    try:
        respuesta_agent_final = response.results["agente_final"].result.message["content"][0]["text"]
        partes["agente_final"] = respuesta_agent_final
        # print("Entrada del agente final:", response.message['content'][0]['text'])

    except Exception:
        pass

    texto_final = "\n\n".join(partes.values())
    return {"respuesta": texto_final}



if __name__ == "__main__":
    print("Model id: ", os.getenv("BEDROCK_MODEL_ID"))

    doc_input, members_input = read_docs()

    app.run()
    # parser = argparse.ArgumentParser()
    # parser.add_argument("payload", type=str, nargs="?", default="", help="User prompt for the agent")
    # args = parser.parse_args()
    # response = strands_agent_bedrock(GraphInput(doc=doc_input, members=members_input, user_prompt=args.payload))
    # print("Respuesta del agente:", response)
