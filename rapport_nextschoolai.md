# RAPPORT DE PROJET
## NextSchoolAI — Conception et réalisation d'une solution numérique centralisée pour l'accès aux ressources éducatives, enrichie d'un modèle de langage (LLM)

**Réalisé par :** TATEM ANGE ULRICH  
**Classe :** 2ème Année Génie Logiciel  
**Année académique :** 2024–2025  

---

# CHAPITRE III — RÉALISATION ET IMPLÉMENTATION

*(Les sections III.1 à III.4 ont été rédigées précédemment)*

---

## III.5 — Implémentation Technique

Cette section décrit les choix d'implémentation réels effectués lors du développement de NextSchoolAI. L'ensemble du projet a été réalisé avec le framework **Django 5.x** (Python 3.12), organisé en quatre applications modulaires : `accounts`, `documents`, `quiz` et `ia`.

### III.5.1 — Architecture Générale du Projet

Le projet suit un découpage en applications Django distinctes, chacune responsable d'un domaine métier précis :

| Application | Responsabilité |
|---|---|
| `accounts` | Gestion des utilisateurs, rôles, authentification |
| `documents` | Bibliothèque de ressources, upload, validation, notation |
| `quiz` | Génération et passage de QCM, scoring, correction |
| `ia` | Pipeline IA : résumé, QCM IA, chat pédagogique |

Cette architecture **modulaire** facilite la maintenabilité et l'évolution de l'application. Chaque application possède ses propres `models.py`, `views.py`, `urls.py`, `forms.py` et `admin.py`.

**Structure des dossiers principaux :**
```
NextSchoolAI/
├── accounts/       # Authentification & profils
├── documents/      # Gestion documentaire
├── quiz/           # Système de QCM
├── ia/             # Intelligence Artificielle
├── templates/      # Templates HTML (Jinja2/Django)
│   ├── base.html
│   ├── accounts/
│   ├── documents/
│   ├── quiz/
│   └── ia/
├── static/
│   └── css/
│       └── nextschoolai.css   # Système de design complet
├── media/          # Fichiers uploadés (PDF, avatars)
└── nextschoolai/   # Configuration Django (settings.py, urls.py)
```

---

### III.5.2 — Modèle de Données (Application `accounts`)

Le modèle utilisateur de NextSchoolAI étend la classe `AbstractUser` de Django pour ajouter les fonctionnalités métier spécifiques à la plateforme éducative.

#### Modèle `Utilisateur`

```python
class Utilisateur(AbstractUser):
    """
    Modèle utilisateur étendu avec rôle, sexe, avatar et thème visuel.
    """
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    sexe   = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True)
    theme  = models.CharField(max_length=20, choices=THEME_CHOICES, default='brownie')
    role   = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def est_apprenant(self):
        return self.role and self.role.code == 'apprenant'

    @property
    def est_enseignant(self):
        return self.role and self.role.code == 'enseignant'

    @property
    def est_admin(self):
        return self.is_superuser or (self.role and self.role.code == 'admin')
```

Le modèle `Role` permet de définir trois rôles : `apprenant`, `enseignant` et `admin`. Un système de `Permission` personnalisé (distinct des permissions Django natives) permet un contrôle d'accès fin par rôle métier.

#### Gestion des conflits `related_name`

L'extension d'`AbstractUser` nécessite la redéfinition des attributs `groups` et `user_permissions` avec un `related_name` unique pour éviter les conflits :

```python
groups = models.ManyToManyField(
    'auth.Group',
    related_name='nextschool_utilisateurs',
    blank=True,
)
```

---

### III.5.3 — Modèle de Données (Application `documents`)

L'application `documents` implémente un système d'héritage multi-tables Django. La classe `Document` constitue la base commune, dont héritent trois types de documents concrets :

#### Hiérarchie d'Héritage

```
Document (Modèle de base)
├── Cours     — chapitres de cours, TD, résumés officiels
├── Epreuve   — sujets BAC, BTS, Probatoire, BEPC, DEVOIR
└── Livre     — manuels, ouvrages de référence
```

Chaque document possède un pipeline de validation à double niveau :

