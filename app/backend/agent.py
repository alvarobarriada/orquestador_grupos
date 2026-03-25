from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import GraphBuilder
from typing import List

load_dotenv()

REGION_NAME = os.getenv("AWS_REGION", "eu-west-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-pro-v1:0")
TEMP = float(os.getenv("MODEL_TEMPERATURE", "0.6"))
MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "1024"))

print("Región:", REGION_NAME)
print("Modelo:", MODEL_ID)

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION_NAME,
    temperature=TEMP,
)

PROMPT_OBJETIVO = (
    "Actúa como un Senior Project Manager experto en definición estratégica."
    "Tu misión es recibir la descripción de un proyecto y extraer los Objetivos Generales."
    "Tu salida debe incluir:"
    " - El propósito principal del proyecto."
    " - Una lista de 3 a 5 objetivos SMART (Específicos, Medibles, Alcanzables, Relevantes y a Tiempo)."
    " - El alcance (qué se incluye y qué no)."
    "RESTRICCIÓN CRÍTICA: El mensaje indica el número máximo de trabajadores a asignar. "
    "Debes leer ese número, mencionarlo explícitamente en tu salida y asegurarte de que los agentes siguientes lo respeten. "
    "Este límite es vinculante para todo el plan: no se puede superar en ningún caso. "
    "Mantén un tono profesional y enfocado a resultados. Este análisis será la base para que el siguiente agente desglose las tareas técnicas."
    "No añadas requisitos que no se piden si no es estrictamente necesario."
)

PROMPT_TAREAS = (
    "Actúa como un Arquitecto de Software y Gestor de Operaciones. Basándote en los objetivos del proyecto, "
    "debes desglosar el trabajo en una lista de tareas técnicas detalladas. "
    "Reglas estrictas de validación: "
    "- Horas: Estima el esfuerzo real de ejecución. "
    "- Personas: Debes asignar entre 1 y 4 personas por tarea (según la complejidad técnica). Nunca excedas este límite. "
    "- Conocimientos: Identifica las tecnologías o habilidades específicas (ej: 'Python', 'React', 'AWS'). "
    "Formato de salida: Debes responder exclusivamente siguiendo el esquema OrganizacionTareas. "
    "Asegúrate de que cada Tarea tenga una descripción clara que permita al siguiente agente saber a quién asignar."
)

PROMPT_ASIGNAR = (
    "Actúa como un Responsable de Recursos Humanos (HRBP). Tu función es recibir la lista de tareas, su descripción, "
    "horas necesarias previstas, personas necesarias y conocimientos para realizarla "
    "proporcionada por el agente anterior y compararlas con el catálogo de personal disponible en el contexto. "
    "RESTRICCIÓN CRÍTICA: El mensaje indica el número máximo de trabajadores a asignar. "
    "Bajo ningún concepto puedes superar ese número total de personas únicas en todas las asignaciones combinadas. "
    "Si el límite es 1, solo puede aparecer 1 persona en todo el plan. Si es 3, un máximo de 3 personas distintas. "
    "Tu tarea: "
    "1. Revisa los miembros disponibles, ya que puede ser que no todos esten disponibles durante el periodo de desarrollo. "
    "2. Analiza el campo 'conocimientos' de cada tarea. "
    "3. Realiza el match óptimo respetando el límite: asigna nombres de personas reales a cada tarea basándote en sus habilidades y experiencia. "
    "Si el límite no permite cubrir todos los conocimientos, indica el riesgo pero respeta el límite. "
    "4. Si una tarea requiere más personas de las disponibles en el límite, señala esta carencia como un riesgo crítico. "
    "Entrega un listado estructurado de Tarea -> Responsables Asignados."
)

