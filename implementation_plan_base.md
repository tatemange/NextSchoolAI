# Refactorisation Complète — NextSchoolAI

Reconstruction de la plateforme NextSchoolAI avec une architecture Django robuste, modulaire et évolutive sur 5 ans. Le projet existant contient une seule app `core` avec des modèles partiels, des vues vides et aucune URL fonctionnelle. Ce plan réorganise tout en respectant le MCD, les diagrammes de séquence et le cahier des charges.

## Changements Majeurs

> [!IMPORTANT]
> L'architecture passe d'**une seule app `core`** à **4 apps Django séparées** (`accounts`, `documents`, `quiz`, `ia`). Les migrations existantes seront supprimées et recréées. La base SQLite de dev sera conservée.

> [!WARNING]
> `AUTH_USER_MODEL` sera changé : nécessite `python manage.py migrate --run-syncdb` après suppression des anciennes migrations.

---

## Proposed Changes

### App `accounts` — Utilisateurs, Rôles, Permissions
Remplace la gestion utilisateur actuelle dans `core`.

#### [NEW] `accounts/` (nouvelle app Django)
- [models.py](file:///mnt/test_disque/NextSchoolAI/core/models.py) : [Role](file:///mnt/test_disque/NextSchoolAI/core/models.py#11-19), `Permission`, [Utilisateur](file:///mnt/test_disque/NextSchoolAI/core/models.py#21-51) (AbstractUser avec `role`, `sexe`, custom manager)
- `managers.py` : `UtilisateurManager` avec méthodes `create_apprenant()`, `create_enseignant()`, etc.
- [admin.py](file:///mnt/test_disque/NextSchoolAI/core/admin.py) : [UtilisateurAdmin](file:///mnt/test_disque/NextSchoolAI/core/admin.py#13-21) complet avec fieldsets, search, filter
- `forms.py` : `InscriptionForm`, `ConnexionForm`, `ProfilForm`
- [views.py](file:///mnt/test_disque/NextSchoolAI/core/views.py) : `inscription`, `connexion`, `deconnexion`, `profil`
- [urls.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/urls.py) : routes auth
- `signals.py` : création auto du profil à l'inscription

---

### App `documents` — Gestion documentaire (Incrément 1)
Coeur fonctionnel du système.

#### [NEW] `documents/` (nouvelle app Django)
- [models.py](file:///mnt/test_disque/NextSchoolAI/core/models.py) : [Niveau](file:///mnt/test_disque/NextSchoolAI/core/models.py#55-63), [Classe](file:///mnt/test_disque/NextSchoolAI/core/models.py#65-78), [Matiere](file:///mnt/test_disque/NextSchoolAI/core/models.py#80-88), [Licence](file:///mnt/test_disque/NextSchoolAI/core/models.py#90-100), [Document](file:///mnt/test_disque/NextSchoolAI/core/models.py#104-174) (abstract), [Cours](file:///mnt/test_disque/NextSchoolAI/core/models.py#178-184), [Epreuve](file:///mnt/test_disque/NextSchoolAI/core/models.py#186-193), [Livre](file:///mnt/test_disque/NextSchoolAI/core/models.py#195-202), `Images`, `Activite`, `Evaluer`
- [admin.py](file:///mnt/test_disque/NextSchoolAI/core/admin.py) : avec actions de modération (valider/rejeter document)
- `forms.py` : `UploadDocumentForm`, `FiltreDocumentForm`
- [views.py](file:///mnt/test_disque/NextSchoolAI/core/views.py) : CRUD documents + workflow validation
- [urls.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/urls.py) : routes RESTful
- `utils.py` : extraction texte PDF (PyMuPDF/pdfplumber), calcul poids fichier

---

### App `quiz` — QCM et Épreuves (Incrément 2)
Gestion des questions, options et scores.

#### [NEW] `quiz/` (nouvelle app Django)
- [models.py](file:///mnt/test_disque/NextSchoolAI/core/models.py) : `Question`, `OptionReponse`, `Session QCM`, `ScoreUtilisateur`
- [admin.py](file:///mnt/test_disque/NextSchoolAI/core/admin.py) : inline Question+Options
- `forms.py` : réponse QCM
- [views.py](file:///mnt/test_disque/NextSchoolAI/core/views.py) : passer QCM, soumettre, voir résultats, correction
- [urls.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/urls.py) : `/qcm/generer/`, `/qcm/soumettre/`, `/qcm/correction/`

---

### App `ia` — Service IA (Incrément 2)
Pipeline IA : résumé, QCM, correction, explication.

#### [NEW] `ia/` (nouvelle app Django)
- [models.py](file:///mnt/test_disque/NextSchoolAI/core/models.py) : [InteractionIA](file:///mnt/test_disque/NextSchoolAI/core/models.py#206-236) (migré depuis `core`)
- `services.py` : `IAService` (Gemini API + Hugging Face fallback)
- `tasks.py` : tâches async (Celery-ready)
- [admin.py](file:///mnt/test_disque/NextSchoolAI/core/admin.py) : logs interactions IA
- [views.py](file:///mnt/test_disque/NextSchoolAI/core/views.py) : endpoints Ajax IA
- [urls.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/urls.py) : `/ia/resumer/`, `/ia/generer-qcm/`, `/ia/expliquer/`

---

### Configuration Principale
#### [MODIFY] [nextschoolai/settings.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/settings.py)
- `AUTH_USER_MODEL = 'accounts.Utilisateur'`
- `INSTALLED_APPS` : 4 nouvelles apps
- `MEDIA_ROOT`, `MEDIA_URL` pour les fichiers uploadés
- `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`
- Variables d'environnement pour clés API IA

#### [MODIFY] [nextschoolai/urls.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/urls.py)
- Inclure les URLs de toutes les apps
- Servir les médias en dev (`DEBUG=True`)

#### [NEW] `.env.example`
- Template des variables d'environnement sans secrets

---

### Templates & Static
#### [NEW] `templates/base.html`
- Layout principal avec navigation responsive
- Messages Django (succès/erreur/info)
- Blocs : `title`, `content`, `extra_js`, `extra_css`

#### [NEW] Templates par app :
- `templates/accounts/` : login, register, profil
- `templates/documents/` : liste, détail, upload, modération
- `templates/quiz/` : passer QCM, résultats, correction
- `templates/ia/` : assistant IA

---

### Correction des erreurs existantes
| Erreur | Correction |
|--------|-----------|
| `from django.db import models` dupliqué | Supprimé |
| `nomLicence` → camelCase | → `nom_licence` (snake_case) |
| `URL_legal` → camelCase | → `url_legal` |
| Pas de `DEFAULT_AUTO_FIELD` | Ajouté en settings |
| [views.py](file:///mnt/test_disque/NextSchoolAI/core/views.py) vide | Implémenté |
| [urls.py](file:///mnt/test_disque/NextSchoolAI/nextschoolai/urls.py) vide | Implémenté |
| Pas de `AUTH_USER_MODEL` | Ajouté |
| Pas de `MEDIA_ROOT/URL` | Ajouté |
| Secret key exposée | → `os.environ.get()` |
| Pas de gestion des permissions | Decorateurs + mixins |
| Pas de tests | `tests/` par app |

---

## Verification Plan

### Vérification automatique
```bash
# Depuis /mnt/test_disque/NextSchoolAI/
python manage.py check          # Vérification système Django
python manage.py makemigrations # Génération migrations
python manage.py migrate        # Application migrations
python manage.py test           # Tests unitaires
```

### Vérification manuelle
1. `python manage.py runserver` → accéder à `http://127.0.0.1:8000/`
2. S'inscrire avec un compte apprenant → vérifier redirection tableau de bord
3. Upload d'un PDF → vérifier statut `en_attente`
4. Admin (`/admin/`) → vérifier validation document → statut `publié`
5. Accéder à un document publié → demander résumé IA
6. Générer QCM depuis un document → passer le QCM → voir score
