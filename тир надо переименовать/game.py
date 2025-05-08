import pygame as pg
import sys
import random
import math
from pygame.locals import *

pg.init()
pg.mixer.init()
shot_sound = pg.mixer.Sound("shot.wav")
explosion_sound = pg.mixer.Sound("explosion.wav")
boom_sound = pg.mixer.Sound('awp-sound.mp3')
WIDTH = 800
HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
RELOAD_TIME = 2000

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Тир")
clock = pg.time.Clock()

# Загрузка изображений (добавьте свои изображения для нового оружия)
background_img = pg.image.load("background.png").convert_alpha()
player_img = pg.image.load("player.png").convert_alpha()
weapon_img = pg.image.load("weapon.png").convert_alpha()
bullet_img = pg.image.load("bullet.png").convert_alpha()
target_img = pg.image.load("target.png").convert_alpha()
target_hit_img = pg.image.load("target_hit.png").convert_alpha()
buy_button_img = pg.image.load("buy_button.png").convert_alpha()
barrier_img = pg.image.load("barrier.png").convert_alpha()
shop_img = pg.image.load("shop.png").convert_alpha()
rpg_img = pg.image.load("rpg.png").convert_alpha()
minigun_img = pg.image.load("minigun.png").convert_alpha()
sniper_img = pg.image.load("sniper.png").convert_alpha()
explosion_img = pg.image.load("explosion.png").convert_alpha()

# Состояния игры
MENU = 0
LEVEL1 = 1
LEVEL2 = 2
SHOP = 3
game_state = MENU

class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = 100
        self.rect.centery = HEIGHT // 2
        self.speed = 5
        self.weapon = Weapon(self, "pistol")  # Стандартное оружие
        self.magazines = 5
        self.bullets_in_magazine = 10
        self.reloading = False
        self.reload_start_time = 0
        self.coins = 0
        self.barrier = None
        self.current_weapon = "pistol"
        self.minigun_ammo = 0
        self.sniper_ammo = 0
        self.rpg_ammo = 0

    def update(self):
        keys = pg.key.get_pressed()
        if keys[K_w] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[K_s] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
        if keys[K_a] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[K_d] and self.rect.right < (self.barrier.rect.left if self.barrier else WIDTH):
            self.rect.x += self.speed

        self.weapon.update()

        if self.reloading:
            current_time = pg.time.get_ticks()
            if current_time - self.reload_start_time >= RELOAD_TIME:
                self.reloading = False
                if self.current_weapon == "pistol":
                    self.bullets_in_magazine = 10
                elif self.current_weapon == "minigun":
                    self.bullets_in_magazine = 50
                elif self.current_weapon == "sniper":
                    self.bullets_in_magazine = 3
                elif self.current_weapon == "rpg":
                    self.bullets_in_magazine = 1

    def shoot(self):
        if self.bullets_in_magazine > 0 and not self.reloading:
            self.bullets_in_magazine -= 1
            bullet_pos = self.weapon.get_muzzle_position()
            if self.current_weapon == 'pistol':
                shot_sound.play()
            if self.current_weapon == "rpg":
                explosion_sound.play()
                return RPGBullet(bullet_pos[0], bullet_pos[1], self.weapon.angle)
            elif self.current_weapon == "minigun":
                # Добавляем небольшой разброс для минигана
                angle = self.weapon.angle + random.uniform(-5, 5)
                return Bullet(bullet_pos[0], bullet_pos[1], angle, "minigun")
            elif self.current_weapon == "sniper":
                boom_sound.play()
                return Bullet(bullet_pos[0], bullet_pos[1], self.weapon.angle, "sniper")
            else:
                return Bullet(bullet_pos[0], bullet_pos[1], self.weapon.angle, "pistol")

        elif self.bullets_in_magazine == 0 and not self.reloading:
            if (self.current_weapon == "pistol" and self.magazines > 0) or \
               (self.current_weapon == "minigun" and self.minigun_ammo > 0) or \
               (self.current_weapon == "sniper" and self.sniper_ammo > 0) or \
               (self.current_weapon == "rpg" and self.rpg_ammo > 0):
                self.reload()

        return None

    def reload(self):
        if not self.reloading:
            if self.current_weapon == "pistol" and self.magazines > 0:
                self.magazines -= 1
            elif self.current_weapon == "minigun" and self.minigun_ammo > 0:
                self.minigun_ammo -= 1
            elif self.current_weapon == "sniper" and self.sniper_ammo > 0:
                self.sniper_ammo -= 1
            elif self.current_weapon == "rpg" and self.rpg_ammo > 0:
                self.rpg_ammo -= 1
            else:
                return False

            self.reloading = True
            self.reload_start_time = pg.time.get_ticks()
            return True
        return False

    def buy_magazines(self):
        if self.coins >= 100:
            self.magazines += 2
            self.coins -= 100
            return True
        return False

    def buy_weapon(self, weapon_type, cost):
        if self.coins >= cost:
            self.coins -= cost
            if weapon_type == "rpg":
                self.rpg_ammo += 2
                return True
            elif weapon_type == "minigun":
                self.minigun_ammo += 2
                return True
            elif weapon_type == "sniper":
                self.sniper_ammo += 4
                return True
        return False

    def switch_weapon(self, weapon_type):
        self.current_weapon = weapon_type
        if weapon_type == "pistol":
            self.weapon = Weapon(self, "pistol")
        elif weapon_type == "rpg":
            self.weapon = Weapon(self, "rpg")
        elif weapon_type == "minigun":
            self.weapon = Weapon(self, "minigun")
        elif weapon_type == "sniper":
            self.weapon = Weapon(self, "sniper")

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.weapon.draw(surface)

