import pygame
import random
import time
import math
from pygame import mixer

# Инициализация pygame
pygame.init()

# Экран
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Space Invaders Deluxe")

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)

# Шрифты
font = pygame.font.SysFont('Arial', 32)
small_font = pygame.font.SysFont('Arial', 24)

# Звуки
mixer.init()
shoot_sound = mixer.Sound('shoot.wav') if pygame.mixer.get_init() else None
explosion_sound = mixer.Sound('explosion.wav') if pygame.mixer.get_init() else None
powerup_sound = mixer.Sound('powerup.wav') if pygame.mixer.get_init() else None

# Игрок
class Player:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - 100
        self.speed = 5
        self.base_speed = 5
        self.lives = 3
        self.shield = False
        self.shield_time = 0
        self.rapid_fire = False
        self.rapid_fire_time = 0
        self.speed_boost = False
        self.speed_boost_time = 0
        self.color = GREEN
        self.shoot_cooldown = 0
        
    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        if self.shield:
            shield_radius = self.width // 2 + 5
            pygame.draw.circle(screen, CYAN, (self.x + self.width // 2, self.y + self.height // 2), 
                             shield_radius, 2)
    
    def update(self):
        # Обновление таймеров улучшений
        current_time = time.time()
        if self.shield and current_time > self.shield_time:
            self.shield = False
        if self.rapid_fire and current_time > self.rapid_fire_time:
            self.rapid_fire = False
        if self.speed_boost and current_time > self.speed_boost_time:
            self.speed = self.base_speed
            self.speed_boost = False
        
        # Охлаждение выстрела
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

# Враги
class Enemy:
    def __init__(self, x, y):
        self.type = random.choice(['red', 'green', 'blue'])
        
        if self.type == 'red':
            self.size = 30
            self.speed = random.choice([-3, -2, 2, 3])
            self.color = RED
            self.points = 10
        elif self.type == 'green':
            self.size = 40
            self.speed = random.choice([-1, 1])
            self.color = GREEN
            self.points = 20
        else:  # blue
            self.size = 50
            self.speed = random.choice([-2, -1, 1, 2])
            self.color = BLUE
            self.points = 15
        
        self.x = x
        self.y = y
        self.direction_change_counter = 0
    
    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
    
    def update(self):
        self.x += self.speed
        self.direction_change_counter += 1
        
        # Изменение направления с небольшим случайным элементом
        if self.direction_change_counter > 60:
            if random.random() < 0.1:
                self.speed *= -1
                self.direction_change_counter = 0
                self.y += 10

# Пули
class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 10
        self.width = 5
        self.height = 15
    
    def draw(self):
        pygame.draw.rect(screen, YELLOW, (self.x, self.y, self.width, self.height))
    
    def update(self):
        self.y -= self.speed
        return self.y < 0  # Возвращает True, если пуля вышла за экран

# Улучшения
class PowerUp:
    def __init__(self, x, y):
        self.type = random.choice(['shield', 'rapid', 'speed'])
        self.x = x
        self.y = y
        self.size = 20
        self.speed = 2
        
        if self.type == 'shield':
            self.color = CYAN
        elif self.type == 'rapid':
            self.color = PURPLE
        else:  # speed
            self.color = WHITE
    
    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
    
    def update(self):
        self.y += self.speed
        return self.y > screen_height  # Возвращает True, если вышло за экран

# Частицы для эффектов
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed_x = random.uniform(-2, 2)
        self.speed_y = random.uniform(-2, 2)
        self.lifetime = random.randint(20, 40)
    
    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        return self.lifetime <= 0  # Возвращает True, если частица умерла

# Инициализация игровых объектов
player = Player()
enemies = []
bullets = []
powerups = []
particles = []

# Счет и время
score = 0
high_score = 0
start_time = time.time()
combo = 0
max_combo = 0
last_hit_time = 0
combo_time_window = 1.5  # секунды для комбо

# Функции
def spawn_enemy():
    if random.random() < 0.03 and len(enemies) < 15:  # Ограничиваем количество врагов
        x = random.randint(0, screen_width - 50)
        y = random.randint(-100, -40)
        enemies.append(Enemy(x, y))

def draw_hud():
    # Счет
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Жизни
    lives_text = font.render(f"Lives: {player.lives}", True, WHITE)
    screen.blit(lives_text, (10, 50))
    
    # Время
    elapsed_time = int(time.time() - start_time)
    time_text = font.render(f"Time: {elapsed_time}s", True, WHITE)
    screen.blit(time_text, (screen_width - 150, 10))
    
    # Комбо
    if combo > 1:
        combo_text = font.render(f"Combo: x{combo}!", True, CYAN)
        screen.blit(combo_text, (screen_width // 2 - 50, 50))
    
    # Улучшения
    powerup_text = small_font.render("Power-ups:", True, WHITE)
    screen.blit(powerup_text, (10, screen_height - 100))
    
    y_offset = screen_height - 70
    if player.shield:
        shield_text = small_font.render("SHIELD", True, CYAN)
        screen.blit(shield_text, (10, y_offset))
        y_offset += 25
    if player.rapid_fire:
        rapid_text = small_font.render("RAPID FIRE", True, PURPLE)
        screen.blit(rapid_text, (10, y_offset))
        y_offset += 25
    if player.speed_boost:
        speed_text = small_font.render("SPEED BOOST", True, WHITE)
        screen.blit(speed_text, (10, y_offset))

def create_explosion(x, y, color, count=20):
    for _ in range(count):
        particles.append(Particle(x + random.randint(-10, 10), 
                         y + random.randint(-10, 10), 
                         color))

def check_collision(obj1, obj2):
    # Упрощенная проверка столкновений
    return (obj1.x < obj2.x + obj2.size and
            obj1.x + obj1.width > obj2.x and
            obj1.y < obj2.y + obj2.size and
            obj1.y + obj1.height > obj2.y)

def game_over():
    global high_score, max_combo
    
    if score > high_score:
        high_score = score
    
    screen.fill((0, 0, 0))
    
    # Тексты окончания игры
    texts = [
        ("GAME OVER", RED, 50),
        (f"Final Score: {score}", WHITE, 0),
        (f"High Score: {high_score}", YELLOW, 25),
        (f"Time: {int(time.time() - start_time)}s", WHITE, 50),
        (f"Max Combo: x{max_combo}!", CYAN, 25)
    ]
    
    y_pos = screen_height // 2 - 100
    for text, color, offset in texts:
        rendered = font.render(text, True, color)
        screen.blit(rendered, (screen_width // 2 - rendered.get_width() // 2, y_pos))
        y_pos += offset + 40
    
    pygame.display.update()
    pygame.time.wait(5000)
    reset_game()

def reset_game():
    global score, start_time, combo, max_combo, last_hit_time
    
    player.__init__()
    enemies.clear()
    bullets.clear()
    powerups.clear()
    particles.clear()
    
    score = 0
    start_time = time.time()
    combo = 0
    max_combo = 0
    last_hit_time = 0

# Игровой цикл
running = True
clock = pygame.time.Clock()

while running:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and player.shoot_cooldown <= 0:
                bullets.append(Bullet(player.x + player.width // 2 - 2, player.y))
                if shoot_sound:
                    shoot_sound.play()
                player.shoot_cooldown = 10 if player.rapid_fire else 20
    
    # Управление игроком
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player.x > 0:
        player.x -= player.speed
    if keys[pygame.K_RIGHT] and player.x < screen_width - player.width:
        player.x += player.speed
    
    # Обновление игрока
    player.update()
    
    # Спавн врагов
    spawn_enemy()
    
    # Обновление врагов
    for enemy in enemies[:]:
        enemy.update()
        
        # Проверка выхода за границы
        if enemy.x <= 0 or enemy.x >= screen_width - enemy.size:
            enemy.speed *= -1
            enemy.y += 10
        
        # Проверка столкновения с игроком
        if check_collision(player, enemy):
            if player.shield:
                player.shield = False
                create_explosion(enemy.x + enemy.size // 2, 
                                enemy.y + enemy.size // 2, 
                                CYAN)
            else:
                player.lives -= 1
                create_explosion(enemy.x + enemy.size // 2, 
                                enemy.y + enemy.size // 2, 
                                enemy.color)
                
                if player.lives <= 0:
                    game_over()
                    continue
            
            enemies.remove(enemy)
            if explosion_sound:
                explosion_sound.play()
    
    # Обновление пуль
    for bullet in bullets[:]:
        if bullet.update():  # Если пуля вышла за экран
            bullets.remove(bullet)
            continue
        
        # Проверка попадания во врагов
        for enemy in enemies[:]:
            if (bullet.x > enemy.x and bullet.x < enemy.x + enemy.size and
                bullet.y > enemy.y and bullet.y < enemy.y + enemy.size):
                
                # Система комбо
                current_time = time.time()
                if current_time - last_hit_time < combo_time_window:
                    combo += 1
                else:
                    combo = 1
                last_hit_time = current_time
                max_combo = max(max_combo, combo)
                
                # Добавляем очки с учетом комбо
                score += enemy.points * combo
                
                # Создаем взрыв
                create_explosion(enemy.x + enemy.size // 2, 
                               enemy.y + enemy.size // 2, 
                               enemy.color)
                
                # 15% шанс дропа улучшения
                if random.random() < 0.15:
                    powerups.append(PowerUp(enemy.x + enemy.size // 2 - 10, 
                                         enemy.y + enemy.size // 2))
                
                # Удаляем пулю и врага
                bullets.remove(bullet)
                enemies.remove(enemy)
                
                if explosion_sound:
                    explosion_sound.play()
                
                break
    
    # Обновление улучшений
    for powerup in powerups[:]:
        if powerup.update():  # Если улучшение вышло за экран
            powerups.remove(powerup)
            continue
        
        # Проверка сбора игроком
        if check_collision(player, powerup):
            current_time = time.time()
            
            if powerup.type == 'shield':
                player.shield = True
                player.shield_time = current_time + 10  # 10 секунд
            elif powerup.type == 'rapid':
                player.rapid_fire = True
                player.rapid_fire_time = current_time + 15  # 15 секунд
            else:  # speed
                player.speed = player.base_speed * 2
                player.speed_boost = True
                player.speed_boost_time = current_time + 8  # 8 секунд
            
            powerups.remove(powerup)
            if powerup_sound:
                powerup_sound.play()
    
    # Обновление частиц
    for particle in particles[:]:
        if particle.update():  # Если частица умерла
            particles.remove(particle)
    
    # Отрисовка
    screen.fill((0, 0, 0))
    
    # Рисуем частицы (под всеми объектами)
    for particle in particles:
        particle.draw()
    
    # Рисуем игрока
    player.draw()
    
    # Рисуем врагов
    for enemy in enemies:
        enemy.draw()
    
    # Рисуем пули
    for bullet in bullets:
        bullet.draw()
    
    # Рисуем улучшения
    for powerup in powerups:
        powerup.draw()
    
    # Рисуем HUD
    draw_hud()
    
    pygame.display.update()
    clock.tick(60)

pygame.quit()