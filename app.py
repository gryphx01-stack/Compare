import streamlit as st
import subprocess
import sys

# --- HACK : FORCER LA MISE A JOUR DE LA LIBRAIRIE ---
try:
    import google.generativeai as genai
    # On vérifie si la version est assez récente, sinon on force l'install
    from importlib.metadata import version
    if version("google-generativeai") < "0.7.0":
        raise ImportError
except ImportError:
    st.warning("Mise à jour des outils IA en cours... (Patientez 10 sec)")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.7.0"])
    st.rerun() # On recharge la page une fois installé

import google.generativeai as genai
from PIL import Image

st.set_page_config(layout="wide", page_title="Audit IA - Final")

# --- RECUPERATION DE LA CLE ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

with st.sidebar:
    st.header("Paramètres")
    if api_key:
        st.success("✅ Clé API connectée")
    else:
        api_key = st.text_input("Clé API", type="password")
        st.warning("Entrez votre clé pour commencer")

# --- FONCTION D'ANALYSE ---
def analyze(key, img1, img2):
    genai.configure(api_key=key)
    # On utilise le modèle Flash 1.5
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = "Agis comme un expert comptable. Compare ces deux documents visuellement. Liste les différences (Prix, Dates, Totaux). Sois précis."
    
    response = model.generate_content([prompt, img1, img2])
    return response.text

# --- INTERFACE ---
st.title("🚀 Comparateur Documents (Force Mode)")

col1, col2 = st.columns(2)
file1 = col1.file_uploader("Document 1", type=["jpg", "png", "jpeg"])
file2 = col2.file_uploader("Document 2", type=["jpg", "png", "jpeg"])

if st.button("Lancer l'analyse"):
    if not api_key:
        st.error("Il manque la clé API !")
    elif not file1 or not file2:
        st.error("Il manque un document.")
    else:
        with st.spinner("Analyse IA en cours..."):
            try:
                img1 = Image.open(file1)
                img2 = Image.open(file2)
                
                resultat = analyze(api_key, img1, img2)
                
                st.success("Analyse terminée !")
                st.markdown(resultat)
                
            except Exception as e:
                st.error(f"Erreur : {e}")
