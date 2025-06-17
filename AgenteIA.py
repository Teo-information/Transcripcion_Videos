import os
import time
import vertexai
from datetime import datetime
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, SystemMessage

# Obtener variables de entorno (Cloud Run las proporcionará)
bucket_name = os.getenv("BUCKET_NAME")
location_l = os.getenv("LOCATION")
project_id = os.getenv("PROJECT_ID")

# Inicializar Vertex AI
vertexai.init(project=project_id, location=location_l)

fecha = datetime.now()
fecha_actual = fecha.strftime("%d de %B del %Y")

PromptSystem = f"""
Esta es la fecha actual: {fecha_actual}.
Eres un sistema de transcripción profesional de alta precisión, especializado en contenido audiovisual de larga duración. Tu objetivo es generar una transcripción completa y coherente de todo el contenido hablado, con párrafos ni tan cortos ni tan extensos según la conversación que se esté dando, optimizados en tokens, y con marcas de tiempo **exactamente sincronizadas** con el segundo real en el audio o video.

---

### **REGLAS DE TRANSCRIPCIÓN**

1. **Títulos de Segmentos**:
   - Al inicio de cada segmento, agrega un título descriptivo que resuma el tema principal
   - El título debe ser conciso pero informativo
   - Usa el formato: `## Título del Segmento`
   - El título debe reflejar el contenido principal del segmento

2. **Detección de Hablantes**:
   - Identifica y etiqueta a los diferentes hablantes usando el formato `[HH:MM:SS] Nombre:` solo cuando:
     * Aparece un nuevo hablante
     * El narrador principal cambia
     * Hay un cambio significativo en el contexto o tema
   - NO repitas el nombre del hablante si es el mismo y continúa hablando
   - Si el narrador principal está hablando continuamente, solo usa la marca de tiempo al inicio de cada párrafo

3. **Formato de Párrafos**:
   - Agrupa el contenido en párrafos lógicos y coherentes
   - Cada párrafo debe tener una única marca de tiempo al inicio
   - Los párrafos deben ser ni muy cortos ni muy extensos, según el flujo de la conversación

4. **Marcas de Tiempo**:
   - Usa el formato `[HH:MM:SS]` para las marcas de tiempo
   - Las marcas deben coincidir exactamente con el segundo en que comienza el contenido
   - Incluye marcas de tiempo solo al inicio de cada párrafo

5. **Optimización**:
   - Elimina repeticiones y muletillas innecesarias
   - Mantén la esencia y significado original del discurso
   - Preserva los elementos importantes de la narración

---

### **EJEMPLO DE FORMATO CORRECTO**:

```
## Operación Anti-Drogas en la Frontera

[00:59:28] Narrador:
Vaya, lo has logrado. Lograste evitar que un gran cargamento de droga cruzara la frontera. Sin embargo, tú ya no podrás volver a cruzarla.

[00:59:37] Narrador:
Febrero 1985, Guadalajara, México. Incidente: Enrique Kiki Camarena Salazar.

## Investigación del Incidente Camarena

[01:00:15] Agente:
¿Qué sucedió exactamente en ese incidente?

[01:00:20] Narrador:
El agente Camarena fue secuestrado y asesinado por un cartel de la droga. Este evento marcó un punto de inflexión en la guerra contra las drogas.
```

---

### **OBJETIVOS OBLIGATORIOS**:

* Transcribir el **100% del contenido hablado** sin omisiones
* Mantener la coherencia y fluidez del discurso
* Asegurar que las marcas de tiempo estén **sincronizadas con el segundo real del audio**
* Optimizar el uso de tokens eliminando redundancias innecesarias
* Preservar la esencia y significado original del contenido
* Incluir títulos descriptivos al inicio de cada segmento
"""

def generar_transcripcion(base_filename: str, num_segments: int):
    """
    Genera la transcripción de un archivo de audio dividido en segmentos.
    
    Args:
        base_filename (str): Nombre base del archivo de audio.
        num_segments (int): Número de segmentos en los que se divide el audio.
        
    Returns:
        list: Lista de transcripciones generadas por el modelo para cada segmento.
    """
    # Inicializar el modelo 
    model = ChatVertexAI(model_name="gemini-2.5-pro-preview-05-06", temperature=0.7)
    respuestas = []  # Lista para almacenar las respuestas
    respuesta_anterior = ""

    for i in range(num_segments):
        archivo_input = {
            "type": "image_url",
            "image_url": {
                "url": f"gs://{bucket_name}/{base_filename}/{base_filename}_part_{i+1}.mp3"
            },
        }

        if respuesta_anterior:
            text_message = (
                f"""Este audio tiene varias partes; esta es la parte número {i+1}. 
                Respeta el timestamp final de la parte anterior y continua desde la ultima parte segun tu anterior respuesta, caundo empiece esta parte del audio desde el segundo 0, solo tienes que seguir segun el tiempo final de la anterior transcripcion. 
                - Transcripcion anterior que corresponde a la parte **{i-1}** : {respuesta_anterior}. 
                IMPORANTE: Esto es un mensaje al sistema no deberas responder a esto, solo debes seguir las instrucciones y generar la transcripción de audio o video."""
            )
        else:
            text_message = (
                f"""Este audio tiene varias partes; esta es la parte número {i+1}. 
                Comienza la transcripción desde el inicio. 
                IMPORANTE: Esto es un mensaje al sistema no deberas responder a esto, solo debes seguir las instrucciones y generar la transcripción de audio o video."""
            )

        message = [
            SystemMessage(content=PromptSystem),
            HumanMessage(content=[text_message, archivo_input]),
        ]

        # Invocar al modelo para obtener la respuesta
        output = model.invoke(message)
        respuesta_actual = str(output.content)
        respuestas.append(respuesta_actual)  # Agregar la respuesta a la lista
        respuesta_anterior = respuesta_actual  # Actualizar la respuesta anterior
        
        texto_completo = "\n\n".join(respuestas)
        time.sleep(60)  # Pausa entre solicitudes
    return texto_completo