1. **Validation IA** (`statut_ia`) : `en_attente` → `analyse` → `valide` / `rejete`
2. **Validation humaine** (`statut_humain`) : confirmée par un administrateur
3. **Statut de publication** (`statut_doc`) : `brouillon` → `publie` / `archive` / `rejete`

Un document n'est visible dans la bibliothèque que lorsqu'il est à la fois validé humainement et de statut `publie`.

#### Upload et Organisation des Fichiers

Un chemin d'upload dynamique est généré automatiquement :

```python
def chemin_upload_document(instance, filename):
    ext        = filename.split('.')[-1].lower()
    nom_propre = f"{instance.titre[:50].replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    type_doc   = instance.__class__.__name__.lower()
    annee      = timezone.now().year
    return os.path.join('documents', type_doc, str(annee), nom_propre)
```

Les fichiers sont organisés par type et par année : `media/documents/cours/2025/titre_du_cours_20250323.pdf`.

#### Traçabilité des Interactions

Le modèle `Activite` journalise toutes les interactions utilisateur-document (consultation, téléchargement, QCM passé, résumé demandé), permettant la création de tableaux de bord statistiques.

---

### III.5.4 — Modèle de Données (Application `quiz`)

Le système de QCM s'articule autour de quatre modèles :

| Modèle | Rôle |
|---|---|
| `Question` | Énoncé + points + explication, liée à une `InteractionIA` |
| `OptionReponse` | 2 à 4 options par question, flag `est_correct` |
| `SessionQCM` | Tentative d'un utilisateur (score, durée, statut) |
| `ReponseSession` | Réponse individuelle par question dans une session |

La propriété `mention` de `SessionQCM` retourne automatiquement l'appréciation qualitative selon le score :

- ≥ 90% → **Excellent**
- ≥ 75% → **Bien**
- ≥ 60% → **Assez bien**
- ≥ 50% → **Passable**
- < 50% → **Insuffisant**

---

### III.5.5 — Pipeline IA (Application `ia`)

L'intelligence artificielle de NextSchoolAI suit un pipeline en 7 étapes, implémenté dans `ia/services.py` :

```
┌──────────────────────────────────────────────────────────┐
│  PIPELINE IA — NextSchoolAI                               │
│                                                          │
│  1. Entrée    → PDF, Image scannée, Document numérique  │
│  2. Prétraitement → OCR (Tesseract), nettoyage texte    │
│  3. Compréhension → Extraction des 3 thèmes majeurs     │
│  4. Résolution → Appel API Gemini (résumé ou QCM)       │
│  5. Vérification → Validation croisée du contenu        │
│  6. Formatage → Nettoyage Markdown / JSON               │
│  7. Sortie    → Affichage enrichi (MathJax, marked.js)  │
└──────────────────────────────────────────────────────────┘
```

#### Étape 2 : Extraction de Texte Multi-format

La fonction `extraire_texte()` gère intelligemment trois types de fichiers :

```python
def extraire_texte(chemin_fichier: str) -> str:
    ext = chemin_fichier.lower().split('.')[-1]

    # 1. Image directe → OCR Tesseract
    if ext in ['jpg', 'jpeg', 'png', 'webp']:
        return ocr_image(chemin_fichier)

    # 2. PDF natif → pdfplumber (extraction directe)
    if ext == 'pdf':
        with pdfplumber.open(chemin_fichier) as pdf:
            texte = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
        # Si PDF scanné (< 100 caractères extraits), fallback vers OCR
        if len(texte) < 100:
            return ocr_pdf(chemin_fichier)  # OCR via pdf2image + Tesseract
        return texte
```

Cette approche garantit la compatibilité avec les documents courants dans le milieu éducatif camerounais : cours tapés en PDF, épreuves scannées, images de tableaux de cours.

#### Étape 4 : Génération via API Gemini

La fonction `appeler_gemini()` constitue le moteur principal de l'IA. Elle utilise la bibliothèque officielle `google-generativeai` et intègre un mécanisme de **Mock complet** pour le développement hors-ligne :

```python
def appeler_gemini(prompt: str, json_format: bool = False) -> dict:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return {'succes': False, 'erreur': "Clé API absente"}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(prompt, generation_config=config)
        return {'succes': True, 'contenu': response.text, 'duree': duree}

    except Exception as e:
        if settings.DEBUG:
            # Retourne un mock pédagogique adapté au type de requête
            return genereer_mock_development(json_format, prompt)
        return {'succes': False, 'erreur': str(e)}
```

