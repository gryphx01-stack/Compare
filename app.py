import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(layout="wide", page_title="Audit IA - Sélecteur")

# --- 1. CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY", None)

# --- 2. FONCTION POUR LISTER LES MODÈLES ---
def get_my_models(key):
    try:
        genai.configure(api_key=key)
        # On récupère tous les modèles qui savent générer du contenu
        all_models = list(genai.list_models())
        # On garde ceux qui ont "generateContent" et qui sont des Gemini
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
        return valid_models
    except Exception as e:
        return ["Erreur de récupération"]

# --- 3. INTERFACE ---
st.title("🎛️ Comparateur avec Choix du Modèle")

with st.sidebar:
    st.header("Paramètres")
    if api_key:
        st.success("✅ Clé connectée")
        
        # --- LE MENU MAGIQUE ICI ---
        # On charge la liste réelle disponible pour votre clé
        with st.spinner("Chargement de vos modèles..."):
            model_options = get_my_models(api_key)
            
        # On essaie de pré-sélectionner un modèle Flash s'il existe
        default_index = 0
        for i, name in enumerate(model_options):
            if "flash" in name and "1.5" in name:
                default_index = i
                break
        
        selected_model = st.selectbox(
            "Choisir le modèle IA :", 
            model_options, 
            index=default_index,
            help="Si un modèle échoue (404 ou 429), essayez-en un autre dans la liste !"
        )
        st.info(f"Modèle actif : `{selected_model}`")
        # ---------------------------
        
    else:
        st.error("❌ Clé manquante")

# --- 4. ANALYSE (Version "Œil de Lynx") ---
def analyze(key, model_name, file1, file2):
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name)
    
    # On force l'IA à être ultra-méticuleuse
    prompt = """
    Tu es un correcteur professionnel et un expert en comparaison de données.
    
    TA MISSION :
    Compare le Document 1 (gauche/haut) et le Document 2 (droite/bas) LIGNE PAR LIGNE.
    Tu dois relever TOUTES les différences textuelles, même minimes.
    
    CE QUE TU DOIS CHERCHER SPÉCIFIQUEMENT :
    1. Mots ajoutés ou supprimés (ex: "les photos" vs "les nouvelles photos").
    2. Fautes de frappe ou changements d'orthographe (ex: "Beaune" vs "Baume les Dames").
    3. Changements de ponctuation (ex: "vous" vs "nous !!").
    4. Différences de dates ou de noms propres.
    
    FORMAT DE RÉPONSE OBLIGATOIRE :
    Présente le résultat sous forme d'un tableau Markdown avec 3 colonnes :
    | Localisation (Ligne approx) | Texte dans Doc 1 (Original) | Texte dans Doc 2 (Modifié) |
    |-----------------------------|-----------------------------|----------------------------|
    | ...                         | ...                         | ...                        |

    Si une ligne est identique, ignore-la. Concentre-toi uniquement sur les différences.
    """
    
    response = model.generate_content([prompt, file1, file2])
    return response.text

# --- 5. ZONES UPLOAD ---
col1, col2 = st.columns(2)
file1 = col1.file_uploader("Document 1", type=["jpg", "png", "jpeg"])
file2 = col2.file_uploader("Document 2", type=["jpg", "png", "jpeg"])

if st.button("Lancer l'analyse", type="primary"):
    if not api_key:
        st.error("Pas de clé.")
    elif not file1 or not file2:
        st.warning("Manque des fichiers.")
    else:
        with st.spinner(f"Analyse avec {selected_model}..."):
            try:
                img1 = Image.open(file1)
                img2 = Image.open(file2)
                
                res = analyze(api_key, selected_model, img1, img2)
                
                st.success("Analyse terminée !")
                st.markdown(res)
                
            except Exception as e:
                st.error(f"Erreur avec ce modèle : {e}")
                st.markdown("👉 **Solution :** Changez de modèle dans le menu de gauche et réessayez !")


