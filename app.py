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
    # Inicializa el contador en session_state si no existe
    if "limpieza" not in st.session_state:
        st.session_state["limpieza"] = 0

    # Botón para limpiar archivos subidos
    if st.button("Limpiar archivos subidos"):
        vaciar_videos_audios()
        st.success("Archivos temporales eliminados.")
        st.session_state["limpieza"] += 1

    archivos_procesados = []  # Inicializar siempre la lista
    archivos = st.file_uploader(
        "Sube tus videos o audios aqui",
        accept_multiple_files=True,
        type=["mp4", "avi", "mov", "mkv", "mp3"],
        key=st.session_state["limpieza"]
    )
    
    if archivos:
        save_folder = "archivos_subidos"
        os.makedirs(save_folder, exist_ok=True)
        
        for archivo in archivos:
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
            
            archivos_procesados.append({
                'nombre': original_file_name,
                'ruta': destino,
                'nombre_base': original_file_base_name
            })
            
            st.success(f"Archivo guardado: {original_file_name}")
            st.video(destino)
        
        st.info(f"Total de archivos cargados: {len(archivos_procesados)}")
    st.divider()
    
    # Transcribir los videos
    st.header("2. Segundo", False)
    st.write("Genera tu transcripcion aqui ✅.")
    if archivos_procesados:
        if st.button("Generar Transcripcion", icon= "📝"):
            with st.chat_message("ai"):
                spinner = st.spinner("Generando transcripciones...", show_time=True)
                with spinner:
                    vaciar_documento()
                    transcripciones_unidas = ""
                    nombre_base_unido = "transcripcion_unificada"
                    for archivo in archivos_procesados:
                        st.write(f"Procesando archivo: {archivo['nombre']}")
                        procesador = ProcesadorVideo(archivo['ruta'])
                        procesador.procesar_y_subir()
                        texto = procesador.send_transcripcion_gemini()
                        transcripciones_unidas += texto + "\n\n"
                    # Generar los documentos unificados
                    CrearDocumentos(transcripciones_unidas, nombre_base_unido)
                    st.success("¡Videos transcritos y unificados con éxito! 💪🦁")
            # Mostrar solo los documentos unificados
            tab1, tab2, tab3 = st.tabs(["📕 PDF UNIFICADO", "📘 WORD UNIFICADO", "📄 TEXTO UNIFICADO"])
            pdf_file_name = f"{nombre_base_unido}.pdf"
            docx_file_name = f"{nombre_base_unido}.docx"
            md_file_name = f"{nombre_base_unido}.md"
            # PDF
            if os.path.exists(pdf_file_name):
                with open(pdf_file_name, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_mostrar = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                tab1.markdown(pdf_mostrar, unsafe_allow_html=True)
            # WORD
            if os.path.exists(docx_file_name):
                with open(docx_file_name, "rb") as file:
                    contenido = file.read()
                    tab2.download_button(
                        label="Descargar documento Word",
                        data=contenido,
                        file_name=docx_file_name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            # TEXTO
            if os.path.exists(md_file_name):
                with open(md_file_name, "r", encoding="utf-8") as f:
                    texto_md = f.read()
                tab3.code(texto_md)

if __name__ == '__main__':
    verificar_credenciales()
    main_app()