# Sprites du chevalier réalisées par Luiz Melo
# https://assetstore.unity.com/packages/2d/characters/hero-knight-167779

import pygame, sys, math, random, perlin_noise

# Constantes
SCREEN_SIZE = (700, 500) # Le jeu est généré en 700 x 500
ACTUAL_SCREEN_SIZE = (700, 500) # mais on peut afficher le jeu dans une plus grande fenêtre
CHUNK_SIZE = 8
BLOCK_SIZE = 48

ARROW_SIZE = 40

DARK_GREY = (35, 39, 42)
DARK_DARK_GREY = (20, 24, 27)

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
noise = perlin_noise.PerlinNoise(seed = seed) # Bruit de Perlin pour la génération aléatoire de la map
gameMap = {} # Variable globale pour la map

score = 0 # Le score de la partie
previousSecond = -1 # On aura besoin d'une variable hors de la boucle pour compter les secondes
xMax = 0 # On aura besoin de connaître la position en x maximale que le joueur a atteint

# Initialisation
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
window = pygame.display.set_mode(ACTUAL_SCREEN_SIZE)
pygame.display.set_caption("Jeu de plateforme")
clock = pygame.time.Clock()
font = pygame.font.Font(None, math.floor(44 * ((ACTUAL_SCREEN_SIZE[0] + ACTUAL_SCREEN_SIZE[1])/2)/((700 + 500)/2)))

mixer = pygame.mixer
mixer.Channel(0).play(mixer.Sound('sounds/music.wav'), loops = -1)

# Fonction pour jouer des sons
def sound(name):
    if not player.dead: # On ne veut pas qu'un son se joue si le joueur est dans l'écran de mort
        path = "sounds/{0}.wav"
        mixer.find_channel().play(mixer.Sound(path.format(name)))

def deathSound():
    mixer.set_num_channels(0)
    mixer.set_num_channels(1)
    mixer.Channel(0).play(mixer.Sound('sounds/death2.wav'))
    mixer.fadeout(8000)

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
dashSprites = loadKnightSprites("dash", 7)
deathSprites = loadKnightSprites("death", 15)

def loadPlatformSprites(spriteName): # des plateformes
    spriteTemplate = "assets/platform/{0}.png"
    return pygame.image.load(spriteTemplate.format(spriteName))

platformSprites = {1: loadPlatformSprites("platform"), 2: loadPlatformSprites("underPlatform")}

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
        platformX = x * CHUNK_SIZE + xPos # On multiplie par CHUNK_SIZE pour arriver aux coordonnées du bloc ciblé (pas du pixel).
        tileType = 0
        # Les facteurs platformFactor et holeFactor ne doivent pas aller au-delà de 3 ou la génération serait vraiment mauvaise
        platformFactor = 1 + xMax / 7000 # platformFactor correspond à la dispersion des plateformes : plus il est élevé, plus les plateformes iront loin en haut et en bas
        platformPrng = platformFactor ** 0.5 * -12 * noise(platformX/10) // 1 #PRNG pour Pseudo Random Number Generator
        holeFactor = 1 + xMax / 7000 # holeFactor correspond à la présence de trous : plus il est élevé, plus il y a de trous
        holePrng = math.floor(1/(holeFactor ** 2.5) * -100 * noise(platformX/10)) + 1

        for yPos in range(CHUNK_SIZE): # On passe dans chaque y et x d'un chunk
            platformY = y * CHUNK_SIZE + yPos

            if platformX == -1: # On veut créer un mur invisible à gauche
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
    def __init__(self, posX, posY):
        # Hitbox du joueur (au passage on récupèrera les coordonnées du rect pour récupérer les coordonnées du joueur)
        self.rect = pygame.Rect(posX, posY, PLAYER_WIDTH, PLAYER_HEIGHT)

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

player = Player(350, -500)

