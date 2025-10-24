import pgzrun
import sys

# ==================================
# 1. CONSTANTES E CONFIGURAÇÃO GLOBAL
# ==================================

# ---------------- Window (Increased Size) ----------------
WIDTH = 1200
HEIGHT = 700
GROUND_Y = 600

# ---------------- Physics ----------------
GRAVITY = 0.5
JUMP_STRENGTH = -11
PLAYER_SPEED = 2
COLLISION_RANGE = 20
ENEMY_SPEED = 0.5
COLLIDER_WIDTH_FACTOR = 0.6

# ---------------- UI Constants for Home Screen ----------------
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 60
BUTTON_COLOR = (255, 165, 0)
BUTTON_TEXT_COLOR = (0, 0, 0)
TITLE_FONT_SIZE = 80
MENU_FONT_SIZE = 40

START_BUTTON_RECT = Rect((WIDTH/2 - BUTTON_WIDTH/2, HEIGHT/2 - 50), (BUTTON_WIDTH, BUTTON_HEIGHT))
MUSIC_BUTTON_RECT = Rect((WIDTH/2 - BUTTON_WIDTH/2, HEIGHT/2 + 30), (BUTTON_WIDTH, BUTTON_HEIGHT))
EXIT_BUTTON_RECT = Rect((WIDTH/2 - BUTTON_WIDTH/2, HEIGHT/2 + 110), (BUTTON_WIDTH, BUTTON_HEIGHT))

# ---------------- Animation Assets ----------------

PLAYER_ANIMATIONS = {
    "stop": ["besouro/besouro_1.1", "besouro/besouro_1.2", "besouro/besouro_1.3"],
    "right": ["besouro/besouro_2.1", "besouro/besouro_2.2", "besouro/besouro_2.3"],
    "left": ["besouro/besouro_3.1", "besouro/besouro_3.2", "besouro/besouro_3.3"],
    "down": ["besouro/besouro_4.1", "besouro/besouro_4.2"],
    "jump_up": ["besouro/besouro_5.1"],
    "fall": ["besouro/besouro_5.2"]
}

PLAYER_ANIMATION_SPEEDS = {
    "stop": 15,
    "down": 15,
    "right": 5,
    "left": 5,
    "jump_up": 5,
    "fall": 5
}

ZOMBIE_ANIMATIONS = {
    "right": [f"zombie/character_zombie_walk{i}" for i in range(7)],
    "left": [f"zombie/character_zombie_walk{i}" for i in range(8, 15)],
}
ZOMBIE_FRAME_COUNT = len(ZOMBIE_ANIMATIONS["right"])

# ==================================
# 2. GLOBAL STATE (Actors and Variables)
# ==================================

player = Actor(PLAYER_ANIMATIONS["stop"][0], (80, GROUND_Y))

platforms = [
    Rect((200, GROUND_Y - 50), (150, 10)),      
    Rect((450, GROUND_Y - 150), (250, 10)),    
    Rect((750, GROUND_Y - 250), (200, 10)), 
    Rect((950, GROUND_Y - 100), (200, 10)),
    Rect((100, GROUND_Y - 250), (100, 10))
]

_TEMP_ZOMBIE_ACTOR = Actor(ZOMBIE_ANIMATIONS["left"][0], (0, 0))
ZOMBIE_HEIGHT = _TEMP_ZOMBIE_ACTOR.height

_ZOMBIE_PATROL_SPECS = [
    {"surface_y": GROUND_Y, "min_x": 0, "max_x": 400}, 
    {"surface_y": platforms[0].top, "min_x": platforms[0].left, "max_x": platforms[0].right},
    {"surface_y": platforms[1].top, "min_x": platforms[1].left, "max_x": platforms[1].right},
    {"surface_y": platforms[3].top, "min_x": platforms[3].left, "max_x": platforms[3].right},
]

