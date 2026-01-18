import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(layout="wide", page_title="Audit IA - Final")

# --- 1. CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

with st.sidebar:
    st.header("État du système")
    if api_key:
        st.success("✅ Clé API connectée")
    else:
        st.error("❌ Clé manquante")

# --- 2. SÉLECTION INTELLIGENTE (FILTRÉE) ---
def get_free_model(key):
    genai.configure(api_key=key)
    try:
        # On récupère la liste des modèles disponibles
        my_models = [m.name for m in genai.list_models()]
        
        # LISTE DE PRIORITÉ (On cherche d'abord les gratuits/rapides)
        # On teste les noms exacts connus pour être dans le tiers gratuit
        priority_list = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-flash-002",
            "models/gemini-pro-vision"  # Le vieux fiable si les flash échouent
        ]
        
        # 1. On cherche une correspondance exacte dans notre liste prioritaire
        for target in priority_list:
            if target in my_models:
                return target

        # 2. Si aucun exact n'est trouvé, on cherche n'importe quel "flash"
        for m in my_models:
            if "flash" in m and "1.5" in m:
                return m
        
        # 3. Dernier recours (le défaut standard)
        return "models/gemini-1.5-flash"
        
    except Exception:
        return "models/gemini-1.5-flash"

# --- 3. FONCTION D'ANALYSE ---
def analyze_documents(key, file1, file2):
    # On trouve le bon modèle GRATUIT
    model_name = get_free_model(key)
    
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name)
    
    prompt = """
    Agis comme un expert comptable rigoureux.
    Compare ces deux documents (le premier est la référence, le second est à vérifier).
    
    Ta mission :
    1. Identifie CHAQUE différence de contenu (Prix unitaire, Quantité, Référence, Dates, Totaux).
    2. Ignore les différences purement visuelles (police, couleur, logo déplacé) si le texte est le même.
    3. Vérifie les calculs mathématiques (Total = Prix x Quantité).
    
    Format de réponse :
    - Commence par une phrase de synthèse (ex: "3 erreurs détectées").
    - Fais une liste à puces des erreurs.
    """
    
    # Appel IA
    response = model.generate_content([prompt, file1, file2])
    return response.text, model_name

# --- 4. INTERFACE ---
st.title("⚡ Comparateur Rapide (Version Gratuite)")
st.markdown("Analyse visuelle alimentée par Gemini 1.5 Flash.")

col1, col2 = st.columns(2)
file_ref = col1.file_uploader("Document 1 (Référence)", type=["jpg", "png", "jpeg"])
file_comp = col2.file_uploader("Document 2 (A vérifier)", type=["jpg", "png", "jpeg"])

if st.button("Lancer l'analyse", type="primary"):
    if not api_key:
        st.error("Clé API manquante.")
    elif not file_ref or not file_comp:
        st.warning("Chargez les deux documents.")
    else:
        with st.spinner("Analyse en cours..."):
            try:
                img1 = Image.open(file_ref)
                img2 = Image.open(file_comp)
                
                resultat, model_used = analyze_documents(api_key, img1, img2)
                
                st.success(f"Analyse terminée (Modèle utilisé : `{model_used}`)")
                st.markdown("### 📝 Résultats")
                st.markdown(resultat)
                
            except Exception as e:
                # Gestion propre des erreurs de quota
                err_msg = str(e)
                if "429" in err_msg:
                    st.error("Trop de demandes ! Attendez une minute et réessayez (Quota gratuit atteint).")
                else:
                    st.error(f"Erreur technique : {e}")
