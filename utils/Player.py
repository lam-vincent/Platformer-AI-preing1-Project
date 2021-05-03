import pygame 

MAX_FPS = 60

# Classe de joueur
class Player:
    def __init__(self, posX, posY):
        self.width = 47
        self.height = 65 

        # Hitbox du joueur (au passage on récupèrera les coordonnées du rect pour récupérer les coordonnées du joueur)
        self.rect = pygame.Rect(posX, posY, self.width, self.height)

        # Vitesse verticale, mouvement du joueur, cooldown des dash
        self.ySpeed = 0
        self.movement = [0, 0]

        # Dash
        self.xDashCD = 0
        self.yDashCD = 0
        self.canXDash = True
        self.canActivateArrows = [True, True]

        # Animation de mort
        self.dead = False
        self.deathAnimationPlayed = False
        self.deathSoundPlayed = False
        self.deathCountdown = MAX_FPS * 25

        # Compteurs de frame pour chaque animation
        self.walkCount = 0
        self.idleCount = 0
        self.jumpCount = 0
        self.fallCount = 0
        self.yDashCount = 0
        self.deathCount = 0

        # Compteur pour les effets sonores
        self.walkSoundCount = 0

        self.lastDirection = ""
        self.onGround = False
        self.airTime = 0