def initialize_zombie_data():
    global zombies, _ENEMY_STATES, _ZOMBIE_DATA
    
    _ZOMBIE_DATA = []
    for spec in _ZOMBIE_PATROL_SPECS:
        center_y = spec["surface_y"] - ZOMBIE_HEIGHT / 2
        center_x = (spec["min_x"] + spec["max_x"]) / 2
        
        _ZOMBIE_DATA.append({
            "pos": (center_x, center_y),
            "patrol_min": spec["min_x"],
            "patrol_max": spec["max_x"],
        })

    zombies = [Actor(ZOMBIE_ANIMATIONS["left"][0], data["pos"]) for data in _ZOMBIE_DATA]
    _ENEMY_STATES = [
        {"direction": 'left', "animation_frame": 0, "animation_timer": 0} for _ in _ZOMBIE_DATA
    ]
    
initialize_zombie_data() 

_PLAYER_STATE = {
    "velocity_y": 0.0,
    "is_jumping": False,
    "current_animation": "stop",
    "animation_frame": 0,
    "animation_timer": 0,
}

_GAME_STATE = {
    "score": 0,
    "current_screen": "HOME",
    "is_music_on": True,
    "objective": "Esmague todos os zumbis pulando em suas cabeças! Marque 5 pontos por zumbi.",
}


# ==================================
# 3. CORE LOGIC FUNCTIONS (Single Responsibility)
# ==================================

def handle_input(player, state):
    """Lida com a entrada do teclado para movimento horizontal e intenção de pulo."""
    moving_state = "stop"

    if _GAME_STATE["current_screen"] != "PLAYING":
        return moving_state

    if keyboard.right:
        player.x += PLAYER_SPEED
        moving_state = "right"
    if keyboard.left:
        player.x -= PLAYER_SPEED
        moving_state = "left"

    player.x = max(player.width / 2, min(WIDTH - player.width / 2, player.x))

    if keyboard.up and not state["is_jumping"]:
        state["velocity_y"] = JUMP_STRENGTH
        state["is_jumping"] = True

    return moving_state

def apply_physics(player, state):
    """Aplica a gravidade à velocidade vertical e atualiza a posição."""
    state["velocity_y"] += GRAVITY
    player.y += state["velocity_y"]

def resolve_collisions(player, state, platforms):
    """Verifica colisões com o chão e plataformas e resolve a posição."""
    standing = False
    previous_bottom = player.bottom - state["velocity_y"]

    for plat in platforms:
        if previous_bottom <= plat.top <= player.bottom:
            if player.right > plat.left and player.left < plat.right:
                player.bottom = plat.top
                state["velocity_y"] = 0
                state["is_jumping"] = False
                standing = True
                break

    if not standing and player.bottom >= GROUND_Y:
        player.bottom = GROUND_Y
        state["velocity_y"] = 0
        state["is_jumping"] = False
        standing = True

    if not standing:
        state["is_jumping"] = True

def update_player_animation(player, state, moving_state):
    """Determina e progride a animação do jogador."""
    
    new_state = "stop"
    if state["is_jumping"]:
        new_state = "jump_up" if state["velocity_y"] < 0 else "fall"
    elif keyboard.down:
        new_state = "down"
    elif moving_state in ["right", "left"]:
        new_state = moving_state
    
    if new_state != state["current_animation"]:
        state["animation_frame"] = 0
        state["animation_timer"] = 0
        state["current_animation"] = new_state
    
    state["animation_timer"] += 1
    frames = PLAYER_ANIMATIONS[new_state]
    speed = PLAYER_ANIMATION_SPEEDS.get(new_state, 5)

    if state["animation_timer"] >= speed:
        state["animation_timer"] = 0
        state["animation_frame"] = (state["animation_frame"] + 1) % len(frames)
        player.image = frames[state["animation_frame"]]

def update_zombie_movement_and_animation():
    """Atualiza a posição, direção e quadro de animação de todos os zumbis, confinados às suas áreas de patrulha."""
    global zombies, _ENEMY_STATES, _ZOMBIE_DATA 

    for i, zombie in enumerate(zombies):
        state = _ENEMY_STATES[i]
        data = _ZOMBIE_DATA[i] 

        direction_factor = 1 if state["direction"] == 'right' else -1
        next_x = zombie.x + ENEMY_SPEED * direction_factor
        
        if state["direction"] == 'right' and next_x >= data["patrol_max"] - zombie.width / 2:
            state["direction"] = 'left'
            direction_factor = -1
        elif state["direction"] == 'left' and next_x <= data["patrol_min"] + zombie.width / 2:
            state["direction"] = 'right'
            direction_factor = 1

        zombie.x += ENEMY_SPEED * direction_factor

        state["animation_timer"] += 1
        frames = ZOMBIE_ANIMATIONS[state["direction"]]
        
        if state["animation_timer"] >= 5:
            state["animation_timer"] = 0
            state["animation_frame"] = (state["animation_frame"] + 1) % len(frames)
            zombie.image = frames[state["animation_frame"]]

