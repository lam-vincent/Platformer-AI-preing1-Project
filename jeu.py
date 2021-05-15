# Sprites du chevalier réalisées par Luiz Melo
# https://assetstore.unity.com/packages/2d/characters/hero-knight-167779

import pygame
import sys
import math
import random
import perlin_noise
from utils.Player import Player
from utils.settings import *
from utils.EvolutionController import *


trueCameraPos = [0, 0]  # Variable globale pour la position de la caméra

seed = random.randint(0, 1 << 25)
print("Seed =", seed)
# Bruit de Perlin pour la génération aléatoire de la map
noise = perlin_noise.PerlinNoise(seed=seed)
gameMap = {}  # Variable globale pour la map


# Initialisation
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
window = pygame.display.set_mode(ACTUAL_SCREEN_SIZE)
pygame.display.set_caption("Jeu de plateforme")
clock = pygame.time.Clock()

mixer = pygame.mixer
mixer.Channel(0).play(mixer.Sound('sounds/music.wav'), loops=-1)


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


def generateChunk(x, y, maximizingPlayer):
    '''maximizingPlayer : le joueur qui va le plus loin'''
    chunkData = []
    for xPos in range(CHUNK_SIZE):
        # On multiplie par CHUNK_SIZE pour arriver aux coordonnées du bloc ciblé (pas du pixel).
        platformX = x * CHUNK_SIZE + xPos
        tileType = 0
        # Les facteurs platformFactor et holeFactor ne doivent pas aller au-delà de 3 ou la génération serait vraiment mauvaise
        # platformFactor correspond à la dispersion des plateformes : plus il est élevé, plus les plateformes iront loin en haut et en bas
        platformFactor = 1 + maximizingPlayer.xMax / 7000
        # PRNG pour Pseudo Random Number Generator
        platformPrng = platformFactor ** 0.5 * -12 * noise(platformX/10) // 1
        # holeFactor correspond à la présence de trous : plus il est élevé, plus il y a de trous
        holeFactor = 1 + maximizingPlayer.xMax / 7000
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


