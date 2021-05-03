# Sprites du chevalier réalisées par Luiz Melo
# https://assetstore.unity.com/packages/2d/characters/hero-knight-167779

import pygame
import sys
import math
import random
import perlin_noise
from utils.Player import Player
from utils.settings import *


trueCameraPos = [0, 0]  # Variable globale pour la position de la caméra

seed = random.randint(0, 1 << 25)
print("Seed =", seed)
# Bruit de Perlin pour la génération aléatoire de la map
noise = perlin_noise.PerlinNoise(seed=seed)
gameMap = {}  # Variable globale pour la map

score = 0  # Le score de la partie
# On aura besoin d'une variable hors de la boucle pour compter les secondes
previousSecond = -1
xMax = 0  # On aura besoin de connaître la position en x maximale que le joueur a atteint

# Initialisation
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
window = pygame.display.set_mode(ACTUAL_SCREEN_SIZE)
pygame.display.set_caption("Jeu de plateforme")
clock = pygame.time.Clock()

mixer = pygame.mixer
mixer.Channel(0).play(mixer.Sound('sounds/music.wav'), loops=-1)

# Fonction pour jouer des sons


def sound(name):
    if not player.dead:  # On ne veut pas qu'un son se joue si le joueur est dans l'écran de mort
        path = "sounds/{0}.wav"
        mixer.find_channel().play(mixer.Sound(path.format(name)))


def deathSound():
    mixer.set_num_channels(0)
    mixer.set_num_channels(1)
    mixer.Channel(0).play(mixer.Sound('sounds/death2.wav'))
    mixer.fadeout(8000)


def loadPlatformSprites(spriteName):  # des plateformes
    spriteTemplate = "assets/platform/{0}.png"
    return pygame.image.load(spriteTemplate.format(spriteName))


platformSprites = {1: loadPlatformSprites(
    "platform"), 2: loadPlatformSprites("underPlatform")}

# Chargement des images


def loadArrow(direction, number):
    path = "assets/arrow/{0}Arrow{1!s}.png"
    return pygame.image.load(path.format(direction, number))


def loadAllArrows(direction):
    return {0: loadArrow(direction, 0), 1: loadArrow(direction, 1)}


rightArrow = loadAllArrows("right")
upArrow = loadAllArrows("up")

# Fonctions utilisées dans le fonctionnement du jeu


def generateChunk(x, y):
    chunkData = []
    for xPos in range(CHUNK_SIZE):
        # On multiplie par CHUNK_SIZE pour arriver aux coordonnées du bloc ciblé (pas du pixel).
        platformX = x * CHUNK_SIZE + xPos
        tileType = 0
        # Les facteurs platformFactor et holeFactor ne doivent pas aller au-delà de 3 ou la génération serait vraiment mauvaise
        # platformFactor correspond à la dispersion des plateformes : plus il est élevé, plus les plateformes iront loin en haut et en bas
        platformFactor = 1 + xMax / 7000
        # PRNG pour Pseudo Random Number Generator
        platformPrng = platformFactor ** 0.5 * -12 * noise(platformX/10) // 1
        # holeFactor correspond à la présence de trous : plus il est élevé, plus il y a de trous
        holeFactor = 1 + xMax / 7000
        holePrng = math.floor(1/(holeFactor ** 2.5) * -
                              100 * noise(platformX/10)) + 1

        for yPos in range(CHUNK_SIZE):  # On passe dans chaque y et x d'un chunk
            platformY = y * CHUNK_SIZE + yPos

            if platformX == -1:  # On veut créer un mur invisible à gauche
                tileType = 1
                chunkData.append([[platformX, platformY], tileType])

            if holePrng == 0:
                tileType = -1
            elif platformY > platformPrng:
                tileType = 2
            elif platformY == platformPrng:
                tileType = 1
            chunkData.append([[platformX, platformY], tileType])

    return chunkData


player = Player(350, -500)

# Fonction d'affichage à l'écran


