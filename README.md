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

- Gérer l'affichage de plusieurs joueurs
    - Mieux gérer la collision de chaque joueur
    - Mieur gérer la caméra 
    - Si un joueur sort de l'écran il meurt et on l'enlève 
- Implémenter un réseau de neurone basique avec Keras sequential
- Need to rewrite event handler for input and implement `keypress`
