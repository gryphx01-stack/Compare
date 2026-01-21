import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import fitz  # C'est PyMuPDF (pour lire les PDF)
import docx  # Pour Word
import io

st.set_page_config(layout="wide", page_title="Auditeur Universel")

# --- 1. CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

# --- 2. FONCTIONS DE CHARGEMENT INTELLIGENT ---
def pdf_to_image(uploaded_file):
    """Convertit la première page d'un PDF en image pour l'IA"""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)  # On prend la page 1
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom x2 pour la qualité
    img_data = pix.tobytes("png")
    return Image.open(io.BytesIO(img_data))

def read_excel(uploaded_file):
    """Transforme un Excel en texte lisible"""
    df = pd.read_excel(uploaded_file)
    return df.to_markdown(index=False)

def read_word(uploaded_file):
    """Lit le texte d'un fichier Word"""
    doc = docx.Document(uploaded_file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    return "\n".join(full_text)

def process_file(uploaded_file):
    """Chef d'orchestre : décide comment traiter le fichier selon son extension"""
    if uploaded_file is None:
        return None, None, None

    file_type = uploaded_file.name.split('.')[-1].lower()
    
    # CAS 1 : IMAGES (JPG, PNG)
    if file_type in ['jpg', 'jpeg', 'png']:
        img = Image.open(uploaded_file)
        return img, img, "Image" # (Data pour IA, Preview pour l'humain, Type)
    
    # CAS 2 : PDF (On le transforme en image pour le visuel)
    elif file_type == 'pdf':
        uploaded_file.seek(0)
        img = pdf_to_image(uploaded_file)
        return img, img, "PDF (Page 1 convertie)"
    
    # CAS 3 : EXCEL (On extrait le texte)
    elif file_type in ['xlsx', 'xls']:
        uploaded_file.seek(0)
        text_data = read_excel(uploaded_file)
        # Pour la preview, on montre un bout du tableau
        uploaded_file.seek(0)
        preview_df = pd.read_excel(uploaded_file)
        return text_data, preview_df, "Excel"
        
    # CAS 4 : WORD (On extrait le texte)
    elif file_type in ['docx', 'doc']:
        uploaded_file.seek(0)
        text_data = read_word(uploaded_file)
        return text_data, text_data, "Word"
        
    return None, None, "Inconnu"

# --- 3. GESTION DU MODÈLE ---
def get_model_name(key):
    # On garde votre logique de sélection manuelle ou auto
    # Ici, on simplifie pour pointer vers le modèle qui a marché pour vous
    return "gemini-2.0-flash-exp" # Ou "models/gemini-1.5-flash" selon ce qui marche

# --- 4. INTERFACE ---
st.title("📂 Auditeur Universel (PDF, Excel, Images...)")

with st.sidebar:
    st.header("Paramètres")
    if api_key:
        st.success("✅ Clé connectée")
        # Menu pour choisir le modèle (au cas où)
        model_choice = st.selectbox(
            "Modèle IA", 
            ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"],
            index=1
        )
    else:
        st.error("❌ Clé manquante")

# --- 5. ZONES D'UPLOAD ---
col1, col2 = st.columns(2)
allowed_types = ["jpg", "png", "jpeg", "pdf", "xlsx", "docx"]

content1, preview1, type1 = None, None, None
content2, preview2, type2 = None, None, None

with col1:
    st.subheader("1. Référence")
    f1 = st.file_uploader("Original", type=allowed_types, key="f1")
    if f1:
        with st.spinner("Lecture..."):
            content1, preview1, type1 = process_file(f1)
            st.caption(f"Format détecté : {type1}")
            if type1 in ["Image", "PDF (Page 1 convertie)"]:
                st.image(preview1, use_container_width=True)
            elif type1 == "Excel":
                st.dataframe(preview1, height=200)
            else:
                st.text_area("Aperçu texte", preview1, height=200)

with col2:
    st.subheader("2. Comparaison")
    f2 = st.file_uploader("A vérifier", type=allowed_types, key="f2")
    if f2:
        with st.spinner("Lecture..."):
            content2, preview2, type2 = process_file(f2)
            st.caption(f"Format détecté : {type2}")
            if type2 in ["Image", "PDF (Page 1 convertie)"]:
                st.image(preview2, use_container_width=True)
            elif type2 == "Excel":
                st.dataframe(preview2, height=200)
            else:
                st.text_area("Aperçu texte", preview2, height=200)

# --- 6. ANALYSE ---
if st.button("Lancer l'audit", type="primary"):
    if not api_key or not content1 or not content2:
        st.error("Documents manquants ou clé absente.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_choice)
            
            with st.spinner("Analyse croisée des formats..."):
                prompt = """
                Agis comme un auditeur expert capable de lire tous les formats.
                Compare le contenu du Document 1 et du Document 2.
                
                ATTENTION : Les documents peuvent être de formats différents (ex: un PDF vs un Excel).
                Concentre-toi sur le FOND (les données, prix, dates, textes) et ignore la FORME (mise en page).
                
                Ta mission :
                1. Repérer les écarts de valeurs (chiffres, prix).
                2. Repérer les ajouts ou suppressions de texte.
                3. Signaler les fautes ou incohérences.
                
                Réponds sous forme de tableau Markdown clair.
                """
                
                # Gemini est magique : on peut lui envoyer une Image ET du Texte dans la même requête
                response = model.generate_content([prompt, content1, content2])
                
                st.success("Analyse terminée !")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Erreur : {str(e)}")
            if "429" in str(e):
                st.warning("Quota dépassé. Essayez le modèle 'gemini-1.5-flash' dans le menu.")
