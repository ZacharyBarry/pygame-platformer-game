# utils.py
import pygame
from constants import COLOR_TEXT # Default color

def draw_text(surface, text, size, x, y, font, color=COLOR_TEXT):
    """Draws text on a surface. Requires font object."""
    if font is None:
        print("Error: draw_text called without a valid font.")
        return # Can't draw if font failed to load or wasn't passed

    try:
        text_surface = font.render(text, True, color) # AA=True
        text_rect = text_surface.get_rect(midtop=(x, y))
        surface.blit(text_surface, text_rect)
    except Exception as e:
        print(f"Error rendering text '{text}': {e}")