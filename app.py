import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

st.set_page_config(layout="wide", page_title="Audit IA 2.0")

# --- CHARGEMENT DE LA CLÉ ---
# On essaie de lire la clé secrète, sinon on laisse vide
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
    # Configuration avec la clé
    genai.configure(api_key=key)
    
    # On utilise le modèle Flash (rapide et gratuit)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = "Compare ces deux images. Liste les différences de prix, dates et totaux sous forme de liste à puces."
    
    # Envoi des 2 images et du texte
    response = model.generate_content([prompt, img1, img2])
    return response.text

# --- INTERFACE ---
st.title("⚡ Comparateur Rapide")

col1, col2 = st.columns(2)
file1 = col1.file_uploader("Document 1", type=["jpg", "png"])
file2 = col2.file_uploader("Document 2", type=["jpg", "png"])

if st.button("Lancer l'analyse"):
    if not api_key:
        st.error("Il manque la clé API !")
    elif not file1 or not file2:
        st.error("Il manque un document.")
    else:
        with st.spinner("Analyse IA en cours..."):
            try:
                # Ouverture des images
                img1 = Image.open(file1)
                img2 = Image.open(file2)
                
                # Appel à l'IA
                resultat = analyze(api_key, img1, img2)
                
                # Résultat
                st.success("Analyse terminée !")
                st.markdown(resultat)
                
            except Exception as e:
                st.error(f"Une erreur technique est survenue : {e}")
