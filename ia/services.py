"""
Service IA — NextSchoolAI.

Impémentation du pipeline de traitement des documents et de génération IA :

    1. Entrée       — PDF natif ou image scannée
    2. Prétraitement — Nettoyage OCR, extraction de texte (pdfplumber / Tesseract)
    3. Compréhension — Analyse de la structure logique du document
    4. Résolution   — Appel au modèle IA spécialisé (Gemini)
    5. Vérification  — Validation croisée du contenu généré
    6. Formatage    — Nettoyage Markdown / JSON
    7. Sortie       — Réponse utilisateur
"""

import os
import time
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Nombre maximum de pages converties lors de l'OCR d'un PDF scané
LIMITE_PAGES_OCR = 10

# Nombre minimum de caractères extrait pour considérer qu'un PDF est natif (non scané)
SEUIL_TEXTE_NATIF_CHARS = 100

# Durée simulée des réponses mock (mode développement hors-ligne)
DUREE_MOCK_SECONDES = 1.0

# Limite de caractères transmis à l'API Hugging Face (augmentée pour le contexte des documents)
LIMITE_PROMPT_HF_CHARS = 15000

# =============================================================================
# ÉTAPE 1 & 2 : ENTRÉE ET PRÉTRAITEMENT (NETTOYAGE & OCR)
# =============================================================================

def ocr_image(chemin_image: str) -> str:
    """Applique l'OCR sur une image et retourne le texte extrait."""
    try:
        from PIL import Image
        import pytesseract
        return pytesseract.image_to_string(Image.open(chemin_image), lang='fra+eng')
    except Exception as e:
        logger.error("Erreur OCR image %s : %s", chemin_image, e)
        return ""


