from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session


from dotenv import load_dotenv
load_dotenv()

# Configurar la sesión de AWS
boto_session = Session()

# Inicializar el runtime
agentcore_runtime = Runtime()

# Nombre del agente (debe ser único)
AGENT_NAME = "orquestador_grupos_agent"

# Configurar el despliegue
response = agentcore_runtime.configure(
    entrypoint="backend/agentcore.py",      # Ruta a tu entrypoint
    requirements_file="requirements.txt",     # Archivo de dependencias
    region="eu-west-1",                      # Región de AWS
    agent_name=AGENT_NAME,                   # Nombre del agente
    auto_create_execution_role=True,         # Crear rol automáticamente
    auto_create_ecr=True,                    # Crear repositorio ECR automáticamente
)

print(f"Configuración completada: {response}")

# Continuando desde setup_agentcore.py
launch_result = agentcore_runtime.launch()
print(f"Agente desplegado: {launch_result.agent_arn}")