def handlePlatform(cameraPos, maximizingPlayer):
    '''
    Loop through platforms, calculates their hitboxes and returns them
    Also generates platforms according to camera position
    '''
    platformHitboxes = []
    for y in range(math.ceil(ACTUAL_SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
        chunkY = y - 1 + int(round(cameraPos[1]/(CHUNK_SIZE * BLOCK_SIZE)))
        for x in range(math.ceil(ACTUAL_SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
            chunkX = x - 1 + int(round(cameraPos[0]/(CHUNK_SIZE * BLOCK_SIZE)))
            targetChunk = str(chunkX) + ";" + str(chunkY)
            if targetChunk not in gameMap:
                gameMap[targetChunk] = generateChunk(
                    chunkX, chunkY, maximizingPlayer)
            for platform in gameMap[targetChunk]:
                if platform[1] > 0:
                    platformHitboxes.append(pygame.Rect(
                        platform[0][0] * BLOCK_SIZE, platform[0][1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

    return platformHitboxes


def handleCamera(player):
    # Camera
    cameraPos = trueCameraPos.copy()
    if player != None:
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
        cameraPos[0] = int(cameraPos[0])
        cameraPos[1] = int(cameraPos[1])

    return cameraPos


def bestXMaxPlayer(players: [Player]) -> Player:
    '''returns player object with the max xMax value from an array'''
    if len(players) != 0:
        return max(players, key=lambda item: item.xMax)
    return None


def bestScorePlayer(players: [Player]) -> Player:
    ''' returns the player with the best score from players in an array '''
    if len(players) != 0:
        return max(players, key=lambda item: item.score)
    return None


def stillPlayersAlive(players: [Player]) -> bool:
    return len(players) != 0


def getPlatformCoord(platformHitboxes):
    coord = []
    for rect in platformHitboxes:
        coord.append(rect.topleft)
    return coord


def getPlayerHeightFromGround(player: Player, platformHitboxes):
    player_bottom = player.rect.bottom
    platformCoord = getPlatformCoord(platformHitboxes)
    minDistance = abs(platformCoord[0][0] - player_bottom)
    selectedPlatformCoord = (0, 0)
    for coord in platformCoord:
        if abs(coord[0] - player_bottom) < minDistance:
            minDistance = abs(coord[0] - player_bottom)
            selectedPlatformCoord = coord

    if minDistance > 200:
        minDistance = 200
    return 1 - minDistance/200


def getPlayerDistanceToNextHole(player: Player):
    player_right = player.rect.center[0] + BLOCK_SIZE / 2
    minDistance = 100000
    for chunk in gameMap.values():
        for tile in chunk:
            if tile[1] == -1:
                if (tile[0][0] * BLOCK_SIZE - player_right) < minDistance and (tile[0][0] * BLOCK_SIZE - player_right) > 0:
                    minDistance = tile[0][0] * BLOCK_SIZE - player_right
    if minDistance > 600:
        minDistance = 600
    return 1 - minDistance / 600


def getPlayerDistanceFromNextBloc(player: Player, platformHitboxes):
    player_right = player.rect.right
    player_center_y = player.rect.center[1]
    platformCoord = getPlatformCoord(platformHitboxes)
    minDistance = 10000000
    selectedPlatformCoord = (0, 0)
    for coord in platformCoord:
        #print(f"coord[1] - player right = {coord[1] - player_right}")
        if (coord[0] - player_right) < minDistance and (coord[0] - player_right) > 0:
            if coord[1] < player_center_y < coord[1] + BLOCK_SIZE:
                minDistance = coord[0] - player_right
                selectedPlatformCoord = coord

    res = abs(selectedPlatformCoord[0] - player_right)
    if res > 80:
        res = 80
    return 1 - res / 80


def display(cameraPos, players: [Player]):
    # On global player pour modifier (uniquement les compteurs de frames)
    # Affichage des plateformes
    # Ces math.ceil() permettent de savoir combien au plus de chunks en y et en x
    for player in players:
        player.display(screen, cameraPos)

    player = bestScorePlayer(players)

    if stillPlayersAlive(players):
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
                            if DISPLAY_SPRITES:
                                screen.blit(platformSprites[platform[1]], (
                                    platform[0][0] * BLOCK_SIZE - cameraPos[0], platform[0][1] * BLOCK_SIZE - cameraPos[1]))
                            else:
                                tmpRect = pygame.Rect(
                                    platform[0][0] * BLOCK_SIZE - cameraPos[0], platform[0][1] * BLOCK_SIZE - cameraPos[1], BLOCK_SIZE, BLOCK_SIZE)
                                pygame.draw.rect(screen, (0, 0, 255), tmpRect)

            # Affichage du compte à rebours de mort du joueur
            colorRect = pygame.Surface((2, 2))
            pygame.draw.line(colorRect, (222, 71, 71), (0, 0), (0, 1))
            # On fait varier un "coefficient" de 0 à 1 pour maintenir une couleur cohérente sur la barre
            difference = (MAX_FPS * 25 - player.deathCountdown) / \
                (MAX_FPS * 25)
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


def getFps(clock) -> str:
    fps = str(int(clock.get_fps()))
    fps_text = pygame.font.SysFont("Arial", 18).render(
        "fps: " + fps, True, pygame.Color("coral"))
    return fps_text


evolutionController = EvolutionController(
    displaySprites=DISPLAY_SPRITES, taillePopulation=20, taillePopulationMutate=8)
evolutionController.generateFirstPopulation()

running = True
while running:
    screen.fill(DARK_GREY)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

    best_score_player = bestScorePlayer(evolutionController.populationAlive)
    best_xMax_player = bestXMaxPlayer(evolutionController.populationAlive)

    cameraPos = handleCamera(best_score_player)

    for index, player in enumerate(evolutionController.populationAlive):
        if player.dead:
            evolutionController.killPlayer(index)

    # Plateformes & Chunks
    platformHitboxes = handlePlatform(
        cameraPos, best_xMax_player)  # handleCollision and create platforms

    for player in evolutionController.populationAlive:
        distanceFromGround = getPlayerHeightFromGround(
            player, platformHitboxes)
        distanceFromWall = getPlayerDistanceFromNextBloc(
            player, platformHitboxes)
        distanceFromHole = getPlayerDistanceToNextHole(player)
        player.decision = player.makeDecision(
            distanceFromGround, distanceFromWall, distanceFromHole)
        player.eventHandler()  # handle input for player
        player.update(platformHitboxes)  # handle physics and collision

    if evolutionController.allPlayerAreDead():
        evolutionController.startNextGeneration()
        cameraPos = trueCameraPos

    # display everything including the player
    display(cameraPos, evolutionController.populationAlive)

    # display fps
    screen.blit(getFps(clock), (SCREEN_SIZE[0] - 65, 0))

    evolutionController.displayText(screen)

    pygame.display.flip()
    clock.tick(MAX_FPS)

pygame.quit()
