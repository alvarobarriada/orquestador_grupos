# Dependencias
from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent import agent

# Inicializa una instancia de la aplicación
app = FastAPI()

# Modelo de datos de entrada
class PromptRequest(BaseModel):
    prompt: str


# Creación de endpoint del agente
@app.post("/v1/agente/", tags=["agente-consultas"])
def chat(req: PromptRequest):
    # Enviar el prompt al agente y obtener la respuesta generada
    respuesta = agent(req.prompt)
    # Extraer el texto principal desde la respuesta JSON del modelo
    try:
        texto = respuesta["message"]["content"][0]["text"]
    except Exception:
        # Si el formato de la respuesta no es el esperado, devolver todo el objeto como texto
        texto = str(respuesta)  # fallback en caso de formato inesperado
    # Devolver la respuesta procesada en formato JSON
    return {"respuesta": texto}


if __name__ == "__main__":
    import uvicorn
    # Ejecutar la aplicación con Uvicorn en el puerto 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)