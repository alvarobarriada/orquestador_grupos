#Dependencias
import streamlit as st
import requests

# Configuración de la interfaz
st.set_page_config(page_title="Agente con Strands", page_icon="🤖")
st.title("🤖 Agente con Strands")

# URL de la API del backend
API_URL = "http://localhost:8080/v1/agente/"

# Manejo del historial de conversación
# Inicializa la lista de mensajes si no existe en la sesión actual
if "historial" not in st.session_state:
    st.session_state.historial = []

# Muestra los mensajes previos (usuario y asistente) en el chat
for mensaje in st.session_state.historial:
    if mensaje["rol"] == "usuario":
        with st.chat_message("user"):
            st.markdown(mensaje["contenido"])
    else:
        with st.chat_message("assistant"):
            st.markdown(mensaje["contenido"])

# Entrada de texto del usuario
prompt = st.chat_input("Escribe tu mensaje para el modelo")

if prompt:
    # Guarda el mensaje del usuario en el historial
    st.session_state.historial.append({"rol": "usuario", "contenido": prompt})
    # Muestra el mensaje del usuario en la interfaz de chat
    with st.chat_message("user"):
        st.markdown(prompt)
    # Enviar el prompt al backend
    with st.spinner("Consultando al modelo"):
        try:
            # Realiza la solicitud POST al endpoint del agente
            respuesta = requests.post(API_URL, json={"prompt": prompt})
            contenido = respuesta.json()["respuesta"]
        except Exception as e:
            # En caso de error en la conexión o formato de respuesta
            contenido = f"⚠️ Error al conectar con la API: {e}"

    # Mostrar y guardar la respuesta del modelo
    st.session_state.historial.append({"rol": "asistente", "contenido": contenido})
    with st.chat_message("assistant"):
        st.markdown(contenido)