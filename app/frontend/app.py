# Dependencies
import json
import os
import tempfile
from pathlib import Path

import fitz  # pymupdf
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from utils import generate_pdf_bytes


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Orquestador de proyectos", page_icon="📆", layout="wide")

# ── Minimal CSS (functional only, dark theme provided by Streamlit) ───────────
st.markdown("""
<style>
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
    [data-testid="stFileUploaderDropzone"] button span {
        font-size: 0 !important; visibility: hidden;
    }
    .empty-state {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; min-height: 40vh; gap: 12px; opacity: 0.45;
    }
    .empty-state span { font-size: 3rem; }
    .empty-state p { font-size: 1rem; margin: 0; }
    section[data-testid="stSidebar"] h4 {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.4rem !important;
        margin-top: 1.2rem !important;
        letter-spacing: 0.01em;
    }
</style>
""", unsafe_allow_html=True)

# ── Backend URL ───────────────────────────────────────────────────────────────
API_URL = "http://localhost:8080/v1/agente/"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_pdf_text(uploaded_files) -> tuple[str, str]:
    """Extract text from PDF files using pymupdf.
    Returns (plain_text_for_api, json_str_for_download).
    """
    texts = []
    json_entries = []

    for uf in uploaded_files:
        suffix = Path(uf.name).suffix.lower()
        try:
            if suffix == ".pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uf.getvalue())
                    tmp_path = tmp.name
                try:
                    doc = fitz.open(tmp_path)
                    pages = [page.get_text() for page in doc]
                    num_pages = len(pages)
                    pages_text = "\n".join(pages)
                    doc.close()
                finally:
                    os.unlink(tmp_path)
                json_entries.append({
                    "nombre": uf.name,
                    "paginas": num_pages,
                    "contenido": pages_text,
                })
            else:
                pages_text = uf.getvalue().decode("utf-8", errors="ignore")
                json_entries.append({
                    "nombre": uf.name,
                    "contenido": pages_text,
                })

            texts.append(f"[Archivo: {uf.name}]\n{pages_text}")

            # ── Log to terminal ──
            print(f"\n{'='*60}")
            print(f"[PDF LOG] Archivo: {uf.name} | Caracteres: {len(pages_text)}")
            print(f"[PDF LOG] Primeros 500 chars:\n{pages_text[:500]}")
            print(f"{'='*60}\n")

        except Exception as exc:
            texts.append(f"[Archivo: {uf.name} — error al leer: {exc}]")
            json_entries.append({"nombre": uf.name, "error": str(exc)})
            print(f"[PDF LOG] ERROR leyendo {uf.name}: {exc}")

    plain_text = "\n\n---\n\n".join(texts)
    json_str = json.dumps({"documentos": json_entries}, ensure_ascii=False, indent=2)
    return plain_text, json_str


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Organizador de equipos y proyectos")
st.markdown("*Acelera la puesta en marcha de proyectos: sube tu idea y encuentra al equipo idóneo*")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Sube tu idea (PDF/docs del proyecto) ──
    st.markdown("#### Sube tu idea")
    idea_files = st.file_uploader(
        label="",
        accept_multiple_files=True,
        type=["pdf", "txt", "doc", "docx", "json"],
        key="idea_uploader",
        label_visibility="hidden",
    )

    if idea_files:
        file_key = tuple(f.name + str(f.size) for f in idea_files)
        if st.session_state.get("_idea_files_key") != file_key:
            with st.spinner("Leyendo documentos..."):
                idea_text, idea_json = _read_pdf_text(idea_files)
                st.session_state.idea_text = idea_text
                st.session_state.idea_json = idea_json
                st.session_state._idea_files_key = file_key
        total_chars = len(st.session_state.get("idea_text", ""))
        st.success(f"✅ {len(idea_files)} archivo(s) · {total_chars:,} chars")
        with st.expander("Ver extracción"):
            st.download_button(
                label="⬇ Descargar extracción (JSON)",
                data=st.session_state.get("idea_json", "{}"),
                file_name="extraccion_pdf.json",
                mime="application/json",
                use_container_width=True,
            )
            st.code(st.session_state.get("idea_text", "")[:2000], language="text")
    else:
        st.session_state.pop("idea_text", None)
        st.session_state.pop("idea_json", None)
        st.session_state.pop("_idea_files_key", None)

    # ── Sube tu equipo (JSON crudo, sin preprocesar) ──
    st.markdown("#### Sube tu equipo")
    team_file = st.file_uploader(
        label="",
        accept_multiple_files=False,
        type=["json", "txt", "doc", "docx", "pdf"],
        key="team_uploader",
        label_visibility="hidden",
    )

    if team_file:
        team_key = team_file.name + str(team_file.size)
        if st.session_state.get("_team_file_key") != team_key:
            # JSON passed through as-is, no preprocessing
            st.session_state.team_text = team_file.getvalue().decode("utf-8", errors="ignore")
            st.session_state._team_file_key = team_key
            print(f"\n[TEAM LOG] Archivo: {team_file.name} | Contenido:\n{st.session_state.team_text[:500]}\n")
        st.success(f"✅ {team_file.name} cargado")
    else:
        st.session_state.pop("team_text", None)
        st.session_state.pop("_team_file_key", None)

    num_workers = st.slider(label="Número de trabajadores", min_value=1, max_value=50,
                            value=st.session_state.get("num_workers", 5))
    st.session_state.num_workers = num_workers

    # ── Generar planificación (siempre habilitado) ──
    if st.button("Generar planificación", type="primary", use_container_width=True):
        payload: dict = {
            "pdf_json":    st.session_state.get("idea_json", "{}"),
            "team_json":   st.session_state.get("team_text", "{}"),
            "num_workers": st.session_state.get("num_workers", 1),
        }

        with st.spinner("Consultando al modelo..."):
            try:
                respuesta = requests.post(API_URL, json=payload)
                print(f"[RESPONSE STATUS] {respuesta.status_code}")
                print(f"[RESPONSE TEXT] {respuesta.text}")
                print(f"[RESPONSE HEADERS] {respuesta.headers}")
                plan_data = respuesta.json()
                print(f"\n[API RESPONSE]\n{json.dumps(plan_data, ensure_ascii=False, indent=2)}\n")
                if "error" in plan_data:
                    st.error(f"⚠️ El agente devolvió un error: {plan_data['error']}")
                else:
                    st.session_state.plan_data = plan_data
                    st.session_state.plan_generado = True
            except Exception as e:
                st.error(f"⚠️ Error al conectar con la API: {e}")
                print(f"[API ERROR] {e}")

    _plan_for_download = st.session_state.get("plan_data")
    if _plan_for_download:
        plan_text = json.dumps(_plan_for_download, ensure_ascii=False, indent=2)
        st.download_button(
            label="Descargar planificación (JSON)",
            data=plan_text,
            file_name="planificacion.json",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
            use_container_width=True,
        )
        st.download_button(
            label="Descargar planificación (PDF)",
            data=generate_pdf_bytes(_plan_for_download),
            file_name="planificacion.pdf",
            mime="application/pdf",
            on_click="ignore",
            type="secondary",
            icon=":material/picture_as_pdf:",
            use_container_width=True,
        )