def ocr_pdf(chemin_pdf: str) -> str:
    """Convertit un PDF scané en images puis applique l'OCR page par page."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(chemin_pdf, dpi=200)
        textes_par_page = []
        for image in images[:LIMITE_PAGES_OCR]:
            texte = pytesseract.image_to_string(image, lang='fra+eng')
            textes_par_page.append(texte)
        return "\n".join(textes_par_page)
    except Exception as e:
        logger.error("Erreur OCR PDF %s : %s", chemin_pdf, e)
        return ""

def extraire_texte(chemin_fichier: str) -> str:
    """
    Extrait le texte d'un fichier de manière intelligente.

    Pour les PDF, tente d'abord l'extraction native (plus rapide et précise).
    Si le texte extrait est insuffisant (<  SEUIL_TEXTE_NATIF_CHARS caractères),
    le fichier est traité comme un scan et l'OCR est lancé.
    """
    if not os.path.exists(chemin_fichier):
        return ""

    extension = chemin_fichier.lower().split('.')[-1]

    if extension in ('jpg', 'jpeg', 'png', 'webp'):
        return ocr_image(chemin_fichier)

    if extension == 'pdf':
        try:
            import pdfplumber
            textes_pages = []
            with pdfplumber.open(chemin_fichier) as pdf:
                for page in pdf.pages:
                    contenu = page.extract_text()
                    if contenu:
                        textes_pages.append(contenu)
            texte_natif = "\n".join(textes_pages).strip()

            if len(texte_natif) < SEUIL_TEXTE_NATIF_CHARS:
                logger.info(
                    "PDF sans texte natif (%d caractères). Lancement de l'OCR.",
                    len(texte_natif)
                )
                return ocr_pdf(chemin_fichier)
            return texte_natif

        except Exception as e:
            logger.error("Erreur pdfplumber, bascule sur l'OCR : %s", e)
            return ocr_pdf(chemin_fichier)

    return ""

def nettoyer_texte(texte: str, max_chars: int = 8000) -> str:
    """
    Nettoie les artefacts OCR et tronque le texte à la limite autorisée.

    La troncature s'effectue sur une limite de mot (rsplit) pour éviter
    de couper une phrase en plein milieu.
    """
    if not texte:
        return ""
    lignes = [ligne.strip() for ligne in texte.splitlines() if ligne.strip()]
    texte_propre = "\n".join(lignes)
    if len(texte_propre) > max_chars:
        texte_propre = texte_propre[:max_chars].rsplit(' ', 1)[0] + "..."
    return texte_propre

# =============================================================================
# REPONSES MOCK (MODE DEVELOPPEMENT HORS-LIGNE)
# =============================================================================

def _mock_qcm() -> dict:
    """Retourne un QCM fictif validé pour les tests sans clé API."""
    contenu_mock = (
        '{"questions": ['
        '{"enonce": "Qu\'est-ce que l\'encapsulation ?", "ordre": 1, "points": 1,'
        ' "explication": "Regrouper données et méthodes pour protéger l\'état interne.",'
        ' "options": ['
        '{"libelle": "Créer des fichiers ZIP", "est_correct": false},'
        '{"libelle": "Protéger les données d\'un objet", "est_correct": true},'
        '{"libelle": "Traduire le code en binaire", "est_correct": false}'
        ']},'
        '{"enonce": "A quoi sert le polymorphisme ?", "ordre": 2, "points": 1,'
        ' "explication": "Utiliser le même nom de méthode pour différents comportements.",'
        ' "options": ['
        '{"libelle": "Plusieurs formes d\'une même méthode", "est_correct": true},'
        '{"libelle": "Faire tourner du code sans serveur", "est_correct": false}'
        ']}'
        ']}'
    )
    return {'succes': True, 'contenu': contenu_mock, 'duree': DUREE_MOCK_SECONDES, 'erreur': ''}


def _mock_chat() -> dict:
    """Retourne une réponse de chat fictive pour les tests sans clé API."""
    contenu_mock = (
        "*(Note : Réponse fictive, mode hors-ligne, clé API Gemini absente ou expirée.)*\n\n"
        "Je suis un **assistant pédagogique IA** capable de :\n"
        "- Expliquer n'importe quelle **section** ou **point** du cours\n"
        "- Générer des **exemples de code** (Python, C, Java, etc.)\n"
        "- Afficher des **formules mathématiques** et physiques en LaTeX\n\n"
        "**Exemple — Code Python (POO) :**\n"
        "```python\n"
        "class Animal:\n"
        "    def __init__(self, nom):\n"
        "        self.nom = nom\n\n"
        "    def parler(self):\n"
        "        raise NotImplementedError('Methode abstraite')\n\n"
        "class Chien(Animal):\n"
        "    def parler(self):\n"
        "        return f'{self.nom} dit : Ouaf !'\n\n"
        "rex = Chien('Rex')\n"
        "print(rex.parler())\n"
        "```\n\n"
        "**Exemple — Formule LaTeX :**\n"
        "$$E = mc^2$$\n\n"
        "> Pour activer les vraies réponses, configurez `GEMINI_API_KEY` dans `.env`."
    )
    return {'succes': True, 'contenu': contenu_mock, 'duree': DUREE_MOCK_SECONDES, 'erreur': ''}


def _mock_resume() -> dict:
    """Retourne un résumé fictif pour les tests sans clé API."""
    contenu_mock = (
        "## Points Cles\n"
        "- Concepts avancés et principes fondamentaux du programme.\n"
        "- Modélisation mathématique et exercices corrigés.\n"
        "- Structure logique et définitions formelles.\n\n"
        "## Resumé Synthétique\n"
        "Ce document aborde en profondeur les notions théoriques liées au programme. "
        "Il présente les mécanismes de résolution d'exercices et des cas pratiques.\n\n"
        "> *(Note : Texte fictif — clé API Google invalide ou expirée.)*"
    )
    return {'succes': True, 'contenu': contenu_mock, 'duree': DUREE_MOCK_SECONDES, 'erreur': ''}


# =============================================================================
# MOTEURS IA (GEMINI ET HUGGING FACE)
# =============================================================================

def appeler_gemini(prompt: str, json_format: bool = False) -> dict:
    """Appelle l'API Gemini et retourne le résultat structuré."""
    cle_api = settings.GEMINI_API_KEY
    if not cle_api:
        return {'succes': False, 'contenu': '', 'erreur': "Clé API absente."}

    try:
        import google.generativeai as genai
        genai.configure(api_key=cle_api)
        modele = genai.GenerativeModel(settings.GEMINI_MODEL)

        configuration = genai.GenerationConfig(
            max_output_tokens=settings.IA_MAX_TOKENS,
            temperature=0.3 if json_format else 0.7,
        )

        debut = time.time()
        reponse = modele.generate_content(prompt, generation_config=configuration)
        duree = round(time.time() - debut, 2)

        contenu = reponse.text if reponse.text else ""
        return {'succes': True, 'contenu': contenu, 'duree': duree, 'erreur': ''}

    except Exception as erreur:
        logger.error("Erreur API Gemini : %s", erreur)

        if settings.DEBUG:
            logger.info("Bascule sur le mock de développement (API absent ou clé invalide).")
            time.sleep(DUREE_MOCK_SECONDES)

            if json_format:
                return _mock_qcm()
            if "Question de l'étudiant :" in prompt:
                return _mock_chat()
            return _mock_resume()

        return {'succes': False, 'contenu': '', 'erreur': str(erreur)}


