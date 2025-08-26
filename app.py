from flask import Flask, request, render_template
from huggingface_hub import InferenceClient
import docx
import os
from dotenv import load_dotenv

# === Cargar variables de entorno ===
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")  # Asegúrate de tener HF_TOKEN en .env o en Render Environment Variables

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

# === Archivos fijos en la carpeta docs/ ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RUBRICA = os.path.join(BASE_DIR, "docs", "rubrica.docx")
RUTA_EJEMPLO = os.path.join(BASE_DIR, "docs", "tareaejemplo.docx")

rubricText = leer_docx(RUTA_RUBRICA)
ejemploTexto = leer_docx(RUTA_EJEMPLO)

# === Ejemplo de calificación predefinida ===
EJEMPLO_CALIFICACION = """
Evaluación de la practica:
        1. Tema e ideas: 1/1 - Contiene varias ideas sobre el tema del texto.
        Calificación Total: 1/1
        Retroalimentación positiva: Excelente integración de ideas.
        Áreas de oportunidad: No se encontraron áreas de oportunidad
"""

# === Inicializar Flask ===
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Leer la tarea del alumno
        tarea_file = request.files["tarea"]
        nueva_tarea = leer_docx(tarea_file)

        # Construir prompt para el modelo
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente docente experto en programación en Python. Tu tarea es evaluar prácticas escolares de los alumnos."
                    "Las prácticas son evaluadas de acuerdo con la rúbrica que te vamos a pasar en el documento."
                    "Reglas para tu respuesta:"
                    "- Evalúa punto por punto, asignando una calificación parcial con una breve justificación."
                    "- Suma al final para dar la calificación total"
                    "- Ofrece una retroalimentación positiva destacando lo mejor del trabajo."
                    "- Señala áreas de oportunidad en un tono constructivo, sugiriendo cómo mejorar."
                    "- Usa un lenguaje claro y motivador para estudiantes de preparatoria."
                )
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