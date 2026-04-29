import pygame
import math
import random
import os
from typing import List, Tuple

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
DARK_BLUE = (0, 17, 34)
BROWN = (101, 67, 33)

class UFO:
    def __init__(self):
        self.x = random.choice([-100, SCREEN_WIDTH + 100])  # Start off-screen
        self.y = random.randint(50, 200)  # Fly at top of screen
        self.target_x = SCREEN_WIDTH - self.x + random.randint(-200, 200)  # Fly across screen
        self.speed = random.uniform(0.8, 1.5)
        self.health = 3  # Takes 3 hits to destroy
        self.max_health = 3
        self.laser_cooldown = 0
        self.laser_frequency = random.randint(60, 120)  # Shoot every 1-2 seconds
        self.wobble = 0  # For floating animation
        self.wobble_speed = random.uniform(0.05, 0.1)
        self.damage_flash = 0  # Flash when taking damage
        
        # Calculate movement direction
        dx = self.target_x - self.x
        distance = abs(dx)
        if distance > 0:
            self.vx = (dx / distance) * self.speed
        else:
            self.vx = self.speed if self.x < SCREEN_WIDTH // 2 else -self.speed
        
        self.vy = random.uniform(-0.2, 0.2)  # Slight vertical drift
    
    def update(self) -> bool:
        """Update UFO position and behavior. Returns True if should be removed."""
        # Move UFO
        self.x += self.vx
        self.y += self.vy
        
        # Floating animation
        self.wobble += self.wobble_speed
        
        # Update laser cooldown
        if self.laser_cooldown > 0:
            self.laser_cooldown -= 1
        
        # Update damage flash
        if self.damage_flash > 0:
            self.damage_flash -= 1
        
        # Remove if off screen
        return self.x < -150 or self.x > SCREEN_WIDTH + 150
    
    def can_shoot_laser(self) -> bool:
        """Check if UFO can shoot a laser."""
        return self.laser_cooldown <= 0
    
    def shoot_laser(self) -> Tuple[float, float]:
        """Shoot a laser and return the target position."""
        self.laser_cooldown = self.laser_frequency
        
        # Aim at a city or random ground position
        target_x = random.randint(0, SCREEN_WIDTH)
        target_y = SCREEN_HEIGHT - 10
        
        return (target_x, target_y)
    
    def take_damage(self) -> bool:
        """Take damage and return True if destroyed."""
        self.health -= 1
        self.damage_flash = 10  # Flash red for 10 frames
        return self.health <= 0
    
    def draw(self, screen: pygame.Surface):
        """Draw the UFO with classy design."""
        # Floating effect
        wobble_y = self.y + math.sin(self.wobble) * 3
        
        # UFO main body - larger metallic saucer
        ufo_width = 80
        ufo_height = 30
        
        # Shadow/depth effect
        shadow_rect = pygame.Rect(self.x - ufo_width//2 + 2, wobble_y - ufo_height//2 + 2, ufo_width, ufo_height)
        pygame.draw.ellipse(screen, (50, 50, 50), shadow_rect)  # Dark shadow
        
        # Main metallic body with gradient effect
        main_rect = pygame.Rect(self.x - ufo_width//2, wobble_y - ufo_height//2, ufo_width, ufo_height)
        if self.damage_flash > 0:
            # Flash red when damaged
            pygame.draw.ellipse(screen, (255, 100, 100), main_rect)
        else:
            # Normal metallic silver
            pygame.draw.ellipse(screen, (180, 180, 200), main_rect)
        
        # Metallic highlight
        highlight_rect = pygame.Rect(self.x - ufo_width//3, wobble_y - ufo_height//3, ufo_width//1.5, ufo_height//2)
        pygame.draw.ellipse(screen, (220, 220, 240), highlight_rect)
        
        # Command dome - more elegant
        dome_width = 50
        dome_height = 35
        dome_rect = pygame.Rect(self.x - dome_width//2, wobble_y - dome_height, dome_width, dome_height)
        
        # Dome shadow
        dome_shadow = pygame.Rect(self.x - dome_width//2 + 1, wobble_y - dome_height + 1, dome_width, dome_height)
        pygame.draw.ellipse(screen, (60, 60, 80), dome_shadow)
        
        # Main dome - translucent blue
        pygame.draw.ellipse(screen, (120, 150, 200), dome_rect)
        
        # Dome highlight
        dome_highlight = pygame.Rect(self.x - dome_width//3, wobble_y - dome_height + 5, dome_width//2, dome_height//2)
        pygame.draw.ellipse(screen, (160, 180, 220), dome_highlight)
        
        # Elegant pulsing lights around the edge
        num_lights = 8
        for i in range(num_lights):
            angle = (i * 360 / num_lights + self.wobble * 30) % 360  # Slow rotating lights
            light_x = self.x + math.cos(math.radians(angle)) * 32
            light_y = wobble_y + math.sin(math.radians(angle)) * 10
            
            # Pulsing effect
            pulse = 0.7 + 0.3 * math.sin(self.wobble * 2 + i)
            light_colors = [
                (255, 100, 100),  # Red
                (100, 255, 100),  # Green  
                (100, 100, 255),  # Blue
                (255, 255, 100),  # Yellow
                (255, 100, 255),  # Magenta
                (100, 255, 255),  # Cyan
                (255, 150, 100),  # Orange
                (150, 100, 255)   # Purple
            ]
            
            color = light_colors[i]
            # Apply pulse to color intensity
            pulsed_color = (int(color[0] * pulse), int(color[1] * pulse), int(color[2] * pulse))
            
            # Draw light with glow effect
            pygame.draw.circle(screen, pulsed_color, (int(light_x), int(light_y)), 4)
            pygame.draw.circle(screen, (255, 255, 255), (int(light_x), int(light_y)), 2)
        
        # Health bar above UFO
        if self.health < self.max_health:
            bar_width = 60
            bar_height = 6
            bar_x = self.x - bar_width // 2
            bar_y = wobble_y - 50
            
            # Background bar
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            
            # Health bar
            health_width = int((self.health / self.max_health) * bar_width)
            health_color = GREEN if self.health > 1 else RED
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
            
            # Bar border
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Thruster effects at the bottom
        for i in range(3):
            thruster_x = self.x - 20 + i * 20
            thruster_y = wobble_y + 12
            thruster_length = random.randint(5, 15)
            thruster_color = (100, 150, 255) if random.random() > 0.5 else (150, 200, 255)
            pygame.draw.line(screen, thruster_color, 
                           (thruster_x, thruster_y), 
                           (thruster_x, thruster_y + thruster_length), 2)

class Laser:
    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = 4.0
        self.width = 3
        self.life = 180  # 3 seconds at 60 FPS
        
        # Calculate velocity
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed
        else:
            self.vx = self.vy = 0
        
        # Visual effects
        self.spark_timer = 0
    
    def update(self) -> bool:
        """Update laser position. Returns True if should be removed."""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.spark_timer += 1
        
        # Check if reached target or off screen
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        reached_target = math.sqrt(dx * dx + dy * dy) < 5
        
        off_screen = (self.x < 0 or self.x > SCREEN_WIDTH or 
                     self.y < 0 or self.y > SCREEN_HEIGHT)
        
        return reached_target or off_screen or self.life <= 0
    
    def draw(self, screen: pygame.Surface):
        """Draw the laser beam."""
        # Main beam
        beam_color = (0, 255, 0)  # Green laser
        start_pos = (self.x - self.vx * 20, self.y - self.vy * 20)  # Trail effect
        end_pos = (self.x, self.y)
        
        # Draw multiple beam segments for thickness
        for i in range(self.width):
            offset = i - self.width // 2
            offset_start = (start_pos[0] + offset, start_pos[1])
            offset_end = (end_pos[0] + offset, end_pos[1])
            pygame.draw.line(screen, beam_color, offset_start, offset_end, 2)
        
        # Core beam (brighter)
        pygame.draw.line(screen, (150, 255, 150), start_pos, end_pos, 1)
        
        # Sparks at the tip
        if self.spark_timer % 5 == 0:
            for i in range(3):
                spark_x = self.x + random.randint(-5, 5)
                spark_y = self.y + random.randint(-5, 5)
                pygame.draw.circle(screen, (255, 255, 255), (int(spark_x), int(spark_y)), 1)

class Missile:
    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float, speed: float = 1.0, missile_type: str = "straight"):
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.missile_type = missile_type
        self.time = 0  # For path calculations
        
        # Calculate base velocity for straight missiles
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            self.base_vx = (dx / distance) * speed
            self.base_vy = (dy / distance) * speed
        else:
            self.base_vx = self.base_vy = 0
        
        # Zigzag specific properties
        if missile_type == "zigzag":
            self.zigzag_amplitude = random.uniform(30, 80)
            self.zigzag_frequency = random.uniform(0.05, 0.15)
        
        # Drunk specific properties
        elif missile_type == "drunk":
            self.drunk_direction = random.uniform(0, 360)
            self.drunk_change_timer = 0
            self.drunk_change_interval = random.randint(10, 30)
        
        # Sine wave properties
        elif missile_type == "sine":
            self.sine_amplitude = random.uniform(40, 100)
            self.sine_frequency = random.uniform(0.03, 0.08)
        
        # Spiral properties
        elif missile_type == "spiral":
            self.spiral_radius = random.uniform(20, 60)
            self.spiral_frequency = random.uniform(0.1, 0.2)
        
        self.trail = []
        
        # Colors for different missile types
        self.color_map = {
            "straight": RED,
            "zigzag": (255, 0, 255),    # Magenta
            "drunk": (255, 165, 0),     # Orange  
            "sine": (0, 255, 255),      # Cyan
            "spiral": (255, 255, 0)     # Yellow
        }
    
    def update(self) -> bool:
        """Update missile position based on type. Returns True if reached target."""
        self.time += 1
        
        if self.missile_type == "straight":
            # Normal straight path
            self.x += self.base_vx
            self.y += self.base_vy
            
        elif self.missile_type == "zigzag":
            # Zigzag pattern
            zigzag_offset = self.zigzag_amplitude * math.sin(self.time * self.zigzag_frequency)
            
            # Calculate perpendicular direction for zigzag
            perp_x = -self.base_vy / self.speed
            perp_y = self.base_vx / self.speed
            
            self.x += self.base_vx + perp_x * zigzag_offset * 0.1
            self.y += self.base_vy + perp_y * zigzag_offset * 0.1
            
        elif self.missile_type == "drunk":
            # Random wobbling path
            self.drunk_change_timer += 1
            if self.drunk_change_timer >= self.drunk_change_interval:
                self.drunk_direction += random.uniform(-45, 45)
                self.drunk_change_timer = 0
                self.drunk_change_interval = random.randint(15, 40)
            
            # Move toward target but with random deviation
            target_angle = math.atan2(self.target_y - self.y, self.target_x - self.x)
            drunk_angle = target_angle + math.radians(self.drunk_direction * 0.3)
            
            self.x += math.cos(drunk_angle) * self.speed
            self.y += math.sin(drunk_angle) * self.speed
            
        elif self.missile_type == "sine":
            # Sine wave pattern
            sine_offset = self.sine_amplitude * math.sin(self.time * self.sine_frequency)
            
            # Calculate perpendicular direction for sine wave
            perp_x = -self.base_vy / self.speed
            perp_y = self.base_vx / self.speed
            
            self.x += self.base_vx + perp_x * sine_offset * 0.05
            self.y += self.base_vy + perp_y * sine_offset * 0.05
            
        elif self.missile_type == "spiral":
            # Spiral pattern toward target
            target_angle = math.atan2(self.target_y - self.y, self.target_x - self.x)
            spiral_angle = target_angle + self.time * self.spiral_frequency
            spiral_x = math.cos(spiral_angle) * self.spiral_radius * (1 - self.time * 0.005)
            spiral_y = math.sin(spiral_angle) * self.spiral_radius * (1 - self.time * 0.005)
            
            # Move toward target with spiral offset
            self.x += self.base_vx * 0.7 + spiral_x * 0.05
            self.y += self.base_vy * 0.7 + spiral_y * 0.05
        
        # Update trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 15:  # Longer trail for funny paths
            self.trail.pop(0)
        
        # Check if reached target (larger tolerance for crazy paths)
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        tolerance = 8 if self.missile_type == "straight" else 15
        return math.sqrt(dx * dx + dy * dy) < tolerance
    
    def draw(self, screen: pygame.Surface):
        """Draw missile and trail with type-specific colors."""
        color = self.color_map.get(self.missile_type, RED)
        
        # Draw trail with fade effect
        for i in range(len(self.trail) - 1):
            start_pos = self.trail[i]
            end_pos = self.trail[i + 1]
            pygame.draw.line(screen, color, start_pos, end_pos, 2)
        
        # Draw missile with type indicator
        missile_size = 4 if self.missile_type == "straight" else 5
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), missile_size)
        
        # Add visual indicator for special missiles
        if self.missile_type != "straight":
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), missile_size + 2, 1)

class Interceptor:
    def __init__(self, start_x: float, start_y: float, target_x: float, target_y: float):
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = 4.0
        
        # Calculate velocity
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed
        else:
            self.vx = self.vy = 0
        
        self.trail = []
    
    def update(self) -> bool:
        """Update interceptor position. Returns True if reached target."""
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        
        self.x += self.vx
        self.y += self.vy
        
        # Check if reached target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        return math.sqrt(dx * dx + dy * dy) < 8
    
    def draw(self, screen: pygame.Surface):
        """Draw interceptor and trail."""
        # Draw trail
        for i in range(len(self.trail) - 1):
            start_pos = self.trail[i]
            end_pos = self.trail[i + 1]
            pygame.draw.line(screen, GREEN, start_pos, end_pos, 1)
        
        # Draw interceptor
        pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), 2)

