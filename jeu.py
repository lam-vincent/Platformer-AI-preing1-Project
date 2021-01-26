# Sprites du chevalier réalisées par Luiz Melo
# https://assetstore.unity.com/packages/2d/characters/hero-knight-167779

import pygame, sys, math

# Constantes
SCREEN_SIZE = (700, 500)
CHUNK_SIZE = 8
BLOCK_SIZE = 32

DARK_GREY = (35, 39, 42)

PLAYER_WIDTH = 47
PLAYER_HEIGHT = 65
JUMP_HEIGHT = 65
ACCELERATION = 0.3

MAX_FPS = 60
ANIMATION_FPS = 12
ANIMATION_REFRESH_RATE = MAX_FPS // ANIMATION_FPS

trueScroll = [0, 0] # Variable globale pour la position de la caméra
gameMap = {} # Variable globale pour la map

# Initialisation
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Jeu de plateforme")
clock = pygame.time.Clock()

# Chargement des sprites
def loadKnightSpirtes(spriteName, spriteCount): # du joueur
    spriteList = []
    spriteTemplate = "assets/knight/{0}/{0}_{1!s}.png"
    for i in range(spriteCount):
        spriteList.append(pygame.image.load(spriteTemplate.format(spriteName, i)))

    return spriteList

idleSprites = loadKnightSpirtes("idle", 11)
walkSprites = loadKnightSpirtes("run", 8)
jumpSprites = loadKnightSpirtes("jump", 3)
fallSprites = loadKnightSpirtes("fall", 3)

def loadPlatformSprites(spriteName): # des plateformes
    spriteTemplate = "assets/platform/{0}.png"
    return pygame.image.load(spriteTemplate.format(spriteName))

platformSprites = {1: loadPlatformSprites("platform"), 2: loadPlatformSprites("underPlatform")}

# Fonctions utilisées dans le fonctionnement du jeu
def generateChunk(x, y):
    chunkData = []
    for yPos in range(CHUNK_SIZE): # On passe dans chaque y et x d'un chunk
        for xPos in range(CHUNK_SIZE):
            platformX = x * CHUNK_SIZE + xPos # On multiplie par CHUNK_SIZE pour arriver aux "vraies" coordonnées du bloc ciblé.
            platformY = y * CHUNK_SIZE + yPos
            tileType = 0
            if platformY > 10:
                tileType = 2
            elif platformY == 10:
                tileType = 1
            if tileType != 0:
                chunkData.append([[platformX, platformY], tileType])
    return chunkData

def collisionTest(rect, platforms):
    hitList = []
    for platform in platforms:
        if rect.colliderect(platform):
            hitList.append(platform)

    return hitList

def move(rect, movement, platforms):
    collisionTypes = {'top': False, 'bottom': False, 'left': False, 'right': False}

    # On vérifie les collisions en déplaçant d'abord en x, puis en y
    rect.x += movement[0]
    hitList = collisionTest(rect, platforms)
    for platform in hitList:
        if movement[0] > 0:
            rect.right = platform.left
            collisionTypes['right'] = True
        elif movement[0] < 0:
            rect.left = platform.right
            collisionTypes['left'] = True

    rect.y += movement[1]
    hitList = collisionTest(rect, platforms)
    for platform in hitList:
        if movement[1] > 0:
            rect.bottom = platform.top
            collisionTypes['bottom'] = True
        elif movement[1] < 0:
            rect.top = platform.bottom
            collisionTypes['top'] = True 

    return rect, collisionTypes

# Classe de joueur
class Player:
    def __init__(self):
        # Hitbox du joueur (au passage on récupèrera les coordonnées du rect pour récupérer les coordonnées du joueur)
        self.rect = pygame.Rect(350, 0, PLAYER_WIDTH, PLAYER_HEIGHT)

        # Vitesse horizontale, mouvement du joueur
        self.ySpeed = 0
        self.movement = [0, 0]

        # Compteurs de frame pour chaque animation
        self.walkCount = 0
        self.idleCount = 0
        self.jumpCount = 0
        self.fallCount = 0

        self.lastDirection = ""
        self.onGround = False
        self.airTime = 0

player = Player()

