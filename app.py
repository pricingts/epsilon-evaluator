import streamlit as st
from io import BytesIO
from pathlib import Path
import pandas as pd
import tempfile, os

from main import run_pipeline 
from dotenv import load_dotenv ; load_dotenv() 

st.set_page_config(page_title="Calificador ÉPSILON", layout="centered")
st.header("📊 Calificador automático – Sistema ÉPSILON")

DEFAULT_KEY = st.secrets.get("OPENAI_API_KEY", "")      # ← 🔑
api_key = DEFAULT_KEY

if not api_key:
    st.subheader("🔑 Ingresa tu clave OpenAI")
    api_key = st.text_input(
        "OPENAI_API_KEY",
        type="password",
        help="Se usará solo durante la sesión y no se almacena en el servidor.",
    )

st.subheader("📥 Sube el archivo Excel con las respuestas")
up_file = st.file_uploader("Arrastra o selecciona", type=["xlsx"])

reps = st.number_input("Repeticiones por evaluación", 1, 30, value=2, step=1)

if st.button("🚀 Calificar"):

    if not up_file:
        st.error("Debes subir un archivo Excel.")
        st.stop()

    if not api_key:
        st.error("Debes proporcionar tu OPENAI_API_KEY.")
        st.stop()

    with st.spinner("Procesando… ⏳"):
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path  = Path(tmpdir) / "respuestas.xlsx"
            in_path.write_bytes(up_file.read())

            os.environ["OPENAI_API_KEY"] = api_key

            out_path = run_pipeline(
                input_file=in_path,
                output_file=Path(tmpdir) / "calificaciones.xlsx",
                repetitions=reps,
            )

            if out_path.exists():
                st.success("✅ ¡Listo! Descarga tu archivo")
                st.download_button(
                    "📤 Descargar resultado",
                    data=out_path.read_bytes(),
                    file_name="calificaciones_epsilion.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )
            else:
                st.error("No se generó el archivo de resultados. "
                        "Revisa si hubo errores en el proceso.")

else:
    st.info("Sube el Excel y pulsa **Calificar**.")
