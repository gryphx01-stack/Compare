import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Audit IA - Comparateur (Version V1)")

# --- CONFIGURATION API ---
# On tente de récupérer la clé, sinon on affiche un champ
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    if api_key:
        st.success("✅ Clé API chargée")
    else:
        api_key = st.text_input("Clé API Gemini", type="password")
    
    st.info("Mode de compatibilité : Utilise le modèle standard Gemini Pro Vision.")

    # Bouton de secours pour vider le cache manuellement si besoin
    if st.button("Vider le cache de l'app"):
        st.cache_data.clear()

# --- FONCTIONS ---
def analyze_documents_v1(key, file_ref, file_comp):
    genai.configure(api_key=key)
    # On utilise le modèle V1 qui passe partout
    model = genai.GenerativeModel("gemini-pro-vision")
    
    prompt = """
    Agis comme un expert comptable. Compare ces deux images de documents.
    Liste les différences de prix, dates, et totaux.
    Sois factuel. Si tout est identique, dis-le.
    """
    
    # Le modèle V1 prend une liste [prompt, image1, image2]
    response = model.generate_content([prompt, file_ref, file_comp])
    return response.text

# --- INTERFACE PRINCIPALE ---
st.title("⚖️ Comparateur de Documents (Mode Compatible)")

col1, col2 = st.columns(2)
img_ref = None
img_comp = None

with col1:
    st.subheader("1. Référence")
    ref_file = st.file_uploader("Document 1", type=['png', 'jpg', 'jpeg'], key="v1_ref")
    if ref_file:
        img_ref = Image.open(ref_file)
        st.image(img_ref, use_container_width=True)

with col2:
    st.subheader("2. Comparaison")
    comp_file = st.file_uploader("Document 2", type=['png', 'jpg', 'jpeg'], key="v1_comp")
    if comp_file:
        img_comp = Image.open(comp_file)
        st.image(img_comp, use_container_width=True)

# BOUTON D'ACTION
if st.button("LANCER L'ANALYSE", type="primary"):
    if not api_key:
        st.error("Il manque la clé API !")
    elif not img_ref or not img_comp:
        st.warning("Il faut deux images pour comparer.")
    else:
        with st.spinner("Analyse en cours avec le modèle standard..."):
            try:
                # Appel direct sans JSON complexe (plus robuste pour la V1)
                resultat = analyze_documents_v1(api_key, img_ref, img_comp)
                
                st.divider()
                st.subheader("📝 Rapport d'analyse")
                st.markdown(resultat)
                st.success("Analyse terminée.")
                
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
                st.markdown("Astuce : Vérifiez que votre clé API est bien valide.")