# ── Main area: tabs ───────────────────────────────────────────────────────────
plan_generado = st.session_state.get("plan_generado", False)
plan_data     = st.session_state.get("plan_data", None)

if plan_generado and plan_data:
    team_members = plan_data.get("team_members", [])
    tab_labels   = ["📊 Resumen", "📋 Gantt"] + [f"👤 {m['name']}" for m in team_members]
    all_tabs     = st.tabs(tab_labels)
    tab_inicio   = None
    tab_resumen  = all_tabs[0]
    tab_gantt    = all_tabs[1]
    worker_tabs  = all_tabs[2:]
else:
    all_tabs    = st.tabs(["🚀 Inicio"])
    tab_inicio  = all_tabs[0]
    tab_resumen = tab_gantt = None
    worker_tabs = []

# ── Tab Inicio ────────────────────────────────────────────────────────────────
if tab_inicio is not None:
    with tab_inicio:

        st.markdown("""
        ### ¿Cómo funciona?

        1. **Sube tu idea** — carga el PDF o documento con la descripción del proyecto (barra lateral).
        2. **Sube tu equipo** — carga el JSON con los perfiles de los trabajadores disponibles.
        3. **Ajusta el número de trabajadores** con el slider.
        4. Pulsa **Generar planificación** — los agentes analizarán los documentos y crearán el plan.
        5. Revisa el **Resumen**, el **Gantt** y las pestañas individuales por trabajador.
        6. Descarga el resultado con **Descargar planificación**.
        """)