PROMPT_FINAL = (
    "Actúa como un Director de Operaciones (COO) experto en optimización de costes y tiempos. "
    "Tu misión es consolidar toda la información anterior en un Plan de Proyecto Final estructurado. "
    "RESTRICCIÓN CRÍTICA: Respeta estrictamente el número máximo de trabajadores indicado en el mensaje inicial. "
    "El plan final no puede incluir más personas únicas que ese límite. Elimina o fusiona asignaciones si es necesario para cumplirlo. "
    "Pasos a seguir: "
    "1. Revisión Global: Analiza el flujo de tareas, horas y personal asignado. "
    "2. Optimización: Si detectas sobrecarga de trabajo en una persona, redistribuye plazos o sugiere cambios. "
    "3. Validación de Hitos: Asegúrate de que el plan respeta los hitos clave si se mencionan en la descripción del proyecto. "
    "4. Estimación de Deadlines: Calcula la fecha de finalización total basada en la ruta crítica del proyecto. "
    "5. Elige el líder del proyecto basándote en la experiencia y responsabilidad del equipo. "
    "FORMATO DE SALIDA OBLIGATORIO: Debes responder exclusivamente siguiendo el esquema PlanFinal. "
    "Cada tarea en 'assignments' debe tener: task_name, assigned_to (lista de nombres reales), "
    "start_date y end_date (formato YYYY-MM-DD), hours (entero), priority (Alta/Media/Baja). "
    "Cada miembro en 'team_members' debe tener: name, role, tasks (lista de task_name asignados), total_hours (entero). "
    "El campo 'objetivos' debe ser una lista de strings con los objetivos SMART del proyecto. "
    "No incluyas texto adicional fuera del esquema."
)


class TaskAssignment(BaseModel):
    task_name: str = Field(description="Nombre de la tarea")
    assigned_to: List[str] = Field(description="Lista de nombres de las personas asignadas")
    start_date: str = Field(description="Fecha de inicio en formato YYYY-MM-DD")
    end_date: str = Field(description="Fecha de fin en formato YYYY-MM-DD")
    hours: int = Field(description="Horas estimadas de esfuerzo")
    priority: str = Field(description="Prioridad: Alta, Media o Baja")


class TeamMember(BaseModel):
    name: str = Field(description="Nombre completo del trabajador")
    role: str = Field(description="Rol o puesto del trabajador en el proyecto")
    tasks: List[str] = Field(description="Lista de nombres de tareas asignadas a este trabajador")
    total_hours: int = Field(description="Total de horas asignadas a este trabajador")


class PlanFinal(BaseModel):
    project_title: str = Field(description="Título del proyecto")
    total_budget: float = Field(description="Presupuesto total estimado en euros")
    estimated_completion_date: str = Field(description="Fecha estimada de finalización en formato YYYY-MM-DD")
    project_leader: str = Field(description="Nombre del líder del proyecto")
    objetivos: List[str] = Field(description="Lista de objetivos SMART del proyecto")
    assignments: List[TaskAssignment] = Field(description="Lista de tareas con sus asignaciones")
    team_members: List[TeamMember] = Field(description="Lista de miembros del equipo con sus horas y tareas")


class Tarea(BaseModel):
    horas: int = Field(description="Horas requeridas para realizar la tarea")
    personas: int = Field(
        description="Número de personas necesarias para realizar la tarea",
        ge=1,
        le=4
        )
    conocimientos: List[str] = Field(description="Lista de conocimientos técnicos necesarios para realizar la tarea")
    descripción: str = Field(description="Descripción breve de la tarea")


class OrganizacionTareas(BaseModel):
    tareas: List[Tarea]


agente_objetivo = Agent(
    name="agente_objetivo",
    model=bedrock_model,
    system_prompt=PROMPT_OBJETIVO,
)

agente_tareas = Agent(
    name="agente_tareas",
    model=bedrock_model,
    system_prompt=PROMPT_TAREAS,
    structured_output_model=OrganizacionTareas,
)

agente_asignar = Agent(
    name="agente_asignar",
    model=bedrock_model,
    system_prompt=PROMPT_ASIGNAR,
)
agente_final = Agent(
    name="agente_final",
    model=bedrock_model,
    system_prompt=PROMPT_FINAL,
    structured_output_model=PlanFinal,
)

builder = GraphBuilder()

builder.add_node(agente_objetivo, "agente_objetivo")
builder.add_node(agente_tareas, "agente_tareas")
builder.add_node(agente_asignar, "agente_asignar")
builder.add_node(agente_final, "agente_final")

builder.add_edge("agente_objetivo", "agente_tareas")
builder.add_edge("agente_tareas", "agente_asignar")
builder.add_edge("agente_asignar", "agente_final")

builder.set_entry_point("agente_objetivo")
builder.set_execution_timeout(600)
builder.set_node_timeout(300)

graph = builder.build()
print("Graph construido")

def get_graph():
    return graph