class Explosion:
    def __init__(self, x: float, y: float, max_radius: float = 50, custom_image=None):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = max_radius
        self.life = 60
        self.max_life = 60
        self.custom_image = custom_image
        
        # No rotation - keep image stationary
        self.scale_pulse = 0
        self.pulse_speed = random.uniform(0.1, 0.3)
        
        # Multiple explosion rings for more visual impact
        self.rings = []
        for i in range(3):
            self.rings.append({
                'radius': 0,
                'max_radius': max_radius * (0.6 + i * 0.3),
                'speed': random.uniform(0.8, 1.2),
                'color_shift': random.randint(-30, 30)
            })
        
        # Scale custom image if provided
        if self.custom_image:
            self.scaled_images = {}
    
    def update(self) -> bool:
        """Update explosion. Returns True if explosion is finished."""
        self.life -= 1
        self.radius = (1 - self.life / self.max_life) * self.max_radius
        
        # Update pulsing effect only
        self.scale_pulse += self.pulse_speed
        
        # Update explosion rings
        for ring in self.rings:
            ring['radius'] = (1 - self.life / self.max_life) * ring['max_radius'] * ring['speed']
        
        return self.life <= 0
    
    def draw(self, screen: pygame.Surface):
        """Draw explosion with stationary image."""
        if self.custom_image and self.life > 0:
            # Calculate dynamic size with pulsing effect only
            pulse_factor = 1 + 0.2 * math.sin(self.scale_pulse)
            size = int(self.radius * 2 * pulse_factor)
            
            if size > 0:
                # Scale image without rotation
                if size not in self.scaled_images:
                    self.scaled_images[size] = pygame.transform.scale(self.custom_image, (size, size))
                
                scaled_img = self.scaled_images[size]
                
                # Create surface with alpha for fading
                alpha = int(255 * (self.life / self.max_life))
                fade_surface = scaled_img.copy()
                fade_surface.set_alpha(alpha)
                
                # Draw centered
                rect = fade_surface.get_rect()
                rect.center = (int(self.x), int(self.y))
                screen.blit(fade_surface, rect)
        else:
            # Enhanced default explosion effect with multiple rings
            if self.life > 0:
                alpha_factor = self.life / self.max_life
                
                # Draw multiple expanding rings with different colors
                for i, ring in enumerate(self.rings):
                    if ring['radius'] > 0:
                        # Calculate ring color with variation
                        base_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (255, 255, 255)]
                        color_index = min(i, len(base_colors) - 1)
                        base_color = base_colors[color_index]
                        
                        # Apply color shift
                        shifted_color = []
                        for component in base_color:
                            shifted = component + ring['color_shift']
                            shifted_color.append(max(0, min(255, shifted)))
                        
                        # Draw ring with pulsing alpha
                        ring_alpha = alpha_factor * (0.8 - i * 0.2)
                        if ring_alpha > 0:
                            # Create temporary surface for alpha blending
                            temp_surface = pygame.Surface((int(ring['radius'] * 2 + 10), int(ring['radius'] * 2 + 10)))
                            temp_surface.set_alpha(int(255 * ring_alpha))
                            temp_surface.fill((0, 0, 0))
                            temp_surface.set_colorkey((0, 0, 0))
                            
                            pygame.draw.circle(temp_surface, shifted_color, 
                                             (int(ring['radius'] + 5), int(ring['radius'] + 5)), 
                                             int(ring['radius']))
                            
                            screen.blit(temp_surface, (self.x - ring['radius'] - 5, self.y - ring['radius'] - 5))
    
    def collides_with(self, x: float, y: float) -> bool:
        """Check if point collides with explosion."""
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx * dx + dy * dy) < self.radius