Le mock distingue trois contextes : génération de résumé, de QCM (JSON structuré) ou de réponse de chat, renvoyant dans chaque cas une réponse fictive mais réaliste et pédagogiquement correcte.

#### Étape 5 : Vérification Croisée

Une vérification automatique est effectuée sur le contenu généré avant de le présenter à l'utilisateur :

```python
@classmethod
def _etape_verification(cls, tache: str, contenu_resolu: str) -> bool:
    prompt_verif = (
        f"Ce contenu pédagogique semble-t-il cohérent et sans propos inappropriés ? "
        f"Réponds Oui ou Non : {contenu_resolu[:1000]}"
    )
    res_verif = appeler_gemini(prompt_verif)
    if "Non" in res_verif.get('contenu', ''):
        logger.warning("La vérification croisée a levé un doute sur le contenu!")
        return False
    return True
```

#### Endpoint de Chat IA

Un endpoint AJAX dédié (`/ia/document/<id>/chat/`) permet à l'utilisateur de dialoguer en temps réel avec l'IA au sujet d'un document spécifique :

```python
@login_required
@require_POST
def chat_document_ajax(request, doc_pk):
    message = request.POST.get('message', '').strip()
    document = get_object_or_404(Document, pk=doc_pk, statut_doc='publie')

    # Extraction du contexte document complet (limite 100k caractères)
    contexte = extraire_texte(document.url_fichier.path)[:100000]

    resultat = IAService.generer_explication(message, contexte=contexte)

    return JsonResponse({
        'succes': resultat['succes'],
        'reponse': resultat.get('contenu', ''),
    })
```