class Weapon(pg.sprite.Sprite):
    def __init__(self, player, weapon_type):
        super().__init__()
        self.player = player
        self.weapon_type = weapon_type

        if weapon_type == "pistol":
            self.image = weapon_img
        elif weapon_type == "rpg":
            self.image = rpg_img
        elif weapon_type == "minigun":
            self.image = minigun_img
        elif weapon_type == "sniper":
            self.image = sniper_img

        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.angle = 0

    def update(self):
        mouse_pos = pg.mouse.get_pos()
        dx = mouse_pos[0] - self.player.rect.centerx
        dy = mouse_pos[1] - self.player.rect.centery
        self.angle = math.degrees(math.atan2(-dy, dx))

        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()

        offset_x = 20
        offset_y = 0
        self.rect.center = (
            self.player.rect.centerx + offset_x * math.cos(math.radians(self.angle)),
            self.player.rect.centery - offset_y * math.sin(math.radians(self.angle))
        )

    def get_muzzle_position(self):
        angle_rad = math.radians(self.angle)
        muzzle_distance = 25
        muzzle_x = self.rect.centerx + math.cos(angle_rad) * muzzle_distance
        muzzle_y = self.rect.centery - math.sin(angle_rad) * muzzle_distance
        return (muzzle_x, muzzle_y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y, angle, weapon_type="pistol"):
        super().__init__()
        self.weapon_type = weapon_type

        if weapon_type == "pistol":
            self.image = bullet_img
            self.speed = 10
            self.damage = 1
        elif weapon_type == "minigun":
            self.image = bullet_img
            self.speed = 15
            self.damage = 1
        elif weapon_type == "sniper":
            self.image = bullet_img
            self.speed = 30
            self.damage = 2

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.angle = angle
        self.image = pg.transform.rotate(self.image, angle)

        angle_rad = math.radians(angle)
        self.speedx = math.cos(angle_rad) * self.speed
        self.speedy = -math.sin(angle_rad) * self.speed

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        if self.rect.right < 0 or self.rect.left > WIDTH or self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()