class City:
    def __init__(self, x: float, y: float, width: float = 40, height: float = 30):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alive = True
    
    def draw(self, screen: pygame.Surface):
        """Draw city."""
        color = GREEN if self.alive else RED
        height = self.height if self.alive else self.height // 2
        
        rect = pygame.Rect(self.x - self.width//2, self.y - height, self.width, height)
        pygame.draw.rect(screen, color, rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Retro Missile Attack")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Game state
        self.running = True
        self.game_active = False
        self.paused = False
        self.score = 0
        
        # Nuke system
        self.nukes_available = 3
        self.nuke_active = False
        self.nuke_timer = 0
        self.nuke_duration = 120
        
        # Game objects
        self.missiles: List[Missile] = []
        self.interceptors: List[Interceptor] = []
        self.explosions: List[Explosion] = []
        self.cities: List[City] = []
        self.ufos: List[UFO] = []
        self.lasers: List[Laser] = []
        
        # Crosshair
        self.crosshair_x = SCREEN_WIDTH // 2
        self.crosshair_y = SCREEN_HEIGHT // 2
        
        # Custom explosion image
        self.explosion_image = None
        self.load_explosion_image()
        
        # Initialize cities
        self.init_cities()
    
    def load_explosion_image(self):
        """Load custom explosion image from file."""
        image_path = "explosion.jpg"
        
        if os.path.exists(image_path):
            try:
                self.explosion_image = pygame.image.load(image_path).convert_alpha()
                print(f"Loaded custom explosion image: {image_path}")
            except pygame.error as e:
                print(f"Could not load image {image_path}: {e}")
                self.explosion_image = None
        else:
            print(f"Image not found: {image_path}")
            print("Place your JPEG file in the same directory as this script and name it 'explosion.jpg'")
    
    def init_cities(self):
        """Initialize cities."""
        self.cities = []
        for i in range(6):
            x = (i + 1) * SCREEN_WIDTH // 7
            y = SCREEN_HEIGHT - 20
            self.cities.append(City(x, y))
    
    def spawn_missile(self):
        """Spawn a new enemy missile with random type."""
        start_x = random.randint(0, SCREEN_WIDTH)
        start_y = 0
        target_x = random.randint(0, SCREEN_WIDTH)
        target_y = SCREEN_HEIGHT
        speed = random.uniform(0.8, 2.2)
        
        # Choose missile type with different probabilities
        missile_types = ["straight", "zigzag", "drunk", "sine", "spiral"]
        weights = [50, 20, 15, 10, 5]
        missile_type = random.choices(missile_types, weights=weights)[0]
        
        self.missiles.append(Missile(start_x, start_y, target_x, target_y, speed, missile_type))
    
    def launch_nuke(self):
        """Launch a screen-clearing nuke."""
        if self.nukes_available > 0 and not self.nuke_active:
            self.nukes_available -= 1
            self.nuke_active = True
            self.nuke_timer = self.nuke_duration
            
            # Clear all missiles immediately
            cleared_missiles = len(self.missiles)
            self.missiles.clear()
            
            # Award bonus points for cleared missiles
            self.score += cleared_missiles * 25
            
            print(f"NUKE LAUNCHED! Cleared {cleared_missiles} missiles for {cleared_missiles * 25} bonus points!")
    
    def launch_interceptor(self, target_x: float, target_y: float):
        """Launch interceptor missile."""
        start_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT - 50
        
        self.interceptors.append(Interceptor(start_x, start_y, target_x, target_y))
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.game_active and not self.paused:
                    self.launch_interceptor(self.crosshair_x, self.crosshair_y)
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.restart_game()
                elif event.key == pygame.K_n and self.game_active and not self.paused:
                    self.launch_nuke()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.game_active and not self.paused:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        self.launch_interceptor(mouse_x, mouse_y)
                    elif not self.game_active:
                        self.restart_game()
        
        # Handle continuous key presses
        if self.game_active and not self.paused:
            keys = pygame.key.get_pressed()
            speed = 5
            
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.crosshair_y = max(0, self.crosshair_y - speed)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.crosshair_y = min(SCREEN_HEIGHT, self.crosshair_y + speed)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.crosshair_x = max(0, self.crosshair_x - speed)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.crosshair_x = min(SCREEN_WIDTH, self.crosshair_x + speed)
        
        # Update crosshair with mouse
        if self.game_active:
            self.crosshair_x, self.crosshair_y = pygame.mouse.get_pos()
    
    def update(self):
        """Update game state."""
        if not self.game_active or self.paused:
            return
        
        # Update nuke timer
        if self.nuke_active:
            self.nuke_timer -= 1
            if self.nuke_timer <= 0:
                self.nuke_active = False
        
        # Don't spawn during nuke
        if not self.nuke_active:
            # Spawn missiles randomly
            if random.random() < 0.02:
                self.spawn_missile()
            
            # Spawn UFO occasionally
            if random.random() < 0.005 and len(self.ufos) < 2:
                self.ufos.append(UFO())
        
        # Update missiles
        for missile in self.missiles[:]:
            if missile.update():
                explosion = Explosion(missile.x, missile.y, 60, None)  # No custom image for regular explosions
                self.explosions.append(explosion)
                self.missiles.remove(missile)
                
                # Check city damage
                for city in self.cities:
                    if city.alive:
                        city_left = city.x - city.width // 2
                        city_right = city.x + city.width // 2
                        city_top = city.y - city.height
                        city_bottom = city.y
                        
                        hit_city = (city_left <= missile.x <= city_right and 
                                   city_top <= missile.y <= city_bottom)
                        
                        explosion_radius = 60
                        distance_to_city = math.sqrt((missile.x - city.x)**2 + (missile.y - city.y)**2)
                        explosion_hit = distance_to_city <= explosion_radius
                        
                        if hit_city or explosion_hit:
                            city.alive = False
                            print(f"City destroyed at x={city.x}!")
        
        # Update interceptors
        for interceptor in self.interceptors[:]:
            if interceptor.update():
                explosion = Explosion(interceptor.x, interceptor.y, 40, None)  # No custom image for regular explosions
                self.explosions.append(explosion)
                self.interceptors.remove(interceptor)
        
        # Update UFOs
        for ufo in self.ufos[:]:
            if ufo.update():
                self.ufos.remove(ufo)
            elif ufo.can_shoot_laser():
                target_x, target_y = ufo.shoot_laser()
                laser = Laser(ufo.x, ufo.y + 10, target_x, target_y)
                self.lasers.append(laser)
        
        # Update lasers
        for laser in self.lasers[:]:
            if laser.update():
                explosion = Explosion(laser.x, laser.y, 40, None)  # No custom image for laser explosions
                self.explosions.append(explosion)
                self.lasers.remove(laser)
                
                # Check city damage from laser
                for city in self.cities:
                    if city.alive:
                        distance_to_city = math.sqrt((laser.x - city.x)**2 + (laser.y - city.y)**2)
                        if distance_to_city <= 50:
                            city.alive = False
                            print(f"City destroyed by UFO laser at x={city.x}!")
        
        # Update explosions
        for explosion in self.explosions[:]:
            if explosion.update():
                self.explosions.remove(explosion)
            else:
                # Check missile collisions with explosions
                for missile in self.missiles[:]:
                    if explosion.collides_with(missile.x, missile.y):
                        self.missiles.remove(missile)
                        self.score += 10
                        # Chain explosion bonus
                        if random.random() < 0.3:
                            chain_explosion = Explosion(
                                missile.x + random.randint(-20, 20), 
                                missile.y + random.randint(-20, 20), 
                                30, None  # No custom image for chain explosions
                            )
                            self.explosions.append(chain_explosion)
                            self.score += 5
                
                # Check UFO collisions with explosions
                for ufo in self.ufos[:]:
                    if explosion.collides_with(ufo.x, ufo.y):
                        if ufo.take_damage():
                            self.ufos.remove(ufo)
                            self.score += 50
                            print(f"UFO destroyed! +50 points!")
        
        # Check game over
        if all(not city.alive for city in self.cities):
            if self.game_active:
                surviving_cities = sum(1 for city in self.cities if city.alive)
                city_bonus = surviving_cities * 50
                self.score += city_bonus
                if city_bonus > 0:
                    print(f"City survival bonus: {city_bonus} points!")
            self.game_active = False
    
    def draw(self):
        """Draw everything."""
        # Clear screen with black background
        self.screen.fill(BLACK)
        
        # Draw nuke effect if active
        if self.nuke_active and self.explosion_image:
            progress = 1 - (self.nuke_timer / self.nuke_duration)
            
            # Flash effect at start
            if self.nuke_timer > self.nuke_duration - 20:
                flash_alpha = int(255 * ((self.nuke_duration - self.nuke_timer) / 20))
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.fill(WHITE)
                flash_surface.set_alpha(flash_alpha)
                self.screen.blit(flash_surface, (0, 0))
            
            # Scale image to fill screen with pulsing effect
            pulse = 1 + 0.1 * math.sin(progress * 20)
            image_width = int(SCREEN_WIDTH * pulse)
            image_height = int(SCREEN_HEIGHT * pulse)
            
            scaled_nuke_image = pygame.transform.scale(self.explosion_image, (image_width, image_height))
            
            # Calculate alpha for fade effect
            if self.nuke_timer > 60:
                alpha = int(255 * (1 - (self.nuke_timer - 60) / 60))
            else:
                alpha = int(255 * (self.nuke_timer / 60))
            
            scaled_nuke_image.set_alpha(alpha)
            
            # Center the image
            image_rect = scaled_nuke_image.get_rect()
            image_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.screen.blit(scaled_nuke_image, image_rect)
            
            # Add screen shake effect
            if self.nuke_timer > self.nuke_duration - 40:
                shake_intensity = 10
                shake_x = random.randint(-shake_intensity, shake_intensity)
                shake_y = random.randint(-shake_intensity, shake_intensity)
                
                temp_surface = self.screen.copy()
                self.screen.fill(BLACK)
                self.screen.blit(temp_surface, (shake_x, shake_y))
        
        # Draw ground
        pygame.draw.rect(self.screen, BROWN, (0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20))
        
        # Draw cities
        for city in self.cities:
            city.draw(self.screen)
        
        # Draw missiles
        for missile in self.missiles:
            missile.draw(self.screen)
        
        # Draw interceptors
        for interceptor in self.interceptors:
            interceptor.draw(self.screen)
        
        # Draw UFOs
        for ufo in self.ufos:
            ufo.draw(self.screen)
        
        # Draw lasers
        for laser in self.lasers:
            laser.draw(self.screen)
        
        # Draw explosions
        for explosion in self.explosions:
            explosion.draw(self.screen)
        
        # Draw crosshair
        if self.game_active:
            pygame.draw.line(self.screen, GREEN, 
                           (self.crosshair_x - 10, self.crosshair_y), 
                           (self.crosshair_x + 10, self.crosshair_y), 2)
            pygame.draw.line(self.screen, GREEN, 
                           (self.crosshair_x, self.crosshair_y - 10), 
                           (self.crosshair_x, self.crosshair_y + 10), 2)
        
        # Draw UI
        score_text = self.font.render(f"SCORE: {self.score:,}", True, GREEN)
        self.screen.blit(score_text, (10, 10))
        
        cities_alive = sum(1 for city in self.cities if city.alive)
        cities_text = self.font.render(f"CITIES: {cities_alive}/6", True, GREEN)
        self.screen.blit(cities_text, (10, 45))
        
        # Show missiles on screen (only if not nuking)
        if not self.nuke_active:
            missiles_text = self.font.render(f"MISSILES: {len(self.missiles)}", True, YELLOW)
            self.screen.blit(missiles_text, (SCREEN_WIDTH - 200, 10))
        
        # Show UFOs on screen
        if len(self.ufos) > 0:
            ufo_text = self.font.render(f"UFOS: {len(self.ufos)}", True, (255, 0, 255))
            self.screen.blit(ufo_text, (SCREEN_WIDTH - 200, 45))
        
        # Show nuke count
        nuke_color = GREEN if self.nukes_available > 0 else RED
        nukes_text = self.font.render(f"NUKES: {self.nukes_available}", True, nuke_color)
        self.screen.blit(nukes_text, (SCREEN_WIDTH - 200, 80))
        
        # Show nuke instructions
        if self.nukes_available > 0 and not self.nuke_active:
            nuke_hint = self.font.render("Press N for NUKE!", True, YELLOW)
            self.screen.blit(nuke_hint, (SCREEN_WIDTH - 200, 115))
        
        if self.nuke_active:
            nuke_text = self.font.render("** NUCLEAR STRIKE IN PROGRESS **", True, WHITE)
            nuke_rect = nuke_text.get_rect(center=(SCREEN_WIDTH//2, 50))
            self.screen.blit(nuke_text, nuke_rect)
        
        if self.paused:
            pause_text = self.font.render("PAUSED - Press P to resume", True, YELLOW)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(pause_text, text_rect)
        
        if not self.game_active:
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.font.render("Press R to restart or click to continue", True, WHITE)
            
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(restart_text, restart_rect)
        
        if not self.game_active and self.score == 0:
            # Clean intro screen
            title_font = pygame.font.Font(None, 56)
            section_font = pygame.font.Font(None, 32)
            instruction_font = pygame.font.Font(None, 24)
            
            # Title
            title_text = title_font.render("RETRO MISSILE ATTACK", True, GREEN)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 60))
            self.screen.blit(title_text, title_rect)
            
            # Mission briefing
            mission_text = instruction_font.render("Defend the cities from incoming missiles", True, WHITE)
            mission_rect = mission_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(mission_text, mission_rect)
            
            # Two column layout
            left_col_x = SCREEN_WIDTH // 4
            right_col_x = 3 * SCREEN_WIDTH // 4
            
            # Left column - Controls
            y_pos = 140
            controls_title = section_font.render("CONTROLS", True, GREEN)
            controls_rect = controls_title.get_rect(center=(left_col_x, y_pos))
            self.screen.blit(controls_title, controls_rect)
            
            y_pos += 40
            control_lines = [
                "Mouse: Aim and shoot",
                "WASD/Arrows: Move crosshair", 
                "SPACE: Launch interceptor",
                "N: NUKE (clears all missiles)",
                "P: Pause   R: Restart"
            ]
            
            for line in control_lines:
                text = instruction_font.render(line, True, YELLOW)
                text_rect = text.get_rect(center=(left_col_x, y_pos))
                self.screen.blit(text, text_rect)
                y_pos += 25
            
            # Right column - Missile Types
            y_pos = 140
            types_title = section_font.render("MISSILE TYPES", True, GREEN)
            types_rect = types_title.get_rect(center=(right_col_x, y_pos))
            self.screen.blit(types_title, types_rect)
            
            y_pos += 40
            type_lines = [
                ("Red: Straight path", RED),
                ("Magenta: Zigzag weaving", (255, 0, 255)),
                ("Orange: Drunk wobbling", (255, 165, 0)),
                ("Cyan: Sine wave", (0, 255, 255)),
                ("Yellow: Spiral approach", (255, 255, 0))
            ]
            
            for line, color in type_lines:
                text = instruction_font.render(line, True, color)
                text_rect = text.get_rect(center=(right_col_x, y_pos))
                self.screen.blit(text, text_rect)
                y_pos += 25
            
            # Bottom section - Scoring
            y_pos = 340
            scoring_title = section_font.render("SCORING", True, GREEN)
            scoring_rect = scoring_title.get_rect(center=(SCREEN_WIDTH//2, y_pos))
            self.screen.blit(scoring_title, scoring_rect)
            
            y_pos += 35
            scoring_lines = [
                "Missile destroyed: +10 pts  •  Chain explosion: +5 pts  •  Nuke cleared: +25 pts each",
                "UFO destroyed: +50 pts  •  City survival bonus awarded at game end"
            ]
            
            for line in scoring_lines:
                text = instruction_font.render(line, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
                self.screen.blit(text, text_rect)
                y_pos += 25
            
            # Start instruction
            y_pos += 30
            start_text = section_font.render("CLICK TO BEGIN MISSION", True, GREEN)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
            self.screen.blit(start_text, start_rect)
    
    def restart_game(self):
        """Restart the game."""
        self.game_active = True
        self.paused = False
        self.score = 0
        self.nukes_available = 3
        self.nuke_active = False
        self.nuke_timer = 0
        self.missiles.clear()
        self.interceptors.clear()
        self.explosions.clear()
        self.ufos.clear()
        self.lasers.clear()
        self.init_cities()
        self.crosshair_x = SCREEN_WIDTH // 2
        self.crosshair_y = SCREEN_HEIGHT // 2
    
    def run(self):
        """Main game loop."""
        print("=== RETRO MISSILE ATTACK ===")
        print("Place your custom explosion image as 'explosion.jpg' in the same directory")
        print("Controls: Mouse to aim and shoot, WASD/arrows to move, Space to shoot, N for nuke, P to pause, R to restart")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()