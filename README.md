# Platformer-AI-preing1-Project

![gif](assets/gif/gif1.gif)

Comparaison de plusieurs IA sur un même jeu ?
Comparaison de plusieurs IA sur plusieurs jeux d'une même famille ?
(plusieurs IA dans le même jeu vs. une IA dans plusieurs jeux différents) 
Comparaison du comportement d'une IA sur des jeux de genre différents ?
Un point à creuser : jeux de plateau et de stratégie tour-par-tour


## Install dependancies 

`pip install -r requirements.txt`

## Questionnement

- Quelle variable utiliser comme var de fitness ? : déplacement maximal ou score instantané ? 
- Comment handle les joueurs qui ne sont pas assez rapides par rapport au meilleur joueur ? On les supprime ?

## Todo 

- [ ] Fix le reset des variables des joueurs quand on les fait respawns 
- [ ] Fix le dash qui caste tout le temps le double dash
- [ ] Enregistrer les weights et les poids du meilleur joueur dans un fichier
- [ ] Faire un système de couleur dans le leaderboard pour les bot best mutated et random
- [x] Enlever les textures des platformes
- [x] Fonction de sélection, reproduction/mutation

## IA inputs

- distance du prochain vide 
- taille du prochain vide
- distance vers le prochain block en face 
- si touche le sol ou non ?