def check_game_state():
    """Verifica condições de vitória/derrota e derrota de zumbis, modificando listas globais."""
    global _GAME_STATE, zombies, _ENEMY_STATES, _ZOMBIE_DATA 

    if _GAME_STATE["current_screen"] in ["GAME_OVER", "GAME_WON"]:
        return

    zombies_to_remove_indices = []
    
    
    player_collider_width = player.width * COLLIDER_WIDTH_FACTOR
    player_collider = Rect((0, 0), (player_collider_width, player.height))
    player_collider.center = player.center

    for i, zombie in enumerate(zombies):
        
        zombie_collider_width = zombie.width * COLLIDER_WIDTH_FACTOR
        zombie_collider = Rect((0, 0), (zombie_collider_width, zombie.height))
        zombie_collider.center = zombie.center
        
        if zombie_collider.colliderect(player_collider):
           
            if _PLAYER_STATE["velocity_y"] > 0 and player.bottom < zombie.centery: 
                sounds.zombie_damage.play()
                _GAME_STATE["score"] += 5
                zombies_to_remove_indices.append(i)
                _PLAYER_STATE["velocity_y"] = -7             
            else:
                sounds.player_damage.play()
                player.image = "besouro/besouro_6"
                _GAME_STATE["current_screen"] = "GAME_OVER"
                break

    if _GAME_STATE["current_screen"] == "GAME_OVER":
        try:
            music.stop()
        except NameError:
            pass
        return

    for index in sorted(zombies_to_remove_indices, reverse=True):
        zombies.pop(index)
        _ENEMY_STATES.pop(index)
        _ZOMBIE_DATA.pop(index) 

    if not zombies:
        _GAME_STATE["current_screen"] = "GAME_WON"

def music_loop():
    """Garante que a música de fundo esteja tocando com base no estado."""
    if not _GAME_STATE["is_music_on"]:
        try:
            music.stop()
        except NameError:
            pass
        return

    try:
        if not music.is_playing('angola'):
            music.play('angola')
        music.fadeout(100)
    except NameError:
        pass

def reset_game():
    """Redefine todo o estado do jogo e as posições dos atores."""
    global player, zombies, _PLAYER_STATE, _ENEMY_STATES, _ZOMBIE_DATA

    player.pos = (80, GROUND_Y)
    _PLAYER_STATE["velocity_y"] = 0.0
    _PLAYER_STATE["is_jumping"] = False
    _PLAYER_STATE["current_animation"] = "stop"
    _PLAYER_STATE["animation_frame"] = 0
    _PLAYER_STATE["animation_timer"] = 0

    initialize_zombie_data()

    _GAME_STATE["score"] = 0

    music_loop()

