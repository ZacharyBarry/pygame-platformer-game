# sprites.py
import pygame
from constants import (TILE_SIZE, PLAYER_JUMP_STRENGTH, PLAYER_GRAVITY,
                     PLAYER_MOVE_SPEED, # Using this for ground AND air now (unless on ice)
                     PLAYER_ACC, PLAYER_FRICTION, # Primarily for ICE now
                     PLAYER_HIT_DURATION, PLAYER_DEATH_DURATION, PLAYER_DODGE_DURATION,
                     PLAYER_INVINCIBILITY_DURATION, PLAYER_FLICKER_RATE, # <-- Added
                     PLAYER_MAX_HEALTH, # <-- Added
                     PLAYER_ANIMATION_SPEED, IMG_PLAYER_IDLE, IMG_PLAYER_WALK,
                     IMG_PLAYER_DODGE, IMG_PLAYER_HIT, IMG_PLAYER_DEATH,
                     IMG_PLAYER_JUMP, COLOR_LOSE, COLOR_INFO, COLOR_WIN,
                     HAZARD_FLASH_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT)
# Import asset loader
from assets import load_image


# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = None
        self.load_animations()

        # --- Health & Invincibility ---
        self.max_health = PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.invincible = False
        self.invincible_timer = 0
        self.flicker_timer = 0
        self.visible = True # For flickering effect
        # --- End Health ---

        if not self.idle_frames_right:
             print("FATAL: Player init failed - no idle frames loaded.")
             self.image = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.image.fill(COLOR_LOSE)
             self.rect = self.image.get_rect(topleft=(x,y)); self.game.running = False; return

        self.image = self.idle_frames_right[0]
        self.rect = self.image.get_rect(bottomleft=(x, y + TILE_SIZE))
        if self.rect.height > TILE_SIZE: self.rect.bottom = y + TILE_SIZE

        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.bottom)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.on_ice = False
        self.facing_right = True
        self.state = 'idle'
        self.current_frame_idx = 0
        self.last_anim_update = pygame.time.get_ticks()
        self.state_timer = 0

    def load_animations(self):
        # Load right-facing frames first
        idle_r = [load_image(f) for f in IMG_PLAYER_IDLE]; walk_r = [load_image(f) for f in IMG_PLAYER_WALK]
        dodge_r = [load_image(f) for f in IMG_PLAYER_DODGE]; hit_r = [load_image(f) for f in IMG_PLAYER_HIT]
        death_r = [load_image(f) for f in IMG_PLAYER_DEATH]; jump_r = load_image(IMG_PLAYER_JUMP)

        # Filter out None values if loading failed
        self.idle_frames_right = [f for f in idle_r if f]; self.walk_frames_right = [f for f in walk_r if f]
        self.dodge_frames_right = [f for f in dodge_r if f]; self.hit_frames_right = [f for f in hit_r if f]
        self.death_frames_right = [f for f in death_r if f]; self.jump_frame_right = jump_r

        # Basic fallback strategy
        if not self.idle_frames_right: self.idle_frames_right = [self.jump_frame_right] if self.jump_frame_right else []
        if not self.walk_frames_right: self.walk_frames_right = self.idle_frames_right
        if not self.jump_frame_right and self.idle_frames_right: self.jump_frame_right = self.idle_frames_right[0]
        if not self.dodge_frames_right: self.dodge_frames_right = self.idle_frames_right
        if not self.hit_frames_right: self.hit_frames_right = self.idle_frames_right
        if not self.death_frames_right: self.death_frames_right = self.hit_frames_right if self.hit_frames_right else self.idle_frames_right

        # Create flipped versions
        self.idle_frames_left = [pygame.transform.flip(f, True, False) for f in self.idle_frames_right if f]
        self.walk_frames_left = [pygame.transform.flip(f, True, False) for f in self.walk_frames_right if f]
        self.dodge_frames_left = [pygame.transform.flip(f, True, False) for f in self.dodge_frames_right if f]
        self.hit_frames_left = [pygame.transform.flip(f, True, False) for f in self.hit_frames_right if f]
        self.death_frames_left = [pygame.transform.flip(f, True, False) for f in self.death_frames_right if f]
        self.jump_frame_left = pygame.transform.flip(self.jump_frame_right, True, False) if self.jump_frame_right else None

    def jump(self):
        if self.state in ['idle', 'walking'] and self.on_ground:
            self.vel.y = PLAYER_JUMP_STRENGTH
            self.on_ground = False
            self.on_ice = False # Cannot be on ice while jumping
            self.set_state('jumping')
            if self.game.sound_jump: self.game.sound_jump.play()

    def dodge(self):
        if self.state in ['idle', 'walking'] and self.on_ground:
             self.set_state('dodging')

        # --- Modified take_hit ---

    def take_hit(self):
        # Cannot take hit if already dying, dodging, or invincible
        if self.state == 'dying' or self.invincible:
            return

        if self.game.sound_hit:
            self.game.sound_hit.play()

        self.health -= 1
        print(f"Player Hit! Health: {self.health}/{self.max_health}")  # Debug

        if self.health <= 0:
            # Start death sequence
            self.set_state('hit')  # Use 'hit' state animation before 'dying'
            self.vel.x = 0  # Stop horizontal motion during hit stun
        else:
            # Become temporarily invincible
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()
            self.visible = False  # Start flicker by being invisible
            self.flicker_timer = pygame.time.get_ticks()
            # Optional: Add small knockback effect here if desired
            # knockback_dir = 1 if self.facing_right else -1
            # self.vel.x = -knockback_dir * 2 # Small horizontal knockback
            # self.vel.y = -2 # Small upward knockback

    def die(self): # This is now mostly triggered by the 'hit' state finishing when health is 0
        if self.state != 'dying':
             self.set_state('dying')
             self.vel.x = 0; self.vel.y = 0

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state; self.current_frame_idx = 0
            self.last_anim_update = pygame.time.get_ticks(); self.state_timer = pygame.time.get_ticks()

    def update(self):
        """Update player physics, state, animation, and invincibility."""
        now = pygame.time.get_ticks()
        # Start with only base gravity
        self.acc = pygame.math.Vector2(0, PLAYER_GRAVITY)

        # --- Handle Invincibility Timer & Flicker ---
        if self.invincible:
            if now - self.invincible_timer > PLAYER_INVINCIBILITY_DURATION:
                self.invincible = False;
                self.visible = True
            else:
                if now - self.flicker_timer > PLAYER_FLICKER_RATE:
                    self.visible = not self.visible;
                    self.flicker_timer = now
        else:
            self.visible = True

        # --- State Machine Logic ---
        if self.state == 'dying':
            if now - self.state_timer > PLAYER_DEATH_DURATION: self.game.signal_player_fully_dead()
            self.vel.x, self.vel.y, self.acc.x, self.acc.y = 0, 0, 0, 0
        elif self.state == 'hit':
            if now - self.state_timer > PLAYER_HIT_DURATION: self.die()
            self.vel.x, self.acc.x = 0, 0
        elif self.state == 'dodging':
            if now - self.state_timer > PLAYER_DODGE_DURATION: self.set_state('idle')
            self.acc.y, self.vel.y = 0, 0
            # Dodge physics should mimic current ground/air type
            if self.on_ice:
                # Apply friction during slippery dodge, no input accel
                friction_force_x = self.vel.x * PLAYER_FRICTION
                self.acc.x = friction_force_x
            else:
                # Instant stop dodge on normal ground/air
                self.vel.x = 0;
                self.acc.x = 0

        # =========================================================== #
        # <<< START OF CORRECTED ICE MOVEMENT LOGIC >>>               #
        # =========================================================== #
        # --- Movement Logic (Only applies if not dying, hit, or dodging) ---
        elif self.state not in ['dying', 'hit', 'dodging']:
            keys = pygame.key.get_pressed()
            moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
            moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

            if self.on_ice:  # --- ICE PHYSICS ---
                # 1. Determine acceleration ONLY from player input keys
                input_acc_x = 0
                if moving_left:
                    input_acc_x = -PLAYER_ACC  # Apply acceleration left
                    self.facing_right = False
                elif moving_right:
                    input_acc_x = PLAYER_ACC  # Apply acceleration right
                    self.facing_right = True

                # 2. Calculate friction force (always opposes current velocity)
                #    PLAYER_FRICTION should be a SMALL negative value (e.g., -0.05 to -0.15)
                #    A smaller magnitude means less friction / more slide.
                friction_force_x = self.vel.x * PLAYER_FRICTION

                # 3. Combine forces: Apply input acceleration AND friction
                #    The input will gradually overcome friction and existing velocity.
                self.acc.x = input_acc_x + friction_force_x
                # print(f"ICE: vel.x={self.vel.x:.2f}, input_acc={input_acc_x:.2f}, fric={friction_force_x:.2f}, total_acc={self.acc.x:.2f}") # Debug

            else:  # --- NORMAL GROUND or AIR PHYSICS ---
                # Use constant speed control, directly setting velocity
                target_vel_x = 0
                if moving_left:
                    target_vel_x = -PLAYER_MOVE_SPEED
                    self.facing_right = False
                elif moving_right:
                    target_vel_x = PLAYER_MOVE_SPEED
                    self.facing_right = True

                self.vel.x = target_vel_x
                # No horizontal acceleration needed here (acc.x remains 0 from start of update)
                # print(f"NON-ICE: vel.x={self.vel.x:.2f}") # Debug

        # =========================================================== #
        # <<< END OF CORRECTED ICE MOVEMENT LOGIC >>>                 #
        # =========================================================== #

        # --- Apply Physics (if not dying) ---
        if self.state != 'dying':
            # Apply acceleration (gravity + horizontal forces) to velocity
            self.vel += self.acc

            # Limit fall speed
            MAX_Y_VEL = 15;
            self.vel.y = min(self.vel.y, MAX_Y_VEL)

            # --- Move & Collide X ---
            self.pos.x += self.vel.x
            self.rect.centerx = round(self.pos.x)
            # Update hitbox position relative to the new drawing rect position
            # self.hitbox.centerx = self.rect.centerx # Removed if not using persistent hitbox
            self.check_collisions('x')  # Checks collision using temp hitbox, corrects self.rect
            # Update physics position based on final drawing rect AFTER potential collision adjustment
            self.pos.x = self.rect.centerx

            # --- Move & Collide Y ---
            self.pos.y += self.vel.y + 0.5 * self.acc.y
            self.rect.bottom = round(self.pos.y)
            # Update hitbox position relative to the new drawing rect position
            # self.hitbox.midbottom = self.rect.midbottom # Removed if not using persistent hitbox
            self.on_ground = False;
            self.on_ice = False  # Reset before check
            self.check_collisions('y')  # Checks collision using temp hitbox, corrects self.rect, sets flags
            # Update physics position based on final drawing rect AFTER potential collision adjustment
            self.pos.y = self.rect.bottom

            # --- Update State (if not dodging/hit/dying) ---
            if self.state not in ['dodging', 'hit', 'dying']:
                if not self.on_ground:
                    self.set_state('jumping')
                elif abs(self.vel.x) > 0.1:
                    self.set_state('walking')
                else:
                    self.set_state('idle')

        # --- Screen Boundaries (Applied to drawing rect) ---
        if self.rect.left < 0: self.rect.left = 0; self.pos.x = self.rect.centerx; self.vel.x = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH; self.pos.x = self.rect.centerx; self.vel.x = 0

        # --- Final Hitbox Position Update (Removed if not using persistent hitbox) ---
        # self.hitbox.midbottom = self.rect.midbottom

        # --- Animation ---
        self._animate()  # Handles image and visibility

    def check_collisions(self, direction):
        """Checks and resolves collisions with platforms, hazards, goals."""
        if direction == 'x':
            hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
            for platform in hits:
                if self.vel.x > 0: self.rect.right = platform.rect.left
                elif self.vel.x < 0: self.rect.left = platform.rect.right
                self.pos.x = self.rect.centerx
                self.vel.x = 0 # Stop horizontal movement on wall collision

        elif direction == 'y':
            hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
            for platform in hits:
                if self.vel.y > 0: # Moving down (landing)
                    # Check if player bottom just crossed the platform top edge
                     if self.pos.y - self.vel.y <= platform.rect.top + 1.5: # Increased tolerance slightly
                        if self.rect.bottom >= platform.rect.top : # Ensure overlap before snapping
                            self.rect.bottom = platform.rect.top
                            self.pos.y = self.rect.bottom # Sync position vector
                            self.vel.y = 0
                            self.on_ground = True
                            # Check if the platform landed on is ice
                            if hasattr(platform, 'tile_type') and platform.tile_type == 'I':
                                self.on_ice = True
                            # Break if landing on solid ground? Depends if multiple overlaps are possible/problematic.
                            # For simplicity, let the first detected ground determine ice status.
                            # break

                elif self.vel.y < 0: # Moving up (hitting ceiling)
                     # Check if player top just crossed the platform bottom edge
                     player_top_prev = (self.pos.y - self.rect.height) - self.vel.y
                     if player_top_prev >= platform.rect.bottom - 1: # -1 tolerance
                         if self.rect.top <= platform.rect.bottom: # Ensure overlap
                            self.rect.top = platform.rect.bottom
                            self.pos.y = self.rect.bottom # Sync position vector
                            self.vel.y = 0 # Stop upward movement
                            # break # Stop checking ceilings once one is hit

            # Hazard/Goal collisions (check AFTER platform resolution)
            if self.state not in ['dodging', 'hit', 'dying']:
                # Use spritecollideany for efficiency if just checking for any hit
                if pygame.sprite.spritecollideany(self, self.game.hazards):
                    self.take_hit()
                elif pygame.sprite.spritecollideany(self, self.game.goals):
                     self.game.level_complete() # Check goal only if no hazard hit in same frame


    def _animate(self):
        """Updates the player's image based on state, direction, and visibility."""

        # --- Handle Visibility for Flicker ---
        if not self.visible:
            # If invisible due to flicker, set a blank image or just return
            # Setting self.image to a cached blank surface is more efficient if done often
            # For simplicity, let's just clear the current image visually
            original_image = self.image # Store the current image
            # Create a temporary blank surface of the same size
            blank_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA) # Use SRCALPHA for transparency
            blank_surface.fill((0, 0, 0, 0)) # Fill with transparent color
            self.image = blank_surface
            # Keep the rect the same size and position
            # We don't need to recalculate the rect here, just swap the image surface
            # When self.visible becomes True again, the normal animation logic will restore the correct image
            return # Skip the rest of the animation update for this frame
        # --- End Visibility Handling ---

        # --- Normal Animation Logic ---
        now = pygame.time.get_ticks()
        frames = []
        loop_animation = True
        facing_left = not self.facing_right

        # (Select frame list based on state - no changes here)
        if self.state == 'idle': frames = self.idle_frames_left if facing_left else self.idle_frames_right
        elif self.state == 'walking': frames = self.walk_frames_left if facing_left else self.walk_frames_right
        elif self.state == 'dodging': frames = self.dodge_frames_left if facing_left else self.dodge_frames_right; loop_animation = False
        elif self.state == 'hit': frames = self.hit_frames_left if facing_left else self.hit_frames_right; loop_animation = False
        elif self.state == 'dying': frames = self.death_frames_left if facing_left else self.death_frames_right; loop_animation = False
        elif self.state == 'jumping':
            jump_img = self.jump_frame_left if facing_left else self.jump_frame_right
            if jump_img: self.image = jump_img
            elif not jump_img and self.idle_frames_right:
                 self.image = self.idle_frames_left[0] if facing_left else self.idle_frames_right[0]
            # Ensure rect is updated if jump image changed
            if self.image: # Check if image exists before getting rect
                old_bottom = self.rect.bottom; old_centerx = self.rect.centerx
                self.rect = self.image.get_rect(centerx=old_centerx, bottom=old_bottom)
            return

        num_frames = len(frames)
        if num_frames == 0:
             if self.image is None and self.idle_frames_right: self.image = self.idle_frames_right[0]
             return

        # Update frame index
        if now - self.last_anim_update > PLAYER_ANIMATION_SPEED:
            self.last_anim_update = now
            if loop_animation: self.current_frame_idx = (self.current_frame_idx + 1) % num_frames
            else: self.current_frame_idx = min(self.current_frame_idx + 1, num_frames - 1)

        # Set the new image
        new_image = frames[self.current_frame_idx]
        if self.image != new_image:
            self.image = new_image
            old_bottom = self.rect.bottom; old_centerx = self.rect.centerx
            self.rect = self.image.get_rect(centerx=old_centerx, bottom=old_bottom)


