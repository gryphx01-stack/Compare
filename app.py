import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import fitz  # PyMuPDF pour les PDF
import docx  # Pour Word
import io

st.set_page_config(layout="wide", page_title="Auditeur Universel")

# --- 1. CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

# --- 2. FONCTION DE RÉCUPÉRATION DES MODÈLES (Le retour !) ---
def get_my_models(key):
    """Récupère la liste réelle des modèles disponibles pour votre clé"""
    try:
        genai.configure(api_key=key)
        all_models = list(genai.list_models())
        # On ne garde que ceux qui sont 'generateContent'
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Petit tri pour mettre les 'flash' et 'pro' en premier
        valid_models.sort(key=lambda x: ('flash' not in x, 'pro' not in x))
        
        if not valid_models:
            return ["models/gemini-1.5-flash"] # Fallback
        return valid_models
    except Exception as e:
        return ["Erreur: Clé invalide ou quota dépassé"]

# --- 3. FONCTIONS DE TRAITEMENT DE FICHIERS ---
def pdf_to_image(uploaded_file):
    """Convertit la page 1 du PDF en image"""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    return Image.open(io.BytesIO(pix.tobytes("png")))

def read_excel(uploaded_file):
    """Lit Excel en mode texte"""
    df = pd.read_excel(uploaded_file)
    return df.to_markdown(index=False)

def read_word(uploaded_file):
    """Lit Word en mode texte"""
    doc = docx.Document(uploaded_file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def process_file(uploaded_file):
    """Détecte le format et prépare les données pour l'IA"""
    if not uploaded_file: return None, None, None
    
    ext = uploaded_file.name.split('.')[-1].lower()
    
    # IMAGE
    if ext in ['jpg', 'jpeg', 'png']:
        img = Image.open(uploaded_file)
        return img, img, "Image"
        
    # PDF
    elif ext == 'pdf':
        uploaded_file.seek(0)
        img = pdf_to_image(uploaded_file)
        return img, img, "PDF (Page 1)"
        
    # EXCEL
    elif ext in ['xlsx', 'xls']:
        uploaded_file.seek(0)
        txt = read_excel(uploaded_file)
        uploaded_file.seek(0)
        return txt, pd.read_excel(uploaded_file), "Excel"
        
    # WORD
    elif ext in ['docx', 'doc']:
        uploaded_file.seek(0)
        txt = read_word(uploaded_file)
        return txt, txt, "Word"
        
    return None, None, "Inconnu"

# --- 4. INTERFACE ---
st.title("📂 Auditeur Universel & Intelligent")

with st.sidebar:
    st.header("Réglages")
    if api_key:
        st.success("✅ Clé connectée")
        
        # LE MENU DÉROULANT DYNAMIQUE EST REVENU ICI
        with st.spinner("Chargement de vos modèles..."):
            my_models = get_my_models(api_key)
            
        selected_model = st.selectbox(
            "Choisir le modèle IA :", 
            my_models,
            index=0,
            help="Si l'un échoue, essayez le suivant (ex: flash-002 ou exp)"
        )
        st.info(f"Modèle actif : `{selected_model}`")
    else:
        st.error("❌ Clé manquante")

# --- 5. ZONES D'UPLOAD ---
col1, col2 = st.columns(2)
# On accepte tout !
allowed = ["jpg", "png", "jpeg", "pdf", "xlsx", "xls", "docx", "doc"]

c1, p1, t1 = None, None, None
c2, p2, t2 = None, None, None

with col1:
    st.subheader("1. Référence")
    f1 = st.file_uploader("Original", type=allowed, key="u1")
    if f1:
        c1, p1, t1 = process_file(f1)
        st.caption(f"Format : {t1}")
        if t1 == "Excel": st.dataframe(p1, height=200)
        elif t1 == "Word": st.text_area("Aperçu", p1, height=200)
        else: st.image(p1, use_container_width=True)

with col2:
    st.subheader("2. A Vérifier")
    f2 = st.file_uploader("Copie", type=allowed, key="u2")
    if f2:
        c2, p2, t2 = process_file(f2)
        st.caption(f"Format : {t2}")
        if t2 == "Excel": st.dataframe(p2, height=200)
        elif t2 == "Word": st.text_area("Aperçu", p2, height=200)
        else: st.image(p2, use_container_width=True)

# --- 6. ANALYSE (PROMPT PARANOÏAQUE) ---
if st.button("Lancer l'audit complet", type="primary"):
    if not api_key or not c1 or not c2:
        st.warning("Documents ou clé manquants.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(selected_model)
            
            with st.spinner(f"Analyse minutieuse avec {selected_model}..."):
                prompt = """
                Tu es un auditeur expert et maniaque.
                Compare le Document 1 (Référence) et le Document 2 (A vérifier).
                
                RÈGLES D'OR :
                1. Ignore la mise en forme (couleurs, polices), concentre-toi sur le FOND (Texte, Chiffres).
                2. Traque CHAQUE différence : faute de frappe, ponctuation changée, chiffre modifié, ligne supprimée.
                3. Si tu compares un PDF (Image) avec un Excel (Texte), fais le lien logique entre les données.
                
                FORMAT DE RÉPONSE (Tableau Markdown) :
                | Type | Valeur Doc 1 | Valeur Doc 2 | Correction à faire |
                |------|--------------|--------------|--------------------|
                | Prix | 45 €         | 48 €         | Remettre à 45 €    |
                | Texte| Bonjour      | Bonsoir      | Corriger salutation|
                """
                
                response = model.generate_content([prompt, c1, c2])
                st.success("Terminé !")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Erreur : {str(e)}")
            st.markdown("👉 **Conseil :** Changez de modèle dans le menu à gauche (essayez un 'pro' ou 'flash-exp').")
