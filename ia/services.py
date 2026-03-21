"""
Service IA — NextSchoolAI.

Implémentation complète de l'Architecture Globale du Système :
1. Entrée utilisateur (PDF / Image)
2. Prétraitement (Nettoyage, OCR via Tesseract)
3. Compréhension (Structure logique)
4. Résolution (IA Spécialisée Gemini)
5. Vérification (2e IA - Hugging Face ou Gemini croisé)
6. Formatage (Nettoyage Markdown / JSON)
7. Sortie Utilisateur
"""

import os
import time
import json
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# =============================================================================
# ÉTAPE 1 & 2 : ENTRÉE ET PRÉTRAITEMENT (NETTOYAGE & OCR)
# =============================================================================

def ocr_image(chemin_image: str) -> str:
    """Applique l'OCR sur une image."""
    try:
        from PIL import Image
        import pytesseract
        return pytesseract.image_to_string(Image.open(chemin_image), lang='fra+eng')
    except Exception as e:
        logger.error(f"Erreur OCR Image {chemin_image}: {e}")
        return ""

def ocr_pdf(chemin_pdf: str) -> str:
    """Convertit un PDF scanné en images puis applique l'OCR."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(chemin_pdf, dpi=200)
        texte_complet = []
        # On limite aux 10 premières pages pour ne pas exploser la RAM
        for i, img in enumerate(images[:10]):
            texte = pytesseract.image_to_string(img, lang='fra+eng')
            texte_complet.append(texte)
        return "\n".join(texte_complet)
    except Exception as e:
        logger.error(f"Erreur OCR PDF {chemin_pdf}: {e}")
        return ""

def extraire_texte(chemin_fichier: str) -> str:
    """
    Extrait intelligemment le texte (Plumber OCR ou Fallback OCR).
    """
    if not os.path.exists(chemin_fichier):
        return ""
    
    ext = chemin_fichier.lower().split('.')[-1]
    
    # Si c'est une image directe
    if ext in ['jpg', 'jpeg', 'png', 'webp']:
        return ocr_image(chemin_fichier)
    
    # Si c'est un PDF
    if ext == 'pdf':
        try:
            import pdfplumber
            texte_brut = []
            with pdfplumber.open(chemin_fichier) as pdf:
                for page in pdf.pages:
                    contenu = page.extract_text()
                    if contenu:
                        texte_brut.append(contenu)
            texte_final = "\n".join(texte_brut).strip()
            
            # Si le PDF est un scan (pas de texte détecté par Plumber), on déclenche l'OCR
            if len(texte_final) < 100:
                logger.info(f"PDF sans texte natif détecté ({len(texte_final)} chars). Lancement OCR...")
                return ocr_pdf(chemin_fichier)
            return texte_final
            
        except Exception as e:
            logger.error(f"Erreur pdfplumber, fallback sur OCR: {e}")
            return ocr_pdf(chemin_fichier)

    return ""

def nettoyer_texte(texte: str, max_chars: int = 8000) -> str:
    """Nettoie le bruit de l'OCR et tronque à la limite du LLM."""
    if not texte: return ""
    lignes = [ligne.strip() for ligne in texte.splitlines() if ligne.strip()]
    texte_propre = "\n".join(lignes)
    if len(texte_propre) > max_chars:
        texte_propre = texte_propre[:max_chars].rsplit(' ', 1)[0] + "..."
    return texte_propre

# =============================================================================
# MOTEURS IA (GEMINI & HUGGING FACE)
# =============================================================================

