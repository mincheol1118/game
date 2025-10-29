import pygame
import random
import math
import os
from settings import * # settings.py의 상수들을 사용합니다.

# 리소스 로드 함수 (Fallback 처리 포함)
# 이 함수는 스프라이트 클래스들에서 이미지를 로드할 때 사용됩니다.
def load_image(filename, size):
    full_path = os.path.join(IMAGE_FOLDER, filename) # settings.py의 IMAGE_FOLDER 사용
    try:
        image = pygame.image.load(full_path).convert_alpha()
        return pygame.transform.scale(image, size)
    except (pygame.error, FileNotFoundError):
        print(f"Warning: Image '{filename}' not found or could not be loaded. Using fallback.")
        return pygame.Surface(size, pygame.SRCALPHA) # 투명한 Surface 반환

# --- 스프라이트 클래스 정의 ---
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__(); self.game = game; self.player_size = (60, 50)
        
        # 플레이어 애니메이션 프레임 로드 또는 기본 도형 생성
        self.animation_frames = [load_image(f'player_fly{i}.png', self.player_size) for i in range(1, 4)]
        if all(img.get_width() == 0 for img in self.animation_frames):
            print("Warning: Player animation images not found. Using default player shape.")
            default_surf = pygame.Surface(self.player_size, pygame.SRCALPHA)
            pygame.draw.polygon(default_surf, GREEN, [(30, 0), (0, 45), (60, 45)]); pygame.draw.polygon(default_surf, YELLOW, [(30, 20), (15, 40), (45, 40)])
            self.animation_frames = [default_surf] * 3 # 3개의 동일한 프레임으로 대체

        self.current_frame, self.last_update, self.frame_rate = 0, pygame.time.get_ticks(), 100
        self.image = self.animation_frames[self.current_frame]
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 60))
        self.radius = int(self.rect.width * 0.8 / 2); self.lives, self.shield = 3, 1
        self.hidden, self.hide_timer = False, pygame.time.get_ticks()
        self.power, self.power_time = 1, pygame.time.get_ticks() # 총알 파워업 (1단계)
        self.shoot_delay, self.last_shot = 200, pygame.time.get_ticks()
        self.is_magnet_active, self.magnet_timer, self.magnet_duration = False, pygame.time.get_ticks(), 7000 # 자석 아이템
        self.speed = 8 # 플레이어 이동 속도
        self.pop_up_message, self.pop_up_timer, self.pop_up_duration = "", 0, 1500 # 팝업 메시지

    def update(self):
        now = pygame.time.get_ticks()
        # 애니메이션 업데이트
        if now - self.last_update > self.frame_rate: self.last_update, self.current_frame, self.image = now, (self.current_frame + 1) % len(self.animation_frames), self.animation_frames[self.current_frame]
        # 숨기기 상태 해제
        if self.hidden and now - self.hide_timer > 1000: self.hidden, self.rect.centerx, self.rect.bottom = False, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 10
        # 총알 파워업 시간 제한
        if self.power > 1 and now - self.power_time > 5000: self.power = 1
        # 자석 효과 시간 제한
        if self.is_magnet_active and now - self.magnet_timer > self.magnet_duration: self.is_magnet_active = False
        # 팝업 메시지 시간 제한
        if self.pop_up_message and now - self.pop_up_timer > self.pop_up_duration: self.pop_up_message = ""
        
        # 키 입력 처리 (이동)
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]: self.rect.x -= self.speed
        if keystate[pygame.K_RIGHT]: self.rect.x += self.speed
        if keystate[pygame.K_UP]: self.rect.y -= self.speed
        if keystate[pygame.K_DOWN]: self.rect.y += self.speed
        
        # 스페이스바로 폭탄 사용 (아이템 획득 시)
        if keystate[pygame.K_SPACE] and self.game.player_has_bomb:
            self.game.activate_bomb()
            self.game.player_has_bomb = False # 폭탄 사용 후 제거

        # 화면 밖으로 나가지 못하게 제한 (수정됨: 모든 방향)
        self.rect.right = min(self.rect.right, SCREEN_WIDTH)
        self.rect.left = max(self.rect.left, 0)
        self.rect.bottom = min(self.rect.bottom, SCREEN_HEIGHT)
        self.rect.top = max(self.rect.top, 0) # 상단도 0으로 제한
        
        # 숨기기 상태가 아니면 총알 발사
        if not self.hidden: self.shoot()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            colors = {1: YELLOW, 2: BLUE, 3: RED}; bullet_color = colors.get(self.power, RED)
            if self.power == 1: self.game.spawn_bullet(self.rect.centerx, self.rect.top, bullet_color)
            elif self.power == 2:
                self.game.spawn_bullet(self.rect.left + 10, self.rect.centery, bullet_color)
                self.game.spawn_bullet(self.rect.right - 10, self.rect.centery, bullet_color)
            elif self.power >= 3:
                self.game.spawn_bullet(self.rect.centerx, self.rect.top, bullet_color)
                self.game.spawn_bullet(self.rect.left + 10, self.rect.centery, bullet_color, -15)
                self.game.spawn_bullet(self.rect.right - 10, self.rect.centery, bullet_color, 15)
            self.game.shoot_sound.play() # 사운드 재생

    def powerup(self, type):
        msg = ""
        if type == 'shield': self.shield, msg = min(self.shield + 1, 3), "쉴드 획득!"
        elif type == 'gun': self.power, self.power_time, msg = min(self.power + 1, 3), pygame.time.get_ticks(), "총알 강화!"
        elif type == 'speed': self.speed, msg = min(self.speed + 2, 14), "속도 증가!"
        elif type == 'hp': self.lives, msg = min(self.lives + 1, 5), "체력 회복!"
        elif type == 'bomb': # 폭탄 아이템 획득 시 플레이어에게 플래그 설정
            self.game.player_has_bomb = True
            msg = "폭탄 획득! (Space Bar)"
        elif type == 'magnet':
            self.is_magnet_active = True; self.magnet_timer = pygame.time.get_ticks()
            msg = "자석 효과 활성화!"

        if msg: self.show_pop_up(msg)
        self.game.powerup_sound.play() # 사운드 재생
        
    def show_pop_up(self, message): self.pop_up_message, self.pop_up_timer = message, pygame.time.get_ticks()
    def hide(self): self.hidden, self.hide_timer, self.rect.center = True, pygame.time.get_ticks(), (SCREEN_WIDTH / 2, SCREEN_HEIGHT + 200) # 화면 밖으로 숨김
    def draw_magnet_aura(self, surf):
        if self.is_magnet_active:
            # 자석 효과 시 빛나는 효과 추가
            glow_radius = 80 + (pygame.time.get_ticks() // 10 % 10) * 2 # 시간에 따라 반지름 변화
            alpha = 150 - (pygame.time.get_ticks() // 10 % 10) * 10 # 시간에 따라 투명도 변화
            aura_color = (LIGHT_BLUE[0], LIGHT_BLUE[1], LIGHT_BLUE[2], max(50, alpha))
            pygame.draw.circle(surf, aura_color, self.rect.center, glow_radius, 0) # 채워진 원으로 빛 표현
            pygame.draw.circle(surf, LIGHT_BLUE, self.rect.center, 80, 2) # 테두리

class Mob(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__(); self.game = game
        self.original_image = self.game.mob_img_normal # 일반 몹 이미지 사용
        
        # 몹 이미지가 없을 경우, 기본 도형으로 생성
        if self.original_image.get_width() == 0:
            size = (40,40)
            self.original_image = pygame.Surface(size, pygame.SRCALPHA); pygame.draw.circle(self.original_image, RED, (size[0]//2, size[1]//2), size[0]//2)

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(random.randrange(40, SCREEN_WIDTH - 40), random.randrange(-150, -100)))
        self.radius = int(self.rect.width * .85 / 2); self.speedy = random.randrange(2, 6); self.speedx = random.randrange(-2, 2)
        self.hp = 1 # 몹 HP

    def update(self):
        self.rect.x += self.speedx; self.rect.y += self.speedy
        # 화면 밖으로 나가면 제거
        if self.rect.top > SCREEN_HEIGHT + 10 or self.rect.left < -25 or self.rect.right > SCREEN_WIDTH + 20: self.kill()
    
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, color, angle_offset=0):
        super().__init__()
        bullet_size = (15, 30) # 원하는 총알 이미지 크기 (bullet.png 크기에 맞춰 조절 가능)

        # bullet.png 이미지를 로드합니다. 파일이 없으면 기존 사각형으로 Fallback
        self.image = load_image('bullet.png', bullet_size) # sprites.py의 load_image 함수 사용
        if self.image.get_width() == 0: # 이미지 로드 실패 시, 기본 사각형으로 대체
            self.image = pygame.Surface(bullet_size, pygame.SRCALPHA)
            self.image.fill(color) # 원래 총알의 색상 유지

        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10
        angle_rad = math.radians(-90 + angle_offset) # 위로 발사
        self.speedx, self.speedy = self.speed * math.cos(angle_rad), self.speed * math.sin(angle_rad)
        self.rect.x += self.speedx; self.rect.y += self.speedy
        if self.rect.bottom < 0: self.kill() # 화면 위로 나가면 제거

class MobBullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y, target=None, speed=6): # game 인자 추가
        super().__init__(); self.game = game # game 객체 저장
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA); pygame.draw.circle(self.image, PURPLE, (8, 8), 7)
        self.rect = self.image.get_rect(center=(x, y)); self.radius, self.speed = 7, speed
        
        # 플레이어를 향해 발사 (없으면 아래로)
        if target and target.alive(): angle_rad = math.atan2(target.rect.centery - self.rect.centery, target.rect.centerx - self.rect.centerx)
        else: angle_rad = math.radians(90) # 기본적으로 아래로
        self.speedx, self.speedy = self.speed * math.cos(angle_rad), self.speed * math.sin(angle_rad)
    def update(self):
        self.rect.x += self.speedx; self.rect.y += self.speedy
        # 화면 밖으로 나가면 제거
        if not self.rect.colliderect(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).inflate(50,50)): self.kill()