# ── Tab Resumen ───────────────────────────────────────────────────────────────
if tab_resumen is not None:
    with tab_resumen:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Proyecto",        plan_data["project_title"])
        col2.metric("Presupuesto Est.", f"{plan_data['total_budget']:,.0f} €")
        col3.metric("Fecha de Entrega", plan_data["estimated_completion_date"])
        col4.metric("Líder",            plan_data.get("project_leader", "—"))

        st.divider()

        objetivos = plan_data.get("objetivos", [])
        if objetivos:
            st.markdown("#### Objetivos")
            for obj in objetivos:
                st.markdown(f"- {obj}")

        assignments_resumen = plan_data.get("assignments", [])
        if assignments_resumen:
            st.markdown("#### Tareas")
            task_rows = []
            for a in assignments_resumen:
                assignees = a.get("assigned_to", "")
                if isinstance(assignees, list):
                    assignees = ", ".join(assignees)
                task_rows.append({
                    "Tarea":       a.get("task_name", ""),
                    "Responsable": assignees,
                    "Horas":       a.get("hours", "—"),
                    "Prioridad":   a.get("priority", "—"),
                })
            st.dataframe(pd.DataFrame(task_rows), use_container_width=True, hide_index=True)

        st.divider()

        st.markdown("#### Equipo")
        team_rows = [
            {"Nombre": m["name"], "Rol": m["role"],
             "Tareas": len(m["tasks"]), "Horas totales": m["total_hours"]}
            for m in plan_data.get("team_members", [])
        ]
        if team_rows:
            st.dataframe(pd.DataFrame(team_rows), use_container_width=True, hide_index=True)

# ── Tab Gantt ─────────────────────────────────────────────────────────────────
if tab_gantt is not None:
    with tab_gantt:
        assignments = plan_data.get("assignments", [])
        if not assignments:
            st.info("No hay tareas en el plan.")
        else:
            # Normalizar assigned_to: puede ser lista o string
            rows = []
            for a in assignments:
                assignees = a["assigned_to"]
                if isinstance(assignees, list):
                    assignees_str = ", ".join(assignees)
                else:
                    assignees_str = assignees
                rows.append({**a, "assigned_to": assignees_str})

            df = pd.DataFrame(rows)
            df["start_date"] = pd.to_datetime(df["start_date"])
            df["end_date"]   = pd.to_datetime(df["end_date"])

            hover = [c for c in ["priority", "hours", "description"] if c in df.columns]
            fig = px.timeline(
                df,
                x_start="start_date",
                x_end="end_date",
                y="task_name",
                color="assigned_to",
                hover_data=hover,
                labels={"task_name": "Tarea", "assigned_to": "Responsable"},
                title="Cronograma de Ejecución (Gantt)",
                template="plotly_dark",
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(xaxis_title="Línea de Tiempo", yaxis_title="Tareas", legend_title="Equipo")
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Ver detalle de asignaciones"):
                detail_cols = [c for c in ["task_name", "assigned_to", "hours", "priority", "skills"] if c in df.columns]
                st.dataframe(df[detail_cols], use_container_width=True, hide_index=True)

# ── Tabs por trabajador ───────────────────────────────────────────────────────
for tab, member in zip(worker_tabs, plan_data.get("team_members", []) if plan_data else []):
    with tab:
        col1, col2, col3 = st.columns(3)
        col1.metric("Nombre", member["name"])
        col2.metric("Rol",    member["role"])
        col3.metric("Horas totales", member["total_hours"])

        st.divider()

        # Tareas asignadas a este miembro
        member_tasks = [
            a for a in plan_data.get("assignments", [])
            if member["name"] in (a["assigned_to"] if isinstance(a["assigned_to"], list) else [a["assigned_to"]])
        ]
        if member_tasks:
            st.markdown("#### Tareas asignadas")
            rows = []
            for a in member_tasks:
                rows.append({
                    "Tarea":       a["task_name"],
                    "Inicio":      a["start_date"],
                    "Fin":         a["end_date"],
                    "Horas":       a.get("hours", "—"),
                    "Prioridad":   a.get("priority", "—"),
                    "Descripción": a.get("description", "—"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            skills_all = []
            for a in member_tasks:
                skills_all.extend(a.get("skills", []))
            if skills_all:
                st.divider()
                st.markdown("#### Habilidades requeridas")
                st.write(", ".join(sorted(set(skills_all))))
        else:
            st.info("Sin tareas asignadas.")
