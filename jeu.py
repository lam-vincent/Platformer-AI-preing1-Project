# Sprites du chevalier réalisées par Luiz Melo
# https://assetstore.unity.com/packages/2d/characters/hero-knight-167779

import pygame, sys, math, random, perlin_noise

# Constantes
SCREEN_SIZE = (700, 500)
CHUNK_SIZE = 8
BLOCK_SIZE = 48

DARK_GREY = (35, 39, 42)

PLAYER_WIDTH = 47
PLAYER_HEIGHT = 65
JUMP_HEIGHT = 115
ACCELERATION = 0.3

MAX_FPS = 60
ANIMATION_FPS = MAX_FPS // 5
ANIMATION_REFRESH_RATE = MAX_FPS // ANIMATION_FPS

trueCameraPos = [0, 0] # Variable globale pour la position de la caméra
seed = random.randint(0, 1 << 25)
print("Seed =", seed)
gameMap = {} # Variable globale pour la map

score = 0 # Le score de la partie
previousSecond = -1 # On aura besoin d'une variable hors de la boucle pour compter les secondes
xMax = 0 # On aura besoin de connaître la position en x maximale que le joueur a atteint

# Initialisation
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Jeu de plateforme")
clock = pygame.time.Clock()

# Chargement des sprites
def loadKnightSprites(spriteName, spriteCount): # du joueur
    spriteList = []
    spriteTemplate = "assets/knight/{0}/{0}_{1!s}.png"
    for i in range(spriteCount):
        spriteList.append(pygame.image.load(spriteTemplate.format(spriteName, i)))

    return spriteList

idleSprites = loadKnightSprites("idle", 11)
walkSprites = loadKnightSprites("run", 8)
jumpSprites = loadKnightSprites("jump", 3)
fallSprites = loadKnightSprites("fall", 3)

def loadPlatformSprites(spriteName): # des plateformes
    spriteTemplate = "assets/platform/{0}.png"
    return pygame.image.load(spriteTemplate.format(spriteName))

platformSprites = {1: loadPlatformSprites("platform"), 2: loadPlatformSprites("underPlatform")}