class Powerup(pygame.sprite.Sprite):
    def __init__(self, game, center): # game 인자 추가
        super().__init__(); self.game = game # game 객체 저장
        self.type = random.choice(['shield', 'gun', 'speed', 'hp', 'bomb', 'magnet'])
        size = (30,30) # 기본 크기

        # game.load_data에서 이미 로드된 이미지를 활용 (혹은 Fallback)
        image_map = {
            'shield': self.game.shield_img,
            'gun': self.game.twin_shot_img,
            'speed': self.game.speed_img,
            'hp': self.game.hp_img,
            'bomb': self.game.bomb_img,
            'magnet': self.game.magnet_img
        }
        self.image = image_map.get(self.type)
        if self.image is None or self.image.get_width() == 0: # 이미지 로드 실패 시 Fallback
            self.image = self.generate_fallback_image(size)

        self.rect = self.image.get_rect(center=center); self.speedy, self.speedx = 5, 0

    # Fallback 이미지를 생성하는 메서드
    def generate_fallback_image(self, size):
        fallback_surf = pygame.Surface(size, pygame.SRCALPHA)
        if self.type == 'shield': # 쉴드
            pygame.draw.circle(fallback_surf, GREEN, (size[0]//2, size[1]//2), size[0]//2 - 2, 2)
            pygame.draw.circle(fallback_surf, GREEN, (size[0]//2, size[1]//2), size[0]//2 - 7, 2)
        elif self.type == 'gun': # 총알 강화
            pygame.draw.rect(fallback_surf, BLUE, (5,10,20,10))
            pygame.draw.rect(fallback_surf, BLUE, (10,5,10,20))
        elif self.type == 'speed': # 속도 증가
            pygame.draw.polygon(fallback_surf, WHITE, [(size[0]//2,0),(0,size[1]),(size[0],size[1])])
        elif self.type == 'hp': # 체력 회복
            pygame.draw.circle(fallback_surf, RED, (size[0]//2 - 5, size[1]//2 - 5), size[0]//4)
            pygame.draw.circle(fallback_surf, RED, (size[0]//2 + 5, size[1]//2 - 5), size[0]//4)
            pygame.draw.polygon(fallback_surf, RED, [(size[0]//4,size[1]//2-2),(size[0]*3//4,size[1]//2-2),(size[0]//2,size[1]*3//4)])
        elif self.type == 'bomb': # 폭탄 (제공된 bomb.png 사용됨)
            pygame.draw.circle(fallback_surf, BLACK, (size[0]//2, size[1]//2), size[0]//2 - 2)
            pygame.draw.rect(fallback_surf, YELLOW, (size[0]//2 - 2, 0, 4, 10))
        elif self.type == 'magnet': # 자석 (제공된 magnet.png 사용됨)
            pygame.draw.arc(fallback_surf, BLUE, (5,5,size[0]-10,size[1]-10), math.pi, math.pi*2, 5) # U자형 자석
            pygame.draw.line(fallback_surf, BLUE, (5, (size[1]-10)//2 + 5), (5, size[1]-5), 5)
            pygame.draw.line(fallback_surf, BLUE, (size[0]-5, (size[1]-10)//2 + 5), (size[0]-5, size[1]-5), 5)
        return fallback_surf

    def update(self):
        self.rect.x += self.speedx; self.rect.y += self.speedy
        
        # 자석 효과: 플레이어가 활성화 상태면 아이템을 끌어당김
        if self.game.player.is_magnet_active: # Powerup 객체에 self.game이 있어서 player 접근 가능
            dx, dy = self.game.player.rect.centerx - self.rect.centerx, self.game.player.rect.centery - self.rect.centery
            dist = math.sqrt(dx**2 + dy**2); magnet_strength = 0.5 # 자석 아이템의 힘
            if dist > 0 and dist < 150: # 플레이어와의 거리가 150픽셀 이내일 때만 당김
                self.speedx += dx / dist * magnet_strength; self.speedy += dy / dist * magnet_strength
                # 최대 속도 제한
                max_pull_speed = 10
                if abs(self.speedx) > max_pull_speed: self.speedx = math.copysign(max_pull_speed, self.speedx)
                if abs(self.speedy) > max_pull_speed: self.speedy = math.copysign(max_pull_speed, self.speedy)
        if self.rect.top > SCREEN_HEIGHT: self.kill() # 화면 아래로 나가면 제거


class Explosion(pygame.sprite.Sprite):
    def __init__(self, game, center, size): # game 인자 추가
        super().__init__(); self.game = game; self.size = size;
        
        # 폭발 애니메이션 로드 또는 Fallback (game.explosion_anim에서 가져옴)
        if len(self.game.explosion_anim[self.size]) == 0 or self.game.explosion_anim[self.size][0].get_width() == 0:
            self.fallback_active = True
            # 폭발 애니메이션 이미지가 없는 경우, 동그란 도형으로 Fallback 생성
            self.fallback_frames = []
            for i in range(9):
                img = pygame.Surface((i*15 + 30, i*15 + 30), pygame.SRCALPHA)
                pygame.draw.circle(img, YELLOW, (img.get_width()//2, img.get_height()//2), i*7 + 15)
                self.fallback_frames.append(img)
            self.image = self.fallback_frames[0]
        else:
            self.fallback_active = False
            self.image = self.game.explosion_anim[self.size][0]

        self.rect = self.image.get_rect(center=center)
        self.frame, self.last_update, self.frame_rate = 0, pygame.time.get_ticks(), 75

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update, self.frame = now, self.frame + 1
            if (self.fallback_active and self.frame == len(self.fallback_frames)) or \
               (not self.fallback_active and self.frame == len(self.game.explosion_anim[self.size])):
                self.kill() # 애니메이션이 끝나면 제거
            else:
                if self.fallback_active: self.image = self.fallback_frames[self.frame]
                else: self.image = self.game.explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect(center=self.rect.center)

# sprites.py 파일의 맨 아래, 다른 클래스들 다음에 이 코드를 추가하세요.

class Boss(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = self.game.boss_img  # main.py에서 로드된 보스 이미지 사용
        if self.image.get_width() == 0:  # 이미지 없으면 Fallback 도형 생성
            size = (200, 150) # 보스 기본 크기
            self.image = pygame.Surface(size, pygame.SRCALPHA)
            # Fallback 보스 그리기 (색상 및 모양 조정)
            pygame.draw.circle(self.image, (100, 0, 100), (size[0] // 2, size[1] // 2), size[0] // 2 - 10)
            pygame.draw.circle(self.image, (200, 0, 200), (size[0] // 2 - 40, size[1] // 2 - 30), 15) # 왼쪽 눈
            pygame.draw.circle(self.image, (200, 0, 200), (size[0] // 2 + 40, size[1] // 2 - 30), 15) # 오른쪽 눈
            pygame.draw.arc(self.image, (200, 0, 200), (size[0] // 2 - 50, size[1] // 2 + 20, 100, 50), math.pi, 0, 5) # 입

        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, -100)) # 화면 상단 밖에서 시작
        self.hp = 200 # 보스 체력 (원하는 값으로 조절)
        self.max_hp = self.hp
        self.speedy = 1 # 등장 속도
        self.speedx = 2 # 좌우 이동 속도
        self.is_active = False # 화면에 완전히 등장하기 전까지는 공격하지 않음
        self.shoot_delay = 800 # 보스 총알 발사 딜레이 (ms)
        self.last_shot_time = pygame.time.get_ticks()

    def update(self):
        if not self.is_active: # 화면에 등장하는 중
            self.rect.y += self.speedy
            if self.rect.centery >= 150: # 화면 특정 위치(Y=150)까지 내려오면 활성화
                self.is_active = True
                self.speedy = 0 # 등장 멈춤
        else: # 활성화 상태일 때
            # 좌우 이동 로직
            self.rect.x += self.speedx
            if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                self.speedx *= -1 # 벽에 닿으면 반대 방향으로 이동

            # 총알 발사
            now = pygame.time.get_ticks()
            if now - self.last_shot_time > self.shoot_delay:
                self.last_shot_time = now
                # 보스 총알 스폰 로직 (두 발 동시 발사)
                self.game.spawn_mob_bullet(self.rect.centerx - 50, self.rect.bottom - 20, self.game.player)
                self.game.spawn_mob_bullet(self.rect.centerx + 50, self.rect.bottom - 20, self.game.player)
                if self.game.enemy_shoot_sound: # 사운드 존재 여부 확인
                    self.game.enemy_shoot_sound.play()

        # 보스 체력 바 그리기 (보스 스프라이트 위에 직접 그림)
        if self.is_active and self.hp > 0: # 보스가 활성화되고 살아있을 때만 그립니다.
            bar_length = 150
            bar_height = 10
            fill = (self.hp / self.max_hp) * bar_length
            # 체력바의 위치를 보스 rect 기준으로 계산
            outline_rect = pygame.Rect(self.rect.centerx - bar_length // 2, self.rect.top - 20, bar_length, bar_height)
            fill_rect = pygame.Rect(self.rect.centerx - bar_length // 2, self.rect.top - 20, fill, bar_height)

            # 주의: 스프라이트의 이미지에 그리는 것은 복잡하므로, Game.draw()에서 직접 화면에 그리는 것이 좋습니다.
            # 임시로 여기에 두지만, Game.draw()의 draw_boss_hp_bar() 메서드를 활용하는 것이 더 깔끔합니다.
            # 여기서는 작동 확인을 위해 남겨둡니다.
            # pygame.draw.rect(self.image, RED, fill_rect)
            # pygame.draw.rect(self.image, WHITE, outline_rect, 2)