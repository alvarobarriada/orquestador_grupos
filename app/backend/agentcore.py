import os
from pydantic import BaseModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from typing import Any

from backend.agent import get_graph

from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path="../.env")

class GraphInput(BaseModel):
    doc: str = "Informacion extraida del documento del proyecto"
    members: str = "Informacion extraida de los JSON con los miembros disponibles para integrar el proyecto"
    user_prompt: str = "Comentarios adicionales del usuario"


def _normalize_payload(req: Any) -> GraphInput:
    """Normaliza el payload independientemente del formato que envíe la UI."""
    if isinstance(req, GraphInput):
        return req

    if isinstance(req, BaseModel):
        data = req.model_dump()
    elif isinstance(req, dict):
        data = req
    else:
        # Algunos runtimes pueden enviar texto plano.
        data = {"user_prompt": str(req)}

    # Soporta payloads anidados típicos: {"input": {...}} o {"body": {...}}
    for wrapper_key in ("input", "body", "payload", "request"):
        nested = data.get(wrapper_key)
        if isinstance(nested, dict):
            data = nested
            break

    return GraphInput.model_validate(data)


def _debug_dump_request(req: Any) -> None:
    """Imprime trazas útiles del payload crudo para diagnóstico en CloudWatch."""
    print("[DEBUG] request_type:", type(req).__name__)

    try:
        req_repr = repr(req)
    except Exception as exc:
        req_repr = f"<repr_error: {repr(exc)}>"

    if len(req_repr) > 1500:
        req_repr = req_repr[:1500] + "...<truncated>"
    print("[DEBUG] request_repr:", req_repr)

    if isinstance(req, BaseModel):
        try:
            dumped = req.model_dump()
            print("[DEBUG] request_model_dump:", dumped)
            print("[DEBUG] request_model_keys:", list(dumped.keys()))
        except Exception as exc:
            print("[DEBUG] request_model_dump_error:", repr(exc))

    if isinstance(req, dict):
        print("[DEBUG] request_dict_keys:", list(req.keys()))
        preview = {k: type(v).__name__ for k, v in req.items()}
        print("[DEBUG] request_dict_value_types:", preview)

app = BedrockAgentCoreApp()

@app.entrypoint
def strands_agent_bedrock(req: Any):
    """
    Invoke the agent with a payload
    """
    print("Ejecutando strands_agent_bedrock(req: Any) ...")
    _debug_dump_request(req)

    try:
        parsed_req = _normalize_payload(req)
        print("Payload normalizado:", parsed_req.model_dump())
    except Exception as exc:
        print("Error normalizando payload:", repr(exc))
        return {
            "ok": False,
            "error_stage": "payload_normalization",
            "error": repr(exc),
            "hint": "Prueba con {'doc':'...','members':'...','user_prompt':'...'}",
        }

    user_input = parsed_req.user_prompt
    doc_input = parsed_req.doc
    members_input = parsed_req.members

    context = f"Este es el documento del proyecto: {doc_input}\nMiembros disponibles: {members_input}\n Input del usuario: {user_input}\n"

    print("Contexto para el grafo:\n", context)

    graph = get_graph()

    try:
        response = graph(context)
    except Exception as exc:
        # Devuelve detalle para evitar 500 opaco durante diagnóstico.
        print("Error ejecutando el grafo:", repr(exc))
        return {
            "ok": False,
            "error_stage": "graph_execution",
            "error": repr(exc),
        }

    respuesta_agent_final = None

    try:
        respuesta_agent_final = response.results["agente_final"].result.structured_output
    except Exception as exc:
        print("No se pudo extraer agente_final.structured_output:", repr(exc))

    if respuesta_agent_final is not None:
        return respuesta_agent_final.model_dump()

    # Fallback de diagnostico si el structured output no llega.
    partes = []
    for node_name in ("agente_objetivo", "agente_tareas", "agente_asignar", "agente_final"):
        try:
            text = response.results[node_name].result.message["content"][0]["text"]
            if isinstance(text, str) and text.strip():
                partes.append(f"[{node_name}]\n{text}")
        except Exception as exc:
            print(f"No se pudo extraer texto de {node_name}:", repr(exc))

    return {
        "ok": False,
        "error_stage": "final_structured_output_missing",
        "error": "agente_final no devolvio structured_output valido",
        "fallback_text": "\n\n".join(partes) if partes else str(response),
    }



if __name__ == "__main__":
    print("Model id: ", os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-pro-v1:0"))
    app.run()
