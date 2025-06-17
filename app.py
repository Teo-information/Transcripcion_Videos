import os
import streamlit as st
from CorteVideos import ProcesadorVideo
from Documento_Convertir import CrearDocumentos, vaciar_documento, vaciar_videos_audios
from transcripcion_mp3 import transcribir_audio_mp3, segmentar_por_temas
import base64
from google.cloud import storage

def verificar_credenciales():
    # Verificar credenciales
    try:
        # Intentar inicializar el cliente de Storage
        storage_client = storage.Client()
        # Si llegamos aquí, las credenciales son válidas
        st.success("✅ Credenciales de Google Cloud verificadas correctamente")
    except Exception as e:
        st.error(f"❌ Error al verificar credenciales: {str(e)}")
        st.stop()

def main_app():
    st.title("Transcripción de Audios MP3 🎵", False)
    st.write("Esta aplicación permite transcribir archivos .mp3 a texto y segmentar por temas.")
    st.divider()

    st.header("1. Sube tu archivo MP3", False)
    vaciar_videos_audios()
    archivo = st.file_uploader("Sube tu video o audio aqui", accept_multiple_files=False, type=["mp4", "avi", "mov", "mkv", "mp3"])  
    if archivo is not None:
        save_folder = "archivos_subidos"
        os.makedirs(save_folder, exist_ok=True)
        
        # Obtener el nombre de archivo original y la extensión
        original_file_name = archivo.name
        original_file_base_name = os.path.splitext(original_file_name)[0]
        file_extension = os.path.splitext(original_file_name)[1]
        
        # Usar el nombre de archivo original para guardar
        destino = os.path.join(save_folder, original_file_name)
        
        # Elimina el archivo existente si tiene la misma extensión
        if os.path.exists(destino):
            os.remove(destino)
        
        # Guarda el archivo en el disco
        with open(destino, "wb") as f:
            f.write(archivo.getbuffer())
        
        st.success(f"Archivo guardado en: {destino}")
        st.video(destino)
    st.divider()
    
    # Transcribir el video
    st.header("2. Segundo", False)
    st.write("Genera tu transcripcion aqui ✅.")
    if archivo is not None:
        if os.path.exists(destino):
                if st.button("Generar Transcripcion", icon= "📝"):
                    with st.chat_message("ai"):
                        spinner = st.spinner("Generando transcripcion...", show_time=True)
                        with spinner:
                            vaciar_documento()
                            procesador = ProcesadorVideo(destino)
                            procesador.procesar_y_subir()
                            texto = procesador.send_transcripcion_gemini()
                            CrearDocumentos(texto, original_file_base_name) # Pasar el nombre base del archivo
                        st.success("Video transcrito con exito! 💪🦁")
                        
                    # Mostrar documentos.
                    tab1, tab2, tab3= st.tabs(["📕 PDF", "📘 WORD", "📄 TEXTO"])

                    tab1.subheader("La transcripcion en formato PDF")
                    tab2.subheader("La transcripcion en formato WORD")
                    tab3.subheader("La transcripcion en formato TEXTO")
                    
                    # Rutas de los nuevos archivos generados
                    pdf_file_name = f"{original_file_base_name}.pdf"
                    docx_file_name = f"{original_file_base_name}.docx"
                    md_file_name = f"{original_file_base_name}.md"

                    # Leer el archivo PDF y codificarlo en base64
                    if os.path.exists(pdf_file_name):
                        with open(pdf_file_name, "rb") as f:
                            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                        # Crear un iframe para mostrar el PDF
                        pdf_mostrar = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                        tab1.markdown(pdf_mostrar, unsafe_allow_html=True)
                    
                        if os.path.exists(docx_file_name):
                            with open(docx_file_name, "rb") as file:
                                contenido = file.read()
                                tab2.download_button(
                                    label="Descargar documento Word",
                                    data=contenido,
                                    file_name=docx_file_name, # Usar el nombre dinámico aquí
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                        if os.path.exists(md_file_name):
                            with open(md_file_name, "r", encoding="utf-8") as f:
                                texto_md = f.read()
                            tab3.code(texto_md)

if __name__ == '__main__':
    verificar_credenciales()
    main_app()