def appeler_huggingface(prompt: str, json_format: bool = False, model_override: str = None) -> dict:
    """Appelle l'API Hugging Face en tant que moteur de référence (désormais prioritaire)."""
    cle_api = settings.HUGGINGFACE_API_KEY
    if not cle_api:
        return {'succes': False, 'contenu': '', 'erreur': "Clé Hugging Face absente."}
    
    model = model_override or settings.HUGGINGFACE_MODEL
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=cle_api)
        debut = time.time()
        
        system_prompt = "Tu es un professeur expert. Réponds en français de manière très claire."
        if json_format:
            system_prompt += " IMPORTANT: Renvoyer UNIQUEMENT un objet JSON valide, SANS texte autour ni code block ```."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt[:LIMITE_PROMPT_HF_CHARS]}
        ]
        
        response = client.chat_completion(
            model=model,
            messages=messages,
            max_tokens=settings.IA_MAX_TOKENS,
            temperature=0.3 if json_format else 0.7
        )
        duree = round(time.time() - debut, 2)

        contenu = response.choices[0].message.content
        return {'succes': True, 'contenu': contenu.strip(), 'duree': duree, 'erreur': ''}
    except Exception as erreur:
        return {'succes': False, 'contenu': '', 'erreur': str(erreur)}

def appeler_ia(prompt: str, json_format: bool = False) -> dict:
    """Routeur IA (Priorité HF avec Fallback DeepSeek, puis Gemini, puis Mock)."""
    if settings.HUGGINGFACE_API_KEY:
        # Essai 1: Modèle préféré (Llama 3.1)
        res = appeler_huggingface(prompt, json_format)
        if res['succes']:
            res['moteur'] = 'huggingface'
            return res
            
        logger.error("HuggingFace primaire échoué: %s", res.get('erreur'))
        
        # Essai 2: Fallback demandé par l'utilisateur
        if "Llama" in settings.HUGGINGFACE_MODEL:
            res_fb = appeler_huggingface(prompt, json_format, "deepseek-ai/DeepSeek-R1")
            if res_fb['succes']:
                res_fb['moteur'] = 'deepseek'
                return res_fb
            
    # Essai 3: Gemini (si clé configurée, ce qui n'est plus le cas mais géré)
    res_gemini = appeler_gemini(prompt, json_format)
    if res_gemini['succes']:
        res_gemini['moteur'] = 'gemini'
        return res_gemini
        
    # Essai 4: Mock (Dernier recours absolu)
    logger.info("Bascule sur le mock IA car tous les moteurs ont échoué.")
    time.sleep(1)
    if json_format: return _mock_qcm()
    if "Question de l'étudiant :" in prompt: return _mock_chat()
    return _mock_resume()


# =============================================================================
# PIPELINE IA COMPLET (ÉTAPES 3, 4, 5, 6, 7)
# =============================================================================

