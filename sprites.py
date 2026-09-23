# sprites.py
import pygame
import math
from constants import (TILE_SIZE, PLAYER_JUMP_STRENGTH, PLAYER_GRAVITY,
                     PLAYER_MOVE_SPEED, # Using this for ground AND air now (unless on ice)
                     PLAYER_ACC, PLAYER_FRICTION, # Primarily for ICE now
                     PLAYER_HIT_DURATION, PLAYER_DEATH_DURATION, PLAYER_DODGE_DURATION,
                     PLAYER_INVINCIBILITY_DURATION, PLAYER_FLICKER_RATE, # <-- Added
                     PLAYER_MAX_HEALTH, # <-- Added
                     PLAYER_ANIMATION_SPEED, IMG_PLAYER_IDLE, IMG_PLAYER_WALK,
                     IMG_PLAYER_DODGE, IMG_PLAYER_HIT, IMG_PLAYER_DEATH,
                     IMG_PLAYER_JUMP, COLOR_LOSE, COLOR_INFO, COLOR_WIN,
                     HAZARD_FLASH_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT,
                     IMG_ENEMY_CRAWLER, IMG_ENEMY_CRAWLER_SQUASH, IMG_ENEMY_FLYER,
                     ENEMY_ANIMATION_SPEED, CRAWLER_SPEED, FLYER_SPEED,
                     FLYER_WAVE_AMPLITUDE, FLYER_WAVE_FREQ)
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

        # Hitbox: ~5-10% narrower horizontally (shaving 2px, 1px on each side)
        # to make squeezing through single-block (16px) gaps significantly smoother
        self.hitbox_width = max(8, self.rect.width - 2)
        self.hitbox = pygame.Rect(0, 0, self.hitbox_width, self.rect.height)
        self.hitbox.midbottom = self.rect.midbottom

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
            self.hitbox.centerx = round(self.pos.x)
            self.rect.centerx = self.hitbox.centerx
            self.check_collisions('x')
            self.pos.x = self.hitbox.centerx
            self.rect.centerx = self.hitbox.centerx

            # --- Move & Collide Y ---
            self.pos.y += self.vel.y + 0.5 * self.acc.y
            self.hitbox.bottom = round(self.pos.y)
            self.rect.bottom = self.hitbox.bottom
            self.on_ground = False;
            self.on_ice = False  # Reset before check
            self.check_collisions('y')
            self.pos.y = self.hitbox.bottom
            self.rect.bottom = self.hitbox.bottom

            # --- Update State (if not dodging/hit/dying) ---
            if self.state not in ['dodging', 'hit', 'dying']:
                if not self.on_ground:
                    self.set_state('jumping')
                elif abs(self.vel.x) > 0.1:
                    self.set_state('walking')
                else:
                    self.set_state('idle')

        # --- Screen Boundaries (Applied to hitbox and drawing rect) ---
        if self.hitbox.left < 0:
            self.hitbox.left = 0; self.pos.x = self.hitbox.centerx; self.rect.centerx = self.hitbox.centerx; self.vel.x = 0
        if self.hitbox.right > SCREEN_WIDTH:
            self.hitbox.right = SCREEN_WIDTH; self.pos.x = self.hitbox.centerx; self.rect.centerx = self.hitbox.centerx; self.vel.x = 0

        # --- Animation ---
        self._animate()  # Handles image and visibility

    def check_collisions(self, direction):
        """Checks and resolves collisions with platforms, hazards, goals using skinnier hitbox."""
        if direction == 'x':
            hits = [p for p in self.game.platforms if self.hitbox.colliderect(p.rect)]
            for platform in hits:
                if self.vel.x > 0: self.hitbox.right = platform.rect.left
                elif self.vel.x < 0: self.hitbox.left = platform.rect.right
                self.pos.x = self.hitbox.centerx
                self.rect.centerx = self.hitbox.centerx
                self.vel.x = 0 # Stop horizontal movement on wall collision

        elif direction == 'y':
            hits = [p for p in self.game.platforms if self.hitbox.colliderect(p.rect)]
            for platform in hits:
                if self.vel.y > 0: # Moving down (landing)
                    if self.pos.y - self.vel.y <= platform.rect.top + 1.5:
                        if self.hitbox.bottom >= platform.rect.top:
                            self.hitbox.bottom = platform.rect.top
                            self.pos.y = self.hitbox.bottom
                            self.rect.bottom = self.hitbox.bottom
                            self.vel.y = 0
                            self.on_ground = True
                            if hasattr(platform, 'tile_type') and platform.tile_type == 'I':
                                self.on_ice = True

                elif self.vel.y < 0: # Moving up (hitting ceiling)
                    player_top_prev = (self.pos.y - self.hitbox.height) - self.vel.y
                    if player_top_prev >= platform.rect.bottom - 1:
                        if self.hitbox.top <= platform.rect.bottom:
                            self.hitbox.top = platform.rect.bottom
                            self.pos.y = self.hitbox.bottom
                            self.rect.bottom = self.hitbox.bottom
                            self.vel.y = 0

            # Hazard/Goal collisions (check AFTER platform resolution)
            if self.state not in ['dodging', 'hit', 'dying']:
                if any(self.hitbox.colliderect(h.rect) for h in self.game.hazards):
                    self.take_hit()
                elif any(self.hitbox.colliderect(g.rect) for g in self.game.goals):
                    self.game.level_complete()

        # Enemy collisions (check for both x and y movement)
        if self.state not in ['hit', 'dying'] and hasattr(self.game, 'enemies'):
            for enemy in list(self.game.enemies):
                if not getattr(enemy, 'alive', True) or getattr(enemy, 'squashed', False):
                    continue
                if self.hitbox.colliderect(enemy.rect):
                    # Stomp condition: player is falling downwards and player's feet touch enemy top
                    if self.vel.y > 0 and self.hitbox.bottom <= enemy.rect.top + 10:
                        enemy.stomp()
                        self.vel.y = PLAYER_JUMP_STRENGTH * 0.75 # High bounce
                        self.on_ground = False
                        if self.game.sound_hit:
                            self.game.sound_hit.play()
                        break
                    elif self.state == 'dodging':
                        # Rolling/dodging grants immunity through enemies
                        pass
                    elif not self.invincible:
                        self.take_hit()
                        break


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
                old_bottom = self.hitbox.bottom; old_centerx = self.hitbox.centerx
                self.rect = self.image.get_rect(centerx=old_centerx, bottom=old_bottom)
                self.hitbox.height = self.rect.height
                self.hitbox.midbottom = self.rect.midbottom
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
            old_bottom = self.hitbox.bottom; old_centerx = self.hitbox.centerx
            self.rect = self.image.get_rect(centerx=old_centerx, bottom=old_bottom)
            self.hitbox.height = self.rect.height
            self.hitbox.midbottom = self.rect.midbottom


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


