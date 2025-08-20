import pygame
import numpy as np
import random

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Tower Defense")
WIDTH, HEIGHT = 900, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 128, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
ORANGE = (255, 128, 0)
PURPLE = (128, 0, 255)
GRAY = (200, 200, 200)

# Path for enemies
path_points = [(100, 100), (300, 100), (300, 300), (500, 300), (700, 500)]

# Game variables
currency = 100
health = 10
wave_number = 1
selected_tower = None
wave_started = False
game_over = False
paused = False
dragging_tower = None  # Tower being dragged
tower_cost = {"normal": 20, "splash": 50, "slow": 15}  # Tower costs

# Font
font = pygame.font.Font(None, 36)

# Path drawing
def draw_path(screen, path_points, color=BLACK, width=3):
    pygame.draw.lines(screen, color, False, path_points, width)

# Check if a point is on the enemy path
def is_on_path(x, y):
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]
        # Check if the point is close to the line segment
        if min(x1, x2) - 20 <= x <= max(x1, x2) + 20 and min(y1, y2) - 20 <= y <= max(y1, y2) + 20:
            return True
    return False

# Classes for Enemy, Tower, and Bullet
class Enemy:
    def __init__(self, path, speed=0.5, health=75, color=RED):
        self.path = path
        self.pos = np.array(self.path[0], dtype=float)
        self.speed = speed
        self.base_speed = speed
        self.health = health
        self.current_point = 0
        self.radius = 15
        self.slow_timer = 0
        self.color = color

    def move(self):
        if self.current_point < len(self.path) - 1:
            target = np.array(self.path[self.current_point + 1], dtype=float)
            direction = target - self.pos
            distance = np.linalg.norm(direction)
            if distance > 0:
                direction /= distance
            self.pos += direction * self.speed
            if distance < self.speed:
                self.current_point += 1
            if self.slow_timer > 0:
                self.slow_timer -= 1
            else:
                self.speed = self.base_speed

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def is_alive(self):
        return self.health > 0

class Bullet:
    def __init__(self, x, y, target, damage, origin_range, origin_pos, color, splash=False, splash_radius=0):
        self.pos = np.array([x, y], dtype=float)
        self.target = target
        self.speed = 6.0
        self.damage = damage
        self.radius = 3
        self.color = color
        self.origin_pos = np.array(origin_pos, dtype=float)
        self.origin_range = origin_range
        self.splash = splash
        self.splash_radius = splash_radius

    def explode(self, enemies):
        if self.splash:
            for enemy in enemies:
                if np.linalg.norm(enemy.pos - self.pos) <= self.splash_radius:
                    enemy.health -= self.damage

    def move(self):
        direction = self.target.pos - self.pos
        distance = np.linalg.norm(direction)
        if distance > 0:
            direction /= distance
        self.pos += direction * self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def has_collided(self):
        distance = np.linalg.norm(self.target.pos - self.pos)
        return distance <= self.radius + self.target.radius

# Normal Tower
class NormalTower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tower_type = "normal"
        self.range = 100
        self.fire_rate = 60
        self.damage = 12
        self.time_since_last_shot = 0
        self.level = 1
        self.upgrade_cost = 15
        self.color = BLUE
        self.upgrade_cooldown = 60
        self.shape = "square"

    def can_shoot(self, enemy):
        dist = np.linalg.norm(np.array([self.x, self.y]) - enemy.pos)
        return dist <= self.range

    def shoot(self, enemies):
        self.time_since_last_shot += 1
        if self.time_since_last_shot >= self.fire_rate:
            for enemy in enemies:
                if self.can_shoot(enemy):
                    self.time_since_last_shot = 0
                    return Bullet(self.x, self.y, enemy, self.damage, self.range, (self.x, self.y), self.color)
        return None

    def upgrade(self):
        global currency
        if currency >= self.upgrade_cost:
            currency -= self.upgrade_cost
            self.level += 1
            self.range += 35
            self.damage += 18
            self.upgrade_cost += 20
            self.upgrade_cooldown = 60  # 1 second cooldown

    def draw(self, screen, is_selected=False):
        color = YELLOW if is_selected else self.color
        pygame.draw.rect(screen, color, (self.x - 20, self.y - 20, 40, 40))
        pygame.draw.circle(screen, GREEN, (self.x, self.y), self.range, 1)

