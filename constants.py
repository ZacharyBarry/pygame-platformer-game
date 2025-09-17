# constants.py
import os

# --- Game Setup ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TITLE = "Retro Platformer Adventure"
TILE_SIZE = 16

# --- Physics ---
PLAYER_MOVE_SPEED = 3     # New constant for non-ice horizontal speed
PLAYER_ACC = .2
PLAYER_FRICTION = -.02
PLAYER_GRAVITY = 0.7
PLAYER_JUMP_STRENGTH = -10
PLAYER_DODGE_DURATION = 400
PLAYER_HIT_DURATION = 350
PLAYER_DEATH_DURATION = 600
PLAYER_INVINCIBILITY_DURATION = 1000 # <-- NEW: How long player is invincible after non-fatal hit (milliseconds)
PLAYER_FLICKER_RATE = 100 # <-- NEW: How fast player flickers when invincible (milliseconds)

# --- Health ---
PLAYER_MAX_HEALTH = 3 # <-- NEW

# --- Animation ---
PLAYER_ANIMATION_SPEED = 80
HAZARD_FLASH_SPEED = 200

# --- Colors ---
COLOR_BG = (20, 15, 25)
COLOR_TEXT = (230, 230, 230)
COLOR_TITLE = (255, 220, 0) # Used for Goal Placeholder now
COLOR_INFO = (100, 180, 255)
COLOR_WIN = (100, 255, 100)
COLOR_LOSE = (255, 100, 100)
COLOR_HAZARD_1 = (255, 0, 0)
COLOR_HAZARD_2 = (200, 0, 0)
COLOR_LEVEL = (220, 100, 255)

# --- Folders ---
# Determine the absolute path of the game's root directory
# NOTE: This assumes constants.py is in the main game directory. Adjust if needed.
GAME_FOLDER = os.path.dirname(os.path.abspath(__file__))
ASSETS_FOLDER = os.path.join(GAME_FOLDER, "assets")
IMAGE_FOLDER = os.path.join(ASSETS_FOLDER, "images")
SOUND_FOLDER = os.path.join(ASSETS_FOLDER, "sounds")
MUSIC_FOLDER = os.path.join(ASSETS_FOLDER, "music")
FONT_FOLDER = os.path.join(ASSETS_FOLDER, "fonts")

# --- Asset Filenames ---
# Player Animations
IMG_PLAYER_IDLE = [f"player_idle_{i}.png" for i in range(4)]
IMG_PLAYER_WALK = [f"player_walk_{i:02d}.png" for i in range(16)]
IMG_PLAYER_DODGE = [f"player_roll_{i}.png" for i in range(8)]
IMG_PLAYER_HIT = [f"player_hit_{i}.png" for i in range(4)]
IMG_PLAYER_DEATH = [f"player_death_{i}.png" for i in range(4)]
IMG_PLAYER_JUMP = "player_walk_04.png"

# UI Assets (NEW - Create or find a small heart image)
IMG_HEART = "heart.png" # <-- NEW: Add a filename for your heart graphic (e.g., 16x16)
IMG_HEART_EMPTY = "heart_empty.png" # <-- NEW: Optional empty heart graphic

# Platform Types (Maps level character to image filename)
PLATFORM_TYPES = {
    'X': "single_green_block_0.png",
    'S': "singledryblock_0.png",
    'F': "single_goldendirtblock_0.png",
    'I': "single_iceblock_0.png",
}

# Background Image
IMG_BG = "background.png"

# Sounds
SND_JUMP = "jump.wav"
SND_HIT = "hurt.wav"
SND_WIN_LEVEL = "coin.wav"
SND_WIN_GAME = "power_up.wav"
SND_GAME_OVER = "explosion.wav"

# Music
MUS_BACKGROUND = "time_for_adventure.mp3"

# Font
FONT_NAME_PIXEL = "PixelOperator8.ttf"