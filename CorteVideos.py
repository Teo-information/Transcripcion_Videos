import os
import math
import re
from dotenv import load_dotenv
from google.cloud import storage
from moviepy.editor import VideoFileClip, AudioFileClip
from AgenteIA import generar_transcripcion

class ProcesadorVideo:
    def __init__(self, base_filename):
        load_dotenv()
        self.base_filename = base_filename
        self.bucket_name = os.getenv("BUCKET_NAME")
        self.output_dir = "audio_segments"
        os.makedirs(self.output_dir, exist_ok=True)

    def upload_to_gcs(self, file_path: str, destination_blob_name: str) -> str:
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        return f"gs://{self.bucket_name}/{destination_blob_name}"

    def procesar_y_subir(self):
        file_extension = os.path.splitext(self.base_filename)[1].lower()

        if file_extension in [".mp4", ".avi", ".mov", ".mkv"]:
            clip = VideoFileClip(self.base_filename)
            audio_clip = clip.audio
        elif file_extension == ".mp3":
            clip = AudioFileClip(self.base_filename)
            audio_clip = clip
        else:
            raise ValueError("Tipo de archivo no soportado. Por favor, sube un video o un archivo MP3.")

        duration = audio_clip.duration
        self.base_name = os.path.basename(self.base_filename)

        # Detectar si el archivo ya es un fragmento (ej: contiene _part_\d+ en el nombre)
        es_fragmento = bool(re.search(r'_part_\d+', self.base_name))

        # Si el video es menor a 15 minutos o ya es un fragmento, no lo fragmentamos
        if duration <= 900 or es_fragmento:  # 15 minutos = 900 segundos
            output_filename = f"{self.base_name}"
            output_path = os.path.join(self.output_dir, output_filename)
            audio_clip.write_audiofile(output_path, logger=None)
            destination_blob_name = f"{self.base_name}/{output_filename}"
            gs_uri = self.upload_to_gcs(output_path, destination_blob_name)
            print(f"✅ Archivo guardado y subido como: {gs_uri}")
            self.num_segments = 1
        else:
            # Para videos más largos, los fragmentamos en segmentos de 15 minutos
            segment_duration = 900  # 15 minutos
            self.num_segments = math.ceil(duration / segment_duration)

            for i in range(self.num_segments):
                start = i * segment_duration
                end = min((i + 1) * segment_duration, duration)
                segment = audio_clip.subclip(start, end)
                output_filename = f"{self.base_name}_part_{i+1}.mp3"
                output_path = os.path.join(self.output_dir, output_filename)
                segment.write_audiofile(output_path, logger=None)
                destination_blob_name = f"{self.base_name}/{output_filename}"
                gs_uri = self.upload_to_gcs(output_path, destination_blob_name)
                print(f"✅ Segmento {i+1} guardado y subido como: {gs_uri}")

        audio_clip.close()
        if file_extension in [".mp4", ".avi", ".mov", ".mkv"]:
            clip.close()

    def send_transcripcion_gemini(self):
        rs_final = generar_transcripcion(self.base_name, self.num_segments)
        print("✅ Transcripción generada exitosamente.")
        return rs_final