# Splash Tower
class SplashTower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tower_type = "splash"
        self.range = 95
        self.fire_rate = 50
        self.damage = 13
        self.time_since_last_shot = 0
        self.level = 1
        self.upgrade_cost = 30
        self.color = ORANGE
        self.upgrade_cooldown = 60
        self.shape = "circle"
        self.splash_radius = 12

    def can_shoot(self, enemy):
        dist = np.linalg.norm(np.array([self.x, self.y]) - enemy.pos)
        return dist <= self.range

    def shoot(self, enemies):
        self.time_since_last_shot += 1
        if self.time_since_last_shot >= self.fire_rate:
            for enemy in enemies:
                if self.can_shoot(enemy):
                    self.time_since_last_shot = 0
                    return Bullet(self.x, self.y, enemy, self.damage, self.range, (self.x, self.y), self.color, splash=True, splash_radius=self.splash_radius)
        return None

    def upgrade(self):
        global currency
        if currency >= self.upgrade_cost:
            currency -= self.upgrade_cost
            self.level += 1
            self.range += 9
            self.damage += 7
            self.upgrade_cost += 20
            self.upgrade_cooldown = 60  # 1 second cooldown

    def draw(self, screen, is_selected=False):
        color = YELLOW if is_selected else self.color
        pygame.draw.circle(screen, color, (self.x, self.y), 20)
        pygame.draw.circle(screen, GREEN, (self.x, self.y), self.range, 1)

# Slow Tower
class SlowTower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tower_type = "slow"
        self.range = 150
        self.fire_rate = 37
        self.damage = 7
        self.time_since_last_shot = 0
        self.level = 1
        self.upgrade_cost = 25
        self.color = PURPLE
        self.upgrade_cooldown = 0
        self.shape = "triangle"
        self.slow_duration = 3600  # Frames
        self.slow_amount = 0.65  # Slow by 50%

    def can_shoot(self, enemy):
        dist = np.linalg.norm(np.array([self.x, self.y]) - enemy.pos)
        return dist <= self.range

    def shoot(self, enemies):
        self.time_since_last_shot += 1
        if self.time_since_last_shot >= self.fire_rate:
            for enemy in enemies:
                if self.can_shoot(enemy):
                    self.time_since_last_shot = 0
                    enemy.speed *= self.slow_amount
                    enemy.slow_timer = self.slow_duration
                    return Bullet(self.x, self.y, enemy, self.damage, self.range, (self.x, self.y), self.color)
        return None

    def upgrade(self):
        global currency
        if currency >= self.upgrade_cost:
            currency -= self.upgrade_cost
            self.level += 1
            self.range += 18
            self.damage += 5
            self.upgrade_cost += 20
            self.upgrade_cooldown = 60  # 1 second cooldown

    def draw(self, screen, is_selected=False):
        color = YELLOW if is_selected else self.color
        pygame.draw.polygon(screen, color, [(self.x, self.y - 20), (self.x - 20, self.y + 20), (self.x + 20, self.y + 20)])
        pygame.draw.circle(screen, GREEN, (self.x, self.y), self.range, 1)

def spawn_wave(wave_number):
    enemies = []
    for _ in range(wave_number * 2):
        speed = random.uniform(0.3, 1.0)
        health = random.randint(40, 80)
        color = random.choice([RED, GREEN, BLUE])
        enemies.append(Enemy(path_points, speed, health, color))
    return enemies

def draw_ui(screen, currency, health, wave_number, selected_tower):
    # Draw currency, health, and wave number
    currency_text = font.render(f"Currency: {currency}", True, BLACK)
    health_text = font.render(f"Health: {health}", True, BLACK)
    wave_text = font.render(f"Wave: {wave_number}", True, BLACK)
    screen.blit(currency_text, (10, 10))
    screen.blit(health_text, (10, 50))
    screen.blit(wave_text, (10, 90))

    # Draw upgrade info
    if selected_tower:
        upgrade_text = font.render(
            f"Upgrade (U): Level {selected_tower.level} | Cost: {selected_tower.upgrade_cost}",
            True, BLACK
        )
        screen.blit(upgrade_text, (10, HEIGHT - 30))

    # Draw tower selection UI at the bottom
    pygame.draw.rect(screen, GRAY, (0, HEIGHT - 100, WIDTH, 100))
    # Normal tower
    pygame.draw.rect(screen, BLUE, (50, HEIGHT - 80, 60, 60))
    normal_tower_text = font.render(f"${tower_cost['normal']}", True, BLACK)
    screen.blit(normal_tower_text, (60, HEIGHT - 20))
    # Splash tower
    pygame.draw.circle(screen, ORANGE, (200, HEIGHT - 50), 30)
    splash_tower_text = font.render(f"${tower_cost['splash']}", True, BLACK)
    screen.blit(splash_tower_text, (180, HEIGHT - 20))
    # Slow tower
    pygame.draw.polygon(screen, PURPLE, [(300, HEIGHT - 80), (270, HEIGHT - 20), (330, HEIGHT - 20)])
    slow_tower_text = font.render(f"${tower_cost['slow']}", True, BLACK)
    screen.blit(slow_tower_text, (290, HEIGHT - 20))

    # Draw "Next Wave" button
    pygame.draw.rect(screen, BLUE, (650, 10, 100, 40))
    start_wave_text = font.render("Next Wave", True, WHITE)
    screen.blit(start_wave_text, (660, 15))