def draw_home_screen():
    """Desenha o menu principal com as opções Iniciar, Música e Sair."""
    screen.clear()
    screen.fill((50, 50, 70))

    screen.draw.text(
        "PLATAFORMA ESMAGA-ZUMBIS", 
        center=(WIDTH/2, HEIGHT/2 - 200), 
        color=(255, 255, 255), 
        fontsize=TITLE_FONT_SIZE
    )
    screen.draw.text(
        "Use as setas para Mover, CIMA para Pular | R para Reiniciar", 
        center=(WIDTH/2, HEIGHT/2 - 130), 
        color=(200, 200, 200), 
        fontsize=MENU_FONT_SIZE - 10
    )
    
    screen.draw.filled_rect(START_BUTTON_RECT, BUTTON_COLOR)
    screen.draw.text(
        "INICIAR JOGO", 
        center=START_BUTTON_RECT.center, 
        color=BUTTON_TEXT_COLOR, 
        fontsize=MENU_FONT_SIZE
    )

    music_text = f"MÚSICA: {'LIGADA' if _GAME_STATE['is_music_on'] else 'DESLIGADA'}"
    screen.draw.filled_rect(MUSIC_BUTTON_RECT, BUTTON_COLOR)
    screen.draw.text(
        music_text, 
        center=MUSIC_BUTTON_RECT.center, 
        color=BUTTON_TEXT_COLOR, 
        fontsize=MENU_FONT_SIZE
    )

    screen.draw.filled_rect(EXIT_BUTTON_RECT, BUTTON_COLOR)
    screen.draw.text(
        "SAIR", 
        center=EXIT_BUTTON_RECT.center, 
        color=BUTTON_TEXT_COLOR, 
        fontsize=MENU_FONT_SIZE
    )


# ==================================
# 4. PGZERO HOOKS
# ==================================

def update():
    """Hook de atualização principal do Pgzero."""
    music_loop()

    if _GAME_STATE["current_screen"] != "PLAYING":
        return

    moving_state = handle_input(player, _PLAYER_STATE)

    apply_physics(player, _PLAYER_STATE)

    resolve_collisions(player, _PLAYER_STATE, platforms)

    update_player_animation(player, _PLAYER_STATE, moving_state)
    update_zombie_movement_and_animation()

    check_game_state()

def on_mouse_down(pos):
    """Lida com cliques do mouse para navegação no menu."""
    if _GAME_STATE["current_screen"] == "HOME":
        if START_BUTTON_RECT.collidepoint(pos):
            _GAME_STATE["current_screen"] = "PLAYING"
            reset_game()
        
        elif MUSIC_BUTTON_RECT.collidepoint(pos):
            _GAME_STATE["is_music_on"] = not _GAME_STATE["is_music_on"]
            music_loop()

        elif EXIT_BUTTON_RECT.collidepoint(pos):
            sys.exit()

def on_key_down(key):
    """Hook de tecla pressionada do Pgzero para lidar com reinício."""
    if _GAME_STATE["current_screen"] in ["GAME_OVER", "GAME_WON"] and key == keys.R:
        _GAME_STATE["current_screen"] = "PLAYING"
        reset_game()
    elif _GAME_STATE["current_screen"] in ["GAME_OVER", "GAME_WON"] and key == keys.ESCAPE:
        _GAME_STATE["current_screen"] = "HOME"

def draw():
    """Hook de desenho principal do Pgzero."""
    
    if _GAME_STATE["current_screen"] == "HOME":
        draw_home_screen()
        return
        
    screen.clear()
    screen.fill((135, 206, 250))

    screen.draw.filled_rect(Rect((0, GROUND_Y), (WIDTH, HEIGHT - GROUND_Y)), (50, 200, 50))

    for plat in platforms:
        screen.draw.filled_rect(plat, (150, 75, 0))

    player.draw()
    for zombie in zombies:
        zombie.draw()

    screen.draw.text(f"PONTUAÇÃO: {_GAME_STATE['score']}", (20, 10), color="black", fontsize=40)
    screen.draw.text(
        f"Objetivo: {_GAME_STATE['objective']}",
        (20, 50),
        color="black",
        fontsize=25
    )

    if _GAME_STATE["current_screen"] == "GAME_OVER":
        screen.draw.text("FIM DE JOGO!", center=(WIDTH/2, HEIGHT/2), color="red", fontsize=100)
        screen.draw.text("Pressione R para Reiniciar ou ESC para o Menu", center=(WIDTH/2, HEIGHT/2 + 80), color="white", fontsize=50)
    elif _GAME_STATE["current_screen"] == "GAME_WON":
        screen.draw.text(f"VOCÊ VENCEU! Pontuação Final: {_GAME_STATE['score']}", center=(WIDTH/2, HEIGHT/2), color="green", fontsize=100)
        screen.draw.text("Pressione R para Reiniciar ou ESC para o Menu", center=(WIDTH/2, HEIGHT/2 + 80), color="white", fontsize=50)


pgzrun.go()
