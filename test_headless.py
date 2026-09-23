import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from game import Game

def test():
    try:
        g = Game()
        g.start_new_game()
        g._load_level(0)
        g.playing = True
        g.running = True
        
        for _ in range(60):
            g._update()
            g._draw()
            
        print("Level 1 passed 60 frames")
        
        # Test level 20 for Boss
        g._load_level(19)
        g.playing = True
        g.running = True
        for _ in range(60):
            g._update()
            g._draw()
            
        print("Level 20 passed 60 frames")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    test()