# --- Enemy Classes ---
class Enemy(pygame.sprite.Sprite):
    """Base class for all enemy types."""
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.alive = True
        self.squashed = False
        self.squash_timer = 0
        self.image = None
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def stomp(self):
        """Called when player stomps on the enemy."""
        self.kill()

    def update(self):
        pass


class CrawlerEnemy(Enemy):
    """Ground patrol enemy ('Goomba' style). Uses gravity, walks, reverses at walls."""
    def __init__(self, game, x, y, speed=CRAWLER_SPEED):
        super().__init__(game, x, y)
        self.speed = speed
        self.direction = -1 # -1 for left, 1 for right
        self.vel = pygame.math.Vector2(self.direction * self.speed, 0)
        self.pos = pygame.math.Vector2(x + TILE_SIZE // 2, y + TILE_SIZE)

        frames = [load_image(f) for f in IMG_ENEMY_CRAWLER]
        self.walk_frames = [f for f in frames if f]
        if not self.walk_frames:
            fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
            fallback.fill((180, 50, 40))
            self.walk_frames = [fallback]

        squash_img = load_image(IMG_ENEMY_CRAWLER_SQUASH)
        if squash_img:
            self.squash_frame = squash_img
        else:
            fb_sq = pygame.Surface((TILE_SIZE, TILE_SIZE // 2))
            fb_sq.fill((180, 50, 40))
            self.squash_frame = fb_sq

        self.current_frame = 0
        self.last_anim_time = pygame.time.get_ticks()
        self.image = self.walk_frames[0]
        self.rect = self.image.get_rect(bottomleft=(x, y + TILE_SIZE))

    def stomp(self):
        if not self.squashed:
            self.squashed = True
            self.image = self.squash_frame
            old_bottom = self.rect.bottom
            self.rect = self.image.get_rect(midbottom=(self.rect.centerx, old_bottom))
            self.squash_timer = pygame.time.get_ticks()
            self.vel.x = 0
            self.vel.y = 0

    def update(self):
        now = pygame.time.get_ticks()

        # Handle squashed timer
        if self.squashed:
            if now - self.squash_timer > 300:
                self.kill()
            return

        # Animate walking
        if now - self.last_anim_time > ENEMY_ANIMATION_SPEED:
            self.last_anim_time = now
            self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            frame = self.walk_frames[self.current_frame]
            if self.direction > 0:
                self.image = pygame.transform.flip(frame, True, False)
            else:
                self.image = frame

        # Apply gravity
        self.vel.y = min(self.vel.y + PLAYER_GRAVITY, 10)

        # Horizontal movement
        self.vel.x = self.direction * self.speed
        self.pos.x += self.vel.x
        self.rect.centerx = round(self.pos.x)

        # Horizontal collision with platforms
        hits_x = [p for p in self.game.platforms if self.rect.colliderect(p.rect)]
        if hits_x:
            for platform in hits_x:
                if self.direction > 0:
                    self.rect.right = platform.rect.left
                    self.pos.x = self.rect.centerx
                    self.direction = -1
                    break
                elif self.direction < 0:
                    self.rect.left = platform.rect.right
                    self.pos.x = self.rect.centerx
                    self.direction = 1
                    break

        # Screen boundary bounce
        if self.rect.left <= self.game.level_offset_x:
            self.rect.left = self.game.level_offset_x
            self.pos.x = self.rect.centerx
            self.direction = 1
        elif self.rect.right >= SCREEN_WIDTH - self.game.level_offset_x:
            self.rect.right = SCREEN_WIDTH - self.game.level_offset_x
            self.pos.x = self.rect.centerx
            self.direction = -1

        # Vertical movement
        self.pos.y += self.vel.y
        self.rect.bottom = round(self.pos.y)

        # Vertical collision with platforms
        hits_y = [p for p in self.game.platforms if self.rect.colliderect(p.rect)]
        for platform in hits_y:
            if self.vel.y > 0:
                self.rect.bottom = platform.rect.top
                self.pos.y = self.rect.bottom
                self.vel.y = 0
            elif self.vel.y < 0:
                self.rect.top = platform.rect.bottom
                self.pos.y = self.rect.bottom
                self.vel.y = 0

        # Collision with active player
        player = self.game.player
        if player and player.alive() and player.state not in ['hit', 'dying']:
            if self.rect.colliderect(player.hitbox):
                if player.vel.y > 0 and player.hitbox.bottom <= self.rect.top + 10:
                    self.stomp()
                    player.vel.y = PLAYER_JUMP_STRENGTH * 0.75
                    player.on_ground = False
                    if self.game.sound_hit:
                        self.game.sound_hit.play()
                elif player.state == 'dodging':
                    pass
                elif not player.invincible:
                    player.take_hit()


class FlyerEnemy(Enemy):
    """Airborne enemy ('Bat' style). Hovers with wave motion, patrols horizontal air path."""
    def __init__(self, game, x, y, patrol_range=70, speed=FLYER_SPEED):
        super().__init__(game, x, y)
        self.speed = speed
        self.direction = -1
        self.start_x = x
        self.start_y = y
        self.patrol_range = patrol_range
        self.pos_x = float(x)
        self.angle = float((x * 13) % 360) # Randomize initial phase per enemy

        frames = [load_image(f) for f in IMG_ENEMY_FLYER]
        self.fly_frames = [f for f in frames if f]
        if not self.fly_frames:
            fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
            fallback.fill((100, 50, 140))
            self.fly_frames = [fallback]

        self.current_frame = 0
        self.last_anim_time = pygame.time.get_ticks()
        self.image = self.fly_frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))

    def stomp(self):
        """Defeat flying enemy immediately when stomped."""
        self.kill()

    def update(self):
        now = pygame.time.get_ticks()

        # Flapping animation
        if now - self.last_anim_time > ENEMY_ANIMATION_SPEED:
            self.last_anim_time = now
            self.current_frame = (self.current_frame + 1) % len(self.fly_frames)
            frame = self.fly_frames[self.current_frame]
            if self.direction > 0:
                self.image = pygame.transform.flip(frame, True, False)
            else:
                self.image = frame

        # Hover wave
        self.angle += FLYER_WAVE_FREQ
        wave_offset = math.sin(self.angle) * FLYER_WAVE_AMPLITUDE

        # Horizontal movement
        self.pos_x += self.direction * self.speed
        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.start_y + wave_offset)

        # Reversal at patrol boundaries
        if self.pos_x <= self.start_x - self.patrol_range:
            self.direction = 1
        elif self.pos_x >= self.start_x + self.patrol_range:
            self.direction = -1

        # Platform collision (reverses direction on wall)
        hits = [p for p in self.game.platforms if self.rect.colliderect(p.rect)]
        if hits:
            self.direction = -self.direction
            self.pos_x += self.direction * 3

        # Collision with active player
        player = self.game.player
        if player and player.alive() and player.state not in ['hit', 'dying']:
            if self.rect.colliderect(player.hitbox):
                if player.vel.y > 0 and player.hitbox.bottom <= self.rect.top + 10:
                    self.stomp()
                    player.vel.y = PLAYER_JUMP_STRENGTH * 0.75
                    player.on_ground = False
                    if self.game.sound_hit:
                        self.game.sound_hit.play()
                elif player.state == 'dodging':
                    pass
                elif not player.invincible:
                    player.take_hit()