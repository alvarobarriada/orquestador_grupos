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
    "horas necesarias previstas, personas necesarias y conocimientos para realizarla"
    "proporcionada por el agente anterior y compararlas con el catálogo de personal disponible en el contexto. "
    "Tu tarea: "
    "1. Analiza el campo 'conocimientos' de cada tarea. "
    "2. Realiza el match óptimo: asigna nombres de personas reales a cada tarea basándote en sus habilidades y experiencia. Valora la experiencia, "
    "pero no limites la selección a las personas que tengan más años de experiencia, incluye personas con menos experiencia cuando lo consideres necesario."
    "3. Si una tarea requiere 3 personas y solo hay 2 aptas, señala esta carencia como un riesgo crítico. "
    "Entrega un listado estructurado de Tarea -> Responsables Asignados."
)

PROMPT_FINAL = (
    "Actúa como un Director de Operaciones (COO) experto en optimización de costes y tiempos. "
    "Tu misión es consolidar toda la información anterior en un Plan de Proyecto Final. "
    "Pasos a seguir: "
    "1. Revisión Global: Analiza el flujo de tareas, horas y personal asignado. "
    "2. Optimización: Si detectas sobrecarga de trabajo en una persona, redistribuye plazos o sugiere cambios. "
    "3. Validación de Hitos: Asegúrate de que el plan respeta los hitos clave si se mencionan en la descripción del proyecto."
    "4. Estimación de Deadlines: Calcula la fecha de finalización total basada en la ruta crítica del proyecto. "
    "5. Resumen Ejecutivo: Presenta un informe con Tabla de Tareas, Responsables, Coste de tiempo total, recomendaciones y líder del proyecto elegido según su experiencia. "
    "Una vez generado este informe, el proceso se considera FINALIZADO."
)


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
# hook para debugear y ver que campos que llegan
agente_final = Agent(
    name="agente_final",
    model=bedrock_model,
    system_prompt=PROMPT_ASIGNAR,
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