class IAService:

    @classmethod
    def _etape_comprehension(cls, texte: str) -> str:
        """Étape 3 : Analyse la structure du document."""
        prompt = f"Analyse ce texte et donne-moi uniquement ses 3 thèmes majeurs très brièvement:\n\n{texte[:3000]}"
        res = appeler_ia(prompt)
        return res['contenu'] if res['succes'] else ""

    @classmethod
    def _etape_verification(cls, tache: str, contenu_resolu: str) -> bool:
        """Étape 5 : 2e IA vérifie la cohérence du contenu."""
        prompt_verif = (
            f"Ce contenu pédagogique semble-t-il cohérent et sans propos inappropriés ? "
            f"Réponds Oui ou Non : {contenu_resolu[:1000]}"
        )
        res_verif = appeler_ia(prompt_verif)
        if res_verif['succes'] and "Non" in res_verif['contenu']:
            logger.warning("[IA] La vérification croisée a levé un doute sur le contenu généré!")
            return False
        return True

    @classmethod
    def generer_resume(cls, texte_document: str, titre: str = "", chemin_document: str = "") -> dict:
        """Pipeline complète de résumé — utilise TOUT le document pour le contexte."""
        texte = extraire_texte(chemin_document) if chemin_document else texte_document
        texte_propre = nettoyer_texte(texte)
        if not texte_propre:
            return {'succes': False, 'contenu': '', 'erreur': "Texte vide après OCR/Prétraitement."}

        structure = cls._etape_comprehension(texte_propre)

        prompt = (
            f"Tu es un professeur expert. Le document s'intitule \"{titre}\" et aborde les thèmes suivants : {structure}.\n"
            f"Génère un résumé éducatif complet et structuré en Markdown (avec ## Titres, **gras**, listes à puces).\n"
            f"Inclure : Points clés, Résumé, Formules importantes si présentes (en LaTeX $$...$$), Ce qu'il faut retenir.\n\n"
            f"Voici le document :\n{texte_propre}"
        )
        resol = appeler_ia(prompt)

        if resol.get('succes'):
            cls._etape_verification("resume", resol.get('contenu', ''))

        resol.setdefault('moteur', 'huggingface')
        return resol

    @classmethod
    def generer_qcm(cls, texte_document: str, nb_questions: int = 10, titre: str = "", chemin_document: str = "") -> dict:
        """Pipeline complète de QCM."""
        texte = extraire_texte(chemin_document) if chemin_document else texte_document
        texte_propre = nettoyer_texte(texte)
        if not texte_propre:
            return {'succes': False, 'questions': [], 'erreur': "Texte vide après OCR/Prétraitement."}

        structure = cls._etape_comprehension(texte_propre)

        prompt = (
            f'Fais un QCM de {nb_questions} questions sur le sujet "{titre}" basé sur ces thèmes: {structure}.\n'
            f'Texte source: {texte_propre}\n'
            f'Réponds en JSON strict UNIQUEMENT: {{"questions": [ {{"enonce": "...", "ordre": 1, "points": 1, '
            f'"explication": "...", "options": [{{"libelle": "A", "est_correct": true}}, '
            f'{{"libelle": "B", "est_correct": false}}] }} ] }}'
        )

        resol = appeler_ia(prompt, json_format=True)
        if not resol['succes']:
            return {'succes': False, 'questions': [], 'erreur': resol['erreur']}

        contenu = resol['contenu'].strip()

        if contenu.startswith('```json'):
            contenu = contenu[7:]
        if contenu.startswith('```'):
            contenu = contenu[3:]
        if contenu.endswith('```'):
            contenu = contenu[:-3]

        try:
            data = json.loads(contenu)
            return {'succes': True, 'questions': data.get('questions', []), 'moteur': resol.get('moteur', 'huggingface'), 'erreur': ''}
        except Exception:
            return {'succes': False, 'questions': [], 'erreur': "Erreur Formatage JSON de l'IA."}

    @classmethod
    def generer_explication(cls, question: str, contexte: str = "") -> dict:
        """
        Chat IA — Répond à une question basée sur le CONTENU COMPLET du document.
        L'IA peut expliquer n'importe quelle section, point, formule ou concept.
        """
        prompt = (
            "Tu es un assistant pédagogique expert. Tu as accès au contenu complet d'un document.\n"
            "Réponds de façon précise, structurée et pédagogique à la question de l'étudiant.\n"
            "- Utilise le **Markdown** pour formater ta réponse (titres, listes, gras).\n"
            "- Si des formules mathématiques ou physiques sont concernées, utilise la notation LaTeX ($$...$$).\n"
            "- Si du code est demandé, fournis un exemple complet et commenté.\n"
            "- Si l'étudiant demande 'la section X' ou 'le point Y', fournis ce contenu précis extrait du document.\n\n"
        )
        if contexte:
            prompt += f"=== CONTENU DU DOCUMENT ===\n{contexte}\n=== FIN DU DOCUMENT ===\n\n"
        prompt += f"Question de l'étudiant : {question}"

        resol = appeler_ia(prompt)
        return resol

    @classmethod
    def analyser_document(cls, document) -> str:
        """Auto-Validation IA (post-upload). Étape OCR + Compréhension."""
        texte = extraire_texte(document.url_fichier.path)
        if len(texte) < 50:
            return 'rejete'
        return 'valide'
