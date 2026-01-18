import streamlit as st
import google.generativeai as genai
import sys

st.set_page_config(page_title="Diagnostic Clé API")

st.title("🛠️ Diagnostic de votre Clé API")

# 1. Récupération de la clé
api_key = st.secrets.get("GEMINI_API_KEY", None)

# Zone de saisie manuelle si le secret ne marche pas
if not api_key:
    api_key = st.text_input("Collez votre clé API ici pour tester :", type="password")

if st.button("LANCER LE DIAGNOSTIC"):
    if not api_key:
        st.error("Pas de clé détectée.")
    else:
        try:
            # Configuration
            genai.configure(api_key=api_key)
            
            st.info(f"Version de la librairie installée : {genai.__version__}")
            st.write("Tentative de connexion aux serveurs Google...")
            
            # ON DEMANDE LA LISTE DES MODÈLES DISPONIBLES
            model_list = []
            for m in genai.list_models():
                model_list.append(m.name)
            
            if len(model_list) > 0:
                st.success(f"✅ SUCCÈS ! Votre clé fonctionne et voit {len(model_list)} modèles.")
                st.write("Voici les noms EXACTS que votre clé a le droit d'utiliser :")
                st.code(model_list)
                st.markdown("---")
                st.write("👉 Copiez un des noms ci-dessus (ex: `models/gemini-pro`) pour le mettre dans votre code.")
            else:
                st.warning("⚠️ La connexion fonctionne, mais AUCUN modèle n'est disponible pour cette clé.")
                st.write("Causes possibles :")
                st.write("1. La clé vient de Google Cloud Platform et l'API 'Generative Language' n'est pas activée.")
                st.write("2. Restriction géographique (Europe) sur une clé gratuite.")

        except Exception as e:
            st.error(f"❌ ERREUR CRITIQUE : {str(e)}")
            st.write("Cela signifie que la clé est invalide ou rejetée par Google.")
