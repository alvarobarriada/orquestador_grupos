# Dependencias
from collections import Counter
from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent import graph


def enforce_worker_limit(plan: dict, num_workers: int) -> dict:
    """Hard-cap the plan to at most num_workers unique people."""
    assignments = plan.get("assignments", [])
    if not assignments:
        return plan

    # Count how many tasks each person has (proxy for importance)
    task_count: Counter = Counter()
    for a in assignments:
        assignees = a.get("assigned_to", [])
        if isinstance(assignees, str):
            assignees = [assignees]
        for person in assignees:
            task_count[person] += 1

    # Keep only the top num_workers people (most tasks = most critical)
    allowed = {person for person, _ in task_count.most_common(num_workers)}
    print(f"[WORKER LIMIT] limit={num_workers}, all={set(task_count)}, kept={allowed}")

    # Filter assignments: remove people not in allowed, drop task if nobody left
    filtered_assignments = []
    for a in assignments:
        assignees = a.get("assigned_to", [])
        if isinstance(assignees, str):
            assignees = [assignees]
        trimmed = [p for p in assignees if p in allowed]
        if trimmed:
            filtered_assignments.append({**a, "assigned_to": trimmed})

    # Filter team_members
    team_members = plan.get("team_members", [])
    filtered_team = [m for m in team_members if m.get("name") in allowed]

    # Recalculate total_hours per remaining member
    hours_by_person: dict = {}
    for a in filtered_assignments:
        for person in a["assigned_to"]:
            hours_by_person[person] = hours_by_person.get(person, 0) + a.get("hours", 0)
    for m in filtered_team:
        m["total_hours"] = hours_by_person.get(m["name"], m.get("total_hours", 0))
        m["tasks"] = [
            a["task_name"] for a in filtered_assignments if m["name"] in a["assigned_to"]
        ]

    return {**plan, "assignments": filtered_assignments, "team_members": filtered_team}


# Inicializa una instancia de la aplicación
app = FastAPI()

# Modelo de datos de entrada
class PromptRequest(BaseModel):
    pdf_json: str = ""
    team_json: str = ""
    num_workers: int = 1


# Creación de endpoint del agente
@app.post("/v1/agente/", tags=["agente-consultas"])
def chat(req: PromptRequest):
    # Construir el mensaje completo con los datos estructurados recibidos
    partes = []
    if req.pdf_json:
        partes.append(f"[DESCRIPCIÓN DEL PROYECTO]\n{req.pdf_json}")
    if req.team_json:
        partes.append(f"[EQUIPO DISPONIBLE]\n{req.team_json}")
    partes.append(f"Número máximo de trabajadores a asignar: {req.num_workers}")
    partes.append("Genera la planificación completa del proyecto.")
    mensaje = "\n\n".join(partes)

    # Enviar el mensaje al grafo de agentes
    resultado = graph(mensaje)
    print(f"[GRAPH RESULT] {resultado}")

    # Extraer resultado estructurado del nodo final
    try:
        node_result = resultado.results["agente_final"]
        agent_result = node_result.result
        print(f"[AGENT RESULT] {agent_result}")

        plan = agent_result.structured_output.model_dump()
        return enforce_worker_limit(plan, req.num_workers)

    except Exception as e:
        print(f"[API ERROR] {e}")
        return {"error": str(e), "raw": str(resultado)}


if __name__ == "__main__":
    import uvicorn
    # Ejecutar la aplicación con Uvicorn en el puerto 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)