# Fonction d'affichage à l'écran
def display(cameraPos):
    global player # On global player pour modifier (uniquement les compteurs de frames)

    if player.dead:
        screen.fill(DARK_DARK_GREY)
        if not player.deathAnimationPlayed:
            if player.deathCount > 14 * (ANIMATION_REFRESH_RATE * 2):
                player.deathAnimationPlayed = True
            else :
                screen.blit(deathSprites[player.deathCount // (ANIMATION_REFRESH_RATE * 2)], ((ACTUAL_SCREEN_SIZE[0] - PLAYER_WIDTH)/2, (ACTUAL_SCREEN_SIZE[1] - PLAYER_HEIGHT)/2))
                player.deathCount += 1
        else:
            # Ajouter un temps de pause
            texte = "Score : " + str(int(score))
            text = font.render(texte, True, (255, 255, 255))
            textSize = font.size(texte)
            screen.blit(text, ((ACTUAL_SCREEN_SIZE[0] - textSize[0])/2, (ACTUAL_SCREEN_SIZE[1] - textSize[1])/2))
    else:
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

        if player.xDashCD >= 48 * (MAX_FPS // 60): # Traitement à part des sprites de la phase de dash horizontale où le joueur prend de la vitesse
            if player.movement[0] < 0 or player.lastDirection == "left": # S'il va vers la gauche ou regarde vers la gauche
                screen.blit(pygame.transform.flip(dashSprites[math.floor((MAX_FPS - player.xDashCD) / (MAX_FPS / 30))], True, False), (player.rect.x - cameraPos[0], player.rect.y - cameraPos[1])) # Divison euclidienne par 2 pour que les sprites de dash rentrent bien dans les temps
            else:
                screen.blit(dashSprites[math.floor((MAX_FPS - player.xDashCD) / (MAX_FPS / 30))], (player.rect.x - cameraPos[0], player.rect.y - cameraPos[1]))
        elif not player.onGround and player.yDashCD > 0 and player.ySpeed <= 0:
            if player.yDashCount + 2 <= 12:
                player.yDashCount += 2
            if player.movement[0] < 0 or player.lastDirection == "left":
                screen.blit(pygame.transform.flip(dashSprites[player.yDashCount // 2], True, False), (player.rect.x - cameraPos[0], player.rect.y - cameraPos[1])) # Divison euclidienne par 2 pour que les sprites de dash rentrent bien dans les temps
            else:
                screen.blit(dashSprites[player.yDashCount // 2], (player.rect.x - cameraPos[0], player.rect.y - cameraPos[1]))
        else:
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
        for y in range(math.ceil(ACTUAL_SCREEN_SIZE[1] / (BLOCK_SIZE * CHUNK_SIZE)) + 2): # Ces math.ceil() permettent de savoir combien au plus de chunks en y et en x
            for x in range(math.ceil(ACTUAL_SCREEN_SIZE[0] / (BLOCK_SIZE * CHUNK_SIZE)) + 2): # seront affichés simultanément à l'écran
                chunkX = x - 1 + int(round(cameraPos[0]/(CHUNK_SIZE * BLOCK_SIZE)))
                chunkY = y - 1 + int(round(cameraPos[1]/(CHUNK_SIZE * BLOCK_SIZE)))
                targetChunk = str(chunkX) + ";" + str(chunkY)
                for platform in gameMap[targetChunk]:
                    if platform[1] > 0:
                        screen.blit(platformSprites[platform[1]], (platform[0][0] * BLOCK_SIZE - cameraPos[0], platform[0][1] * BLOCK_SIZE - cameraPos[1]))

        # Affichage du compte à rebours de mort du joueur
        colorRect = pygame.Surface((2, 2))
        pygame.draw.line(colorRect, (222, 71, 71), (0, 0), (0, 1))
        difference = (MAX_FPS * 25 - player.deathCountdown) / (MAX_FPS * 25) # On fait varier un "coefficient" de 0 à 1 pour maintenir une couleur cohérente sur la barre
        pygame.draw.line(colorRect, (104 + math.floor((222 - 104) * difference), 222 - math.floor((222 - 71) * difference), 71), (1, 0), (1, 1))
        rectWidth = math.floor(ACTUAL_SCREEN_SIZE[0] // 2 * (player.deathCountdown / (MAX_FPS * 25)))
        if rectWidth < 0:
            rectWidth = 0
        rectHeight = ACTUAL_SCREEN_SIZE[1] // 50
        colorRect = pygame.transform.smoothscale(colorRect, (rectWidth, rectHeight))
        screen.blit(colorRect, ((ACTUAL_SCREEN_SIZE[0] - rectWidth) // 2, ACTUAL_SCREEN_SIZE[1] // 10))

        # Affichage des flèches de dash
        arrowDisplayY = ACTUAL_SCREEN_SIZE[1] // 2 + 100
        coordsLeft = ((ACTUAL_SCREEN_SIZE[0] - ARROW_SIZE) // 2 - ARROW_SIZE, arrowDisplayY)
        coordsRight = ((ACTUAL_SCREEN_SIZE[0] + ARROW_SIZE) // 2, arrowDisplayY)
        if not player.canActivateArrows[0] or player.onGround:
            screen.blit(rightArrow[0], coordsLeft)
        else:
            screen.blit(rightArrow[1], coordsLeft)
        if not player.canActivateArrows[1] or player.onGround:
            screen.blit(upArrow[0], coordsRight)
        else:
            screen.blit(upArrow[1], coordsRight)


    window.blit(pygame.transform.scale(screen, ACTUAL_SCREEN_SIZE), (0, 0)) # On affiche l'écran à la taille indiquée
    pygame.display.flip()

# Boucle de jeu
running = True
while running:

    # Camera
    tempTrueCameraPosX = (player.rect.x - trueCameraPos[0] - (ACTUAL_SCREEN_SIZE[0] // 2 - PLAYER_WIDTH // 2))/20
    trueCameraPos[0] += tempTrueCameraPosX
    if trueCameraPos[0] < 0: # On ne veut pas que la caméra aille trop sur la gauche
        trueCameraPos[0] -= tempTrueCameraPosX
    temptrueCameraPosY = (player.rect.y - trueCameraPos[1] - (ACTUAL_SCREEN_SIZE[1] // 2 - PLAYER_HEIGHT // 2))/20
    trueCameraPos[1] += temptrueCameraPosY
    if trueCameraPos[1] > 0: # On ne veut pas que la caméra aille trop bas
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
    if player.ySpeed > 20: # et on la limite à 20 maximum
        player.ySpeed = 20
    if player.rect.y > SCREEN_SIZE[1] - PLAYER_HEIGHT: # Si jamais le joueur arrive en bas de l'écran
        if not player.deathSoundPlayed:
            deathSound()
            player.deathSoundPlayed = True
        player.dead = True
        player.movement[0] = 0

    # Traitement du cooldown du dash (on le fait ici pour mettre ySpeed à 0 s'il est en train de dash)
    if player.xDashCD > 0:
        player.xDashCD -= 1
        if player.xDashCD <= MAX_FPS/1.3: # Si le joueur est dans la phase "descendante" du dash, on veut que sa vitesse revienne à la normale
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

    player.movement[1] += player.ySpeed # On ajoute la vitesse à la position à chaque frame (pour que sa position en y soit polynômiale en fonction du temps)

    player.rect, collisions = move(player.rect, player.movement, platformHitboxes)
    if collisions['bottom']: # S'il y a eu une collision en bas, on réinitialise toutes les variables de joueurs liées au saut et on lui redonne son dash
        player.ySpeed = 0
        player.airTime = 0
        player.onGround = True
        player.xDashCD = 0
        player.canXDash = True
        player.canActivateArrows = [True, True]
    else:
        player.airTime += 1
        if player.airTime >= 6: # Si le joueur a dépassé son temps de saut, on le considère dans les airs (ceci permet aussi de fixer un bug graphique)
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

        if xMax > 500: # On ne veut pas faire commencer le compte à rebours trop tôt
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