from flask import Flask, request, render_template, redirect, url_for
from huggingface_hub import InferenceClient
import docx
import os
from dotenv import load_dotenv

# === Cargar variables de entorno ===
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")  # Token de Hugging Face

# === Configuración del cliente de Hugging Face ===
client = InferenceClient(
    model="openai/gpt-oss-120b",
    token=HF_TOKEN
)

# === Inicializar Flask ===
app = Flask(__name__)

# === Carpeta donde se guardará la configuración ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)  # Crear carpeta si no existe

# === Función para leer .docx ===
def leer_docx(ruta_archivo):
    doc = docx.Document(ruta_archivo)
    texto = ""
    for parrafo in doc.paragraphs:
        texto += parrafo.text + "\n"
    return texto.strip()

# === Función para leer prompt de archivo de texto ===
def leer_prompt():
    prompt_path = os.path.join(DOCS_DIR, "prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""  # Si no existe, devuelve vacío

# === Ruta de configuración para subir archivos ===
@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        # Guardar rúbrica
        if "rubrica" in request.files:
            rubrica_file = request.files["rubrica"]
            rubrica_file.save(os.path.join(DOCS_DIR, "rubrica.docx"))
        # Guardar tarea ejemplo
        if "tarea_ejemplo" in request.files:
            ejemplo_file = request.files["tarea_ejemplo"]
            ejemplo_file.save(os.path.join(DOCS_DIR, "tareaejemplo.docx"))
        # Guardar evaluación ejemplo
        if "eval_ejemplo" in request.files:
            eval_file = request.files["eval_ejemplo"]
            eval_file.save(os.path.join(DOCS_DIR, "evaluacionejemplo.docx"))
        # Guardar prompt
        prompt_text = request.form.get("prompt")
        if prompt_text:
            with open(os.path.join(DOCS_DIR, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt_text)

        return redirect(url_for("config"))

    return render_template("config.html")

# === Ruta principal para evaluar tareas ===
@app.route("/", methods=["GET", "POST"])
def index():
    # Cargar configuración actual
    rubric_path = os.path.join(DOCS_DIR, "rubrica.docx")
    ejemplo_path = os.path.join(DOCS_DIR, "tareaejemplo.docx")
    eval_path = os.path.join(DOCS_DIR, "evaluacionejemplo.docx")

    if not os.path.exists(rubric_path) or not os.path.exists(ejemplo_path) or not os.path.exists(eval_path):
        return "La configuración aún no está lista. Sube los archivos en /config"

    rubric_text = leer_docx(rubric_path)
    ejemplo_text = leer_docx(ejemplo_path)
    ejemplo_eval_text = leer_docx(eval_path)
    prompt_text = leer_prompt()

    if request.method == "POST":
        tarea_file = request.files["tarea"]
        nueva_tarea = leer_docx(tarea_file)

        # Construir prompt final
        messages = [
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": f"""
Rúbrica:
{rubric_text}

Ejemplo de tarea evaluada:
{ejemplo_text}
{ejemplo_eval_text}

Ahora evalúa esta tarea siguiendo el mismo formato:
Texto del alumno: {nueva_tarea}
"""}
        ]

        response = client.chat_completion(messages=messages, max_tokens=500)
        evaluacion = response.choices[0].message["content"]

        return render_template("resultado.html", evaluacion=evaluacion)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
