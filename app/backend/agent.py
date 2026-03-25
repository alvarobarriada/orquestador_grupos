#Dependencias
import os
from strands import Agent
from strands.models import BedrockModel

from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env

REGION_NAME = os.getenv("AWS_REGION", "eu-west-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0")
TEMP = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "1024"))

print("Región:", REGION_NAME)
print("Modelo:", MODEL_ID)

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION_NAME,
    temperature=TEMP,
    max_tokens=MAX_TOKENS,
)

# Creación del agente con el modelo configurado
agent = Agent(model=bedrock_model)