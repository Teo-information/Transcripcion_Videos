import os
from pdf2docx import parse
from markdown_pdf import MarkdownPdf, Section

def vaciar_videos_audios():
    print("🗑️ Eliminando archivos temporales de videos/audios...")
    deleted_any = False

    # Eliminar archivos en 'archivos_subidos'
    if os.path.exists("archivos_subidos"):
        for f in os.listdir("archivos_subidos"):
            file_path = os.path.join("archivos_subidos", f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted_any = True

    # Eliminar archivos en 'audio_segments'
    if os.path.exists("audio_segments"):
        for f in os.listdir("audio_segments"):
            file_path = os.path.join("audio_segments", f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted_any = True

    if deleted_any:
        print("🗑️ Archivos temporales de videos/audios eliminados.")
    else:
        print("🗑️ No hay archivos temporales de videos/audios para eliminar.")

def vaciar_documento():
    print("🗑️ Eliminando documentos temporales...")
    deleted_any = False
    for ext in [".md", ".docx", ".pdf"]:
        for f in os.listdir("."):
            if f.endswith(ext):
                os.remove(f)
                deleted_any = True
    
    if deleted_any:
        print("🗑️ Documentos temporales eliminados.")
    else:
        print("🗑️ No hay documentos temporales para eliminar.")

def CrearDocumentos(texto_md: str, original_file_base_name: str):
    # Asegurarse de que el texto comience con un título de nivel 1 para el PDF
    contenido_para_pdf = f"# Transcripción Generada para {original_file_base_name}\n\n{texto_md}"

    md_file_name = f"{original_file_base_name}.md"
    pdf_file_name = f"{original_file_base_name}.pdf"
    docx_file_name = f"{original_file_base_name}.docx"

    with open(md_file_name, "w", encoding="utf-8") as f:
        f.write(contenido_para_pdf)
    print(f"✅ MD generado exitosamente como {md_file_name}.")
    
    pdf = MarkdownPdf(
        toc_level=2,
        optimize=True
    )

    with open(md_file_name, "r", encoding="utf-8") as f:
        contenido_leido = f.read()

    pdf.add_section(Section(contenido_leido))

    pdf.save(pdf_file_name)
    print(f"✅ PDF generado exitosamente como {pdf_file_name}.")
    
    parse(pdf_file_name, docx_file_name)
    print(f"✅ DOCX generado exitosamente como {docx_file_name}.")