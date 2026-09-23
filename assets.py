# assets.py
import pygame
import os
# Import folder constants (assuming assets.py is in the same directory as constants.py)
from constants import IMAGE_FOLDER, SOUND_FOLDER, MUSIC_FOLDER, FONT_FOLDER

def _ensure_asset(filename):
    """Generates standard retro CC0 pixel art PNG assets if they don't already exist."""
    filepath = os.path.join(IMAGE_FOLDER, filename)
    if os.path.exists(filepath):
        return True

    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    try:
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)

        if filename == "enemy_crawler_0.png":
            cap_main = (190, 55, 45, 255)
            cap_dark = (140, 35, 30, 255)
            spot = (250, 235, 195, 255)
            skin = (235, 190, 145, 255)
            eye_dark = (30, 25, 30, 255)
            eye_white = (255, 255, 255, 255)
            foot = (85, 45, 25, 255)

            for y, (x1, x2) in enumerate([(5, 10), (3, 12), (2, 13), (1, 14), (1, 14)], start=3):
                for x in range(x1, x2 + 1): surf.set_at((x, y), cap_main)
            for x in range(1, 15): surf.set_at((x, 7), cap_dark)
            surf.set_at((5, 4), spot); surf.set_at((6, 4), spot); surf.set_at((10, 4), spot)
            surf.set_at((3, 6), spot); surf.set_at((12, 6), spot)

            for y in range(8, 12):
                for x in range(4, 12): surf.set_at((x, y), skin)
            surf.set_at((5, 8), eye_dark); surf.set_at((6, 9), eye_dark); surf.set_at((5, 9), eye_white)
            surf.set_at((10, 8), eye_dark); surf.set_at((9, 9), eye_dark); surf.set_at((10, 9), eye_white)
            surf.set_at((7, 11), cap_dark); surf.set_at((8, 11), cap_dark)

            for x in range(2, 7):
                surf.set_at((x, 12), foot); surf.set_at((x, 13), foot); surf.set_at((x, 14), foot)
            for x in range(9, 14):
                surf.set_at((x, 12), foot); surf.set_at((x, 13), foot); surf.set_at((x, 14), foot)
            for x in range(1, 7): surf.set_at((x, 15), foot)
            for x in range(9, 15): surf.set_at((x, 15), foot)

        elif filename == "enemy_crawler_1.png":
            cap_main = (190, 55, 45, 255)
            cap_dark = (140, 35, 30, 255)
            spot = (250, 235, 195, 255)
            skin = (235, 190, 145, 255)
            eye_dark = (30, 25, 30, 255)
            eye_white = (255, 255, 255, 255)
            foot = (85, 45, 25, 255)

            for y, (x1, x2) in enumerate([(5, 10), (3, 12), (2, 13), (1, 14), (1, 14)], start=3):
                for x in range(x1, x2 + 1): surf.set_at((x, y), cap_main)
            for x in range(1, 15): surf.set_at((x, 7), cap_dark)
            surf.set_at((5, 4), spot); surf.set_at((6, 4), spot); surf.set_at((10, 4), spot)
            surf.set_at((3, 6), spot); surf.set_at((12, 6), spot)

            for y in range(8, 12):
                for x in range(4, 12): surf.set_at((x, y), skin)
            surf.set_at((5, 8), eye_dark); surf.set_at((6, 9), eye_dark); surf.set_at((5, 9), eye_white)
            surf.set_at((10, 8), eye_dark); surf.set_at((9, 9), eye_dark); surf.set_at((10, 9), eye_white)
            surf.set_at((7, 11), cap_dark); surf.set_at((8, 11), cap_dark)

            # Shifted walk foot
            for x in range(3, 7):
                surf.set_at((x, 12), foot); surf.set_at((x, 13), foot); surf.set_at((x, 14), foot)
            for x in range(8, 14):
                surf.set_at((x, 12), foot); surf.set_at((x, 13), foot); surf.set_at((x, 14), foot); surf.set_at((x, 15), foot)
            surf.set_at((14, 15), foot); surf.set_at((15, 15), foot)

        elif filename == "enemy_crawler_squash.png":
            cap_main = (190, 55, 45, 255)
            cap_dark = (140, 35, 30, 255)
            skin = (235, 190, 145, 255)
            eye_dark = (30, 25, 30, 255)
            foot = (85, 45, 25, 255)

            for y in range(9, 12):
                for x in range(1, 15): surf.set_at((x, y), cap_main)
            for x in range(1, 15): surf.set_at((x, 11), cap_dark)
            for y in range(12, 14):
                for x in range(2, 14): surf.set_at((x, y), skin)
            surf.set_at((4, 12), eye_dark); surf.set_at((6, 12), eye_dark); surf.set_at((5, 13), eye_dark)
            surf.set_at((9, 12), eye_dark); surf.set_at((11, 12), eye_dark); surf.set_at((10, 13), eye_dark)
            for x in range(0, 16):
                surf.set_at((x, 14), foot); surf.set_at((x, 15), foot)

        elif filename == "enemy_flyer_0.png":
            body = (90, 45, 130, 255)
            body_dark = (55, 25, 80, 255)
            wing = (120, 65, 160, 255)
            wing_border = (60, 30, 85, 255)
            eye = (255, 60, 60, 255)
            fang = (245, 245, 255, 255)

            for x in range(0, 6):
                for y in range(5, 10):
                    if (x + y) >= 6: surf.set_at((x, y), wing)
            surf.set_at((0, 4), wing_border); surf.set_at((1, 4), wing_border); surf.set_at((2, 3), wing_border)
            surf.set_at((0, 9), wing_border); surf.set_at((3, 10), wing_border)

            for x in range(10, 16):
                for y in range(5, 10):
                    if (15 - x + y) >= 6: surf.set_at((x, y), wing)
            surf.set_at((15, 4), wing_border); surf.set_at((14, 4), wing_border); surf.set_at((13, 3), wing_border)
            surf.set_at((15, 9), wing_border); surf.set_at((12, 10), wing_border)

            surf.set_at((5, 3), body_dark); surf.set_at((5, 4), body); surf.set_at((10, 3), body_dark); surf.set_at((10, 4), body)
            for y in range(5, 13):
                for x in range(5, 11): surf.set_at((x, y), body)
            for x in range(6, 10): surf.set_at((x, 13), body_dark)
            surf.set_at((6, 7), eye); surf.set_at((9, 7), eye)
            surf.set_at((7, 10), fang); surf.set_at((8, 10), fang)

        elif filename == "enemy_flyer_1.png":
            body = (90, 45, 130, 255)
            body_dark = (55, 25, 80, 255)
            wing = (120, 65, 160, 255)
            wing_border = (60, 30, 85, 255)
            eye = (255, 60, 60, 255)
            fang = (245, 245, 255, 255)

            surf.set_at((5, 3), body_dark); surf.set_at((5, 4), body); surf.set_at((10, 3), body_dark); surf.set_at((10, 4), body)
            for y in range(7, 14):
                for x in range(2, 6): surf.set_at((x, y), wing)
                for x in range(10, 14): surf.set_at((x, y), wing)
            for x in range(1, 5): surf.set_at((x, 13), wing_border)
            for x in range(11, 15): surf.set_at((x, 13), wing_border)

            for y in range(5, 13):
                for x in range(5, 11): surf.set_at((x, y), body)
            for x in range(6, 10): surf.set_at((x, 13), body_dark)
            surf.set_at((6, 7), eye); surf.set_at((9, 7), eye)
            surf.set_at((7, 10), fang); surf.set_at((8, 10), fang)

        elif filename == "heart_empty.png":
            border = (120, 60, 70, 220)
            coords_border = [
                (3, 2), (4, 2), (5, 2), (10, 2), (11, 2), (12, 2),
                (2, 3), (6, 3), (9, 3), (13, 3),
                (1, 4), (7, 4), (8, 4), (14, 4),
                (1, 5), (14, 5), (1, 6), (14, 6), (1, 7), (14, 7),
                (2, 8), (13, 8), (3, 9), (12, 9), (4, 10), (11, 10),
                (5, 11), (10, 11), (6, 12), (9, 12), (7, 13), (8, 13)
            ]
            for cx, cy in coords_border: surf.set_at((cx, cy), border)

        else:
            return False

        pygame.image.save(surf, filepath)
        print(f"  Generated CC0 retro sprite: {filename}")
        return True
    except Exception as e:
        print(f"Warning: Could not auto-generate asset '{filename}': {e}")
        return False

def load_image(filename, use_colorkey=False, color_key=(0, 0, 0)):
    """Loads an image from the IMAGE_FOLDER, attempts alpha, returns None on failure."""
    filepath = os.path.join(IMAGE_FOLDER, filename)
    if not os.path.exists(filepath):
        _ensure_asset(filename)
    try:
        image = pygame.image.load(filepath).convert_alpha()
        return image
    except pygame.error:
        try:
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