def display(cameraPos):
    # On global player pour modifier (uniquement les compteurs de frames)
    global player
    # Affichage des plateformes
    # Ces math.ceil() permettent de savoir combien au plus de chunks en y et en x
    player.display(screen, cameraPos, score)

    if player.dead == False:
        for y in range(math.ceil(ACTUAL_SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
            # seront affichés simultanément à l'écran
            for x in range(math.ceil(ACTUAL_SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
                chunkX = x - 1 + \
                    int(round(cameraPos[0]/(CHUNK_SIZE * BLOCK_SIZE)))
                chunkY = y - 1 + \
                    int(round(cameraPos[1]/(CHUNK_SIZE * BLOCK_SIZE)))
                targetChunk = str(chunkX) + ";" + str(chunkY)
                for platform in gameMap[targetChunk]:
                    if platform[1] > 0:
                        screen.blit(platformSprites[platform[1]], (
                            platform[0][0] * BLOCK_SIZE - cameraPos[0], platform[0][1] * BLOCK_SIZE - cameraPos[1]))

        # Affichage du compte à rebours de mort du joueur
        colorRect = pygame.Surface((2, 2))
        pygame.draw.line(colorRect, (222, 71, 71), (0, 0), (0, 1))
        # On fait varier un "coefficient" de 0 à 1 pour maintenir une couleur cohérente sur la barre
        difference = (MAX_FPS * 25 - player.deathCountdown) / (MAX_FPS * 25)
        pygame.draw.line(colorRect, (104 + math.floor((222 - 104) * difference),
                                     222 - math.floor((222 - 71) * difference), 71), (1, 0), (1, 1))
        rectWidth = math.floor(
            ACTUAL_SCREEN_SIZE[0] // 2 * (player.deathCountdown / (MAX_FPS * 25)))
        if rectWidth < 0:
            rectWidth = 0
        rectHeight = ACTUAL_SCREEN_SIZE[1] // 50
        colorRect = pygame.transform.smoothscale(
            colorRect, (rectWidth, rectHeight))
        screen.blit(colorRect, ((
            ACTUAL_SCREEN_SIZE[0] - rectWidth) // 2, ACTUAL_SCREEN_SIZE[1] // 10))

        # Affichage des flèches de dash
        arrowDisplayY = ACTUAL_SCREEN_SIZE[1] // 2 + 100
        coordsLeft = (
            (ACTUAL_SCREEN_SIZE[0] - ARROW_SIZE) // 2 - ARROW_SIZE, arrowDisplayY)
        coordsRight = (
            (ACTUAL_SCREEN_SIZE[0] + ARROW_SIZE) // 2, arrowDisplayY)
        if not player.canActivateArrows[0] or player.onGround:
            screen.blit(rightArrow[0], coordsLeft)
        else:
            screen.blit(rightArrow[1], coordsLeft)
        if not player.canActivateArrows[1] or player.onGround:
            screen.blit(upArrow[0], coordsRight)
        else:
            screen.blit(upArrow[1], coordsRight)

    window.blit(pygame.transform.scale(screen, ACTUAL_SCREEN_SIZE),
                (0, 0))  # On affiche l'écran à la taille indiquée
    pygame.display.flip()


# Boucle de jeu
running = True
while running:

    # Camera
    tempTrueCameraPosX = (
        player.rect.x - trueCameraPos[0] - (ACTUAL_SCREEN_SIZE[0] // 2 - player.width // 2))/20
    trueCameraPos[0] += tempTrueCameraPosX
    if trueCameraPos[0] < 0:  # On ne veut pas que la caméra aille trop sur la gauche
        trueCameraPos[0] -= tempTrueCameraPosX
    temptrueCameraPosY = (
        player.rect.y - trueCameraPos[1] - (ACTUAL_SCREEN_SIZE[1] // 2 - player.height // 2))/20
    trueCameraPos[1] += temptrueCameraPosY
    if trueCameraPos[1] > 0:  # On ne veut pas que la caméra aille trop bas
        trueCameraPos[1] -= temptrueCameraPosY
    cameraPos = trueCameraPos.copy()
    cameraPos[0] = int(cameraPos[0])
    cameraPos[1] = int(cameraPos[1])

    # Plateformes & Chunks
    platformHitboxes = []
    for y in range(math.ceil(ACTUAL_SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
        chunkY = y - 1 + int(round(cameraPos[1]/(CHUNK_SIZE * BLOCK_SIZE)))
        for x in range(math.ceil(ACTUAL_SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
            chunkX = x - 1 + int(round(cameraPos[0]/(CHUNK_SIZE * BLOCK_SIZE)))
            targetChunk = str(chunkX) + ";" + str(chunkY)
            if targetChunk not in gameMap:
                gameMap[targetChunk] = generateChunk(chunkX, chunkY)
            for platform in gameMap[targetChunk]:
                if platform[1] > 0:
                    platformHitboxes.append(pygame.Rect(
                        platform[0][0] * BLOCK_SIZE, platform[0][1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

    # Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                player.movement[0] = -4
                player.lastDirection = "left"

            if event.key == pygame.K_d:
                player.movement[0] = 4
                player.lastDirection = "right"

            # Si le joueur est dans les airs depuis moins de 6 frames, il peut quand même sauter
            if event.key == pygame.K_SPACE and player.onGround and player.airTime < 6:
                player.ySpeed = -math.sqrt(2 * JUMP_HEIGHT * ACCELERATION)
                player.walkCount = 0
                player.walkSoundCount = 0
                player.onGround = False
                sound("jump")

        if event.type == pygame.KEYUP:
            if (player.movement[0] < 0 and event.key == pygame.K_q) or (player.movement[0] > 0 and event.key == pygame.K_d):
                player.movement[0] = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                if player.xDashCD == 0 and player.movement[0] != 0 and player.canXDash and not player.onGround:
                    if player.movement[0] < 0:
                        player.movement[0] = -10
                    else:
                        player.movement[0] = 10
                    player.xDashCD = MAX_FPS
                    player.canXDash = False
                    player.canActivateArrows[0] = False
                    sound("dashX")
                if player.xDashCD > 0 and player.xDashCD < MAX_FPS - 1 and player.yDashCD == 0 and not player.onGround and player.airTime >= 14:
                    player.ySpeed = -10
                    player.yDashCD = player.xDashCD
                    player.canActivateArrows[1] = False
                    sound("dashY")

    # On applique la gravité au joueur
    player.ySpeed += ACCELERATION
    if player.ySpeed > 20:  # et on la limite à 20 maximum
        player.ySpeed = 20
    # Si jamais le joueur arrive en bas de l'écran
    if player.rect.y > SCREEN_SIZE[1] - player.height:
        if not player.deathSoundPlayed:
            deathSound()
            player.deathSoundPlayed = True
        player.dead = True
        player.movement[0] = 0

    # Traitement du cooldown du dash (on le fait ici pour mettre ySpeed à 0 s'il est en train de dash)
    if player.xDashCD > 0:
        player.xDashCD -= 1
        if player.xDashCD <= MAX_FPS/1.3:  # Si le joueur est dans la phase "descendante" du dash, on veut que sa vitesse revienne à la normale
            if player.movement[0] < 0:
                player.movement[0] = (player.movement[0] - 3) // 2
            if player.movement[0] > 0:
                player.movement[0] = (player.movement[0] + 4) // 2
        elif player.yDashCD == 0:
            player.ySpeed = 0
    if player.yDashCD > 0:
        player.yDashCD -= 1
        if player.yDashCD == 0:
            player.yDashCount = 0

    # On ajoute la vitesse à la position à chaque frame (pour que sa position en y soit polynômiale en fonction du temps)
    player.movement[1] += player.ySpeed

    collisions = player.move(platformHitboxes)
    if collisions['bottom']:  # S'il y a eu une collision en bas, on réinitialise toutes les variables de joueurs liées au saut et on lui redonne son dash
        player.ySpeed = 0
        player.airTime = 0
        player.onGround = True
        player.xDashCD = 0
        player.canXDash = True
        player.canActivateArrows = [True, True]
    else:
        player.airTime += 1
        # Si le joueur a dépassé son temps de saut, on le considère dans les airs (ceci permet aussi de fixer un bug graphique)
        if player.airTime >= 6:
            player.onGround = False

    player.movement[1] = 0

    if player.movement[0] != 0 and player.onGround:
        if player.walkSoundCount + 1 > 30:
            player.walkSoundCount = 0
        else:
            player.walkSoundCount += 1
        if player.walkSoundCount == 1:
            sound("walk1")
        if player.walkSoundCount == 16:
            sound("walk2")

    # Calcul du score, traitement du compte à rebours de mort du joueur
    if not player.dead:
        seconds = pygame.time.get_ticks() // (1000/(MAX_FPS/60))

        if previousSecond + 1 <= seconds:
            previousSecond += 1
            if score - 1 > 0:
                score -= 1

        if xMax > 500:  # On ne veut pas faire commencer le compte à rebours trop tôt
            if player.deathCountdown - xMax / 1000 + 0.9 < 0:
                player.deathCountdown = 0
            else:
                player.deathCountdown -= xMax / 1000 + 0.9

        if xMax < player.rect.x:
            if player.deathCountdown > 0 and xMax > 500:
                if player.deathCountdown + xMax / 600 + 0.9 > MAX_FPS * 25:
                    player.deathCountdown = MAX_FPS * 25
                else:
                    player.deathCountdown += xMax / 600 + 0.9
            xMax = player.rect.x
            score += 0.1

        if player.deathCountdown == 0:
            if not player.deathSoundPlayed:
                deathSound()
                player.deathSoundPlayed = True
            player.dead = True

    display(cameraPos)

    clock.tick(MAX_FPS)

pygame.quit()
