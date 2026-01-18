import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Audit IA - Comparateur de Documents")

# --- STYLES CSS PERSONNALISÉS ---
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6 }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
    h1 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def configure_gemini(api_key):
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True

def analyze_documents(model, file_ref, file_comp):
    prompt = """
    Tu es un auditeur expert. Compare ces deux documents (images ou texte) et détecte TOUTES les différences.
    
    INSTRUCTIONS :
    1. Compare les prix, quantités, références, dates et totaux.
    2. Ignore les différences minimes de mise en page, concentre-toi sur le CONTENU.
    
    FORMAT DE SORTIE JSON STRICT :
    {
        "differences_found": true,
        "total_differences": 0,
        "resume": "Phrase de synthèse",
        "details": [
            {"objet": "Prix Art. A", "ref": "10€", "comp": "12€", "type": "prix"},
            {"objet": "Total HT", "ref": "100€", "comp": "120€", "type": "total"}
        ],
        "niveau_alerte": "faible/moyen/critique"
    }
    """
    
    # Préparation des contenus pour Gemini
    contents = [prompt, "DOCUMENT REFERENCE:", file_ref, "DOCUMENT A COMPARER:", file_comp]
    
    response = model.generate_content(
        contents,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)

# --- INTERFACE UTILISATEUR ---
st.title("🔍 Comparateur de Documents Intelligent")
st.markdown("Solution d'audit automatisée par IA pour la validation de factures et documents comptables.")

# Barre latérale pour la configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # On vérifie si la clé est cachée dans les secrets Streamlit
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ Clé API chargée automatiquement")
    else:
        # Sinon, on laisse le champ manuel (au cas où)
        api_key = st.text_input("Clé API Gemini", type="password", help="Nécessaire pour l'analyse")
        
    st.info("Cette application utilise le modèle Gemini 1.5 Flash pour une analyse rapide et multimodale.")

# Zone d'Upload
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Document de Référence")
    ref_file = st.file_uploader("Déposez le bon de commande / devis", type=['png', 'jpg', 'jpeg'])
    if ref_file:
        img_ref = Image.open(ref_file)
        st.image(img_ref, caption="Référence", use_container_width=True)

with col2:
    st.subheader("2. Document à Comparer")
    comp_file = st.file_uploader("Déposez la facture / bon de livraison", type=['png', 'jpg', 'jpeg'])
    if comp_file:
        img_comp = Image.open(comp_file)
        st.image(img_comp, caption="Comparaison", use_container_width=True)

# Bouton d'action
if ref_file and comp_file and api_key:
    if st.button("🚀 LANCER L'ANALYSE COMPARATIVE"):
        if not configure_gemini(api_key):
            st.error("Clé API invalide")
        else:
            model = genai.GenerativeModel("gemini-1.5-pro")
            
            with st.spinner('L\'IA analyse les documents pixel par pixel...'):
                try:
                    # Conversion pour l'API
                    result = analyze_documents(model, img_ref, img_comp)
                    
                    # AFFICHAGE DES RÉSULTATS
                    st.divider()
                    
                    # En-tête de résultat
                    r_col1, r_col2 = st.columns([1, 3])
                    with r_col1:
                        color = "red" if result['niveau_alerte'] == "critique" else "orange" if result['niveau_alerte'] == "moyen" else "green"
                        st.markdown(f"""
                        <div class="metric-card" style="border-left: 5px solid {color}">
                            <h2 style="color:{color}">{result['total_differences']}</h2>
                            <p>Différences</p>
                            <small>{result['niveau_alerte'].upper()}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with r_col2:
                        st.subheader("Synthèse de l'audit")
                        st.info(result['resume'])

                    # Tableau détaillé
                    if result['differences_found']:
                        st.subheader("Détail des écarts")
                        df = pd.DataFrame(result['details'])
                        # Renommer les colonnes pour l'affichage
                        df.columns = ['Élément concerné', 'Valeur Réf.', 'Valeur Comp.', 'Type']
                        
                        # Coloration conditionnelle du tableau
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Type": st.column_config.TextColumn(
                                    "Catégorie",
                                    help="Type d'erreur",
                                    width="medium",
                                ),
                            }
                        )
                    else:
                        st.balloons()
                        st.success("Aucune différence détectée. Les documents sont identiques.")

                except Exception as e:
                    st.error(f"Une erreur est survenue : {str(e)}")
elif not api_key:

    st.warning("Veuillez entrer une clé API Gemini dans le menu de gauche pour commencer.")


