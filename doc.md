# Guide de Test : Vider l'Interface Admin et Rajouter les Données

Pour tester l'application **NextSchoolAI** dans de bonnes conditions, l'ordre de création des données dans ton interface d'administration (`/admin/`) est important, car la plupart des éléments dépendent les uns des autres (par exemple, un document dépend d'une matière et d'une classe).

Voici l'ordre exact et la marche à suivre pour ajouter tes données de test depuis ton panneau admin (**http://127.0.0.1:8000/admin/**) :

## 1. Préparer les Rôles (Accounts)
Avant de pouvoir créer des utilisateurs correctement, tu dois t'assurer que les rôles existent dans le système.
* Va dans **Comptes > Rôles** et ajoute au minimum deux rôles avec ces codes précis :
  * Code : `apprenant` / Libellé : `Apprenant` *(Important, car "apprenant" est le choix par défaut à l'inscription)*
  * Code : `enseignant` / Libellé : `Enseignant`

## 2. Créer l'Arborescence Scolaire (Classification)
L'application propose des filtres (Niveau > Classe) et des Matières. Il faut les créer en premier.
* Va dans **Documents > Niveaux** : Ajoute des niveaux d'études (ex: *Lycée*, *Collège*, ou *Terminale*).
* Va dans **Documents > Classes** : Ajoute des classes et associe-les aux Niveaux (ex: libellé *Terminale D* associé au niveau *Terminale*).
* Va dans **Documents > Matières** : Ajoute tes matières (ex: *Mathématiques*, *Physique*, *Philosophie*).
* Va dans **Documents > Licences** : Ajoute au moins une licence par défaut (ex: *Domaine Public* ou *Creative Commons*) pour des questions de droits d'auteur sur les documents.

## 3. Ajouter des Utilisateurs de test (Comptes)
Tu as déjà ton compte admin, mais c'est bien de créer de "faux" apprenants et enseignants pour voir ce qu'ils voient.
* Va dans **Comptes > Utilisateurs**.
* Clique sur **"Ajouter un utilisateur"**.
* Remplis les informations obligatoires, puis dans la section *Informations supplémentaires* (ou *Informations NextSchoolAI*), attribue-lui le rôle **Apprenant** ou **Enseignant**.

## 4. Ajouter des Documents (Cours, Épreuves, Livres)
Maintenant que le socle de base existe, tu peux uploader du contenu de test.
* Va dans **Documents > Cours** (ou Epreuves / Livres).
* Clique sur **"Ajouter Cours"**.
* Remplis les informations de base (Titre, Fichier PDF ou Image, etc.).
* Choisis la **Matière** et la **Classe** créées à l'étape 2.
* Sélectionne un **Utilisateur** comme auteur du document.
* ⚠️ **TRÈS IMPORTANT POUR TESTER** : Dans la section **Validation**, passe le **Statut doc** sur `Validé (valide)` et le **Statut humain** sur `Validé`, sinon les utilisateurs normaux ne verront pas les documents dans la bibliothèque ! (Seuls les documents validés y apparaissent).

## 5. Créer des QCM (Quiz)
Si tu veux tester le système d'examen/quiz :
* Va dans **Quiz > Questions** et clique sur **"Ajouter Question"**.
* Écris ton `Enoncé`, choisis la `Matière` concernée et les `Points` attribués.
* Au bas de cette même page (dans la partie en ligne *"Options de réponse"*), ajoute 2 à 4 choix possibles.
* N'oublie pas de **cocher la case "Est correct"** pour la ou les bonne(s) réponse(s) !

---
Une fois ces étapes réalisées (créer 1 ou 2 éléments à chaque fois suffit), tu pourras te déconnecter de l'admin, te rendre sur **http://127.0.0.1:8000/biblio/** (ou la page d'accueil) avec un compte Apprenant, et tu verras les documents s'afficher correctement avec leurs filtres associés !

## 6. Tester les Nouvelles Fonctionnalités d'Intelligence Artificielle (IA)
Pour tester l'IA intégrée directement sur les documents :
* Allez sur la page de lecture d'un document validé.
* Cliquez sur **"Générer le résumé IA"**.
* Une fois le résumé affiché en Markdown (avec rendu LaTeX pour les formules si présentes), vous verrez la zone de **Chat IA**.
* Posez une question pointue (ex: "Peux-tu me donner le point 1 ?" ou "Donne-moi un exemple de code Python POO").
* **Note de développement** : Si la clé API `GEMINI_API_KEY` n'est pas configurée dans votre `.env`, un **Mock de développement (Offline)** très intelligent vous répondra instantanément avec des exemples complets pour valider le design.

## 7. Tester la Recherche Avancée (Command Palette)
Une nouvelle recherche avancée de type "Command Palette" a été intégrée, offrant un design premium (Thème Noir ou Clair).
* Sur n'importe quelle page, cliquez sur la barre de recherche en haut ou appuyez sur les touches **`Ctrl + K`** (ou **`Cmd + K`** sur Mac).
* Le modal plein écran avec effet Blur s'affichera.
* Testez les "**Pills**" (boutons radio interactifs) pour filtrer par Niveau, Matière ou Type de Document.
* L'interface simule une "Recherche Sémantique Pro" et conserve vos recherches récentes pour un confort optimal.