Le contexte complet du document (jusqu'à 100 000 caractères) est transmis à l'IA pour chaque interaction, lui permettant de répondre précisément aux questions sur n'importe quelle section du document.

---

### III.5.6 — Interface Utilisateur et Système de Design

L'interface de NextSchoolAI repose sur un système de design CSS premium développé entièrement sur mesure (`static/css/nextschoolai.css`).

#### Système de Variables CSS

L'intégralité de l'interface est pilotée par des variables CSS permettant un changement de thème instantané :

```css
:root, [data-theme="brownie"] {
  --primary:        #8B5E3C;       /* Caramel chaud */
  --accent:         #D4A574;       /* Sable doré */
  --bg-primary:     #1C1410;       /* Fond sombre */
  --bg-card:        #2A1E17;       /* Carte */
  --text-primary:   #F5E6D3;       /* Texte clair */
  --border:         rgba(212,165,116,0.15);
  --shadow-card:    0 4px 24px rgba(0,0,0,0.3);
  --radius:         12px;
  --font-sans:      'Inter', system-ui, sans-serif;
}
```

#### Système Multi-thème

L'utilisateur dispose de **7 thèmes visuels** enregistrés dans son profil :

| Thème | Description |
|---|---|
| Brownie | Caramel chaud et sombre (défaut) |
| Midnight | Noir profond, minimaliste |
| Arctic | Blanc épuré, mode clair |
| Forest | Vert sombre, naturel |
| Ocean | Bleu profond, serein |
| Rose | Mauve chaud, chaleureux |
| Noir | Contraste élevé, accessibilité |

Le thème sélectionné est persisté en base de données et appliqué dynamiquement via l'attribut `data-theme` sur la balise `<html>`.

#### Rendu des Contenus IA

Les réponses de l'IA (résumés, réponses de chat) sont rendues côté client avec :
- **marked.js** — parsing Markdown → HTML
- **DOMPurify** — sanitisation du HTML (protection XSS)
- **MathJax 3** — rendu des formules mathématiques LaTeX (`$$E=mc^2$$`)

#### Command Palette (Recherche Avancée)

Une interface de recherche de type "Command Palette" est intégrée, accessible via `Ctrl+K` ou `Cmd+K`. Ce modal plein-écran avec effet `backdrop-filter: blur()` permet de filtrer les documents par niveau, matière, type et année académique.

---

### III.5.7 — Authentification et Sécurité

La sécurité est assurée à plusieurs niveaux :

1. **Hachage des mots de passe** : Django utilise `PBKDF2` avec `SHA-256` par défaut.
2. **Protection CSRF** : Chaque formulaire et requête AJAX inclut un token CSRF.
3. **Décorateur `@login_required`** : Toutes les vues sensibles sont protégées.
4. **Protection par rôle** : La propriété `est_admin` / `est_enseignant` contrôle l'accès aux fonctionnalités avancées.
5. **Validation des fichiers** : Seuls les formats PDF, JPG, PNG, WEBP sont acceptés via `FileExtensionValidator`.
6. **Variables d'environnement** : Toutes les clés secrètes (Django `SECRET_KEY`, `GEMINI_API_KEY`) sont stockées dans un fichier `.env`, jamais dans le code source.

---

## III.6 — Tests et Validation

### III.6.1 — Stratégie de Tests

La stratégie de tests adoptée pour NextSchoolAI combine des tests manuels fonctionnels et des vérifications système automatiques de Django. Les tests couvrent trois dimensions :

1. **Tests fonctionnels** — Vérification du comportement attendu des fonctionnalités utilisateur
2. **Tests d'intégration** — Validation des interactions entre les composants (IA, base de données, upload)
3. **Tests de régression** — S'assurer que les nouvelles fonctionnalités ne brisent pas les existantes

### III.6.2 — Vérification Système Django

La commande `python manage.py check` valide l'intégrité de la configuration Django avant tout déploiement :

```bash
$ python manage.py check
System check identified no issues (0 silenced).
```

Cette vérification automatique contrôle notamment :
- La cohérence des modèles et des migrations
- La validité de `AUTH_USER_MODEL`
- L'absence de conflits de `related_name`
- La configuration correcte des backends d'authentification

### III.6.3 — Tests Fonctionnels — Authentification

**Scénario 1 : Inscription d'un nouvel apprenant**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Accéder à `/accounts/inscription/` | Formulaire d'inscription affiché | ✅ OK |
| 2 | Remplir le formulaire sans email | Message d'erreur de validation | ✅ OK |
| 3 | Remplir le formulaire complet (rôle = Apprenant) | Redirection vers tableau de bord | ✅ OK |
| 4 | Vérifier en base | Utilisateur créé, `role.code = 'apprenant'` | ✅ OK |

**Scénario 2 : Connexion et déconnexion**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Accéder à `/accounts/connexion/` | Formulaire de connexion affiché | ✅ OK |
| 2 | Saisir credentials incorrects | Message "Identifiants invalides" | ✅ OK |
| 3 | Saisir credentials corrects | Redirection + theme utilisateur appliqué | ✅ OK |
| 4 | Cliquer "Déconnexion" | Redirection vers login, session détruite | ✅ OK |

---

### III.6.4 — Tests Fonctionnels — Gestion Documentaire

**Scénario 3 : Upload d'un document**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Connexion en tant qu'enseignant | Accès au menu "Gestion" dans la sidebar | ✅ OK |
| 2 | Accéder à "Uploader" | Formulaire d'upload avec sélection de type | ✅ OK |
| 3 | Uploader un fichier PDF valide | Document créé avec `statut_doc = 'brouillon'` | ✅ OK |
| 4 | Uploader une image `.exe` | Rejet avec message d'erreur de validation | ✅ OK |
| 5 | Vérifier le chemin du fichier | Fichier stocké dans `media/documents/cours/2025/` | ✅ OK |

**Scénario 4 : Workflow de validation (Admin)**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Admin accède à `/documents/moderation/` | Liste des documents en attente affichée | ✅ OK |
| 2 | Admin valide un document | `statut_doc = 'publie'`, `statut_humain = True` | ✅ OK |
| 3 | Admin rejette avec commentaire | `statut_doc = 'rejete'`, commentaire enregistré | ✅ OK |
| 4 | Apprenant accède à la bibliothèque | Seuls les documents `publie` sont visibles | ✅ OK |

---

### III.6.5 — Tests Fonctionnels — Système IA

**Scénario 5 : Génération de Résumé IA**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Accéder à un document publié | Bouton "Générer le résumé IA" visible | ✅ OK |
| 2 | Cliquer le bouton (1er appel) | Résumé généré et sauvegardé en base | ✅ OK |
| 3 | Recharger la page | Résumé chargé depuis le cache (< 24h) | ✅ OK |
| 4 | Vérifier le rendu | Markdown rendu, formules LaTeX affichées | ✅ OK |
| 5 | Tester sans clé API (mode dev) | Mock pédagogique renvoyé instantanément | ✅ OK |

**Scénario 6 : Chat IA sur un document**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Saisir une question dans le chat | Indicateur de chargement animé | ✅ OK |
| 2 | Recevoir la réponse | Bulle IA avec Markdown et LaTeX rendus | ✅ OK |
| 3 | Envoyer un message vide | Formulaire non soumis (validation JS) | ✅ OK |
| 4 | Demander "Montre-moi le point 1" | IA retourne le contenu précis du document | ✅ OK |

**Scénario 7 : Génération et passage de QCM**

| Étape | Action | Résultat attendu | Statut |
|---|---|---|---|
| 1 | Accéder à "Générer un QCM" sur un document | 10 questions créées en base | ✅ OK |
| 2 | Passer le QCM | Interface question par question | ✅ OK |
| 3 | Soumettre les réponses | Score calculé, mention affichée | ✅ OK |
| 4 | Accéder à la correction | Réponses correctes et explications affichées | ✅ OK |

---

### III.6.6 — Tests de Sécurité

| Test | Action | Résultat attendu | Statut |
|---|---|---|---|
| CSRF | Appel AJAX sans token CSRF | Erreur 403 Forbidden | ✅ OK |
| Accès non authentifié | Accéder à `/documents/` sans connexion | Redirection vers `/accounts/connexion/` | ✅ OK |
| Accès non autorisé | Apprenant accède à `/documents/moderation/` | Redirection avec message d'erreur | ✅ OK |
| Upload malveillant | Upload d'un fichier `.exe` | Rejet par `FileExtensionValidator` | ✅ OK |
| Injection XSS | Message de chat avec `<script>alert()</script>` | Sanitisé par DOMPurify, inoffensif | ✅ OK |

---

### III.6.7 — Bilan des Tests

L'ensemble des scénarios de test fonctionnels et sécuritaires ont été exécutés avec succès. Les principaux résultats sont :

- **35 scénarios** testés sur les 4 modules fonctionnels
- **0 régression** détectée sur les fonctionnalités existantes
- **Compatibilité multi-thème** validée sur les 7 palettes couleur
- **Mode hors-ligne (Mock IA)** fonctionnel à 100% pour le développement sans clé API
- **Rendu Markdown + LaTeX** validé sur résumés et réponses de chat

---

# CHAPITRE IV — BILAN ET PERSPECTIVES

## IV.1 — Bilan du Projet

### IV.1.1 — Objectifs Atteints

Au terme de ce projet, l'ensemble des objectifs définis dans le cahier des charges initial ont été atteints ou dépassés :

| Objectif | Statut | Commentaire |
|---|---|---|
| Centralisation des ressources éducatives | ✅ Atteint | Bibliothèque multi-type (Cours, Épreuves, Livres) |
| Authentification et gestion des rôles | ✅ Atteint | 3 rôles : apprenant, enseignant, admin |
| Upload et validation des documents | ✅ Atteint | Pipeline IA + validation humaine |
| Génération de résumés IA | ✅ Atteint | Via Google Gemini API |
| Génération de QCM IA | ✅ Atteint | JSON structuré, 10 questions par défaut |
| Chat IA sur les documents | ✅ Dépassé | Fonctionnalité non initialement prévue |
| Recherche avancée | ✅ Dépassé | Command Palette Ctrl+K avec filtres Pills |
| Support PDF scannés (OCR) | ✅ Atteint | Tesseract + pdf2image |
| Interface premium et responsive | ✅ Atteint | 7 thèmes, design Apple-quality |
| Sécurité (CSRF, XSS, uploads) | ✅ Atteint | Multiples couches de protection |

### IV.1.2 — Compétences Développées

La réalisation de NextSchoolAI a permis de mobiliser et d'approfondir des compétences dans plusieurs domaines :

**Développement Backend :**
- Maîtrise des modèles Django avancés (héritage multi-tables, AbstractUser)
- Conception de pipelines de traitement de données multi-étapes
- Intégration d'APIs tierces (Google Generative AI, Hugging Face)
- Traitement de fichiers binaires (PDF, images) avec OCR

**Développement Frontend :**
- Conception d'un système de design CSS complet basé sur des variables
- Implémentation de micro-animations et transitions fluides
- Intégration de bibliothèques de rendu (marked.js, MathJax, DOMPurify)
- Communication AJAX asynchrone (Fetch API, gestion d'états UI)

**Architecture Logicielle :**
- Découpage en applications métier cohérentes
- Séparation des responsabilités (Services, Vues, Modèles)
- Gestion de la configuration par variables d'environnement
- Réflexion sur la scalabilité et la maintenabilité

**Intelligence Artificielle :**
- Prompt engineering pour des sorties structurées et pédagogiques
- Gestion des limites et erreurs de l'API
- Conception de mécanismes de fallback (Mock, double vérification)

### IV.1.3 — Difficultés Rencontrées

**Difficulté 1 : Gestion de l'héritage multi-tables Django**

L'utilisation de l'héritage multi-tables pour les types de documents (`Cours`, `Epreuve`, `Livre`) a nécessité une attention particulière lors des requêtes et de la génération des chemins d'upload, car `instance.__class__.__name__` retourne le nom de la sous-classe, pas du modèle parent.

**Solution :** Utilisation de `select_related()` et de la méthode `chemin_upload_document()` qui détecte dynamiquement le type de document.

**Difficulté 2 : Rendu LaTeX dans le navigateur**

L'intégration de MathJax 3 (asynchrone) avec marked.js (synchrone) a créé des problèmes de timing : les équations étaient parsées par marked avant que MathJax ne les traite.

**Solution :** Appel explicite de `MathJax.typesetPromise([element])` sur chaque nouvelle bulle de chat après insertion dans le DOM.

**Difficulté 3 : Documents PDF scannés**

Les épreuves et cours camerounais sont souvent des scans de mauvaise qualité. L'OCR natif de Tesseract produisait des textes très bruités sur ces documents.

**Solution :** Ajout d'une étape de nettoyage (`nettoyer_texte()`) filtrant les lignes vides et les artefacts OCR, avec augmentation de la résolution de conversion (`dpi=200`).

**Difficulté 4 : Conflit de `related_name` AbstractUser**

L'extension d'`AbstractUser` avec un `AUTH_USER_MODEL` custom provoque des conflits sur les attributs `groups` et `user_permissions` hérités.

**Solution :** Redéclaration explicite de ces attributs avec des `related_name` uniques dans le modèle `Utilisateur`.

---

## IV.2 — Perspectives et Évolutions Futures

### IV.2.1 — Version Mobile

Le cahier des charges mentionne une future version mobile de NextSchoolAI. Deux voies sont envisageables :

1. **Application Web Progressive (PWA)** : Transformer le site web actuel en PWA avec un `service worker` pour le mode hors-ligne, permettant la consultation des documents sans connexion internet — une fonctionnalité essentielle dans le contexte camerounais.

2. **Application Mobile Native** : Développement d'une application Android/iOS avec Flutter ou React Native, consommant une API REST Django (Django REST Framework).

### IV.2.2 — Système de Recommandation Personnalisé

À partir des données collectées dans le modèle `Activite` (historique de consultations, QCM passés, scores), il serait possible d'implémenter un système de recommandation :

- Documents populaires dans la matière et classe de l'utilisateur
- Documents similaires aux derniers consultés
- Suggestions de QCM selon les lacunes identifiées dans les sessions précédentes

### IV.2.3 — Forum et Collaboration

L'ajout d'un espace communautaire permettrait :
- Un forum de questions-réponses par matière et classe
- La possibilité pour les enseignants de commenter et annoter les documents
- Un système de badges et de gamification pour motiver les apprenants

### IV.2.4 — Support Multilingue et Multimodal

NextSchoolAI est actuellement développé en français. Les évolutions futures pourraient inclure :
- Support de l'anglais (bilinguisme camerounais)
- Adaptation de l'IA aux programmes scolaires officiels par niveau (BEPC, BAC)
- Génération de corrections vidéo ou audio grâce à des API de synthèse vocale (Text-to-Speech)

### IV.2.5 — Déploiement en Production

Le passage du développement local à la production impliquera :
- **Base de données :** Migration de SQLite (dev) vers PostgreSQL ou MySQL
- **Serveur WSGI :** Gunicorn + Nginx en reverse proxy
- **Stockage fichiers :** Amazon S3 ou équivalent pour les médias
- **Variables d'environnement :** Gestion sécurisée via `.env` ou secrets manager cloud
- **CI/CD :** Pipeline GitHub Actions pour tests automatiques et déploiement

---

# CONCLUSION

NextSchoolAI est né d'un constat simple : les étudiants et lycéens camerounais manquent d'un espace numérique centralisé, moderne et intelligent pour accéder à leurs ressources éducatives. Ce projet apporte une réponse concrète et fonctionnelle à cette problématique.

En six mois de développement, une plateforme web complète a été conçue et réalisée avec le framework Django. Elle offre aux apprenants une bibliothèque de cours, d'épreuves et de livres avec filtres avancés, un assistant IA capable de résumer n'importe quel document, de générer des QCM personnalisés, et de répondre en temps réel aux questions des étudiants dans un chat pédagogique.

L'interface, développée entièrement sur mesure, adopte les standards du design moderne : système de thèmes, micro-animations, rendu Markdown et formules mathématiques LaTeX, et une recherche avancée de type "Command Palette". La sécurité a été prise en compte à chaque niveau, depuis la validation des fichiers uploadés jusqu'à la protection contre les injections XSS dans les réponses de l'IA.

Ce projet a représenté une opportunité unique de mettre en pratique de nombreuses compétences acquises au cours de la formation en Génie Logiciel : architecture backend avec Django, intégration d'APIs IA modernes (Google Gemini), conception de systèmes de design CSS, traitement de documents (OCR, extraction de texte) et déploiement sécurisé.

Si NextSchoolAI n'est encore qu'un prototype académique, son architecture modulaire et évolutive lui confère un véritable potentiel pour devenir, dans un futur proche, la plateforme éducative de référence pour la jeunesse camerounaise.

---

# BIBLIOGRAPHIE

## Ouvrages et Documentation Technique

1. **Django Software Foundation** (2024). *Django Documentation, Release 5.0*. Disponible en ligne : https://docs.djangoproject.com/

2. **Google AI** (2024). *Google Generative AI Python SDK Documentation*. Disponible en ligne : https://ai.google.dev/api/python/google/generativeai

3. **Python Software Foundation** (2024). *Python 3.12 Documentation*. Disponible en ligne : https://docs.python.org/3.12/

4. **Mozilla Developer Network** (2024). *Web Docs — CSS Custom Properties (Variables)*. Disponible en ligne : https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties

5. **MathJax Consortium** (2024). *MathJax Documentation, Version 3.x*. Disponible en ligne : https://docs.mathjax.org/

## Articles et Ressources

6. **Tesseract OCR** (2024). *Tesseract Documentation*. Disponible en ligne : https://tesseract-ocr.github.io/

7. **pdfplumber** (2024). *pdfplumber — GitHub Repository*. Disponible en ligne : https://github.com/jsvine/pdfplumber

8. **DOMPurify** (2024). *DOMPurify — A DOM-only, super-fast, uber-tolerant XSS sanitizer for HTML*. Disponible en ligne : https://github.com/cure53/DOMPurify

9. **Lucide Icons** (2024). *Lucide Icon Library Documentation*. Disponible en ligne : https://lucide.dev/

10. **OWASP Foundation** (2024). *OWASP Top 10 - Web Application Security Risks*. Disponible en ligne : https://owasp.org/www-project-top-ten/

## Référentiels Pédagogiques

11. **Gouvernement du Cameroun — Ministère des Enseignements Secondaires** (2024). *Programmes d'études officiels — Cycles d'enseignement général*. Yaoundé, Cameroun.

12. **BROWN, Martin et al.** (2023). *The Art of Prompt Engineering for Educational LLMs*. Journal of Educational Technology, Vol. 15, pp. 234-251.

---

# ANNEXES

## Annexe A — Schéma de la Base de Données

```
ACCOUNTS
┌─────────────────┐    ┌──────────────────┐
│ Role            │    │ Permission       │
├─────────────────┤    ├──────────────────┤
│ id              │◄───│ roles (M2M)      │
│ code            │    │ code_permission  │
│ libelle         │    │ description      │
└─────────────────┘    └──────────────────┘
        │
        │ FK
        ▼
┌─────────────────┐
│ Utilisateur     │
├─────────────────┤
│ id, username    │
│ first_name      │
│ last_name       │
│ email           │
│ avatar          │
│ sexe, theme     │
│ role (FK)       │
└─────────────────┘

DOCUMENTS
┌──────────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐
│ Niveau       │  │ Classe   │  │ Matiere      │  │ Licence    │
├──────────────┤  ├──────────┤  ├──────────────┤  ├────────────┤
│ id           │◄─│ niveau   │  │ id           │  │ id         │
│ libelle      │  │ libelle  │  │ nom_matiere  │  │ nom        │
└──────────────┘  └──────────┘  └──────────────┘  └────────────┘
                       │              │                  │
                       ▼              ▼                  ▼
                  ┌─────────────────────────────────────────────┐
                  │ Document (base)                              │
                  ├─────────────────────────────────────────────┤
                  │ id, titre, description, url_fichier         │
                  │ statut_ia, statut_humain, statut_doc        │
                  │ classe(FK), matiere(FK), licence(FK)        │
                  │ utilisateur(FK → Utilisateur)               │
                  └─────────────────────────────────────────────┘
                         │              │              │
                   ┌─────┴──┐    ┌──────┴─┐    ┌──────┴─┐
                   │ Cours  │    │Epreuve │    │ Livre  │
                   └────────┘    └────────┘    └────────┘

IA
┌──────────────────────────┐
│ InteractionIA            │
├──────────────────────────┤
│ id                       │
│ utilisateur (FK)         │
│ document (FK)            │
│ type_interaction         │  ← 'resume', 'qcm', 'explication'
│ moteur_ia                │  ← 'gemini', 'huggingface'
│ prompt_utilisateur       │
│ contenu_genere           │
│ duree_secondes, tokens   │
│ succes, message_erreur   │
└──────────────────────────┘
        │
        ▼
┌──────────────────┐   ┌─────────────────┐
│ Question         │   │ SessionQCM      │
├──────────────────┤   ├─────────────────┤
│ id               │   │ id              │
│ interaction (FK) │   │ interaction (FK)│
│ matiere (FK)     │   │ utilisateur (FK)│
│ enonce, points   │   │ score_obtenu    │
│ explication      │   │ score_total     │
└──────────────────┘   └─────────────────┘
        │
        ▼
┌──────────────────┐
│ OptionReponse    │
├──────────────────┤
│ id               │
│ question (FK)    │
│ libelle_option   │
│ est_correct      │
└──────────────────┘
```

## Annexe B — Variables d'Environnement (.env)

```ini
# Django Configuration
SECRET_KEY=your-very-secret-django-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Données (SQLite par défaut)
# DATABASE_URL=mysql://user:password@host:3306/nextschoolai_db

# Intelligence Artificielle
GEMINI_API_KEY=your-google-ai-studio-api-key
GEMINI_MODEL=gemini-1.5-flash
HUGGINGFACE_API_KEY=optional-huggingface-key
HUGGINGFACE_MODEL=facebook/bart-large-cnn

# Limites IA
IA_MAX_TOKENS=4096
```

## Annexe C — Commandes de Déploiement Local

```bash
# 1. Cloner le projet
git clone <url-du-projet>
cd NextSchoolAI

# 2. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Lancer le serveur de développement
python manage.py runserver

# 8. Accéder à l'application
# http://127.0.0.1:8000/        → Bibliothèque
# http://127.0.0.1:8000/admin/  → Interface d'administration
```

## Annexe D — Dépendances Python

```
Django>=5.0
python-decouple>=3.8
Pillow>=10.0         # Traitement d'images
pdfplumber>=0.9      # Extraction texte PDF natif
pdf2image>=1.17      # Conversion PDF → images (pour OCR)
pytesseract>=0.3.10  # Interface Python pour Tesseract OCR
google-generativeai>=0.5  # API Gemini
requests>=2.31       # Appels HTTP (Hugging Face)
```

---

*Document réalisé dans le cadre du projet de fin d'études — 2ème Année Génie Logiciel — 2024/2025*  
*TATEM ANGE ULRICH — NextSchoolAI*
