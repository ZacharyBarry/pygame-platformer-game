# main.py
import pygame
import sys
import os

# Import constants needed for folder creation BEFORE game init
from constants import ASSETS_FOLDER, IMAGE_FOLDER, SOUND_FOLDER, MUSIC_FOLDER, FONT_FOLDER

# Import the Game class
from game import Game

def main():
    """Main entry point for the game."""
    print("Game starting...")

    # Optional: Create asset folders if they don't exist
    # This should ideally be done just once, perhaps by an installer,
    # but it's helpful during development.
    folders_to_check = [ASSETS_FOLDER, IMAGE_FOLDER, SOUND_FOLDER, MUSIC_FOLDER, FONT_FOLDER]
    for folder_path in folders_to_check:
        if not os.path.exists(folder_path):
             try:
                 os.makedirs(folder_path)
                 print(f"Created missing folder: {folder_path}")
             except OSError as e:
                 # Use print for errors before pygame display is fully up
                 print(f"ERROR: Could not create folder {folder_path}: {e}")
                 # Depending on severity, you might want to exit here:
                 # sys.exit(f"Failed to create essential folder: {folder_path}")


    # Create the Game instance
    # The Game class __init__ handles pygame.init() and asset loading
    try:
        game_instance = Game()
    except Exception as e:
         # Catch potential errors during Game initialization (e.g., display setup)
         print(f"\nFATAL ERROR during game initialization: {e}")
         pygame.quit() # Attempt to clean up pygame
         sys.exit("Game initialization failed.")


    # Start the game's main execution flow (shows start screen, runs game loop)
    try:
         game_instance.start()
    except Exception as e:
         # Catch potential errors during the main game loop
         print(f"\nFATAL ERROR during game execution: {e}")
         # Add more detailed error logging here if needed
         import traceback
         traceback.print_exc() # Print the full traceback
    finally:
         # Ensure pygame quits even if errors occurred
         print("Cleaning up Pygame...")
         pygame.quit()
         sys.exit("Game exited.")


# --- Script Execution ---
if __name__ == "__main__":
    main()