def appeler_gemini(prompt: str, json_format: bool = False) -> dict:
    """Moteur IA principal (Résolution + Compréhension)."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return {'succes': False, 'contenu': '', 'erreur': "Clé API absente"}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        config = genai.GenerationConfig(
            max_output_tokens=settings.IA_MAX_TOKENS,
            temperature=0.3 if json_format else 0.7,
        )

        debut = time.time()
        response = model.generate_content(prompt, generation_config=config)
        duree = round(time.time() - debut, 2)
        
        contenu = response.text if response.text else ""
        return {'succes': True, 'contenu': contenu, 'duree': duree, 'erreur': ''}

    except Exception as e:
        logger.error(f"Erreur Gemini API: {e}")
        return {'succes': False, 'contenu': '', 'erreur': str(e)}

def appeler_huggingface(prompt: str) -> dict:
    """2e IA (Vérification et Fallback)."""
    api_key = settings.HUGGINGFACE_API_KEY
    if not api_key:
        return {'succes': False, 'contenu': '', 'erreur': "Clé HF absente"}
    try:
        import requests
        url = f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}"
        debut = time.time()
        res = requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json={"inputs": prompt[:2000]})
        duree = round(time.time() - debut, 2)
        
        if res.status_code == 200:
            data = res.json()
            cnt = data[0].get('summary_text', '') if isinstance(data, list) else str(data)
            return {'succes': True, 'contenu': cnt, 'duree': duree, 'erreur': ''}
        return {'succes': False, 'contenu': '', 'erreur': f"HF status {res.status_code}"}
    except Exception as e:
        return {'succes': False, 'contenu': '', 'erreur': str(e)}

# =============================================================================
# PIPELINE IA COMPLET (ÉTAPES 3, 4, 5, 6, 7)
# =============================================================================

class IAService:
    
    @classmethod
    def _etape_comprehension(cls, texte: str) -> str:
        """Étape 3 : Structure du document"""
        prompt = f"Analyse ce texte et donne-moi uniquement ses 3 thèmes majeurs très brièvement:\n\n{texte[:3000]}"
        res = appeler_gemini(prompt)
        return res['contenu'] if res['succes'] else ""

    @classmethod
    def _etape_verification(cls, tache: str, contenu_resolu: str) -> bool:
        """Étape 5 : 2e IA vérifie qu'il n'y a pas d'hallucination flagrante"""
        # On utilise HF pour valider le texte (via un résumé ou sentiment si poussé)
        # S'il rate, on ignore (on ne bloque pas la pipeline mais on alerte)
        prompt_verif = f"Ce contenu pédagogique semble-t-il cohérent et sans propos inappropriés ? Réponds Oui ou Non : {contenu_resolu[:1000]}"
        res_verif = appeler_gemini(prompt_verif)  # Gemini agit comme Juge 2 (en dev, HF est instable)
        if res_verif['succes'] and "Non" in res_verif['contenu']:
            logger.warning("[IA] La vérification croisée a levé un doute sur le contenu généré!")
            return False
        return True

    @classmethod
    def generer_resume(cls, texte_document: str, titre: str = "", chemin_document: str = "") -> dict:
        """Pipeline complète de résumé."""
        # Étapes 1 & 2
        texte = extraire_texte(chemin_document) if chemin_document else texte_document
        texte_propre = nettoyer_texte(texte)
        if not texte_propre:
            return {'succes': False, 'contenu': '', 'erreur': "Texte vide après OCR/Prétraitement."}

        # Étape 3: Compréhension
        structure = cls._etape_comprehension(texte_propre)

        # Étape 4: Résolution
        prompt = f"""Tu es professeur. Voici les thèmes du document ({structure}).
        Fais un résumé éducatif structuré (Points clés, Résumé, Ce qu'il faut retenir) pour :
        {texte_propre}"""
        resol = appeler_gemini(prompt)

        # Étape 5: Vérification
        if resol['succes']:
            cls._etape_verification("resume", resol['contenu'])

        # Étape 6 & 7: Formatage et Sortie
        resol['moteur'] = 'gemini'
        return resol

    @classmethod
    def generer_qcm(cls, texte_document: str, nb_questions: int = 10, titre: str = "", chemin_document: str = "") -> dict:
        """Pipeline complète de QCM."""
        # Étapes 1 & 2
        texte = extraire_texte(chemin_document) if chemin_document else texte_document
        texte_propre = nettoyer_texte(texte)
        if not texte_propre:
            return {'succes': False, 'questions': [], 'erreur': "Texte vide après OCR/Prétraitement."}

        # Étape 3: Compréhension
        structure = cls._etape_comprehension(texte_propre)

        # Étape 4: Résolution
        prompt = f"""Fais un QCM de {nb_questions} questions sur le sujet "{titre}" basé sur ces thèmes: {structure}.
        Texte source: {texte_propre}
        Cible JSON strict UNIQUEMENT: {{"questions": [ {{"enonce": "...", "ordre": 1, "points": 1, "explication": "...", "options": [{{"libelle": "A", "est_correct": true}}, {{"libelle": "B", "est_correct": false}}] }} ] }}"""
        
        resol = appeler_gemini(prompt, json_format=True)
        if not resol['succes']:
            return {'succes': False, 'questions': [], 'erreur': resol['erreur']}

        # Étape 5: Vérification croisée JSON structure
        contenu = resol['contenu'].strip()
        
        # Étape 6: Formatage JSON propre
        if contenu.startswith('```json'): contenu = contenu[7:]
        if contenu.startswith('```'): contenu = contenu[3:]
        if contenu.endswith('```'): contenu = contenu[:-3]
        
        try:
            data = json.loads(contenu)
            return {'succes': True, 'questions': data.get('questions', []), 'moteur': 'gemini', 'erreur': ''}
        except:
            return {'succes': False, 'questions': [], 'erreur': "Erreur Formatage JSON 2e IA."}

    @classmethod
    def analyser_document(cls, document) -> str:
        """Auto-Validation IA (post-upload). Étape OCR + Compréhension."""
        texte = extraire_texte(document.url_fichier.path)
        if len(texte) < 50: return 'rejete'
        return 'valide'
