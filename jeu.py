# Sprites du chevalier réalisées par Luiz Melo
# https://assetstore.unity.com/packages/2d/characters/hero-knight-167779

import pygame, sys

            # ------------------ #
            #     Constantes     #
            # ------------------ #
SCREEN_SIZE = (700, 500)

DARK_GREY = (35, 39, 42)
WHITE = (255, 255, 255)

PLAYER_WIDTH = 47
PLAYER_HEIGHT = 65

MAX_FPS = 60
ANIMATION_FPS = 12
ANIMATION_REFRESH_RATE = MAX_FPS // ANIMATION_FPS
            # ------------------ #
            #   Initialisation   #
            # ------------------ #
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE) # Définition de la fenêtre de jeu
pygame.display.set_caption("Jeu")
clock = pygame.time.Clock()

# Chargement des sprites dans des listes
player_idle = []
player_walk_right = []
player_jump = []
player_fall = []
for i in range(11):
    player_idle.append(pygame.image.load("assets/knight/idle/idle_" + str(i) + ".png"))
for i in range(8):
    player_walk_right.append(pygame.image.load("assets/knight/run/run_" + str(i) + ".png"))
for i in range(3):
    player_jump.append(pygame.image.load("assets/knight/jump/jump_" + str(i) + ".png"))
for i in range(3):
    player_fall.append(pygame.image.load("assets/knight/fall/fall_" + str(i) + ".png"))

# Position, vitesse du joueur
player_x = 300
player_y = 0
player_speed = 0
player_acceleration = 0.2

# Compteur pour les frames d'animation, et booléens pour savoir où le joueur regarde (pour animer du bon côté)
player_walk_count = 0
player_idle_count = 0
player_jump_count = 0
player_fall_count = 0

player_left = False
player_right = False
player_last_direction = "right"
player_on_ground = False

# Plateformes
platforms = [
    pygame.Rect(100, 300, 400, 50),
    pygame.Rect(100, 250 ,50, 50),
    pygame.Rect(450, 250, 50, 50)
]

# Définition de la fonction pour afficher la fenêtre de jeu
def draw():
    global player_walk_count
    global player_idle_count
    global player_jump_count
    global player_fall_count

    # Background
    screen.fill(DARK_GREY)

    # Plateformes
    for p in platforms:
        pygame.draw.rect(screen, WHITE, p)
    
    # Affichage du joueur
    if player_walk_count + 1 >= 8 * ANIMATION_REFRESH_RATE: # Pour éviter d'avoir de l'index out of range et que l'animation loop correctement
        player_walk_count = 0
    if player_idle_count + 1 >= 11 * ANIMATION_REFRESH_RATE:
        player_idle_count = 0
    if player_jump_count + 1 >= 3 * ANIMATION_REFRESH_RATE:
        player_jump_count = 0
    if player_fall_count + 1 >= 3 * ANIMATION_REFRESH_RATE:
        player_fall_count = 0

    if player_left: # S'il va vers la gauche (marche ou saut)
        usedList = player_walk_right # On utilise une variable qu'on fera varier selon les cas, pour éviter de réécrire la fonction qu'on va appeler trois fois
        usedCount = player_walk_count # La même chose mais pour le compteur de /5 de frames
        if not player_on_ground: # S'il est dans les airs, on utilise la sprite du saut ou de la chute
            if player_speed <= 0:
                usedList = player_jump
                usedCount = player_jump_count
            else:
                usedList = player_fall
                usedCount = player_fall_count
        screen.blit(pygame.transform.flip(usedList[usedCount // ANIMATION_REFRESH_RATE], True, False), (player_x, player_y)) # Divison euclidienne par 5 pour qu'il y ait une sprite toutes les 5 secondes, soit un framerate d'animation à 12FPS (60 / 5) 
        
        if not player_on_ground: # Aller à 1/5 de la frame suivante
            if player_speed <= 0:
                player_jump_count += 1
            else:
                player_fall_count += 1
        else:
            player_walk_count += 1
    elif player_right: # Same mais à droite
        usedList = player_walk_right
        usedCount = player_walk_count
        if not player_on_ground:
            if player_speed <= 0:
                usedList = player_jump
                usedCount = player_jump_count
            else:
                usedList = player_fall
                usedCount = player_fall_count
        screen.blit(usedList[usedCount // ANIMATION_REFRESH_RATE], (player_x, player_y))
        
        if not player_on_ground:
            if player_speed <= 0:
                player_jump_count += 1
            else:
                player_fall_count += 1
        else:
            player_walk_count += 1
    else:
        usedList = player_idle
        usedCount = player_idle_count
        if not player_on_ground:
            if player_speed <= 0:
                usedList = player_jump
                usedCount = player_jump_count
            else:
                usedList = player_fall
                usedCount = player_fall_count
        if player_last_direction == "left": # On vérifie sa dernière direction pour éviter que la sprite se retourne subitement
            screen.blit(pygame.transform.flip(usedList[usedCount // ANIMATION_REFRESH_RATE], True, False), (player_x, player_y))
        else:
            screen.blit(usedList[usedCount // ANIMATION_REFRESH_RATE], (player_x, player_y))

        if not player_on_ground:
            if player_speed <= 0:
                player_jump_count += 1
            else:
                player_fall_count += 1
        else:
            player_idle_count += 1

    pygame.display.flip() # Afficher le tout

            # ------------------- #
            #    Boucle de jeu    #
            # ------------------- #
running = True
while running:

            # ------------------- #
            #        Input        #
            # ------------------- #

    # Quitter le jeu
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

    new_player_x = player_x
    new_player_y = player_y

    # Input de joueur
    keys = pygame.key.get_pressed()
    if keys[pygame.K_q]:
        new_player_x -= 2
        player_left = True
        player_right = False
        player_last_direction = "left"
    elif keys[pygame.K_d]:
        new_player_x += 2
        player_left = False
        player_right = True
        player_last_direction = "right"
    else:
        player_left = False
        player_right = False
        player_walk_count = 0
    
    if keys[pygame.K_SPACE] and player_on_ground:
        player_speed = -5
        player_left = False
        player_right = False
        player_walk_count = 0
        player_on_ground = False

    # Mouvement horizontal
    new_player_rect = pygame.Rect(new_player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    x_collision = False

    for p in platforms:
        if p.colliderect(new_player_rect):
            x_collision = True
            break

    if x_collision == False:
        player_x = new_player_x

    # Mouvement vertical
    player_speed += player_acceleration
    new_player_y += player_speed

    new_player_rect = pygame.Rect(player_x, new_player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    y_collision = False

    for p in platforms:
        if p.colliderect(new_player_rect):
            y_collision = True
            player_speed = 0
            if p[1] > new_player_y: # On vérifie si le joueur est juste au-dessus de la plateforme
                player_y = p[1] - PLAYER_HEIGHT # On le téléporte à la plateforme pour éviter que la vitesse soit à 0, et qu'il reprenne un peu de vitesse
                player_on_ground = True
                player_jump_count = 0
                player_fall_count = 0
            break

    if y_collision == False:
        player_y = new_player_y

    if player_y > SCREEN_SIZE[1] - PLAYER_HEIGHT:
        player_speed = -player_speed

    # Afficher la fenêtre
    draw()

    clock.tick(MAX_FPS) # Forcer 60 FPS max

# Quitter
pygame.quit()