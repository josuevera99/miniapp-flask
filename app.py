from flask import Flask, request, render_template, redirect, url_for
from huggingface_hub import InferenceClient
import docx
import os
from dotenv import load_dotenv

# === Cargar variables de entorno ===
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")  # Debe estar en .env o en Render Environment Variables

# === Configuración del cliente de Hugging Face ===
client = InferenceClient(
    model="openai/gpt-oss-120b",
    token=HF_TOKEN
)

# === Función para leer .docx ===
def leer_docx(ruta_archivo):
    doc = docx.Document(ruta_archivo)
    texto = ""
    for parrafo in doc.paragraphs:
        texto += parrafo.text + "\n"
    return texto.strip()

# === Carpeta de configuración ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)

# === Función para leer configuración ===
def leer_config():
    rubrica_path = os.path.join(CONFIG_DIR, "rubrica.docx")
    tarea_path = os.path.join(CONFIG_DIR, "tarea.docx")
    evaluacion_path = os.path.join(CONFIG_DIR, "evaluacion.docx")
    prompt_path = os.path.join(CONFIG_DIR, "prompt.txt")

    rubricText = leer_docx(rubrica_path) if os.path.exists(rubrica_path) else ""
    ejemploTexto = leer_docx(tarea_path) if os.path.exists(tarea_path) else ""
    ejemploCalificacion = leer_docx(evaluacion_path) if os.path.exists(evaluacion_path) else ""
    prompt_text = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()
    return rubricText, ejemploTexto, ejemploCalificacion, prompt_text

# === Inicializar Flask ===
app = Flask(__name__)

# === Ruta de configuración ===
@app.route("/config", methods=["GET", "POST"])
def config():
    mensaje = None
    if request.method == "POST":
        # Guardar archivos subidos
        rubrica_file = request.files.get("rubrica")
        tarea_file = request.files.get("tarea")
        evaluacion_file = request.files.get("evaluacion")
        prompt_text = request.form.get("prompt")

        if rubrica_file:
            rubrica_file.save(os.path.join(CONFIG_DIR, "rubrica.docx"))
        if tarea_file:
            tarea_file.save(os.path.join(CONFIG_DIR, "tarea.docx"))
        if evaluacion_file:
            evaluacion_file.save(os.path.join(CONFIG_DIR, "evaluacion.docx"))
        if prompt_text:
            with open(os.path.join(CONFIG_DIR, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)

        mensaje = "Configuración guardada correctamente."

    return render_template("config.html", mensaje=mensaje)

# === Ruta principal para alumnos ===
@app.route("/", methods=["GET", "POST"])
def index():
    rubricText, ejemploTexto, EJEMPLO_CALIFICACION, prompt_text = leer_config()

    if request.method == "POST":
        # Leer la tarea del alumno
        tarea_file = request.files["tarea"]
        nueva_tarea = leer_docx(tarea_file)

        # Construir prompt para el modelo
        messages = [
            {
                "role": "system",
                "content": prompt_text
            },
            {
                "role": "user",
                "content": f"""
Rúbrica:
{rubricText}

Ejemplo de tarea evaluada:
{ejemploTexto}
{EJEMPLO_CALIFICACION}

Ahora evalúa esta tarea siguiendo el mismo formato:
Texto del alumno: {nueva_tarea}
"""
            }
        ]

        # Solicitud al modelo
        response = client.chat_completion(messages=messages, max_tokens=500)
        evaluacion = response.choices[0].message["content"]

        return render_template("resultado.html", evaluacion=evaluacion)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
