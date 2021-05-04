import pygame
import math
from utils.settings import *
# Classe de joueur


class Player:
    def __init__(self, posX, posY):
        self.width = 47
        self.height = 65

        self.score = 0  # Score actuel du joueur utilisé comme score de fitness
        self.xMax = 0  # Position maximal atteinte

        self.previousSecond = -1

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

        self.idleSprites = self.loadKnightSprites("idle", 11)
        self.walkSprites = self.loadKnightSprites("run", 8)
        self.jumpSprites = self.loadKnightSprites("jump", 3)
        self.fallSprites = self.loadKnightSprites("fall", 3)
        self.dashSprites = self.loadKnightSprites("dash", 7)
        self.deathSprites = self.loadKnightSprites("death", 15)

        self.font = pygame.font.Font(None, math.floor(
            44 * ((ACTUAL_SCREEN_SIZE[0] + ACTUAL_SCREEN_SIZE[1])/2)/((700 + 500)/2)))

    def loadKnightSprites(self, spriteName, spriteCount):  # du joueur
        spriteList = []
        spriteTemplate = "assets/knight/{0}/{0}_{1!s}.png"
        for i in range(spriteCount):
            spriteList.append(pygame.image.load(
                spriteTemplate.format(spriteName, i)))

        return spriteList

    def move(self, platforms):
        collisionTypes = {'top': False, 'bottom': False,
                          'left': False, 'right': False}

        # On vérifie les collisions en déplaçant d'abord en x, puis en y
        self.rect.x += self.movement[0]
        hitList = self.collisionTest(platforms)
        for platform in hitList:
            if self.movement[0] > 0:
                self.rect.right = platform.left
                collisionTypes['right'] = True
            elif self.movement[0] < 0:
                self.rect.left = platform.right
                collisionTypes['left'] = True

        self.rect.y += self.movement[1]
        hitList = self.collisionTest(platforms)
        for platform in hitList:
            if self.movement[1] > 0:
                self.rect.bottom = platform.top
                collisionTypes['bottom'] = True
            elif self.movement[1] < 0:
                self.rect.top = platform.bottom
                collisionTypes['top'] = True

        return collisionTypes

    def collisionTest(self, platforms):
        hitList = []
        for platform in platforms:
            if self.rect.colliderect(platform):
                hitList.append(platform)

        return hitList

    def gravity(self):
        self.ySpeed += ACCELERATION
        if self.ySpeed > 20:  # et on la limite à 20 maximum
            self.ySpeed = 20

    def display(self, screen, cameraPos):
        if self.dead:
            screen.fill(DARK_DARK_GREY)
            if not self.deathAnimationPlayed:
                if self.deathCount > 14 * (ANIMATION_REFRESH_RATE * 2):
                    self.deathAnimationPlayed = True
                else:
                    screen.blit(self.deathSprites[self.deathCount // (ANIMATION_REFRESH_RATE * 2)], ((
                        ACTUAL_SCREEN_SIZE[0] - self.width)/2, (ACTUAL_SCREEN_SIZE[1] - self.height)/2))
                    self.deathCount += 1
            else:
                # Ajouter un temps de pause
                texte = "score : " + str(int(self.score))
                text = self.font.render(texte, True, (255, 255, 255))
                textSize = self.font.size(texte)
                screen.blit(text, ((
                    ACTUAL_SCREEN_SIZE[0] - textSize[0])/2, (ACTUAL_SCREEN_SIZE[1] - textSize[1])/2))
        else:
            # On remplit l'écran de gris foncé pour qu'une frame ne persiste pas sur la frame suivante
            screen.fill(DARK_GREY)

            # Affichage du joueur
            # On loop les sprites (comme un GIF quoi)
            if self.walkCount + 1 >= 8 * ANIMATION_REFRESH_RATE:
                self.walkCount = 0
            if self.idleCount + 1 >= 11 * ANIMATION_REFRESH_RATE:
                self.idleCount = 0
            if self.jumpCount + 1 >= 3 * ANIMATION_REFRESH_RATE:
                self.jumpCount = 0
            if self.fallCount + 1 >= 3 * ANIMATION_REFRESH_RATE:
                self.fallCount = 0

            # Traitement à part des sprites de la phase de dash horizontale où le joueur prend de la vitesse
            if self.xDashCD >= 48 * (MAX_FPS // 60):
                # S'il va vers la gauche ou regarde vers la gauche
                if self.movement[0] < 0 or self.lastDirection == "left":
                    # Divison euclidienne par 2 pour que les sprites de dash rentrent bien dans les temps
                    screen.blit(pygame.transform.flip(self.dashSprites[math.floor((MAX_FPS - self.xDashCD) / (
                        MAX_FPS / 30))], True, False), (self.rect.x - cameraPos[0], self.rect.y - cameraPos[1]))
                else:
                    screen.blit(self.dashSprites[math.floor((MAX_FPS - self.xDashCD) / (
                        MAX_FPS / 30))], (self.rect.x - cameraPos[0], self.rect.y - cameraPos[1]))
            elif not self.onGround and self.yDashCD > 0 and self.ySpeed <= 0:
                if self.yDashCount + 2 <= 12:
                    self.yDashCount += 2
                if self.movement[0] < 0 or self.lastDirection == "left":
                    # Divison euclidienne par 2 pour que les sprites de dash rentrent bien dans les temps
                    screen.blit(pygame.transform.flip(
                        self.dashSprites[self.yDashCount // 2], True, False), (self.rect.x - cameraPos[0], self.rect.y - cameraPos[1]))
                else:
                    screen.blit(self.dashSprites[self.yDashCount // 2],
                                (self.rect.x - cameraPos[0], self.rect.y - cameraPos[1]))
            else:
                # Choix des sprites idle ou walk selon sa vitesse horizontale
                if not self.onGround:
                    if self.ySpeed <= 0:
                        usedSprites = self.jumpSprites
                        usedCount = self.jumpCount
                    else:
                        usedSprites = self.fallSprites
                        usedCount = self.fallCount
                elif self.movement[0] == 0:
                    # On utilise une variable qu'on fera varier selon les cas, pour éviter de réécrire la fonction qu'on va appeler plusieurs fois
                    usedSprites = self.idleSprites
                    usedCount = self.idleCount
                else:
                    usedSprites = self.walkSprites
                    usedCount = self.walkCount

                # Affichage des sprites, on inverse la sprite s'il regarde à gauche
                # S'il va vers la gauche ou regarde vers la gauche
                if self.movement[0] < 0 or self.lastDirection == "left":
                    # Divison euclidienne par 5 pour qu'il y ait une sprite toutes les 5 frames, soit un framerate d'animation à 12FPS (60 / 5)
                    screen.blit(pygame.transform.flip(
                        usedSprites[usedCount // ANIMATION_REFRESH_RATE], True, False), (self.rect.x - cameraPos[0], self.rect.y - cameraPos[1]))
                else:
                    screen.blit(usedSprites[usedCount // ANIMATION_REFRESH_RATE],
                                (self.rect.x - cameraPos[0], self.rect.y - cameraPos[1]))

                # On ajoute 1 au compteur de frame
                if not self.onGround:
                    if self.ySpeed <= 0:
                        self.jumpCount += 1
                    else:
                        self.fallCount += 1
                elif self.movement[0] == 0:
                    self.idleCount += 1
                else:
                    self.walkCount += 1

    def update(self, platformHitboxes, sound, deathSound):
        # On applique la gravité au joueur
        self.gravity()

        # Si jamais le joueur arrive en bas de l'écran
        if self.rect.y > SCREEN_SIZE[1] - self.height:
            if not self.deathSoundPlayed:
                deathSound()
                self.deathSoundPlayed = True
            self.dead = True
            self.movement[0] = 0

        # Traitement du cooldown du dash (on le fait ici pour mettre ySpeed à 0 s'il est en train de dash)
        if self.xDashCD > 0:
            self.xDashCD -= 1
            if self.xDashCD <= MAX_FPS/1.3:  # Si le joueur est dans la phase "descendante" du dash, on veut que sa vitesse revienne à la normale
                if self.movement[0] < 0:
                    self.movement[0] = (self.movement[0] - 3) // 2
                if self.movement[0] > 0:
                    self.movement[0] = (self.movement[0] + 4) // 2
            elif self.yDashCD == 0:
                self.ySpeed = 0
        if self.yDashCD > 0:
            self.yDashCD -= 1
            if self.yDashCD == 0:
                self.yDashCount = 0

        # On ajoute la vitesse à la position à chaque frame (pour que sa position en y soit polynômiale en fonction du temps)
        self.movement[1] += self.ySpeed

        collisions = self.move(platformHitboxes)
        if collisions['bottom']:  # S'il y a eu une collision en bas, on réinitialise toutes les variables de joueurs liées au saut et on lui redonne son dash
            self.ySpeed = 0
            self.airTime = 0
            self.onGround = True
            self.xDashCD = 0
            self.canXDash = True
            self.canActivateArrows = [True, True]
        else:
            self.airTime += 1
            # Si le joueur a dépassé son temps de saut, on le considère dans les airs (ceci permet aussi de fixer un bug graphique)
            if self.airTime >= 6:
                self.onGround = False

        self.movement[1] = 0

        if self.movement[0] != 0 and self.onGround:
            if self.walkSoundCount + 1 > 30:
                self.walkSoundCount = 0
            else:
                self.walkSoundCount += 1
            if self.walkSoundCount == 1:
                sound("walk1")
            if self.walkSoundCount == 16:
                sound("walk2")

        # Calcul du score, traitement du compte à rebours de mort du joueur
        if not self.dead:
            seconds = pygame.time.get_ticks() // (1000/(MAX_FPS/60))

            if self.previousSecond + 1 <= seconds:
                self.previousSecond += 1
                if self.score - 1 > 0:
                    self.score -= 1

            if self.xMax > 500:  # On ne veut pas faire commencer le compte à rebours trop tôt
                if self.deathCountdown - self.xMax / 1000 + 0.9 < 0:
                    self.deathCountdown = 0
                else:
                    self.deathCountdown -= self.xMax / 1000 + 0.9

            if self.xMax < self.rect.x:
                if self.deathCountdown > 0 and self.xMax > 500:
                    if self.deathCountdown + self.xMax / 600 + 0.9 > MAX_FPS * 25:
                        self.deathCountdown = MAX_FPS * 25
                    else:
                        self.deathCountdown += self.xMax / 600 + 0.9
                self.xMax = self.rect.x
                self.score += 0.1

            if self.deathCountdown == 0:
                if not self.deathSoundPlayed:
                    deathSound()
                    self.deathSoundPlayed = True
                self.dead = True
