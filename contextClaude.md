# Contexte NextSchoolAI — À donner à Claude au début de chaque session

## Projet

Application web éducative NextSchoolAI (Cameroun)
Stack : Django 6.0.3 / Python 3.12.3 / SQLite (dev) / MySQL (prod) / Gemini IA

## État d'avancement du rapport

- Chapitre 1 ✅ complet
- Chapitre 2 ✅ complet
- Chapitre 3 : III.1 ✅ III.2 ✅ III.3 ✅ III.4 ✅ rédigé
- III.5 Implémentation ⏳ en cours
- III.6 Tests ❌ à faire
- Chapitre 4 ❌ à faire
- Conclusion, Biblio, Annexes ❌ à faire

## État d'avancement du code

- Projet Django créé ✅
- App "core" créée ✅
- models.py complet ✅ (Role, Utilisateur, Niveau, Classe, Matiere,
  Licence, Document, Cours, Epreuve, Livre, InteractionIA)
- admin.py configuré ✅
- Superuser créé ✅
- migrations effectuées ✅
- AUTH_USER_MODEL = 'core.Utilisateur' dans settings.py ✅

## Prochaine étape

Créer les vues (views.py) et les URLs pour :

1. Page d'accueil
2. Authentification (inscription / connexion / déconnexion)
3. Upload de documents
4. Interface IA (résumés / QCM)
