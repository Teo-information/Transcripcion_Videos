from google.cloud import speech_v1p1beta1 as speech
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credenciales.json"  # cambia si está en otra carpeta

def test_google_speech():
    client = speech.SpeechClient()
    print("✅ Cliente inicializado correctamente")
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="es-ES",
    )
    audio = speech.RecognitionAudio(uri="gs://cloud-samples-data/speech/brooklyn_bridge.raw")
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        print("🎤 Transcripción:", result.alternatives[0].transcript)

test_google_speech()    