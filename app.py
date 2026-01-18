import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(layout="wide", page_title="Audit IA - Final")

# --- 1. CONFIGURATION DE LA CLÉ ---
# On récupère la clé stockée dans les secrets de Streamlit
api_key = st.secrets.get("GEMINI_API_KEY", None)

# --- 2. CONFIGURATION DE L'INTERFACE ---
st.title("🚀 Comparateur de Documents Intelligent")
st.markdown("### Outil de démo pour validation client")

# Sidebar pour le statut
with st.sidebar:
    st.header("État du système")
    if api_key:
        st.success("✅ Clé API connectée")
        st.info("Modèle actif : Gemini 1.5 Flash")
    else:
        st.error("❌ Aucune clé API trouvée.")
        st.warning("Veuillez ajouter votre clé dans les 'Secrets' de Streamlit.")

# --- 3. FONCTION D'ANALYSE ---
def analyze_documents(key, file1, file2):
    # Configuration
    genai.configure(api_key=key)
    
    # ICI : On utilise le nom exact qui fonctionne avec la version 0.8.6
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = """
    Tu es un expert en audit. Compare visuellement ces deux documents.
    Ta mission :
    1. Détecter les différences de prix, de quantités, de dates et de totaux.
    2. Ignorer les simples différences de mise en page.
    3. Lister les écarts sous forme de points précis.
    
    Format de réponse souhaité :
    - Résumé global en une phrase.
    - Liste des différences trouvées.
    """
    
    # Envoi de la requête (Prompt + Image 1 + Image 2)
    response = model.generate_content([prompt, file1, file2])
    return response.text

# --- 4. ZONES D'UPLOAD ---
col1, col2 = st.columns(2)

file_ref = None
file_comp = None

with col1:
    st.subheader("📄 Document de Référence")
    upload1 = st.file_uploader("Déposez l'original", type=["jpg", "png", "jpeg"], key="doc1")
    if upload1:
        file_ref = Image.open(upload1)
        st.image(file_ref, use_container_width=True)

with col2:
    st.subheader("📄 Document à Comparer")
    upload2 = st.file_uploader("Déposez la copie/facture", type=["jpg", "png", "jpeg"], key="doc2")
    if upload2:
        file_comp = Image.open(upload2)
        st.image(file_comp, use_container_width=True)

# --- 5. BOUTON D'ACTION ---
if st.button("Lancer la comparaison", type="primary", use_container_width=True):
    if not api_key:
        st.error("Impossible de lancer : Clé API manquante.")
    elif not file_ref or not file_comp:
        st.warning("Veuillez charger les deux documents avant de lancer.")
    else:
        with st.spinner("Analyse en cours par l'IA..."):
            try:
                # Appel à la fonction
                resultat = analyze_documents(api_key, file_ref, file_comp)
                
                # Affichage du résultat
                st.divider()
                st.success("Analyse terminée !")
                st.markdown("### 📝 Rapport de différences")
                st.markdown(resultat)
                
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