# Fonction d'affichage à l'écran
def display(scroll):
    global player # On global player pour modifier (uniquement les compteurs de frames)

    # On remplit l'écran de gris foncé pour qu'une frame ne persiste pas sur la frame suivante
    screen.fill(DARK_GREY)

    # Affichage du joueur
    # On loop les sprites (comme un GIF quoi)
    if player.walkCount + 1 >= 8 * ANIMATION_REFRESH_RATE:
        player.walkCount = 0
    if player.idleCount + 1 >= 11 * ANIMATION_REFRESH_RATE:
        player.idleCount = 0
    if player.jumpCount + 1 >= 3 * ANIMATION_REFRESH_RATE:
        player.jumpCount = 0
    if player.fallCount + 1 >= 3 * ANIMATION_REFRESH_RATE:
        player.fallCount = 0

    # Choix des sprites idle ou walk selon sa vitesse horizontale
    if player.movement[0] == 0:
        usedSprites = idleSprites # On utilise une variable qu'on fera varier selon les cas, pour éviter de réécrire la fonction qu'on va appeler plusieurs fois
        usedCount = player.idleCount
    else:
        usedSprites = walkSprites 
        usedCount = player.walkCount
    if not player.onGround:
        if player.ySpeed <= 0:
            usedSprites = jumpSprites
            usedCount = player.jumpCount
        else:
            usedSprites = fallSprites
            usedCount = player.fallCount

    # Affichage des sprites, on inverse la sprite s'il regarde à gauche
    if player.movement[0] < 0 or player.lastDirection == "left": # S'il va vers la gauche ou regarde vers la gauche
        screen.blit(pygame.transform.flip(usedSprites[usedCount // ANIMATION_REFRESH_RATE], True, False), (player.rect.x - scroll[0], player.rect.y - scroll[1])) # Divison euclidienne par 5 pour qu'il y ait une sprite toutes les 5 frames, soit un framerate d'animation à 12FPS (60 / 5)
    else:
        screen.blit(usedSprites[usedCount // ANIMATION_REFRESH_RATE], (player.rect.x - scroll[0], player.rect.y - scroll[1]))

    # On ajoute 1 au compteur de frame
    if not player.onGround:
        if player.ySpeed <= 0:
            player.jumpCount += 1
        else:
            player.fallCount += 1
    else:
        if player.movement[0] == 0:
            player.idleCount += 1
        else:
            player.walkCount += 1

    # Affichage des plateformes
    for y in range(math.ceil(SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2): # Ces math.ceil() permettent de savoir combien au plus de chunks en y et en x
        for x in range(math.ceil(SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2): # seront affichés simultanément à l'écran
            chunkX = x - 1 + int(round(scroll[0]/(CHUNK_SIZE * BLOCK_SIZE)))
            chunkY = y - 1 + int(round(scroll[1]/(CHUNK_SIZE * BLOCK_SIZE)))
            targetChunk = str(chunkX) + ";" + str(chunkY)
            for platform in gameMap[targetChunk]:
                screen.blit(platformSprites[platform[1]], (platform[0][0] * BLOCK_SIZE - scroll[0], platform[0][1] * BLOCK_SIZE - scroll[1]))

    pygame.display.flip()

# Boucle de jeu
running = True
while running:

    # Camera
    trueScroll[0] += (player.rect.x - trueScroll[0] - (SCREEN_SIZE[0] // 2 - PLAYER_WIDTH // 2))/20
    trueScroll[1] += (player.rect.y - trueScroll[1] - (SCREEN_SIZE[1] // 2 - PLAYER_HEIGHT // 2))/20
    scroll = trueScroll.copy()
    scroll[0] = int(scroll[0])
    scroll[1] = int(scroll[1])

    # Plateformes & Chunks
    platformHitboxes = []
    for y in range(math.ceil(SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
        for x in range(math.ceil(SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
            chunkX = x - 1 + int(round(scroll[0]/(CHUNK_SIZE * BLOCK_SIZE)))
            chunkY = y - 1 + int(round(scroll[1]/(CHUNK_SIZE * BLOCK_SIZE)))
            targetChunk = str(chunkX) + ";" + str(chunkY)
            if targetChunk not in gameMap:
                gameMap[targetChunk] = generateChunk(chunkX, chunkY)
            for platform in gameMap[targetChunk]:
                if platform[1] in [1, 2]:
                    platformHitboxes.append(pygame.Rect(platform[0][0] * BLOCK_SIZE, platform[0][1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

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

            if event.key == pygame.K_SPACE and player.onGround and player.airTime < 6:
                    player.ySpeed = -math.sqrt(2 * JUMP_HEIGHT * ACCELERATION)
                    player.walkCount = 0
                    player.onGround = False

        if event.type == pygame.KEYUP:
            if (player.movement[0] < 0 and event.key == pygame.K_q) or (player.movement[0] > 0 and event.key == pygame.K_d):
                player.movement[0] = 0

    # On applique la gravité au joueur
    player.ySpeed += ACCELERATION
    if player.ySpeed > 20: # et on la limite à 20 maximum
        player.ySpeed = 20
    if player.rect.y > SCREEN_SIZE[1] - PLAYER_HEIGHT: # Si jamais le joueur arrive en bas de l'écran
        pass
    player.movement[1] += player.ySpeed # On ajoute la vitesse à la position à chaque frame (pour que sa position en y soit polynômiale en fonction du temps)

    player.rect, collisions = move(player.rect, player.movement, platformHitboxes)
    player.movement[1] = 0
    if collisions['bottom']: # S'il y a eu une collision en bas, on réinitialise toutes les variables de joueurs liées au saut
        player.ySpeed = 0
        player.airTime = 0
        player.onGround = True
    else:
        player.airTime += 1

    display(scroll)

    clock.tick(MAX_FPS)

pygame.quit()