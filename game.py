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
from sprites import Player, Platform, Hazard, Goal, CrawlerEnemy, FlyerEnemy, BossEnemy, TooltipTile # Import sprite classes

LEVEL_NAMES = [
    "Awakening", "Bloom", "Hazards", "Climb", "Ice Intro",
    "Labyrinth", "Dodge Test", "Slide Run", "Gauntlet", "Ice Finale",
    "Islands", "Hazard Maze", "Ice Cavern", "Pillars", "Dunes",
    "Split Paths", "Ice & Fire", "Fortress", "Precision", "Citadel"
]

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
        self.screen_shake = 0
        self.display_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

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
        
        self.volumes = {'Master': 1.0, 'SFX': 1.0, 'Music': 0.3}

        # Sprite groups
        self.all_sprites = pygame.sprite.Group();
        self.platforms = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group();
        self.goals = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.tooltips = pygame.sprite.Group()
        self.player_sprite = pygame.sprite.GroupSingle()

        self._load_assets()
        print(f"--- Game Mode Set To: {self.game_mode.upper()} ---")

    @property
    def edits_used(self):
        """Calculates total blocks changed compared to the original level layout."""
        if not self.active_level_grid or not (0 <= self.current_level_index < len(levels.LEVELS)):
            return 0
        orig = levels.LEVELS[self.current_level_index]
        diff_count = 0
        for r in range(min(len(self.active_level_grid), len(orig))):
            for c in range(min(len(self.active_level_grid[r]), len(orig[r]))):
                if self.active_level_grid[r][c] != orig[r][c]:
                    diff_count += 1
        return diff_count

    @edits_used.setter
    def edits_used(self, val):
        pass

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
        load_music(MUS_BACKGROUND)
        self._apply_volumes()

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
        self.all_sprites.empty(); self.platforms.empty(); self.hazards.empty(); self.goals.empty(); self.enemies.empty(); self.tooltips.empty(); self.player_sprite.empty()
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
                elif tile_char in ('C', 'E'): # Crawler Ground Enemy ("Goomba")
                    enemy = CrawlerEnemy(self, x, y)
                    self.all_sprites.add(enemy); self.enemies.add(enemy)
                elif tile_char == 'B': # Flyer Airborne Enemy ("Bat")
                    flyer = FlyerEnemy(self, x, y)
                    self.all_sprites.add(flyer); self.enemies.add(flyer)
                elif tile_char == 'Z': # Boss Enemy
                    boss = BossEnemy(self, x, y)
                    self.all_sprites.add(boss); self.enemies.add(boss)
                elif tile_char == 'T': # Tooltip
                    tip = TooltipTile(x, y, "Use Edits to reach the goal!")
                    self.all_sprites.add(tip); self.tooltips.add(tip)
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
                    if event.key == pygame.K_ESCAPE: 
                        self.show_pause_menu()
                    elif event.key == pygame.K_e:
                        self.editing = False
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
                    
                    # Check UI clicks
                    palette_x_start = SCREEN_WIDTH / 2 - 70
                    palette_y = 95
                    block_keys = ['X', 'S', 'F', 'I']
                    clicked_ui = False
                    for i, block_key in enumerate(block_keys):
                        bx = palette_x_start + i * 40
                        if bx <= mouse_x <= bx + TILE_SIZE and palette_y <= mouse_y <= palette_y + TILE_SIZE:
                            if event.button == 1: self.selected_block_type = block_key
                            clicked_ui = True
                            break
                    if clicked_ui: continue

                    c = int((mouse_x - self.level_offset_x) // TILE_SIZE)
                    r = int((mouse_y - self.level_offset_y) // TILE_SIZE)
                    if 0 <= r < len(self.active_level_grid) and 0 <= c < len(self.active_level_grid[0]):
                        if event.button == 1: # Left
                            block_rect = pygame.Rect(self.level_offset_x + c * TILE_SIZE, self.level_offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                            # Do not allow placing a platform block on top of the player's active body or enemies
                            if self.player and block_rect.colliderect(self.player.rect.inflate(-2, -2)):
                                pass
                            elif any(block_rect.colliderect(e.rect) for e in self.enemies):
                                pass
                            elif self.active_level_grid[r][c] == '.':
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
                    if event.key == pygame.K_ESCAPE: 
                        self.show_pause_menu()
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

    def add_shake(self, intensity):
        self.screen_shake = max(self.screen_shake, intensity)

    def _update(self):
        """Updates all game objects and checks game conditions."""
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - 1)
            
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
            self.display_surface.blit(self.img_background, (0, 0))
        else:
            self.display_surface.fill(COLOR_BG)
        self.all_sprites.draw(self.display_surface)

        # --- Draw Player Overhead Healthbar ---
        if self.player and self.player_sprite.sprite and self.player.alive() and self.player.state != 'dying' and self.player.visible:
            bar_w = 16
            bar_h = 3
            bar_x = self.player.rect.centerx - bar_w // 2
            bar_y = self.player.rect.top - 6
            # Background / Border
            pygame.draw.rect(self.display_surface, (20, 20, 25), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(self.display_surface, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h))
            
            # Health width & color: starts green, turns red when hit
            pct = max(0.0, min(1.0, self.player.health / self.player.max_health))
            fill_w = int(bar_w * pct)
            if self.player.health == self.player.max_health:
                health_color = (60, 230, 60) # Vibrant Green
            elif self.player.health == 2:
                health_color = (240, 110, 30) # Orange/Red when hit
            else:
                health_color = (230, 40, 40) # Bright Red
            
            if fill_w > 0:
                pygame.draw.rect(self.display_surface, health_color, (bar_x, bar_y, fill_w, bar_h))

        # --- Draw Editor ---
        if self.editing:
            # Draw overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(COLOR_UI_BG)
            self.display_surface.blit(overlay, (0, 0))
            
            # Draw subtle grid
            for r in range(len(self.active_level_grid)):
                for c in range(len(self.active_level_grid[0])):
                    rect = pygame.Rect(self.level_offset_x + c * TILE_SIZE, self.level_offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.display_surface, COLOR_GRID, rect, 1)

            # Highlight modified / edited cells
            if 0 <= self.current_level_index < len(levels.LEVELS):
                orig = levels.LEVELS[self.current_level_index]
                pulse = (pygame.time.get_ticks() // 250) % 2
                for r in range(min(len(self.active_level_grid), len(orig))):
                    for c in range(min(len(self.active_level_grid[r]), len(orig[r]))):
                        if self.active_level_grid[r][c] != orig[r][c]:
                            rx = self.level_offset_x + c * TILE_SIZE
                            ry = self.level_offset_y + r * TILE_SIZE
                            rect = pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE)
                            edit_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                            if self.active_level_grid[r][c] != '.':
                                # Added or modified block: highlight in bright gold/yellow glow
                                fill_color = (255, 220, 0, 80 if pulse else 120)
                                border_color = (255, 240, 90) if pulse else (255, 190, 0)
                                edit_surf.fill(fill_color)
                                self.display_surface.blit(edit_surf, (rx, ry))
                                pygame.draw.rect(self.display_surface, border_color, rect, 2)
                            else:
                                # Removed block: highlight empty slot in soft red with an indicator
                                fill_color = (255, 60, 60, 70 if pulse else 110)
                                border_color = (255, 100, 100) if pulse else (200, 50, 50)
                                edit_surf.fill(fill_color)
                                self.display_surface.blit(edit_surf, (rx, ry))
                                pygame.draw.rect(self.display_surface, border_color, rect, 2)
                                pygame.draw.line(self.display_surface, border_color, (rx + 3, ry + 3), (rx + TILE_SIZE - 4, ry + TILE_SIZE - 4), 1)
                                pygame.draw.line(self.display_surface, border_color, (rx + TILE_SIZE - 4, ry + 3), (rx + 3, ry + TILE_SIZE - 4), 1)
            
            # Highlight hovered cell
            mouse_x, mouse_y = pygame.mouse.get_pos()
            c = int((mouse_x - self.level_offset_x) // TILE_SIZE)
            r = int((mouse_y - self.level_offset_y) // TILE_SIZE)
            if 0 <= r < len(self.active_level_grid) and 0 <= c < len(self.active_level_grid[0]):
                highlight = pygame.Rect(self.level_offset_x + c * TILE_SIZE, self.level_offset_y + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                on_player = self.player and highlight.colliderect(self.player.rect.inflate(-2, -2))
                hl_color = COLOR_LOSE if on_player else COLOR_HIGHLIGHT
                pygame.draw.rect(self.display_surface, hl_color, highlight, 2)
            
            # Draw UI Panel
            if self.title_font and self.default_font:
                draw_text(self.display_surface, "EDIT MODE (Paused)", 24, SCREEN_WIDTH / 2, 30, self.title_font, COLOR_WIN)
                total_edits = self.edits_used
                color_score = COLOR_WIN if total_edits <= MAX_EDITS_FOR_FULL_POINTS else COLOR_TITLE
                draw_text(self.display_surface, f"Edits Used: {total_edits} (Par: {MAX_EDITS_FOR_FULL_POINTS})", 12, SCREEN_WIDTH / 2, 70, self.default_font, color_score)
                
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
                            pygame.draw.rect(self.display_surface, COLOR_WIN, (bx - 4, palette_y - 4, TILE_SIZE + 8, TILE_SIZE + 8), 2)
                        self.display_surface.blit(img, (bx, palette_y))
                        # Number hint
                        draw_text(self.display_surface, str(i+1), 8, bx + TILE_SIZE/2, palette_y + TILE_SIZE + 8, self.small_font, COLOR_TEXT)

                draw_text(self.display_surface, "Left Click: Place | Right Click: Remove | Z: Undo | R: Hard Reset Level", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 30, self.small_font, COLOR_INFO)
                draw_text(self.display_surface, "(Yellow border = Added block | Red X = Removed block)", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 15, self.small_font, COLOR_TITLE)

        # --- Draw HUD ---
        if self.small_font:  # Draw Level Text
            draw_text(self.display_surface, f"Lvl: {self.current_level_index + 1}/{self.total_levels}",
                      8, SCREEN_WIDTH - 35, 5, self.small_font, COLOR_LEVEL)
                      
        # --- Draw Tooltips ---
        if self.player and self.player.alive():
            for tip in self.tooltips:
                if tip.rect.colliderect(self.player.rect.inflate(30, 30)):
                    draw_text(self.display_surface, tip.text, 12, tip.rect.centerx, tip.rect.top - 20, self.default_font, COLOR_WIN)

        # --- Draw Hearts ---
        if self.img_heart and self.player:  # Check heart image loaded and player exists
            heart_x = 10
            heart_y = 10
            heart_spacing = (self.img_heart.get_width() if self.img_heart else TILE_SIZE) + 4  # Spacing between hearts

            # Draw filled hearts for current health
            for i in range(self.player.health):
                self.display_surface.blit(self.img_heart, (heart_x + i * heart_spacing, heart_y))

            # Optional: Draw empty hearts for missing health
            if self.img_heart_empty:
                for i in range(self.player.health, self.player.max_health):
                    self.display_surface.blit(self.img_heart_empty, (heart_x + i * heart_spacing, heart_y))
                    
        # Apply Screen Shake and Blit to actual screen
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        
        # Clear physical screen first (to avoid artifacts from shake)
        self.screen.fill(COLOR_BG)
        self.screen.blit(self.display_surface, (shake_x, shake_y))
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

    def _apply_volumes(self):
        master = self.volumes['Master']
        sfx_vol = self.volumes['SFX'] * master
        music_vol = self.volumes['Music'] * master
        
        if self.sound_jump: self.sound_jump.set_volume(0.2 * sfx_vol)
        if self.sound_hit: self.sound_hit.set_volume(1.0 * sfx_vol)
        if self.sound_win_level: self.sound_win_level.set_volume(1.0 * sfx_vol)
        if self.sound_win_game: self.sound_win_game.set_volume(1.0 * sfx_vol)
        if self.sound_game_over: self.sound_game_over.set_volume(1.0 * sfx_vol)
        pygame.mixer.music.set_volume(music_vol)

    def show_pause_menu(self):
        """Displays the unified pause menu with tabs, sliders, and level select."""
        menu_active = True
        
        # Capture current game frame to display as frozen backdrop
        bg_snapshot = self.screen.copy()
        
        # Tabs: 0: "MENU", 1: "AUDIO", 2: "CONTROLS"
        TABS = ["MENU", "AUDIO SETTINGS", "CONTROLS"]
        current_tab = 0
        
        # Menu options for Tab 0
        menu_options = [
            ("RESUME GAME", "Return directly to your game", COLOR_WIN),
            ("RESTART LEVEL", "Start current level over from start", COLOR_TITLE),
            ("LEVEL SELECT", "Choose any level (Dev / Testing Portal)", COLOR_INFO),
            ("AUDIO SETTINGS", "Adjust Master, Music, and SFX volumes", (210, 190, 255)),
            ("CONTROLS & HELP", "View movement, dodge, and editor keys", (180, 220, 255)),
            ("QUIT TO TITLE", "Save progress and return to Title Screen", COLOR_LOSE)
        ]
        selected_menu_idx = 0
        
        # Audio rows for Tab 1
        audio_keys = ["Master", "SFX", "Music"]
        audio_labels = {
            "Master": "MASTER VOLUME",
            "SFX": "SOUND EFFECTS",
            "Music": "MUSIC VOLUME"
        }
        selected_audio_idx = 0  # 0-2: sliders, 3: test sound, 4: reset defaults, 5: resume
        dragging_slider = None

        # Modal Box Layout (Centered)
        modal_w, modal_h = 640, 520
        modal_x = (SCREEN_WIDTH - modal_w) // 2
        modal_y = (SCREEN_HEIGHT - modal_h) // 2
        modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        while menu_active and self.running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            mouse_held = pygame.mouse.get_pressed()[0]
            
            if not mouse_held:
                dragging_slider = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.playing = False
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_clicked = True
                    elif event.button == 4:  # Wheel Up
                        if current_tab == 0:
                            selected_menu_idx = (selected_menu_idx - 1) % len(menu_options)
                        elif current_tab == 1 and selected_audio_idx < len(audio_keys):
                            k = audio_keys[selected_audio_idx]
                            self.volumes[k] = round(min(1.0, self.volumes[k] + 0.05), 2)
                            self._apply_volumes()
                    elif event.button == 5:  # Wheel Down
                        if current_tab == 0:
                            selected_menu_idx = (selected_menu_idx + 1) % len(menu_options)
                        elif current_tab == 1 and selected_audio_idx < len(audio_keys):
                            k = audio_keys[selected_audio_idx]
                            self.volumes[k] = round(max(0.0, self.volumes[k] - 0.05), 2)
                            self._apply_volumes()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        dragging_slider = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if current_tab != 0:
                            current_tab = 0
                        else:
                            menu_active = False  # Resume
                    elif event.key == pygame.K_TAB:
                        current_tab = (current_tab + 1) % len(TABS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if current_tab == 0:
                            selected_menu_idx = (selected_menu_idx + 1) % len(menu_options)
                        elif current_tab == 1:
                            selected_audio_idx = (selected_audio_idx + 1) % 6
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if current_tab == 0:
                            selected_menu_idx = (selected_menu_idx - 1) % len(menu_options)
                        elif current_tab == 1:
                            selected_audio_idx = (selected_audio_idx - 1) % 6
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if current_tab == 1 and selected_audio_idx < len(audio_keys):
                            k = audio_keys[selected_audio_idx]
                            self.volumes[k] = round(max(0.0, self.volumes[k] - 0.1), 2)
                            self._apply_volumes()
                            if self.sound_jump: self.sound_jump.play()
                        else:
                            current_tab = (current_tab - 1) % len(TABS)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if current_tab == 1 and selected_audio_idx < len(audio_keys):
                            k = audio_keys[selected_audio_idx]
                            self.volumes[k] = round(min(1.0, self.volumes[k] + 0.1), 2)
                            self._apply_volumes()
                            if self.sound_jump: self.sound_jump.play()
                        else:
                            current_tab = (current_tab + 1) % len(TABS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if current_tab == 0:
                            if selected_menu_idx == 0:  # Resume
                                menu_active = False
                            elif selected_menu_idx == 1:  # Restart Level
                                self.editing = False
                                self._load_level(self.current_level_index, hard_reset=True)
                                menu_active = False
                            elif selected_menu_idx == 2:  # Level Select
                                chosen = self.show_level_select_screen()
                                if chosen is not None:
                                    self.editing = False
                                    self.current_level_index = chosen
                                    self._load_level(chosen, hard_reset=True)
                                    menu_active = False
                                else:
                                    bg_snapshot = self.screen.copy()
                            elif selected_menu_idx == 3:  # Audio Settings
                                current_tab = 1
                            elif selected_menu_idx == 4:  # Controls Guide
                                current_tab = 2
                            elif selected_menu_idx == 5:  # Quit to Title
                                self.playing = False
                                menu_active = False
                        elif current_tab == 1:
                            if selected_audio_idx == 3:  # Test Sound
                                if self.sound_jump: self.sound_jump.play()
                            elif selected_audio_idx == 4:  # Reset Defaults
                                self.volumes = {'Master': 1.0, 'SFX': 1.0, 'Music': 0.3}
                                self._apply_volumes()
                                if self.sound_jump: self.sound_jump.play()
                            elif selected_audio_idx == 5:  # Resume
                                menu_active = False
                        elif current_tab == 2:
                            menu_active = False

            # --- RENDER PAUSE MENU ---
            # Draw frozen game backdrop and dark dim overlay
            self.screen.blit(bg_snapshot, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 6, 14, 215))
            self.screen.blit(overlay, (0, 0))

            # Modal Box
            pygame.draw.rect(self.screen, (24, 20, 32), modal_rect, border_radius=12)
            pygame.draw.rect(self.screen, (75, 65, 95), modal_rect, width=2, border_radius=12)
            pygame.draw.rect(self.screen, (40, 34, 52), modal_rect.inflate(-4, -4), width=1, border_radius=10)
            pygame.draw.line(self.screen, COLOR_TITLE, (modal_x + 25, modal_y + 2), (modal_x + modal_w - 25, modal_y + 2), width=3)

            # Close [X] Button
            close_rect = pygame.Rect(modal_x + modal_w - 38, modal_y + 14, 24, 24)
            close_hover = close_rect.collidepoint(mouse_pos)
            pygame.draw.rect(self.screen, (190, 45, 55) if close_hover else (45, 38, 55), close_rect, border_radius=4)
            pygame.draw.rect(self.screen, (255, 120, 120) if close_hover else (80, 70, 95), close_rect, 1, border_radius=4)
            draw_text(self.screen, "X", 10, close_rect.centerx, close_rect.top + 4, self.default_font, (255, 255, 255))
            if close_hover and mouse_clicked:
                menu_active = False

            # Title Header
            draw_text(self.screen, "PAUSED", 26, SCREEN_WIDTH // 2, modal_y + 14, self.title_font, COLOR_TITLE)
            lvl_name = LEVEL_NAMES[self.current_level_index] if (0 <= self.current_level_index < len(LEVEL_NAMES)) else f"Level {self.current_level_index + 1}"
            draw_text(self.screen, f"-- LEVEL {self.current_level_index + 1}: {lvl_name.upper()} --", 10, SCREEN_WIDTH // 2, modal_y + 44, self.default_font, COLOR_INFO)

            # Tab Strip
            tab_w, tab_h, tab_gap = 175, 32, 12
            total_tabs_w = len(TABS) * tab_w + (len(TABS) - 1) * tab_gap
            tab_start_x = modal_x + (modal_w - total_tabs_w) // 2
            tab_y = modal_y + 68

            for t_idx, t_name in enumerate(TABS):
                t_rect = pygame.Rect(tab_start_x + t_idx * (tab_w + tab_gap), tab_y, tab_w, tab_h)
                t_hover = t_rect.collidepoint(mouse_pos)
                if t_hover and mouse_clicked:
                    current_tab = t_idx

                if t_idx == current_tab:
                    pygame.draw.rect(self.screen, (60, 46, 82), t_rect, border_radius=6)
                    pygame.draw.rect(self.screen, COLOR_TITLE, t_rect, 2, border_radius=6)
                    draw_text(self.screen, t_name, 10, t_rect.centerx, t_rect.top + 8, self.default_font, COLOR_TITLE)
                else:
                    pygame.draw.rect(self.screen, (40, 32, 54) if t_hover else (28, 22, 38), t_rect, border_radius=6)
                    pygame.draw.rect(self.screen, COLOR_INFO if t_hover else (60, 52, 78), t_rect, 1, border_radius=6)
                    draw_text(self.screen, t_name, 10, t_rect.centerx, t_rect.top + 8, self.default_font, COLOR_TEXT if t_hover else (150, 150, 170))

            # --- TAB 0: MENU ---
            if current_tab == 0:
                btn_w, btn_h, btn_gap = 460, 46, 10
                btn_x = modal_x + (modal_w - btn_w) // 2
                start_btn_y = modal_y + 116

                for idx, (btn_title, btn_desc, btn_color) in enumerate(menu_options):
                    btn_rect = pygame.Rect(btn_x, start_btn_y + idx * (btn_h + btn_gap), btn_w, btn_h)
                    hovered = btn_rect.collidepoint(mouse_pos)
                    if hovered:
                        selected_menu_idx = idx

                    is_active = (selected_menu_idx == idx)
                    bg_col = (62, 48, 82) if is_active else (32, 26, 44)
                    border_col = btn_color if is_active else (65, 58, 85)
                    border_thickness = 2 if is_active else 1

                    pygame.draw.rect(self.screen, bg_col, btn_rect, border_radius=8)
                    pygame.draw.rect(self.screen, border_col, btn_rect, border_thickness, border_radius=8)

                    title_prefix = "> " if is_active else "  "
                    title_suffix = " <" if is_active else ""
                    draw_text(self.screen, f"{title_prefix}{btn_title}{title_suffix}", 12, btn_rect.centerx, btn_rect.top + 8, self.default_font, btn_color if is_active else COLOR_TEXT)
                    draw_text(self.screen, btn_desc, 8, btn_rect.centerx, btn_rect.top + 28, self.small_font, (220, 220, 230) if is_active else (130, 130, 150))

                    if hovered and mouse_clicked:
                        if idx == 0:  # Resume
                            menu_active = False
                        elif idx == 1:  # Restart Level
                            self.editing = False
                            self._load_level(self.current_level_index, hard_reset=True)
                            menu_active = False
                        elif idx == 2:  # Level Select
                            chosen = self.show_level_select_screen()
                            if chosen is not None:
                                self.editing = False
                                self.current_level_index = chosen
                                self._load_level(chosen, hard_reset=True)
                                menu_active = False
                            else:
                                bg_snapshot = self.screen.copy()
                        elif idx == 3:  # Audio Settings
                            current_tab = 1
                        elif idx == 4:  # Controls Guide
                            current_tab = 2
                        elif idx == 5:  # Quit to Title
                            self.playing = False
                            menu_active = False

            # --- TAB 1: AUDIO SETTINGS ---
            elif current_tab == 1:
                start_audio_y = modal_y + 124
                row_h = 56
                row_gap = 10
                row_w = modal_w - 70
                row_x = modal_x + 35

                for idx, k in enumerate(audio_keys):
                    row_y = start_audio_y + idx * (row_h + row_gap)
                    row_rect = pygame.Rect(row_x, row_y, row_w, row_h)
                    
                    is_row_selected = (selected_audio_idx == idx)
                    pygame.draw.rect(self.screen, (32, 26, 42), row_rect, border_radius=8)
                    pygame.draw.rect(self.screen, COLOR_TITLE if is_row_selected else (60, 52, 78), row_rect, 2 if is_row_selected else 1, border_radius=8)

                    # Label
                    label_str = audio_labels[k]
                    draw_text(self.screen, label_str, 12, row_rect.left + 105, row_y + 19, self.default_font, COLOR_TITLE if is_row_selected else COLOR_TEXT)

                    # Percentage
                    pct_val = int(round(self.volumes[k] * 100))
                    draw_text(self.screen, f"{pct_val}%", 12, row_rect.left + 235, row_y + 19, self.default_font, COLOR_WIN if pct_val > 0 else COLOR_LOSE)

                    # Minus Button [-]
                    minus_rect = pygame.Rect(row_rect.left + 270, row_y + 12, 34, 32)
                    m_hover = minus_rect.collidepoint(mouse_pos)
                    pygame.draw.rect(self.screen, (60, 48, 80) if m_hover else (42, 34, 56), minus_rect, border_radius=6)
                    pygame.draw.rect(self.screen, COLOR_TITLE if m_hover else (80, 72, 100), minus_rect, 1, border_radius=6)
                    draw_text(self.screen, "-", 14, minus_rect.centerx, minus_rect.top + 6, self.default_font, COLOR_TEXT)
                    if m_hover and mouse_clicked:
                        selected_audio_idx = idx
                        self.volumes[k] = round(max(0.0, self.volumes[k] - 0.1), 2)
                        self._apply_volumes()
                        if self.sound_jump: self.sound_jump.play()

                    # Slider Track
                    track_rect = pygame.Rect(row_rect.left + 316, row_y + 18, 185, 20)
                    t_hover = track_rect.collidepoint(mouse_pos)
                    pygame.draw.rect(self.screen, (18, 14, 25), track_rect, border_radius=6)
                    
                    fill_w = int(track_rect.width * self.volumes[k])
                    if fill_w > 0:
                        fill_rect = pygame.Rect(track_rect.x, track_rect.y, fill_w, track_rect.height)
                        pygame.draw.rect(self.screen, (70, 210, 180), fill_rect, border_radius=6)
                    
                    pygame.draw.rect(self.screen, (110, 100, 140) if t_hover else (65, 55, 85), track_rect, 1, border_radius=6)
                    
                    handle_x = track_rect.x + fill_w
                    handle_rect = pygame.Rect(handle_x - 5, track_rect.y - 3, 10, track_rect.height + 6)
                    pygame.draw.rect(self.screen, (255, 255, 255), handle_rect, border_radius=3)
                    pygame.draw.rect(self.screen, COLOR_TITLE, handle_rect, 1, border_radius=3)

                    # Slider Click & Drag
                    if t_hover and mouse_clicked:
                        selected_audio_idx = idx
                        dragging_slider = k
                        rel = (mouse_pos[0] - track_rect.x) / track_rect.width
                        self.volumes[k] = round(max(0.0, min(1.0, rel)), 2)
                        self._apply_volumes()
                    if dragging_slider == k:
                        rel = (mouse_pos[0] - track_rect.x) / track_rect.width
                        self.volumes[k] = round(max(0.0, min(1.0, rel)), 2)
                        self._apply_volumes()

                    # Plus Button [+]
                    plus_rect = pygame.Rect(row_rect.left + 512, row_y + 12, 34, 32)
                    p_hover = plus_rect.collidepoint(mouse_pos)
                    pygame.draw.rect(self.screen, (60, 48, 80) if p_hover else (42, 34, 56), plus_rect, border_radius=6)
                    pygame.draw.rect(self.screen, COLOR_TITLE if p_hover else (80, 72, 100), plus_rect, 1, border_radius=6)
                    draw_text(self.screen, "+", 14, plus_rect.centerx, plus_rect.top + 6, self.default_font, COLOR_TEXT)
                    if p_hover and mouse_clicked:
                        selected_audio_idx = idx
                        self.volumes[k] = round(min(1.0, self.volumes[k] + 0.1), 2)
                        self._apply_volumes()
                        if self.sound_jump: self.sound_jump.play()

                # Action Buttons inside Audio tab
                btn_audio_y = start_audio_y + 3 * (row_h + row_gap) + 12
                test_rect = pygame.Rect(modal_x + 50, btn_audio_y, 250, 40)
                test_hover = test_rect.collidepoint(mouse_pos)
                if test_hover: selected_audio_idx = 3
                is_test_sel = (selected_audio_idx == 3)
                pygame.draw.rect(self.screen, (62, 48, 82) if is_test_sel else (32, 26, 44), test_rect, border_radius=8)
                pygame.draw.rect(self.screen, COLOR_INFO if is_test_sel else (65, 58, 85), test_rect, 2 if is_test_sel else 1, border_radius=8)
                draw_text(self.screen, "TEST SOUND (SFX)", 10, test_rect.centerx, test_rect.top + 13, self.default_font, COLOR_INFO if is_test_sel else COLOR_TEXT)
                if test_hover and mouse_clicked:
                    if self.sound_jump: self.sound_jump.play()

                reset_rect = pygame.Rect(modal_x + 340, btn_audio_y, 250, 40)
                reset_hover = reset_rect.collidepoint(mouse_pos)
                if reset_hover: selected_audio_idx = 4
                is_reset_sel = (selected_audio_idx == 4)
                pygame.draw.rect(self.screen, (62, 48, 82) if is_reset_sel else (32, 26, 44), reset_rect, border_radius=8)
                pygame.draw.rect(self.screen, COLOR_TITLE if is_reset_sel else (65, 58, 85), reset_rect, 2 if is_reset_sel else 1, border_radius=8)
                draw_text(self.screen, "RESET DEFAULTS", 10, reset_rect.centerx, reset_rect.top + 13, self.default_font, COLOR_TITLE if is_reset_sel else COLOR_TEXT)
                if reset_hover and mouse_clicked:
                    self.volumes = {'Master': 1.0, 'SFX': 1.0, 'Music': 0.3}
                    self._apply_volumes()
                    if self.sound_jump: self.sound_jump.play()

                # Bottom Return Button
                done_rect = pygame.Rect(modal_x + 180, btn_audio_y + 54, 280, 42)
                done_hover = done_rect.collidepoint(mouse_pos)
                if done_hover: selected_audio_idx = 5
                is_done_sel = (selected_audio_idx == 5)
                pygame.draw.rect(self.screen, (65, 52, 88) if is_done_sel else (35, 28, 48), done_rect, border_radius=8)
                pygame.draw.rect(self.screen, COLOR_WIN if is_done_sel else (75, 68, 95), done_rect, 2 if is_done_sel else 1, border_radius=8)
                draw_text(self.screen, "APPLY & RESUME GAME", 12, done_rect.centerx, done_rect.top + 13, self.default_font, COLOR_WIN if is_done_sel else COLOR_TEXT)
                if done_hover and mouse_clicked:
                    menu_active = False

            # --- TAB 2: CONTROLS ---
            elif current_tab == 2:
                card_y = modal_y + 116
                card_w = 275
                card_h = 270

                # Left Card: Player Controls
                left_card = pygame.Rect(modal_x + 35, card_y, card_w, card_h)
                pygame.draw.rect(self.screen, (30, 24, 40), left_card, border_radius=8)
                pygame.draw.rect(self.screen, (65, 55, 85), left_card, 1, border_radius=8)
                draw_text(self.screen, "PLAYER CONTROLS", 12, left_card.centerx, left_card.top + 12, self.default_font, COLOR_TITLE)
                pygame.draw.line(self.screen, (55, 48, 72), (left_card.left + 15, left_card.top + 34), (left_card.right - 15, left_card.top + 34))

                player_ctrls = [
                    ("Move Left/Right", "A / D or Arrows"),
                    ("Jump", "Space / W / Up"),
                    ("Dodge Roll", "Left Shift"),
                    ("Coyote Jump", "100ms Grace Period"),
                    ("Jump Buffer", "150ms Pre-Landing"),
                    ("Goal", "Touch Gold Trophy")
                ]
                for c_i, (action, bind) in enumerate(player_ctrls):
                    draw_text(self.screen, action + ":", 8, left_card.left + 65, left_card.top + 50 + c_i * 34, self.small_font, COLOR_INFO)
                    draw_text(self.screen, bind, 10, left_card.left + 185, left_card.top + 48 + c_i * 34, self.default_font, COLOR_WIN)

                # Right Card: Editor Controls
                right_card = pygame.Rect(modal_x + 330, card_y, card_w, card_h)
                pygame.draw.rect(self.screen, (30, 24, 40), right_card, border_radius=8)
                pygame.draw.rect(self.screen, (65, 55, 85), right_card, 1, border_radius=8)
                draw_text(self.screen, "LEVEL EDITOR CONTROLS", 12, right_card.centerx, right_card.top + 12, self.default_font, COLOR_WIN)
                pygame.draw.line(self.screen, (55, 48, 72), (right_card.left + 15, right_card.top + 34), (right_card.right - 15, right_card.top + 34))

                editor_ctrls = [
                    ("Toggle Edit Mode", "Key E"),
                    ("Place Block", "Left Click"),
                    ("Remove Block", "Right Click"),
                    ("Palette Types", "Keys 1, 2, 3, 4"),
                    ("Undo Last Edit", "Key Z"),
                    ("Hard Reset Level", "Key R")
                ]
                for c_i, (action, bind) in enumerate(editor_ctrls):
                    draw_text(self.screen, action + ":", 8, right_card.left + 65, right_card.top + 50 + c_i * 34, self.small_font, COLOR_INFO)
                    draw_text(self.screen, bind, 10, right_card.left + 185, right_card.top + 48 + c_i * 34, self.default_font, COLOR_TITLE)

                # Bottom Return Button
                ctrl_done_rect = pygame.Rect(modal_x + 180, card_y + card_h + 18, 280, 42)
                ctrl_done_hover = ctrl_done_rect.collidepoint(mouse_pos)
                pygame.draw.rect(self.screen, (65, 52, 88) if ctrl_done_hover else (35, 28, 48), ctrl_done_rect, border_radius=8)
                pygame.draw.rect(self.screen, COLOR_WIN if ctrl_done_hover else (75, 68, 95), ctrl_done_rect, 2 if ctrl_done_hover else 1, border_radius=8)
                draw_text(self.screen, "BACK TO GAME", 12, ctrl_done_rect.centerx, ctrl_done_rect.top + 13, self.default_font, COLOR_WIN if ctrl_done_hover else COLOR_TEXT)
                if ctrl_done_hover and mouse_clicked:
                    menu_active = False

            # Footer
            draw_text(self.screen, "Click any option or use WASD / Arrow Keys + ENTER  |  ESC to Resume", 8, SCREEN_WIDTH // 2, modal_rect.bottom - 22, self.small_font, (160, 160, 185))

            pygame.display.flip()

    def show_level_select_screen(self):
        """Displays a retro Level Select menu with a visual grid of level cards."""
        if not self.running: return None

        total = len(levels.LEVELS)
        selected = self.current_level_index if (0 <= self.current_level_index < total) else 0

        cols = 5
        rows = (total + cols - 1) // cols
        card_w, card_h = 150, 70
        gap_x, gap_y = 16, 16
        grid_w = cols * card_w + (cols - 1) * gap_x
        grid_h = rows * card_h + (rows - 1) * gap_y
        start_x = (SCREEN_WIDTH - grid_w) // 2
        start_y = (SCREEN_HEIGHT - grid_h) // 2 + 10

        menu_active = True

        while menu_active and self.running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return selected
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        selected = (selected + 1) % total
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        selected = (selected - 1) % total
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if selected + cols < total:
                            selected += cols
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if selected - cols >= 0:
                            selected -= cols
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_clicked = True

            # Background
            if self.img_background:
                self.screen.blit(self.img_background, (0, 0))
                dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                dark_overlay.fill((10, 10, 20, 220))
                self.screen.blit(dark_overlay, (0, 0))
            else:
                self.screen.fill(COLOR_BG)

            # Header
            draw_text(self.screen, "LEVEL SELECT", 26, SCREEN_WIDTH / 2, 35, self.title_font, COLOR_TITLE)
            draw_text(self.screen, "DEVELOPER / TESTING PORTAL", 10, SCREEN_WIDTH / 2, 68, self.default_font, COLOR_INFO)

            # Draw Level Cards
            for idx in range(total):
                r = idx // cols
                c = idx % cols
                card_x = start_x + c * (card_w + gap_x)
                card_y = start_y + r * (card_h + gap_y)
                card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

                # Check mouse hover
                if card_rect.collidepoint(mouse_pos):
                    selected = idx
                    if mouse_clicked:
                        return idx

                is_selected = (idx == selected)

                # Retro Card Styling
                bg_color = (65, 50, 85) if is_selected else (30, 25, 40)
                border_color = COLOR_TITLE if is_selected else (70, 70, 95)
                border_width = 3 if is_selected else 1

                pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=6)
                pygame.draw.rect(self.screen, border_color, card_rect, border_width, border_radius=6)

                # Level Number
                lvl_str = f"LVL {idx + 1:02d}"
                lvl_color = COLOR_WIN if is_selected else COLOR_TEXT
                draw_text(self.screen, lvl_str, 12, card_rect.centerx, card_rect.top + 16, self.default_font, lvl_color)

                # Level Name
                name_str = LEVEL_NAMES[idx] if idx < len(LEVEL_NAMES) else f"Level {idx + 1}"
                name_color = COLOR_TITLE if is_selected else COLOR_INFO
                draw_text(self.screen, name_str, 8, card_rect.centerx, card_rect.top + 42, self.small_font, name_color)

            # Clickable Back button
            back_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 45, 220, 30)
            b_hover = back_btn_rect.collidepoint(mouse_pos)
            pygame.draw.rect(self.screen, (55, 42, 75) if b_hover else (32, 26, 42), back_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_TITLE if b_hover else (75, 68, 95), back_btn_rect, 1, border_radius=6)
            draw_text(self.screen, "< BACK TO MENU (ESC)", 10, back_btn_rect.centerx, back_btn_rect.top + 8, self.default_font, COLOR_TITLE if b_hover else COLOR_TEXT)
            if b_hover and mouse_clicked:
                return None

            pygame.display.flip()

        return None

    def show_start_screen(self):
        if not self.title_font or not self.default_font or not self.small_font: print("Cannot show start screen - fonts missing."); self.running = False; return

        waiting = True
        while waiting and self.running:
            self.clock.tick(FPS)

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
            draw_text(self.screen, "--- LEVEL EDITOR & DEV ---", 16, SCREEN_WIDTH / 2, start_y + 115, self.default_font, COLOR_TEXT)
            draw_text(self.screen, "Press 'E' in-game to pause and edit levels!", 12, SCREEN_WIDTH / 2, start_y + 145, self.default_font, COLOR_WIN)
            draw_text(self.screen, "Press 'ESC' anytime for Pause Menu (Settings/Levels)", 12, SCREEN_WIDTH / 2, start_y + 170, self.default_font, COLOR_TITLE)

            # Bottom prompts
            draw_text(self.screen, "Press SPACE / ENTER to Start", 12, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 40, self.default_font, COLOR_TEXT)
            draw_text(self.screen, f"Current Mode: {self.game_mode.upper()} | (ESC to Quit)", 8, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 30, self.small_font, COLOR_INFO)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False
                        self.running = False
                    elif event.key == pygame.K_l:
                        chosen = self.show_level_select_screen()
                        if chosen is not None:
                            self.current_level_index = chosen
                            waiting = False
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.current_level_index = 0
                        waiting = False

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
        first_game = True
        while self.running:
            # --- Reset for a new game attempt ---
            self.game_over = False            # Reset hardcore game over
            self.restart_level_pending = False # Reset normal restart flag
            self.game_won = False
            self.next_level_pending = False
            if first_game:
                first_game = False
            else:
                self.current_level_index = 0      # Reset to level 0 after win / hardcore game over
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