class RPGBullet(pg.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = bullet_img  # Можно использовать другое изображение для RPG
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.angle = angle
        self.speed = 8
        self.explosion_radius = 100
        self.exploded = False
        self.explosion_time = 0

        angle_rad = math.radians(angle)
        self.speedx = math.cos(angle_rad) * self.speed
        self.speedy = -math.sin(angle_rad) * self.speed

    def update(self):
        if not self.exploded:
            self.rect.x += self.speedx
            self.rect.y += self.speedy

            if self.rect.right < 0 or self.rect.left > WIDTH or self.rect.bottom < 0 or self.rect.top > HEIGHT:
                self.explode()
        else:
            if pg.time.get_ticks() - self.explosion_time > 500:  # Время показа взрыва
                self.kill()

    def explode(self):
        self.exploded = True
        self.explosion_time = pg.time.get_ticks()
        self.image = explosion_img
        self.rect = self.image.get_rect(center=self.rect.center)

class Target(pg.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        self.image = target_img
        self.rect = self.image.get_rect()

        if level == 1:
            self.rect.x = random.randint(int(WIDTH * 0.3), WIDTH - self.rect.width)
            self.rect.y = random.randint(50, HEIGHT - 50)
            self.speed = random.uniform(1, 3)
            self.direction = random.choice([-1, 1])
            self.min_y = random.randint(50, HEIGHT // 2)
            self.max_y = random.randint(self.min_y + 100, HEIGHT - 50)
        else:  # Уровень 2 - мишени появляются на короткое время
            self.rect.x = random.randint(int(WIDTH * 0.3), WIDTH - self.rect.width)
            self.rect.y = random.randint(50, HEIGHT - 50)
            self.speed = 0
            self.lifetime = 2000  # 2 секунды
            self.spawn_time = pg.time.get_ticks()

        self.hits = 0

    def update(self):
        if hasattr(self, 'lifetime'):  # Для уровня 2
            if pg.time.get_ticks() - self.spawn_time > self.lifetime:
                self.kill()
        else:  # Для уровня 1
            self.rect.y += self.speed * self.direction
            if self.rect.top < self.min_y:
                self.rect.top = self.min_y
                self.direction *= -1
            elif self.rect.bottom > self.max_y:
                self.rect.bottom = self.max_y
                self.direction *= -1

    def hit(self, damage=1):
        self.hits += damage
        if self.hits == 1:
            self.image = target_hit_img
        return self.hits >= 2

class Button:
    def __init__(self, image, pos, text="", font_size=30, text_color=WHITE):
        self.image = image
        self.rect = image.get_rect()
        self.rect.topleft = pos
        self.text = text
        self.font = pg.font.SysFont(None, font_size)
        self.text_color = text_color
        self.text_surf = self.font.render(text, True, text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.text:
            surface.blit(self.text_surf, self.text_rect)

class ShopMenu:
    def __init__(self):
        self.visible = False
        self.background = pg.Surface((600, 400))
        self.background.fill((50, 50, 50))
        self.background.set_alpha(230)
        self.rect = self.background.get_rect(center=(WIDTH//2, HEIGHT//2))

        # Кнопки оружия
        self.rpg_button = Button(pg.Surface((150, 200)), (self.rect.x + 50, self.rect.y + 100), "РПГ (500)")
        self.minigun_button = Button(pg.Surface((150, 200)), (self.rect.x + 225, self.rect.y + 100), "Миниган (600)")
        self.sniper_button = Button(pg.Surface((150, 200)), (self.rect.x + 400, self.rect.y + 100), "Винтовка (200)")
        self.close_button = Button(pg.Surface((100, 40)), (self.rect.x + 250, self.rect.y + 350), "Закрыть")

    def draw(self, surface, player):
        if self.visible:
            surface.blit(self.background, self.rect)

            # Заголовок
            font = pg.font.SysFont(None, 48)
            title = font.render("Магазин оружия", True, WHITE)
            surface.blit(title, (self.rect.x + 200, self.rect.y + 30))

            # Информация о монетах
            coins_text = font.render(f"Монеты: {player.coins}", True, YELLOW)
            surface.blit(coins_text, (self.rect.x + 220, self.rect.y + 70))

            # Отрисовка кнопок
            self.rpg_button.draw(surface)
            self.minigun_button.draw(surface)
            self.sniper_button.draw(surface)
            self.close_button.draw(surface)

            # Описание оружия
            small_font = pg.font.SysFont(None, 24)

            # РПГ
            rpg_desc = [
                "Ракетница:",
                "- Взрыв при попадании",
                "- Поражает все цели в радиусе",
                "- Магазин: 1 патрон",
                "- Стоимость: 500"
            ]
            for i, line in enumerate(rpg_desc):
                text = small_font.render(line, True, WHITE)
                surface.blit(text, (self.rpg_button.rect.x, self.rpg_button.rect.y + 40 + i*20))

            # Миниган
            minigun_desc = [
                "Миниган:",
                "- Автоматическая стрельба",
                "- Большой магазин (50)",
                "- Высокая скорострельность",
                "- Стоимость: 600"
            ]
            for i, line in enumerate(minigun_desc):
                text = small_font.render(line, True, WHITE)
                surface.blit(text, (self.minigun_button.rect.x, self.minigun_button.rect.y + 40 + i*20))

            # Снайперка
            sniper_desc = [
                "Снайперская винтовка:",
                "- Мощный выстрел",
                "- Магазин: 3 патрона",
                "- Моментальное попадание",
                "- Стоимость: 200"
            ]
            for i, line in enumerate(sniper_desc):
                text = small_font.render(line, True, WHITE)
                surface.blit(text, (self.sniper_button.rect.x, self.sniper_button.rect.y + 40 + i*20))

    def handle_event(self, event, player):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rpg_button.is_clicked(event.pos):
                if player.buy_weapon("rpg", 500):
                    player.switch_weapon("rpg")
            elif self.minigun_button.is_clicked(event.pos):
                if player.buy_weapon("minigun", 600):
                    player.switch_weapon("minigun")
            elif self.sniper_button.is_clicked(event.pos):
                if player.buy_weapon("sniper", 200):
                    player.switch_weapon("sniper")
            elif self.close_button.is_clicked(event.pos):
                self.visible = False

class MainMenu:
    def __init__(self):
        self.background = pg.Surface((WIDTH, HEIGHT))
        self.background.fill((30, 30, 50))

        # Кнопки меню
        self.level1_button = Button(pg.Surface((300, 60)), (WIDTH//2 - 150, HEIGHT//2 - 100), "Уровень 1: Дуэль")
        self.level2_button = Button(pg.Surface((300, 60)), (WIDTH//2 - 150, HEIGHT//2), "Уровень 2: Тренировка")
        self.shop_button = Button(pg.Surface((300, 60)), (WIDTH//2 - 150, HEIGHT//2 + 100), "Магазин")

        # Заголовок
        self.font = pg.font.SysFont(None, 72)
        self.title = self.font.render("Тир", True, WHITE)
        self.title_rect = self.title.get_rect(center=(WIDTH//2, HEIGHT//4))

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        surface.blit(self.title, self.title_rect)
        self.level1_button.draw(surface)
        self.level2_button.draw(surface)
        self.shop_button.draw(surface)

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.level1_button.is_clicked(event.pos):
                return LEVEL1
            elif self.level2_button.is_clicked(event.pos):
                return LEVEL2
            elif self.shop_button.is_clicked(event.pos):
                return SHOP
        return MENU

def draw_ui(surface, player, score):
    font = pg.font.SysFont(None, 36)
    score_text = font.render(f"Счёт: {score}", True, WHITE)
    surface.blit(score_text, (10, 10))

    coins_text = font.render(f"Монеты: {player.coins}", True, WHITE)
    surface.blit(coins_text, (10, 50))

    # Отображение информации о текущем оружии и боеприпасах
    if player.current_weapon == "pistol":
        weapon_text = font.render(f"Пистолет: {player.bullets_in_magazine}/10", True, WHITE)
        magazines_text = font.render(f"Магазины: {player.magazines}", True, WHITE)
    elif player.current_weapon == "rpg":
        weapon_text = font.render(f"РПГ: {player.bullets_in_magazine}/1", True, WHITE)
        magazines_text = font.render(f"Ракеты: {player.rpg_ammo}", True, WHITE)
    elif player.current_weapon == "minigun":
        weapon_text = font.render(f"Миниган: {player.bullets_in_magazine}/50", True, WHITE)
        magazines_text = font.render(f"Ленты: {player.minigun_ammo}", True, WHITE)
    elif player.current_weapon == "sniper":
        weapon_text = font.render(f"Винтовка: {player.bullets_in_magazine}/3", True, WHITE)
        magazines_text = font.render(f"Обоймы: {player.sniper_ammo}", True, WHITE)

    surface.blit(weapon_text, (10, 90))
    surface.blit(magazines_text, (10, 130))

    if player.reloading:
        current_time = pg.time.get_ticks()
        elapsed = current_time - player.reload_start_time
        reload_percentage = min(elapsed / RELOAD_TIME, 1.0)

        pg.draw.rect(surface, GRAY, (10, 170, 200, 20))
        pg.draw.rect(surface, GREEN, (10, 170, 200 * reload_percentage, 20))

        reload_font = pg.font.SysFont(None, 24)
        reload_text = reload_font.render("Перезарядка", True, WHITE)
        reload_text_rect = reload_text.get_rect(center=(110, 180))
        surface.blit(reload_text, reload_text_rect)

class Barrier(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = barrier_img
        self.rect = self.image.get_rect()
        self.rect.x = int(WIDTH * 0.3)
        self.rect.y = 0
        self.rect.height = HEIGHT

def game_level1():
    all_sprites = pg.sprite.Group()
    bullets = pg.sprite.Group()
    targets = pg.sprite.Group()

    player = Player()
    all_sprites.add(player)
    all_sprites.add(player.weapon)

    barrier = Barrier()
    player.barrier = barrier
    all_sprites.add(barrier)

    buy_button = Button(buy_button_img, (WIDTH - 110, 10))
    shop_button = Button(shop_img, (WIDTH - 110, 60))

    for _ in range(10):
        target = Target(level=1)
        all_sprites.add(target)
        targets.add(target)

    score = 0
    shop_menu = ShopMenu()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == QUIT:
                running = False
                pg.quit()
                sys.exit()

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if shop_menu.visible:
                        shop_menu.handle_event(event, player)
                    else:
                        if buy_button.is_clicked(event.pos):
                            player.buy_magazines()
                        elif shop_button.is_clicked(event.pos):
                            shop_menu.visible = True
                        else:
                            bullet = player.shoot()
                            if bullet:
                                all_sprites.add(bullet)
                                bullets.add(bullet)

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if shop_menu.visible:
                        shop_menu.visible = False
                    else:
                        return MENU

        all_sprites.update()

        # Проверка попаданий
        hits = pg.sprite.groupcollide(bullets, targets, True, False)
        for bullet, target_list in hits.items():
            for target in target_list:
                if isinstance(bullet, RPGBullet):
                    # Взрыв RPG поражает все цели в радиусе
                    explosion_center = bullet.rect.center
                    for t in targets:
                        distance = math.sqrt((t.rect.centerx - explosion_center[0])**2 +
                                           (t.rect.centery - explosion_center[1])**2)
                        if distance < bullet.explosion_radius:
                            if t.hit(2):  # Двойной урон от взрыва
                                score += 10
                                player.coins += 10
                                t.kill()
                    bullet.explode()
                else:
                    if target.hit(bullet.damage):
                        score += 10
                        player.coins += 10
                        target.kill()

        if len(targets) == 0:
            for _ in range(10):
                target = Target(level=1)
                all_sprites.add(target)
                targets.add(target)

        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)
        buy_button.draw(screen)
        shop_button.draw(screen)
        draw_ui(screen, player, score)
        shop_menu.draw(screen, player)
        pg.display.flip()
        clock.tick(60)

    return MENU

def game_level2():
    all_sprites = pg.sprite.Group()
    bullets = pg.sprite.Group()
    targets = pg.sprite.Group()

    player = Player()
    player.switch_weapon("sniper")
    player.sniper_ammo = 5  # Даем немного патронов
    all_sprites.add(player)
    all_sprites.add(player.weapon)

    barrier = Barrier()
    player.barrier = barrier
    all_sprites.add(barrier)

    score = 0
    last_target_time = pg.time.get_ticks()
    target_spawn_delay = 1500  # 1.5 секунды между появлениями мишеней

    running = True
    while running:
        current_time = pg.time.get_ticks()

        for event in pg.event.get():
            if event.type == QUIT:
                running = False
                pg.quit()
                sys.exit()

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    bullet = player.shoot()
                    if bullet:
                        all_sprites.add(bullet)
                        bullets.add(bullet)

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return MENU

        # Спавн новых мишеней
        if current_time - last_target_time > target_spawn_delay and len(targets) < 5:
            target = Target(level=2)
            all_sprites.add(target)
            targets.add(target)
            last_target_time = current_time

        all_sprites.update()

        # Проверка попаданий
        hits = pg.sprite.groupcollide(bullets, targets, True, False)
        for bullet, target_list in hits.items():
            for target in target_list:
                if target.hit(bullet.damage):
                    score += 10
                    player.coins += 10
                    target.kill()

        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)
        draw_ui(screen, player, score)
        pg.display.flip()
        clock.tick(60)

    return MENU

def shop_screen(player):
    shop_menu = ShopMenu()
    shop_menu.visible = True

    running = True
    while running:
        for event in pg.event.get():
            if event.type == QUIT:
                running = False
                pg.quit()
                sys.exit()

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    shop_menu.handle_event(event, player)

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return MENU

        screen.fill((30, 30, 50))
        shop_menu.draw(screen, player)

        # Кнопка возврата
        font = pg.font.SysFont(None, 36)
        back_text = font.render("Нажмите ESC для возврата", True, WHITE)
        screen.blit(back_text, (WIDTH//2 - 150, HEIGHT - 50))

        pg.display.flip()
        clock.tick(60)

    return MENU

def main():
    global game_state

    main_menu = MainMenu()
    player = Player()
    shop_menu = ShopMenu()

    while True:
        if game_state == MENU:
            for event in pg.event.get():
                if event.type == QUIT:
                    pg.quit()
                    sys.exit()

                new_state = main_menu.handle_event(event)
                if new_state != MENU:
                    game_state = new_state
                    if game_state == LEVEL1:
                        player = Player()  # Сброс игрока для нового уровня
                    elif game_state == LEVEL2:
                        player = Player()
                        player.switch_weapon("sniper")
                        player.sniper_ammo = 5

            main_menu.draw(screen)

        elif game_state == LEVEL1:
            game_state = game_level1()
        elif game_state == LEVEL2:
            game_state = game_level2()
        elif game_state == SHOP:
            game_state = shop_screen(player)

        pg.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