def game_over_screen(screen):
    screen.fill(BLACK)
    game_over_text = font.render("Game Over! Press R to Restart", True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2))
    pygame.display.update()

def game_loop():
    global currency, health, wave_number, selected_tower, wave_started, game_over, paused, dragging_tower
    running = True
    enemies = []
    towers = []
    bullets = []

    while running:
        screen.fill("#7a5f74")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if event.button == 1:  # Left-click
                    # Check if clicking on a tower in the UI
                    if HEIGHT - 100 <= y <= HEIGHT:
                        if 50 <= x <= 110:  # Normal tower
                            if currency >= tower_cost["normal"]:
                                dragging_tower = NormalTower(x, y)
                        elif 170 <= x <= 230:  # Splash tower
                            if currency >= tower_cost["splash"]:
                                dragging_tower = SplashTower(x, y)
                        elif 270 <= x <= 330:  # Slow tower
                            if currency >= tower_cost["slow"]:
                                dragging_tower = SlowTower(x, y)
                    # Check if clicking on the "Next Wave" button
                    if 650 <= x <= 750 and 10 <= y <= 50 and not wave_started:
                        wave_started = True
                    # Check if clicking on a tower to select it
                    for tower in towers:
                        if np.linalg.norm(np.array([tower.x, tower.y]) - np.array([x, y])) <= 20:
                            selected_tower = tower
                            break
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and dragging_tower:
                    # Place the tower if the position is valid
                    if not is_on_path(dragging_tower.x, dragging_tower.y):
                        towers.append(dragging_tower)
                        currency -= tower_cost[dragging_tower.tower_type]
                    dragging_tower = None
            elif event.type == pygame.MOUSEMOTION:
                if dragging_tower:
                    dragging_tower.x, dragging_tower.y = event.pos
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u and selected_tower:  # Upgrade tower
                    selected_tower.upgrade()
                elif event.key == pygame.K_p:  # Pause game
                    paused = not paused
                elif event.key == pygame.K_r and game_over:  # Restart game
                    game_over = False
                    health = 10
                    currency = 100
                    wave_number = 1
                    enemies = []
                    towers = []
                    bullets = []

        if not paused and not game_over:
            if wave_started and not enemies:
                enemies.extend(spawn_wave(wave_number))
                wave_number += 1
                wave_started = False

            for enemy in enemies[:]:
                enemy.move()
                if enemy.health <= 0:
                    enemies.remove(enemy)
                    currency += 10
                elif enemy.current_point == len(enemy.path) - 1:
                    enemies.remove(enemy)
                    health -= 1

            if health <= 0:
                game_over = True

            for tower in towers:
                if tower.upgrade_cooldown > 0:
                    tower.upgrade_cooldown -= 1
                bullet = tower.shoot(enemies)
                if bullet:
                    bullets.append(bullet)

            for bullet in bullets[:]:
                bullet.move()
                if bullet.has_collided():
                    if bullet.splash:
                        bullet.explode(enemies)
                    bullet.target.health -= bullet.damage
                    bullets.remove(bullet)
                elif not bullet.target.is_alive() or np.linalg.norm(bullet.pos - bullet.origin_pos) > bullet.origin_range:
                    bullets.remove(bullet)

        draw_path(screen, path_points)
        for enemy in enemies:
            enemy.draw(screen)
        for tower in towers:
            tower.draw(screen, is_selected=(tower == selected_tower))
        for bullet in bullets:
            bullet.draw(screen)

        draw_ui(screen, currency, health, wave_number, selected_tower)

        if dragging_tower:
            dragging_tower.draw(screen)
            if is_on_path(dragging_tower.x, dragging_tower.y):
                pygame.draw.circle(screen, RED, (int(dragging_tower.x), int(dragging_tower.y)), 25, 3)

        if game_over:
            game_over_screen(screen)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()

# Run the game loop
game_loop()