# --- Other Sprite Classes ---
class Platform(pygame.sprite.Sprite):
    """Represents a basic platform tile. Stores its type."""
    def __init__(self, x, y, image, tile_type='?'):
        super().__init__()
        self.image = image
        self.tile_type = tile_type # Store the type ('X', 'S', 'F', 'I', etc.)
        self.grid_pos = (0, 0) # Store grid coordinates for level editor
        if self.image is None:
             print(f"Warning: Platform '{tile_type}' created with no image at ({x},{y}). Using fallback.")
             self.image = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.image.fill(COLOR_INFO)
        self.rect = self.image.get_rect(topleft=(x, y))

class Hazard(pygame.sprite.Sprite):
    """Represents a hazard tile, potentially animated."""
    def __init__(self, x, y, images):
        super().__init__()
        self.images = images if images else []
        if not self.images:
            print(f"Warning: Hazard created with no images at ({x},{y}). Using fallback.")
            img = pygame.Surface((TILE_SIZE, TILE_SIZE)); img.fill(COLOR_LOSE); self.images = [img]
        self.current_image_idx = 0; self.image = self.images[self.current_image_idx]
        self.rect = self.image.get_rect(topleft=(x, y)); self.last_update_time = pygame.time.get_ticks()

    def update(self):
        """Animates the hazard by cycling through its images."""
        if len(self.images) > 1:
            now = pygame.time.get_ticks()
            if now - self.last_update_time > HAZARD_FLASH_SPEED:
                self.last_update_time = now
                self.current_image_idx = (self.current_image_idx + 1) % len(self.images)
                self.image = self.images[self.current_image_idx]

class Goal(pygame.sprite.Sprite):
    """Represents the goal tile."""
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        if self.image is None:
             print(f"Warning: Goal created with no image at ({x},{y}). Using fallback.")
             self.image = pygame.Surface((TILE_SIZE, TILE_SIZE)); self.image.fill(COLOR_WIN)
        self.rect = self.image.get_rect(topleft=(x, y))