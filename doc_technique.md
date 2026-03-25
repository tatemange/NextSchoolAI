# NextSchoolAI — Documentation Technique

> **Version** : 1.1 — Dernière mise à jour : 25/03/2026

---

## 1. Architecture du Projet

```
NextSchoolAI/
├── accounts/         # Authentification, profils, gestion des rôles
├── documents/        # Gestion des documents (CRUD, modération, évaluation)
├── quiz/             # QCM générés par IA, correction, historique
├── ia/               # Pipeline IA : OCR, résumé, QCM, chat
├── core/             # Configuration Django (settings, wsgi, asgi)
├── templates/        # Templates HTML (Jinja2/Django)
├── static/css/       # Design system CSS (nextschoolai.css)
├── media/            # Fichiers uploadés (documents, images)
└── manage.py
```

### Applications Django

| App | Rôle | Modèles principaux |
|-----|------|-------------------|
| `accounts` | Auth, profils, rôles (étudiant, enseignant, admin) | `Utilisateur` |
| `documents` | Upload, modération, évaluation, téléchargement | `Document`, `Cours`, `Epreuve`, `Livre`, `Activite`, `Evaluer` |
| `quiz` | Génération QCM IA, passage, correction | `QCM`, `Question`, `Option`, `Tentative` |
| `ia` | Pipeline IA, interactions, chat | `InteractionIA` |

---

## 2. Pipeline IA (`ia/services.py`)

### Étapes du pipeline

```
PDF/Image → OCR/Extraction → Nettoyage → Compréhension → Résolution IA → Vérification → Formatage → Réponse
```

| Étape | Fonction | Description |
|-------|----------|-------------|
| 1-2 | `extraire_texte()` | Extraction native (pdfplumber) ou OCR (Tesseract) |
| 2 | `nettoyer_texte()` | Nettoyage artefacts OCR, troncature |
| 3 | `_etape_comprehension()` | Analyse thématique du document |
| 4 | `appeler_ia()` | Routeur multi-moteur : HuggingFace → DeepSeek → Gemini → Mock |
| 5 | `_etape_verification()` | Vérification croisée par 2ème appel IA |
| 6-7 | `IAService.*` | Formatage Markdown/JSON, réponse utilisateur |

### Chaîne de fallback des moteurs IA

```
HuggingFace (Llama 3.1) → DeepSeek R1 → Google Gemini → Mock (hors-ligne)
```

### Constantes clés

| Constante | Valeur | Rôle |
|-----------|--------|------|
| `LIMITE_PAGES_OCR` | 10 | Max pages pour l'OCR |
| `SEUIL_TEXTE_NATIF_CHARS` | 100 | Seuil pour détecter un PDF natif vs scanné |
| `LIMITE_PROMPT_HF_CHARS` | 15000 | Limite de caractères envoyés à l'API HF |

---

## 3. Endpoints de l'API IA

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/ia/document/<pk>/resumer/` | GET/POST | Génération de résumé IA |
| `/ia/document/<pk>/chat/` | POST (AJAX) | Chat IA sur un document |

### Paramètres du chat AJAX (`ia:chat_ajax`)

- **Entrée** : `POST { message: string }` + CSRF token
- **Sortie** : `JSON { succes: bool, reponse: string, erreur: string }`

---

## 4. Modèle de données IA

### `InteractionIA`

| Champ | Type | Description |
|-------|------|-------------|
| `utilisateur` | FK → User | Utilisateur qui a interagi |
| `document` | FK → Document | Document source |
| `type_interaction` | CharField | `resume`, `qcm`, `correction`, `explication` |
| `moteur_ia` | CharField | `gemini`, `huggingface`, `deepseek`, `local` |
| `prompt_utilisateur` | TextField | Prompt envoyé |
| `contenu_genere` | TextField | Réponse de l'IA |
| `duree_secondes` | PositiveSmallInteger | Temps de génération |
| `succes` | BooleanField | Succès de l'opération |

---

## 5. Design System CSS

Fichier : `static/css/nextschoolai.css` — Palette **Brownie/Coffee/Caramel/Cream**.

### Variables principales

```css
--color-cream:   #F8E9C0    /* Texte principal */
--color-caramel: #C0A86E    /* Accents */
--color-coffee:  #895737    /* Boutons primaires */
--color-brownie: #5E3023    /* Fond des boutons */
--bg-base:       #120a06    /* Fond extrême */
--bg-primary:    #1a0f0a    /* Corps de page */
--bg-surface:    #2b1b13    /* Cards, panels */
--font-sans:     'Inter'    /* Typographie principale */
```

### Composants UI

- **Cards** : `.card`, `.card-header`, `.card-body`, `.card-footer`
- **Boutons** : `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`
- **Formulaires** : `.floating-group`, `.form-input`, `.floating-label`
- **Chat** : `.chat-zone`, `.chat-bubble-user`, `.chat-bubble-ai`, `.chat-input-bar`
- **Badges** : `.badge-blue`, `.badge-gray`, `.badge-green`

---

## 6. Interface de Chat IA

### Architecture frontend

```
chat-zone
├── chat-zone-header    → Titre + avatar IA + bouton nouvelle conversation
├── chat-attachment     → Document attaché (pièce jointe)
├── chat-messages       → Zone scrollable des messages
│   ├── chat-bubble-ai  → Message IA (avec avatar, markdown, LaTeX)
│   └── chat-bubble-user → Message utilisateur
└── chat-input-bar      → Textarea auto-resize + bouton envoi
```

### Fonctionnalités

- **Auto-resize** du textarea (max 160px)
- **Shift+Enter** pour nouvelle ligne, **Enter** pour envoyer
- **Suggestions** cliquables (résumé, concepts, formules, fiches)
- **Rendu Markdown** via `marked.js` + sanitisation `DOMPurify`
- **Rendu LaTeX** via `MathJax 3`
- **Animation** d'apparition des bulles (fade + slide up)
- **Indicateur de frappe** (3 points animés)

---

## 7. Configuration `.env`

```env
HUGGINGFACE_API_KEY=hf_xxx       # Clé API HuggingFace (prioritaire)
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct
GEMINI_API_KEY=                   # Optionnel, fallback
GEMINI_MODEL=gemini-pro
IA_MAX_TOKENS=4096
SECRET_KEY=xxx
DEBUG=True
```

---

## 8. Dépendances principales

| Package | Version | Rôle |
|---------|---------|------|
| Django | 5.x | Framework web |
| pdfplumber | latest | Extraction texte PDF natif |
| pytesseract | latest | OCR (scans) |
| pdf2image | latest | Conversion PDF → images |
| Pillow | latest | Manipulation d'images |
| huggingface_hub | latest | Client API HuggingFace |
| google-generativeai | latest | Client API Gemini (fallback) |
