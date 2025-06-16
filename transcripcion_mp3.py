import os
import io
import ast
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI

def subir_a_gcs(local_path, bucket_name, destino_blob):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destino_blob)
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{destino_blob}"


def transcribir_audio_mp3(ruta_mp3):
    """
    Transcribe un archivo mp3 largo usando Google Speech-to-Text (long_running_recognize)
    y devuelve el texto y los timestamps. Si el audio es muy largo, lo sube a GCS y usa la URI.
    """
    load_dotenv()
    cred_path = os.path.abspath("credenciales.json")
    if not os.path.isfile(cred_path):
        raise FileNotFoundError(f"❌ No se encontró el archivo de credenciales en {cred_path}")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    try:
        credentials = service_account.Credentials.from_service_account_file(cred_path)
        client = speech.SpeechClient(credentials=credentials)
        storage_client = storage.Client(credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"❌ Error al autenticar con Google Cloud: {e}")

    # Leer el archivo de audio
    try:
        with io.open(ruta_mp3, "rb") as audio_file:
            content = audio_file.read()
    except Exception as e:
        raise IOError(f"❌ Error al leer el archivo de audio: {e}")

    # Detectar duración del audio (solo para MP3)
    try:
        from mutagen.mp3 import MP3
        audio_mp3 = MP3(ruta_mp3)
        duracion_segundos = int(audio_mp3.info.length)
    except Exception:
        duracion_segundos = None

    # Si el audio es mayor a 60 segundos, subir a GCS y usar URI
    if duracion_segundos is not None and duracion_segundos > 60:
        bucket_name = os.getenv("BUCKET_NAME")
        if not bucket_name:
            raise RuntimeError("❌ Debes definir la variable de entorno BUCKET_NAME en tu .env")
        destino_blob = os.path.basename(ruta_mp3)
        gcs_uri = subir_a_gcs(ruta_mp3, bucket_name, destino_blob)
        audio = speech.RecognitionAudio(uri=gcs_uri)
    else:
        audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=44100,
        language_code="es-ES",
        enable_word_time_offsets=True,
        enable_automatic_punctuation=True,
        model="default"
    )

    try:
        operation = client.long_running_recognize(config=config, audio=audio)
        print("⌛ Esperando a que termine la transcripción (puede tardar unos minutos)...")
        response = operation.result(timeout=3600)
    except Exception as e:
        raise RuntimeError(f"❌ Error durante la transcripción: {e}")

    texto = ""
    timestamps = ""

    for result in response.results:
        alternative = result.alternatives[0]
        texto += alternative.transcript + "\n"
        for word_info in alternative.words:
            start = word_info.start_time
            segundos = int(start.seconds)
            minutos = segundos // 60
            horas = minutos // 60
            tiempo = f"[{horas:02}:{minutos%60:02}:{segundos%60:02}]"
            timestamps += f"{tiempo} {word_info.word} "
        timestamps += "\n"

    return texto.strip(), timestamps.strip()


def segmentar_por_temas(texto):
    """
    Usa un modelo de lenguaje para segmentar el texto por temas detectados.
    Devuelve un diccionario {tema: contenido}
    """
    prompt = f"""
    Analiza el siguiente texto transcrito de un audio y segmenta el contenido en secciones temáticas.
    Para cada tema detectado, proporciona un título breve y el texto correspondiente.
    Devuelve el resultado como un diccionario Python, donde la clave es el nombre del tema y el valor es el texto de esa sección.
    Texto:
    {texto}
    """

    try:
        model = ChatVertexAI(model_name="gemini-2.5-pro-preview-05-06", temperature=0.3)
        response = model.invoke(prompt)
    except Exception as e:
        raise RuntimeError(f"❌ Error al invocar el modelo de Vertex AI: {e}")

    try:
        secciones = ast.literal_eval(response.content)
        if isinstance(secciones, dict):
            return secciones
    except Exception:
        pass  # Si falla el parsing, devolvemos todo como un solo tema

    return {"Transcripción completa": texto}