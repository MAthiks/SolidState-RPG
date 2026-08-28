SOLID STATE — OFFLINE TEST v0.1
===============================

Statut : EXPERIMENTAL / NON CERTIFIE

But
---
Tester rapidement l'expérience Solid State entièrement hors connexion sur téléphone ou ordinateur, sans modifier le Checkpoint 326 certifié.

Lancement Android
-----------------
1. Décompresser le ZIP.
2. Ouvrir index.html dans un navigateur Android compatible avec les fichiers locaux.
3. Si votre navigateur refuse l'ouverture directe, utilisez un petit serveur HTTP local Android et ouvrez index.html via localhost. Aucune connexion Internet n'est requise.

Fonctions incluses
------------------
- 1 à 4 joueurs.
- Un personnage par joueur dans le prototype.
- PV / SAN / PM / Chance / inventaire.
- Connaissances séparées par joueur et partage explicite.
- Mode Normal / Libre : « Que fais-tu ? ».
- Mode Facile / Assisté : exactement 3 choix + 1 action libre.
- Jets d100 / d20 / d10 / d6 via crypto.getRandomValues du navigateur.
- Journal de session.
- Sauvegarde locale.
- Export / import JSON.
- Petit scénario original de démonstration « Les Archives de Minuit ».

Limites importantes
-------------------
- Ce n'est PAS un Checkpoint Solid State certifié.
- Le package n'embarque pas les textes complets des scénarios PASS_REAL ni les livres CoC7.
- Le save/resume certifié du moteur reste le chantier Checkpoint 327.
- Strict Replay n'est pas encore intégré.
- Les jets utilisent le RNG cryptographique local du navigateur mais ne constituent pas encore le mécanisme RNG externe/certifié du moteur final.

Aucun appel réseau, CDN ou ressource externe n'est utilisé par index.html.
