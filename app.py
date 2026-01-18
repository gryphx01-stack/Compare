import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(layout="wide", page_title="Audit IA - Auto")

# --- 1. CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

with st.sidebar:
    st.header("État du système")
    if api_key:
        st.success("✅ Clé API connectée")
    else:
        st.error("❌ Clé manquante")
        st.info("Ajoutez GEMINI_API_KEY dans les Secrets.")

# --- 2. FONCTION INTELLIGENTE DE SÉLECTION DE MODÈLE ---
def get_available_model(key):
    genai.configure(api_key=key)
    try:
        # On demande à Google la liste exacte des modèles disponibles pour CETTE clé
        all_models = list(genai.list_models())
        
        # 1. On cherche le meilleur (Flash 1.5)
        for m in all_models:
            if "flash" in m.name.lower() and "1.5" in m.name and "generateContent" in m.supported_generation_methods:
                return m.name # On retourne le nom EXACT trouvé (ex: models/gemini-1.5-flash-001)
        
        # 2. Sinon on cherche le Pro 1.5
        for m in all_models:
            if "pro" in m.name.lower() and "1.5" in m.name and "generateContent" in m.supported_generation_methods:
                return m.name
                
        # 3. Sinon n'importe quel Gemini Pro
        for m in all_models:
            if "gemini-pro" in m.name.lower() and "vision" not in m.name:
                return m.name
                
        return "models/gemini-1.5-flash" # Fallback par défaut
    except Exception as e:
        return "models/gemini-1.5-flash"

# --- 3. FONCTION D'ANALYSE ---
def analyze_documents(key, file1, file2):
    # On trouve le bon modèle dynamiquement
    model_name = get_available_model(key)
    
    # On configure
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name)
    
    prompt = """
    Expert comptable : Compare ces deux images.
    Identifie les écarts de Prix, Dates, Totaux.
    Sois précis et concis.
    """
    
    # Appel IA
    response = model.generate_content([prompt, file1, file2])
    return response.text, model_name

# --- 4. INTERFACE ---
st.title("🤖 Comparateur Intelligent (Auto-Détection)")
st.markdown("Ce système détecte automatiquement le modèle IA compatible avec votre clé.")

col1, col2 = st.columns(2)
file_ref = col1.file_uploader("Document 1", type=["jpg", "png", "jpeg"])
file_comp = col2.file_uploader("Document 2", type=["jpg", "png", "jpeg"])

if st.button("Lancer l'analyse", type="primary"):
    if not api_key:
        st.error("Clé API manquante.")
    elif not file_ref or not file_comp:
        st.warning("Chargez les deux documents.")
    else:
        with st.spinner("Recherche du modèle et analyse en cours..."):
            try:
                img1 = Image.open(file_ref)
                img2 = Image.open(file_comp)
                
                # On lance l'analyse qui va chercher le modèle toute seule
                resultat, model_used = analyze_documents(api_key, img1, img2)
                
                st.success(f"Analyse réussie avec le modèle : `{model_used}`")
                st.markdown("### Résultats")
                st.markdown(resultat)
                
            except Exception as e:
                st.error(f"Erreur : {e}")
