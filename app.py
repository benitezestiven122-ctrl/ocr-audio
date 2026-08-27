import streamlit as st
import os
import time
import glob
import cv2
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS
from googletrans import Translator

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="LingoEdu | Aprende Idiomas", page_icon="📚", layout="centered")

# --- ESTILOS CSS (TEMA MORADO Y MODERNO) ---
st.markdown("""
<style>
    /* Fondo principal y color de texto */
    .stApp {
        background-color: #f8f6fc;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #5a189a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Botones principales */
    .stButton>button {
        background-color: #7b2cbf;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #3c096c;
        color: #e0aaff;
    }
    
    /* Cajas de texto y selectores */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 2px solid #e0aaff;
    }
    
    /* Paneles de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        background-color: #e0aaff;
        color: #3c096c;
    }
    .stTabs [aria-selected="true"] {
        background-color: #7b2cbf;
        color: white;
    }
    
    /* Contenedor de advertencias o info */
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""

# --- FUNCIONES ---
def text_to_speech(input_language, output_language, text, tld):
    translator = Translator()
    translation = translator.translate(text, src=input_language, dest=output_language)
    trans_text = translation.text
    tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    try:
        my_file_name = text[0:15].strip().replace(" ", "_")
    except:
        my_file_name = "audio"
    
    # Crear carpeta temp si no existe
    if not os.path.exists("temp"):
        os.mkdir("temp")
        
    file_path = f"temp/{my_file_name}_{int(time.time())}.mp3"
    tts.save(file_path)
    return file_path, trans_text

def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)

# Limpiar archivos viejos
remove_files(7)

def process_image(image_buffer, apply_filter):
    # Convertir buffer a imagen OpenCV
    bytes_data = image_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    if apply_filter == 'Sí':
        cv2_img = cv2.bitwise_not(cv2_img)
        
    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(img_rgb)
    return text

# --- ENCABEZADO DE LA APP ---
st.markdown("<h1 style='text-align: center;'>📚 LingoEdu</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #5a189a;'>Tu plataforma interactiva para extraer, traducir y escuchar vocabulario en el mundo real.</p>", unsafe_allow_html=True)
st.write("---")

# --- SECCIÓN 1: ENTRADA DE DATOS ---
st.markdown("### 1. ¿Qué deseas traducir hoy?")

tab1, tab2, tab3 = st.tabs(["🖼️ Cargar Imagen", "📷 Usar Cámara", "✍️ Escribir Texto"])

with tab1:
    bg_image = st.file_uploader("Sube una imagen con texto:", type=["png", "jpg", "jpeg"])
    filtro_up = st.radio("¿Invertir colores? (Útil para fondos oscuros)", ('No', 'Sí'), key="f1")
    if bg_image is not None:
        st.image(bg_image, caption='Imagen cargada', width=300)
        if st.button("Extraer texto de la imagen", key="btn_extract_up"):
            with st.spinner("Leyendo la imagen..."):
                st.session_state.extracted_text = process_image(bg_image, filtro_up)

with tab2:
    img_file_buffer = st.camera_input("Toma una foto de un letrero, libro o apunte:")
    filtro_cam = st.radio("¿Invertir colores?", ('No', 'Sí'), key="f2")
    if img_file_buffer is not None:
        if st.button("Extraer texto de la foto", key="btn_extract_cam"):
            with st.spinner("Analizando la foto..."):
                st.session_state.extracted_text = process_image(img_file_buffer, filtro_cam)

with tab3:
    st.info("Escribe directamente la palabra o frase que deseas estudiar.")
    manual_text = st.text_area("Ingresa tu texto aquí:", value=st.session_state.extracted_text)
    if manual_text != st.session_state.extracted_text:
        st.session_state.extracted_text = manual_text

# --- SECCIÓN 2: TRADUCCIÓN Y AUDIO ---
st.write("---")
st.markdown("### 2. Estudio y Traducción")

if st.session_state.extracted_text.strip() == "":
    st.warning("☝️ Esperando texto. Sube una imagen o escribe algo arriba para comenzar.")
else:
    # Mostramos el texto a traducir para que el usuario pueda corregirlo si el OCR falló
    text_to_translate = st.text_area("Texto detectado (puedes editarlo):", value=st.session_state.extracted_text, height=100)
    
    col1, col2, col3 = st.columns(3)
    
    idiomas_disp = ("Inglés", "Español", "Alemán", "Francés", "Italiano", "Portugués", "Japonés", "Mandarín", "Coreano")
    codigos_idioma = {"Inglés": "en", "Español": "es", "Alemán": "de", "Francés": "fr", "Italiano": "it", "Portugués": "pt", "Japonés": "ja", "Mandarín": "zh-cn", "Coreano": "ko"}
    
    with col1:
        in_lang = st.selectbox("Idioma de origen", idiomas_disp, index=1)
        input_language = codigos_idioma[in_lang]
        
    with col2:
        out_lang = st.selectbox("Idioma a aprender", idiomas_disp, index=0)
        output_language = codigos_idioma[out_lang]
        
    with col3:
        english_accent = st.selectbox("Acento de voz", ("Defecto", "Estados Unidos", "Reino Unido", "Australia", "España", "México"))
        
        # Mapeo de acentos (TLD)
        tld_dict = {"Defecto": "com", "Estados Unidos": "com", "Reino Unido": "co.uk", "Australia": "com.au", "España": "es", "México": "com.mx"}
        tld = tld_dict[english_accent]

    if st.button("✨ Traducir y Escuchar"):
        with st.spinner("Procesando la magia..."):
            audio_path, output_text = text_to_speech(input_language, output_language, text_to_translate, tld)
            
            st.success("¡Traducción completada!")
            
            # Caja de resultado estilizada
            st.markdown(f"""
            <div style="background-color: #e0aaff; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h3 style="color: #3c096c; margin-top: 0;">{output_text}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Reproductor de audio
            audio_file = open(audio_path, "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3", start_time=0)
