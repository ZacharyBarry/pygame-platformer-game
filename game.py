# game.py
import pygame
import sys
import os
import random
import importlib  # <-- 1. Import importlib

# Import necessary components from other modules
from constants import * # Import all constants
# from levels import LEVELS # <-- 2. Remove direct import of LEVELS
import levels            # <-- 2. Import the module itself
from assets import load_image, load_sound, load_music, load_font
from utils import draw_text
from sprites import Player, Platform, Hazard, Goal # Import sprite classes

class Game:
    """
    Manages the main game loop, states, levels, assets, and game objects.
    """

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512);
        pygame.init();
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True;
        self.playing = False
        self.dt = 0

        # --- Game Mode & State ---
        self.game_mode = "normal"  # Options: "normal", "hardcore" <-- SET DEFAULT MODE HERE
        self.game_over = False  # Means return to level 1 (used by hardcore mode)
        self.restart_level_pending = False  # Flag for normal mode level restart
        self.game_won = False
        self.next_level_pending = False
        # --- End Game Mode ---

        self.current_level_index = 0
        self.total_levels = len(levels.LEVELS)
        self.player_start_pos = (0, 0)

        # --- Editor Mode State ---
        self.editing = False
        self.edits_used = 0
        self.current_edit_session = []
        self.selected_block_type = 'X'
        self.active_level_grid = []
        self.level_offset_x = 0
        self.level_offset_y = 0

        # Asset storage
        self.platform_images = {};
        self.img_hazard = [];
        self.img_goal = None
        self.img_background = None;
        self.img_heart = None;
        self.img_heart_empty = None  # <-- Added heart images
        self.sound_jump = None;
        self.sound_hit = None;
        self.sound_win_level = None
        self.sound_win_game = None;
        self.sound_game_over = None
        self.title_font = None;
        self.default_font = None;
        self.small_font = None

        # Sprite groups
        self.all_sprites = pygame.sprite.Group();
        self.platforms = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group();
        self.goals = pygame.sprite.Group()
        self.player_sprite = pygame.sprite.GroupSingle()

        self._load_assets()
        print(f"--- Game Mode Set To: {self.game_mode.upper()} ---")

    def _load_assets(self):
        print("Loading assets...")
        any_fail = False
        # (Load Fonts, Platforms, Goal, Background, Hazards, Sounds, Music - NO CHANGES HERE)
        self.title_font = load_font(FONT_NAME_PIXEL, 24); self.default_font = load_font(FONT_NAME_PIXEL, 12); self.small_font = load_font(FONT_NAME_PIXEL, 8)
        if not self.default_font or not self.title_font or not self.small_font: print("FATAL: Font loading failed."); self.running = False; any_fail = True; return
        print("  Loading platform tiles..."); # ... platform loading ...
        for char, filename in PLATFORM_TYPES.items(): img = load_image(filename); self.platform_images[char] = img; #... error check ...
        print("  Creating goal placeholder..."); # ... goal creation ...
        try: goal_surface = pygame.Surface((TILE_SIZE, TILE_SIZE)); goal_surface.fill(COLOR_TITLE); self.img_goal = goal_surface.convert(); #... success msg ...
        except Exception as e: print(f"    - ERROR creating goal: {e}"); self.img_goal = None; any_fail = True
        print("  Loading background..."); # ... background loading ...
        bg_img_temp = load_image(IMG_BG) #... scale bg ...
        if bg_img_temp: #... try scale ...
            try: self.img_background = pygame.transform.scale(bg_img_temp, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception as e: print(f"    ! Warning: Could not scale background: {e}"); self.img_background = None
        else: any_fail = True; self.img_background = None
        print("  Creating hazard placeholders..."); # ... hazard creation ...
        try: h1 = pygame.Surface((TILE_SIZE, TILE_SIZE)); h1.fill(COLOR_HAZARD_1); h2 = pygame.Surface((TILE_SIZE, TILE_SIZE)); h2.fill(COLOR_HAZARD_2); self.img_hazard = [h1.convert(), h2.convert()]
        except Exception as e: print(f"    - ERROR creating hazard: {e}"); any_fail = True; #... fallback ...
        print("  Loading sounds..."); # ... sound loading ...
        self.sound_jump = load_sound(SND_JUMP); self.sound_hit = load_sound(SND_HIT); self.sound_win_level = load_sound(SND_WIN_LEVEL); self.sound_win_game = load_sound(SND_WIN_GAME); self.sound_game_over = load_sound(SND_GAME_OVER)
        print("  Loading music..."); # ... music loading ...
        if load_music(MUS_BACKGROUND): pygame.mixer.music.set_volume(0.3);
        else: print(f"    ! Warning: Music load failed.")

        # --- Load UI Images ---
        print("  Loading UI images...")
        self.img_heart = load_image(IMG_HEART)
        self.img_heart_empty = load_image(IMG_HEART_EMPTY) # Optional
        if not self.img_heart:
            print(f"    ! Warning: Failed to load heart image '{IMG_HEART}'. Health display may not work.")
            # We could create a fallback drawing here, but let's assume the image exists for now.
            # any_fail = True # Should UI failure stop the game? Maybe not.
        if not self.img_heart_empty:
             print(f"    - Info: Empty heart image '{IMG_HEART_EMPTY}' not found. Using full hearts only.")


        if any_fail: print("\n--- WARNING: Some critical assets failed! ---")
        else: print("Assets loaded successfully.")


    def _load_level(self, level_index, hard_reset=False):
        if not (0 <= level_index < len(levels.LEVELS)): print(f"Error: Invalid level index {level_index}"); self.playing = False; self.running = False; return
        print(f"Loading Level {level_index + 1}...")
        
        if hard_reset or level_index != getattr(self, 'loaded_level_layout_index', -1) or not self.active_level_grid:
            self.active_level_grid = [list(row) for row in levels.LEVELS[level_index]]
            self.loaded_level_layout_index = level_index
            self.edits_used = 0
            self.current_edit_session = []

        level_map = self.active_level_grid
        self.current_level_index = level_index
        self.all_sprites.empty(); self.platforms.empty(); self.hazards.empty(); self.goals.empty(); self.player_sprite.empty()
        level_h_tiles = len(level_map); level_w_tiles = len(level_map[0]) if level_h_tiles > 0 else 0
        level_pixel_h = level_h_tiles * TILE_SIZE; level_pixel_w = level_w_tiles * TILE_SIZE
        offset_x = max(0, (SCREEN_WIDTH - level_pixel_w) // 2); offset_y = max(0, (SCREEN_HEIGHT - level_pixel_h) // 2)
        self.level_offset_x = offset_x
        self.level_offset_y = offset_y
        player_found = False
        for r, row in enumerate(level_map):
            for c, tile_char in enumerate(row):
                x = offset_x + c * TILE_SIZE; y = offset_y + r * TILE_SIZE
                if tile_char in self.platform_images: # Platform
                    img = self.platform_images.get(tile_char)
                    if img:
                        plat = Platform(x, y, img, tile_type=tile_char)
                        plat.grid_pos = (r, c)
                        self.all_sprites.add(plat); self.platforms.add(plat)
                elif tile_char == 'H': # Hazard
                    if self.img_hazard: haz = Hazard(x, y, self.img_hazard); self.all_sprites.add(haz); self.hazards.add(haz)
                elif tile_char == 'G': # Goal
                    if self.img_goal: goal = Goal(x, y, self.img_goal)
                    else: goal = Goal(x, y, None)
                    self.all_sprites.add(goal); self.goals.add(goal)
                elif tile_char == 'P': # Player Start
                    if not player_found: self.player_start_pos = (x, y); player_found = True
                    else: print(f"Warning: Multiple 'P'...")
        if not player_found: print(f"FATAL: No 'P' in level {level_index+1}!"); self.running = False; return
        # Create Player (will init with full health)
        self.player = Player(self, self.player_start_pos[0], self.player_start_pos[1])
        if self.running: self.all_sprites.add(self.player); self.player_sprite.add(self.player)
        else: print("Game stopped due to Player initialization failure.")


    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.playing = False; self.running = False
            
            if self.editing:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.playing = False; self.running = False
                    elif event.key == pygame.K_e:
                        self.editing = False
                        self.edits_used += len(self.current_edit_session)
                        self.current_edit_session = []
                    elif event.key == pygame.K_r:
                        print(f"--- Hard Reset Level {self.current_level_index + 1} ---")
                        self.editing = False
                        self._load_level(self.current_level_index, hard_reset=True)
                    elif event.key == pygame.K_z:
                        if self.current_edit_session:
                            action = self.current_edit_session.pop()
                            action_type, (r, c), tile_char = action
                            if action_type == 'add':
                                self.active_level_grid[r][c] = '.'
                                for plat in self.platforms:
                                    if hasattr(plat, 'grid_pos') and plat.grid_pos == (r, c): plat.kill(); break
                            elif action_type == 'remove':
                                self.active_level_grid[r][c] = tile_char
                                img = self.platform_images.get(tile_char)
                                x = self.level_offset_x + c * TILE_SIZE; y = self.level_offset_y + r * TILE_SIZE
                                plat = Platform(x, y, img, tile_type=tile_char)
                                plat.grid_pos = (r, c)
                                self.all_sprites.add(plat); self.platforms.add(plat)
                    elif event.key == pygame.K_1: self.selected_block_type = 'X'
                    elif event.key == pygame.K_2: self.selected_block_type = 'S'
                    elif event.key == pygame.K_3: self.selected_block_type = 'F'
                    elif event.key == pygame.K_4: self.selected_block_type = 'I'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    c = int((mouse_x - self.level_offset_x) // TILE_SIZE)
                    r = int((mouse_y - self.level_offset_y) // TILE_SIZE)
                    if 0 <= r < len(self.active_level_grid) and 0 <= c < len(self.active_level_grid[0]):
                        if event.button == 1: # Left
                            if self.active_level_grid[r][c] == '.':
                                self.active_level_grid[r][c] = self.selected_block_type
                                self.current_edit_session.append(('add', (r, c), self.selected_block_type))
                                img = self.platform_images.get(self.selected_block_type)
                                x = self.level_offset_x + c * TILE_SIZE; y = self.level_offset_y + r * TILE_SIZE
                                plat = Platform(x, y, img, tile_type=self.selected_block_type)
                                plat.grid_pos = (r, c)
                                self.all_sprites.add(plat); self.platforms.add(plat)
                        elif event.button == 3: # Right
                            char = self.active_level_grid[r][c]
                            if char in PLATFORM_TYPES:
                                self.active_level_grid[r][c] = '.'
                                self.current_edit_session.append(('remove', (r, c), char))
                                for plat in self.platforms:
                                    if hasattr(plat, 'grid_pos') and plat.grid_pos == (r, c): plat.kill(); break
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.playing = False; self.running = False
                    elif event.key == pygame.K_e:
                        if self.playing: self.editing = True
                    elif event.key == pygame.K_r: # Reload
                        if self.playing:
                            print(f"--- Reloading Level {self.current_level_index + 1} ---")
                            try: importlib.reload(levels); self.total_levels = len(levels.LEVELS)
                            except Exception as e: print(f"!!! ERROR Reloading: {e} !!!"); continue # Skip load if reload failed
                            self._load_level(self.current_level_index)
                        else: print("Cannot reload: Not playing.")
                    # Player Controls
                    elif self.player and self.player_sprite.sprite:
                        if self.player.state not in ['hit', 'dying', 'dodging'] and not self.player.invincible:
                            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w): self.player.jump()
                        if self.player.state in ['idle', 'walking'] and self.player.on_ground:
                             if event.key == pygame.K_LSHIFT: self.player.dodge()


    # --- The rest of the Game class methods remain unchanged ---
    # (_update, _draw, signal_player_fully_dead, level_complete,
    # show_start_screen, show_game_over_screen, show_win_screen,
    # _wait_for_key, start_new_game, _start_current_level, run_level, start)

    def start_new_game(self):
        """Resets game state and prepares to start level 1."""
        print("Starting new game...")
        self.game_over = False; self.game_won = False; self.next_level_pending = False
        self.current_level_index = 0

    def _start_current_level(self):
        """Loads and starts the gameplay loop for the current level index."""
        self._load_level(self.current_level_index)
        if not self.running: print("Failed to start level due to loading error."); return

        self.playing = True; self.next_level_pending = False

        if MUS_BACKGROUND and pygame.mixer.music.get_volume() > 0 and not pygame.mixer.music.get_busy():
            try: pygame.mixer.music.play(loops=-1)
            except pygame.error as e: print(f"Warning: Could not play music: {e}")
        self.run_level()

    def run_level(self):
        """Main gameplay loop for a single level."""
        print(f"Entering level {self.current_level_index + 1} gameplay loop...")
        while self.playing and self.running:
            self.dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            if not self.playing or not self.running: break
            self._update()
            self._draw()
        print(f"Exiting level {self.current_level_index + 1} gameplay loop.")

    def _update(self):
        """Updates all game objects and checks game conditions."""
        if not self.playing: return
        if self.editing: return
        self.all_sprites.update()
        if self.player and self.player_sprite.sprite:
             if self.player.rect.top > SCREEN_HEIGHT + TILE_SIZE * 2:
                 if self.player.state not in ['hit', 'dying']:
                     print("Player fell off screen - initiating death sequence.")
                     self.player.die()

    def _draw(self):
        """Draws the background, sprites, and HUD (including hearts)."""
        if self.img_background:
            self.screen.blit(self.img_background, (0, 0))
        else:
            self.screen.fill(COLOR_BG)
        self.all_sprites.draw(self.screen)

        # --- Draw Editor ---
        if self.editing:
            # Draw overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(COLOR_UI_BG)
            self.screen.blit(overlay, (0, 0))
            
            # Draw subtle grid
            for r in range(len(self.active_level_grid)):
                for c in range(len(self.active_level_grid[0])):
                    rect = pygame.Rect(self.level_offset_x + c * TILE_SIZE, self.level_offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
            
            # Highlight hovered cell
            mouse_x, mouse_y = pygame.mouse.get_pos()
            c = int((mouse_x - self.level_offset_x) // TILE_SIZE)
            r = int((mouse_y - self.level_offset_y) // TILE_SIZE)
            if 0 <= r < len(self.active_level_grid) and 0 <= c < len(self.active_level_grid[0]):
                highlight = pygame.Rect(self.level_offset_x + c * TILE_SIZE, self.level_offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, COLOR_HIGHLIGHT, highlight, 2)
            
            # Draw UI Panel
            if self.title_font and self.default_font:
                draw_text(self.screen, "EDIT MODE (Paused)", 24, SCREEN_WIDTH / 2, 30, self.title_font, COLOR_WIN)
                total_edits = self.edits_used + len(self.current_edit_session)
                color_score = COLOR_WIN if total_edits <= MAX_EDITS_FOR_FULL_POINTS else COLOR_TITLE
                draw_text(self.screen, f"Edits Used: {total_edits} (Par: {MAX_EDITS_FOR_FULL_POINTS})", 12, SCREEN_WIDTH / 2, 70, self.default_font, color_score)
                
                # Draw Visual Block Palette
                palette_x_start = SCREEN_WIDTH / 2 - 70
                palette_y = 95
                block_keys = ['X', 'S', 'F', 'I']
                for i, block_key in enumerate(block_keys):
                    img = self.platform_images.get(block_key)
                    if img:
                        bx = palette_x_start + i * 40
                        # Highlight if selected
                        if block_key == self.selected_block_type:
                            pygame.draw.rect(self.screen, COLOR_WIN, (bx - 4, palette_y - 4, TILE_SIZE + 8, TILE_SIZE + 8), 2)
                        self.screen.blit(img, (bx, palette_y))
                        # Number hint
                        draw_text(self.screen, str(i+1), 8, bx + TILE_SIZE/2, palette_y + TILE_SIZE + 8, self.small_font, COLOR_TEXT)

                draw_text(self.screen, "Left Click: Place | Right Click: Remove | Z: Undo | R: Hard Reset Level", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20, self.small_font, COLOR_INFO)

        # --- Draw HUD ---
        if self.small_font:  # Draw Level Text
            draw_text(self.screen, f"Lvl: {self.current_level_index + 1}/{self.total_levels}",
                      8, SCREEN_WIDTH - 35, 5, self.small_font, COLOR_LEVEL)

        # --- Draw Hearts ---
        if self.img_heart and self.player:  # Check heart image loaded and player exists
            heart_x = 10
            heart_y = 10
            heart_spacing = (self.img_heart.get_width() if self.img_heart else TILE_SIZE) + 4  # Spacing between hearts

            # Draw filled hearts for current health
            for i in range(self.player.health):
                self.screen.blit(self.img_heart, (heart_x + i * heart_spacing, heart_y))

            # Optional: Draw empty hearts for missing health
            if self.img_heart_empty:
                for i in range(self.player.health, self.player.max_health):
                    self.screen.blit(self.img_heart_empty, (heart_x + i * heart_spacing, heart_y))
            # Alternative if no empty heart image: Draw total number of heart outlines? Or just show current health?
            # Simpler: Just show the current filled hearts.

        pygame.display.flip()

    def signal_player_fully_dead(self):
        """Called by Player death animation finish. Handles game mode."""
        if self.playing: # Only process if player was actively playing
            self.playing = False # Stop current level loop regardless of mode
            if self.sound_game_over: self.sound_game_over.play()
            pygame.mixer.music.fadeout(500)

            if self.game_mode == "hardcore":
                print("Player Died (Hardcore Mode) -> Game Over (Restart from Lvl 1)")
                self.game_over = True # Set flag for main loop to handle restart from Lvl 1
            else: # Normal mode
                print(f"Player Died (Normal Mode) -> Restarting Level {self.current_level_index + 1}")
                self.restart_level_pending = True # Set flag for main loop to restart current level

    def level_complete(self):
        """Called when the player collides with the Goal."""
        if not self.playing: return
        print(f"Level {self.current_level_index + 1} Complete!"); self.playing = False
        
        # Display score popup
        if self.title_font and self.default_font:
            self._draw() # Render the frame
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            draw_text(self.screen, "LEVEL CLEARED!", 24, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, self.title_font, COLOR_WIN)
            if self.edits_used <= MAX_EDITS_FOR_FULL_POINTS:
                draw_text(self.screen, f"PERFECT! (Edits: {self.edits_used}/{MAX_EDITS_FOR_FULL_POINTS})", 16, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, self.default_font, COLOR_WIN)
            else:
                draw_text(self.screen, f"GOOD! (Edits: {self.edits_used})", 16, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, self.default_font, COLOR_TITLE)
            draw_text(self.screen, "Press any key to continue...", 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 2 / 3, self.default_font, COLOR_TEXT)
            pygame.display.flip()
            self._wait_for_key()

        # <-- Access LEVELS via the module -->
        if self.current_level_index + 1 < len(levels.LEVELS):
            if self.sound_win_level: self.sound_win_level.play()
            self.next_level_pending = True
        else:
            if self.sound_win_game: self.sound_win_game.play()
            pygame.mixer.music.fadeout(500); self.game_won = True

    def show_start_screen(self):
        if not self.title_font or not self.default_font or not self.small_font: print("Cannot show start screen - fonts missing."); self.running = False; return
        
        # Add a dark semi-transparent overlay to make text pop against background
        if self.img_background:
            self.screen.blit(self.img_background, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) # Darken background
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(COLOR_BG)
            
        # Title
        draw_text(self.screen, TITLE, 32, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, self.title_font, COLOR_TITLE)
        
        # Subtitle
        draw_text(self.screen, "A Retro Puzzle Platformer", 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 + 40, self.default_font, COLOR_INFO)

        # Controls Section
        start_y = SCREEN_HEIGHT / 2 - 20
        draw_text(self.screen, "--- CONTROLS ---", 16, SCREEN_WIDTH / 2, start_y, self.default_font, COLOR_TEXT)
        draw_text(self.screen, "Move: Arrows / A & D", 12, SCREEN_WIDTH / 2, start_y + 35, self.default_font, COLOR_WIN)
        draw_text(self.screen, "Jump: Space / W / Up", 12, SCREEN_WIDTH / 2, start_y + 55, self.default_font, COLOR_WIN)
        draw_text(self.screen, "Dodge Roll: Left Shift", 12, SCREEN_WIDTH / 2, start_y + 75, self.default_font, COLOR_INFO)
        
        # Edit Mode Section
        draw_text(self.screen, "--- LEVEL EDITOR ---", 16, SCREEN_WIDTH / 2, start_y + 115, self.default_font, COLOR_TEXT)
        draw_text(self.screen, "Press 'E' to pause and edit difficult levels!", 12, SCREEN_WIDTH / 2, start_y + 150, self.default_font, COLOR_WIN)
        draw_text(self.screen, "Beat the level in under 3 edits for a PERFECT score.", 10, SCREEN_WIDTH / 2, start_y + 175, self.default_font, COLOR_TEXT)
        
        # Bottom prompts
        draw_text(self.screen, "Press any key to embark...", 16, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 40, self.default_font, COLOR_TITLE)
        draw_text(self.screen, f"Current Mode: {self.game_mode.upper()} | (ESC to Quit)", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 30, self.small_font, COLOR_TEXT)
        
        pygame.display.flip()
        self._wait_for_key(allow_quit=True)

    def show_game_over_screen(self): # This screen now primarily shows for Hardcore mode 'Game Over'
        if not self.running or not self.title_font or not self.default_font or not self.small_font: return
        self.screen.fill(COLOR_BG)
        title = "GAME OVER" if self.game_mode == "hardcore" else "LEVEL FAILED" # Adjust title maybe?
        draw_text(self.screen, title, 24, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, self.title_font, COLOR_LOSE)
        draw_text(self.screen, f"Failed on Level {self.current_level_index + 1}", 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, self.default_font, COLOR_INFO)
        retry_text = "Press key to retry from Level 1" if self.game_mode == "hardcore" else "Press key to retry level"
        draw_text(self.screen, retry_text, 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4, self.default_font, COLOR_TEXT)
        draw_text(self.screen, "(ESC to Quit)", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 30, self.small_font, COLOR_TEXT)
        pygame.display.flip(); self._wait_for_key(allow_quit=True)

    def show_win_screen(self): # No changes needed
        if not self.running or not self.title_font or not self.default_font or not self.small_font: return
        self.screen.fill(COLOR_BG)
        draw_text(self.screen, "YOU WIN!", 24, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3, self.title_font, COLOR_WIN)
        draw_text(self.screen, "Congratulations!", 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, self.default_font, COLOR_TITLE)
        draw_text(self.screen, "Press any key to play again", 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4, self.default_font, COLOR_TEXT)
        draw_text(self.screen, "(ESC to Quit)", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 30, self.small_font, COLOR_TEXT)
        pygame.display.flip(); self._wait_for_key(allow_quit=True)

    def _wait_for_key(self, allow_quit=False):
        pygame.event.clear(); waiting = True
        while waiting and self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: waiting = False; self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if allow_quit: waiting = False; self.running = False
                    else: waiting = False # Any other key

    def start(self):
        """Main application entry point and game flow manager."""
        if not self.running: print("Initialization failed."); pygame.quit(); sys.exit()
        self.show_start_screen()
        if not self.running: print("Exiting after start screen."); pygame.quit(); sys.exit()

        # ========================
        # Main Application Loop
        # ========================
        while self.running:
            # --- Reset for a new game attempt ---
            self.game_over = False            # Reset hardcore game over
            self.restart_level_pending = False # Reset normal restart flag
            self.game_won = False
            self.next_level_pending = False
            self.current_level_index = 0      # Always start at level 0 on new game/retry hardcore
            print("-" * 30)
            print(f"Starting Game (Mode: {self.game_mode.upper()}, Level {self.current_level_index + 1})")
            print("-" * 30)

            # ========================
            # Inner Loop (Play Levels)
            # ========================
            while self.running and not self.game_over and not self.game_won:
                # --- Start or Restart the current level ---
                if self.restart_level_pending:
                    print(f"Restarting level {self.current_level_index + 1}...")
                    self.restart_level_pending = False # Consume the flag
                    # Don't increment level index, just reload current one
                # (If not restarting, _start_current_level will use the current index)

                self._start_current_level() # Loads level and runs its gameplay loop
                # --- Execution resumes here after the level ends (win, die, quit) ---

                if not self.running: break # Check if user quit during level/reload

                # --- Handle Level End State ---
                if self.next_level_pending:
                    self.current_level_index += 1; self.next_level_pending = False
                    print(f"Advancing to level {self.current_level_index + 1}")
                    # Loop continues to load the next level

                elif self.restart_level_pending:
                    # This flag was set by signal_player_fully_dead in normal mode.
                    # The loop will continue, and the block at the start of the
                    # inner loop will handle the restart.
                    print("DEBUG: Restart Level Pending flag active after level end.")
                    pass # Just let the loop restart the current level

                elif self.game_won or self.game_over:
                    break # Exit inner loop for win/hardcore game over screens

                elif not self.playing and self.running:
                    # Should not happen if logic is correct, but acts as a safety break
                    print("Warning: Level ended unexpectedly. Breaking inner loop.")
                    break
            # ========================
            # End of Inner Loop
            # ========================

            if not self.running: break # Exit main loop if quit occurred

            # --- Show Appropriate End Screen ---
            if self.game_won:
                self.show_win_screen() # Waits for key
            elif self.game_over: # Only true in Hardcore mode after death
                self.show_game_over_screen() # Waits for key
            # If it was Normal mode death, restart_level_pending was handled,
            # and neither game_won nor game_over is true, so the outer loop simply continues,
            # leading to a new game attempt starting from level 1 (because game_over was reset).
            # -> Correction: The 'restart_level_pending' should have been handled *inside* the inner loop.
            # The logic above seems correct now: if neither win nor hardcore game over, the outer loop restarts.

        # --- Cleanup ---
        print("Exiting game."); pygame.quit(); sys.exit()