# Fonctions utilisées dans le fonctionnement du jeu
def generateChunk(x, y):
    chunkData = []
    for yPos in range(CHUNK_SIZE): # On passe dans chaque y et x d'un chunk
        for xPos in range(CHUNK_SIZE):
            platformX = x * CHUNK_SIZE + xPos # On multiplie par CHUNK_SIZE pour arriver aux coordonnées du bloc ciblé (pas du pixel).
            platformY = y * CHUNK_SIZE + yPos
            tileType = 0
            if platformX == -1: # On veut créer un mur invisible à gauche
                tileType = 1
                chunkData.append([[platformX, platformY], tileType])
            else:
                noise = perlin_noise.PerlinNoise(seed = seed)
                # Les facteurs platformFactor et holeFactor ne doivent pas aller au-delà de 3 ou la génération serait vraiment mauvaise
                platformFactor = 9 # platformFactor correspond à la dispersion des plateformes : plus il est élevé, plus les plateformes iront loin en haut et en bas
                platformPrng = platformFactor ** 0.5 * -12 * noise(platformX/10) // 1 
                holeFactor = 1 # holeFactor correspond à la présence de trous : plus il est élevé, plus il y a de trous
                holePrng = math.floor(1/(holeFactor ** 2.5) * -100 * noise(platformX/10)) + 1
                if holePrng != 0:
                    if platformY > platformPrng:
                        tileType = 2
                    elif platformY == platformPrng:
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
        self.rect = pygame.Rect(350, -500, PLAYER_WIDTH, PLAYER_HEIGHT)

        # Vitesse verticale, mouvement du joueur
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
def display(cameraPos):
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
    if not player.onGround:
        if player.ySpeed <= 0:
            usedSprites = jumpSprites
            usedCount = player.jumpCount
        else:
            usedSprites = fallSprites
            usedCount = player.fallCount
    elif player.movement[0] == 0:
        usedSprites = idleSprites # On utilise une variable qu'on fera varier selon les cas, pour éviter de réécrire la fonction qu'on va appeler plusieurs fois
        usedCount = player.idleCount
    else:
        usedSprites = walkSprites 
        usedCount = player.walkCount

    # Affichage des sprites, on inverse la sprite s'il regarde à gauche
    if player.movement[0] < 0 or player.lastDirection == "left": # S'il va vers la gauche ou regarde vers la gauche
        screen.blit(pygame.transform.flip(usedSprites[usedCount // ANIMATION_REFRESH_RATE], True, False), (player.rect.x - cameraPos[0], player.rect.y - cameraPos[1])) # Divison euclidienne par 5 pour qu'il y ait une sprite toutes les 5 frames, soit un framerate d'animation à 12FPS (60 / 5)
    else:
        screen.blit(usedSprites[usedCount // ANIMATION_REFRESH_RATE], (player.rect.x - cameraPos[0], player.rect.y - cameraPos[1]))

    # On ajoute 1 au compteur de frame
    if not player.onGround:
        if player.ySpeed <= 0:
            player.jumpCount += 1
        else:
            player.fallCount += 1
    elif player.movement[0] == 0:
        player.idleCount += 1 
    else:
        player.walkCount += 1

    # Affichage des plateformes
    for y in range(math.ceil(SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2): # Ces math.ceil() permettent de savoir combien au plus de chunks en y et en x
        for x in range(math.ceil(SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2): # seront affichés simultanément à l'écran
            chunkX = x - 1 + int(round(cameraPos[0]/(CHUNK_SIZE * BLOCK_SIZE)))
            chunkY = y - 1 + int(round(cameraPos[1]/(CHUNK_SIZE * BLOCK_SIZE)))
            targetChunk = str(chunkX) + ";" + str(chunkY)
            for platform in gameMap[targetChunk]:
                screen.blit(platformSprites[platform[1]], (platform[0][0] * BLOCK_SIZE - cameraPos[0], platform[0][1] * BLOCK_SIZE - cameraPos[1]))

    # Affichage du score


    pygame.display.flip()

# Boucle de jeu
running = True
while running:

    # Camera
    tempTrueCameraPosX = (player.rect.x - trueCameraPos[0] - (SCREEN_SIZE[0] // 2 - PLAYER_WIDTH // 2))/20
    trueCameraPos[0] += tempTrueCameraPosX
    if trueCameraPos[0] < 0: # On ne veut pas que la caméra aille trop sur la gauche
        trueCameraPos[0] -= tempTrueCameraPosX
    temptrueCameraPosY = (player.rect.y - trueCameraPos[1] - (SCREEN_SIZE[1] // 2 - PLAYER_HEIGHT // 2))/20
    trueCameraPos[1] += temptrueCameraPosY
    if trueCameraPos[1] > 0: # On ne veut pas que la caméra aille trop bas
        trueCameraPos[1] -= temptrueCameraPosY
    cameraPos = trueCameraPos.copy()
    cameraPos[0] = int(cameraPos[0])
    cameraPos[1] = int(cameraPos[1])

    # Plateformes & Chunks
    platformHitboxes = []
    for y in range(math.ceil(SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
        for x in range(math.ceil(SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2):
            chunkX = x - 1 + int(round(cameraPos[0]/(CHUNK_SIZE * BLOCK_SIZE)))
            chunkY = y - 1 + int(round(cameraPos[1]/(CHUNK_SIZE * BLOCK_SIZE)))
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

            if event.key == pygame.K_SPACE and player.onGround and player.airTime < 6: # Si le joueur est dans les airs depuis moins de 6 frames, il peut quand même sauter
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
    if collisions['bottom']: # S'il y a eu une collision en bas, on réinitialise toutes les variables de joueurs liées au saut
        player.ySpeed = 0
        player.airTime = 0
        player.onGround = True
    else:
        player.airTime += 1
        if player.airTime >= 6: # Si le joueur a dépassé son temps de saut, on le considère dans les airs (ceci permet aussi de fixer un bug graphique)
            player.onGround = False

    player.movement[1] = 0

    # Calcul du score
    if player.ySpeed < 20:
        seconds = pygame.time.get_ticks() // (1000/(MAX_FPS/60))

        if previousSecond + 1 <= seconds:
            previousSecond += 1
            if score - 1 > 0:
                score -= 1

        if xMax < player.rect.x:
            xMax = player.rect.x
            score += 0.1

        print(int(score))

    display(cameraPos)

    clock.tick(MAX_FPS)

pygame.quit()