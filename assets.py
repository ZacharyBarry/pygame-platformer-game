# assets.py
import pygame
import os
# Import folder constants (assuming assets.py is in the same directory as constants.py)
from constants import IMAGE_FOLDER, SOUND_FOLDER, MUSIC_FOLDER, FONT_FOLDER

def load_image(filename, use_colorkey=False, color_key=(0, 0, 0)):
    """Loads an image from the IMAGE_FOLDER, attempts alpha, returns None on failure."""
    filepath = os.path.join(IMAGE_FOLDER, filename)
    try:
        image = pygame.image.load(filepath).convert_alpha()
        return image
    except pygame.error:
        try:
            # Try without alpha if convert_alpha fails
            image = pygame.image.load(filepath).convert()
            if use_colorkey:
                image.set_colorkey(color_key)
            return image
        except Exception as e:
            print(f"ERROR loading image '{filename}': {e}")
            return None
    except FileNotFoundError:
         print(f"ERROR: Image file not found: '{filepath}'")
         return None

def load_sound(filename):
    """Loads a sound from the SOUND_FOLDER, returns None on failure."""
    filepath = os.path.join(SOUND_FOLDER, filename)
    # Check if mixer is initialized, though Game class should handle this
    if not pygame.mixer.get_init():
        print("Warning: Mixer not initialized when loading sound.")
        return None
    try:
        sound = pygame.mixer.Sound(filepath)
        return sound
    except Exception as e:
        print(f"Warning: Sound load failed '{filename}': {e}")
        return None

def load_music(filename):
    """Loads music from the MUSIC_FOLDER, returns True on success, False on failure."""
    filepath = os.path.join(MUSIC_FOLDER, filename)
    if not pygame.mixer.get_init():
        print("Warning: Mixer not initialized when loading music.")
        return False
    try:
        pygame.mixer.music.load(filepath)
        return True
    except Exception as e:
        print(f"Warning: Music load failed '{filename}': {e}")
        return False

def load_font(font_name, size):
    """Loads a font from FONT_FOLDER, falls back to default, returns None on total failure."""
    custom_font_path = os.path.join(FONT_FOLDER, font_name)
    if os.path.exists(custom_font_path):
        try:
            return pygame.font.Font(custom_font_path, size)
        except Exception as e:
            print(f"Warning: Font load failed '{font_name}': {e}")

    print(f"Warning: Custom font '{font_name}' failed or not found. Using default.")
    try:
        # Use the requested size for default font as well
        return pygame.font.Font(None, size)
    except Exception as e:
        print(f"FATAL: Default font failed: {e}")
        return None