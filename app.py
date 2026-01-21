import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import fitz  # PyMuPDF
import docx
import io

# --- SÉCURITÉ : MOT DE PASSE ---
def check_password():
    """Renvoie True si l'utilisateur a le bon mot de passe."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Champ de saisie
    pwd = st.text_input("Veuillez entrer le mot de passe d'accès :", type="password")
    
    # DÉFINISSEZ VOTRE MOT DE PASSE ICI (ex: "client2024")
    if st.button("Se connecter"):
        if pwd == "xA?VU*(B*sp3:j0A":  # <--- Changez ceci !
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    return False

if not check_password():
    st.stop() # On arrête tout si pas de mot de passe


# --- CONFIGURATION DU MODÈLE ---
# On fixe le modèle exact que vous avez repéré
MODEL_ID = "models/gemini-3-flash-preview"

st.set_page_config(layout="wide", page_title="Auditeur Expert")

# --- 1. CONFIGURATION CLÉ ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

# --- 2. FONCTIONS TECHNIQUES ---
def pdf_to_image(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    return Image.open(io.BytesIO(pix.tobytes("png")))

def read_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df.to_markdown(index=False)

def read_word(uploaded_file):
    doc = docx.Document(uploaded_file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def process_file(uploaded_file):
    if not uploaded_file: return None, None, None
    ext = uploaded_file.name.split('.')[-1].lower()
    
    if ext in ['jpg', 'jpeg', 'png']:
        img = Image.open(uploaded_file)
        return img, img, "Image"
    elif ext == 'pdf':
        uploaded_file.seek(0)
        img = pdf_to_image(uploaded_file)
        return img, img, "PDF"
    elif ext in ['xlsx', 'xls']:
        uploaded_file.seek(0)
        txt = read_excel(uploaded_file)
        uploaded_file.seek(0)
        return txt, pd.read_excel(uploaded_file), "Excel"
    elif ext in ['docx', 'doc']:
        uploaded_file.seek(0)
        txt = read_word(uploaded_file)
        return txt, txt, "Word"
    return None, None, "Inconnu"

# --- 3. INTERFACE ÉPURÉE ---
st.title("⚖️ Auditeur de Conformité")
st.markdown("Comparaison automatisée : PDF, Excel, Word, Images.")

# Sidebar minimaliste (Juste le statut, plus de choix)
with st.sidebar:
    st.header("Statut")
    if api_key:
        st.success("✅ Système connecté")
        st.info(f"Moteur actif : {MODEL_ID}") # On affiche juste le nom pour info
    else:
        st.error("❌ Clé API manquante")

# --- 4. ZONES D'UPLOAD ---
col1, col2 = st.columns(2)
allowed = ["jpg", "png", "jpeg", "pdf", "xlsx", "xls", "docx", "doc"]
c1, p1, t1 = None, None, None
c2, p2, t2 = None, None, None

with col1:
    st.subheader("1. Document de Référence")
    f1 = st.file_uploader("Original", type=allowed, key="u1")
    if f1:
        c1, p1, t1 = process_file(f1)
        if t1 == "Excel": st.dataframe(p1, height=200)
        elif t1 == "Word": st.info("Fichier Word chargé")
        else: st.image(p1, use_container_width=True)

with col2:
    st.subheader("2. Document à Vérifier")
    f2 = st.file_uploader("Copie / Facture", type=allowed, key="u2")
    if f2:
        c2, p2, t2 = process_file(f2)
        if t2 == "Excel": st.dataframe(p2, height=200)
        elif t2 == "Word": st.info("Fichier Word chargé")
        else: st.image(p2, use_container_width=True)

# --- 5. ANALYSE ---
if st.button("Lancer l'audit de conformité", type="primary", use_container_width=True):
    if not api_key or not c1 or not c2:
        st.warning("Veuillez charger les deux documents.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(MODEL_ID)
            
            with st.spinner("Analyse approfondie en cours..."):
                prompt = """
                Tu es un auditeur expert en conformité.
                Compare le Document 1 (Référence) et le Document 2 (A vérifier).
                
                MISSION :
                1. Ignore le style. Concentre-toi sur le FOND (Texte, Chiffres, Dates).
                2. Traque CHAQUE différence : faute de frappe, chiffre modifié, ligne manquante.
                3. Si tu compares Image/PDF vs Excel, fais le lien logique entre les données.
                
                RÉPONSE ATTENDUE (Tableau Markdown) :
                | Élément concerné | Valeur Document 1 | Valeur Document 2 | Statut |
                |------------------|-------------------|-------------------|--------|
                | (ex: Prix Art.1) | 45 €              | 48 €              | ❌ ERREUR |
                | (ex: Adresse)    | Paris             | Parris            | ❌ FAUTE |
                """
                
                response = model.generate_content([prompt, c1, c2])
                st.markdown("### 📝 Rapport d'anomalies")
                st.markdown(response.text)
                st.success("Audit terminé.")
                
        except Exception as e:
            st.error(f"Erreur technique : {str(e)}")
            st.error("Le modèle Gemini 3 semble indisponible ou surchargé. Essayez de recharger la page.")

