import pygame
import random
import sys
import math
import os

# settings.py, ui_elements.py, sprites.py, background_module.py에서 필요한 것들을 임포트합니다.
from settings import *
from ui_elements import Button
from sprites import Player, Mob, Bullet, MobBullet, Powerup, Explosion
from background_module import Background
from sprites import *

# 리소스 로드 함수 (Fallback 처리 포함)
# 이미지가 없으면 투명한 Surface를 반환하여 오류 대신 기본 도형을 사용하도록
def load_image(filename, size):
    full_path = os.path.join(IMAGE_FOLDER, filename)
    try:
        image = pygame.image.load(full_path).convert_alpha()
        return pygame.transform.scale(image, size)
    except (pygame.error, FileNotFoundError):
        print(f"Warning: Image '{filename}' not found or could not be loaded. Using fallback.")
        return pygame.Surface(size, pygame.SRCALPHA) # 투명한 Surface 반환

# --- Game 클래스 시작 ---
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_name = pygame.font.match_font('malgungothic')
        if not self.font_name:
            self.font_name = pygame.font.get_default_font()
        self.paused = False
        
        self.load_data() # 리소스 로드는 게임 객체 생성 시 한 번만
        self.player_has_bomb = False # 플레이어가 폭탄 아이템을 가지고 있는지 여부
        self.boss = None # 보스 객체 초기화
        self.boss_spawned = False # 보스가 이미 스폰되었는지 확인하는 플래그

        # 배경 모듈 초기화
        self.background = Background(self) # Background 객체 생성 시 game 인스턴스 전달

    # 텍스트 그리기 함수 (이동하지 않고 여기에 유지)
    def draw_text(self, surf, text, size, x, y, color, align="midtop", shadow=False):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        
        if align == "midtop": text_rect.midtop = (x, y)
        elif align == "topleft": text_rect.topleft = (x, y)
        elif align == "center": text_rect.center = (x, y)
        elif align == "midbottom": text_rect.midbottom = (x, y)

        if shadow:
            shadow_surface = font.render(text, True, SHADOW)
            shadow_rect = shadow_surface.get_rect()
            shadow_offset = 2
            if align == "midtop": shadow_rect.midtop = (x + shadow_offset, y + shadow_offset)
            elif align == "topleft": shadow_rect.topleft = (x + shadow_offset, y + shadow_offset)
            elif align == "center": shadow_rect.center = (x + shadow_offset, y + shadow_offset)
            elif align == "midbottom": shadow_rect.midbottom = (x + shadow_offset, y + shadow_offset)
            surf.blit(shadow_surface, shadow_rect)
            
        surf.blit(text_surface, text_rect)
        
    # HP 바 그리기 함수 (이동하지 않고 여기에 유지)
    def draw_hp_bar(self, surf, x, y, pct):
        if pct < 0: pct = 0
        BAR_LENGTH, BAR_HEIGHT = 200, 20
        fill = (pct / 100) * BAR_LENGTH
        outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
        fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
        color = GREEN if pct > 50 else YELLOW if pct > 20 else RED
        pygame.draw.rect(surf, color, fill_rect)
        pygame.draw.rect(surf, WHITE, outline_rect, 2)
    
    def load_data(self):
        # 최고 점수 로드
        try:
            with open(HIGHSCORE_FILE, 'r') as f:
                self.highscore = int(f.read())
        except:
            self.highscore = 0
        
        # --- 이미지 로드 ---
        # 제공된 이미지만 로드, 없는 이미지는 빈 Surface로 Fallback 처리
        self.mob_img_normal = load_image('mob.png', (40, 40))
        self.mob_img_fast = load_image('mob_fast.png', (30, 30))
        # self.mob_img_bomber = load_image('mob_bomber.png', (50, 50)) # 현재 사용하지 않으므로 주석 처리
        # self.shooter_img = load_image('shooter.png', (50, 40)) # 현재 사용하지 않으므로 주석 처리
        # self.boss_img = load_image('boss.png', (200, 150)) # 보스는 나중에 추가 (이미지는 제공됨)

        self.shield_img = load_image('shield.png', (30, 30))
        self.twin_shot_img = load_image('twin_shot.png', (30, 30))
        self.speed_img = load_image('speed.png', (30, 30))
        self.hp_img = load_image('hp.png', (30, 30))
        self.bomb_img = load_image('bomb.png', (30, 30)) # bomb.png는 제공됨
        self.magnet_img = load_image('magnet.png', (30, 30)) # magnet.png는 제공됨

        # 구름 이미지 로드 (없으면 Fallback은 Background 클래스에서 처리)
        self.cloud_img1 = load_image('cloud1.png', (random.randrange(100,200), random.randrange(50,100)))
        self.cloud_img2 = load_image('cloud2.png', (random.randrange(100,200), random.randrange(50,100)))
        self.cloud_img3 = load_image('cloud3.png', (random.randrange(100,200), random.randrange(50,100)))

        # Explosion animation Fallback
        self.explosion_anim = {'lg': [], 'sm': []}
        found_expl_images = False
        try:
            for i in range(9):
                img = load_image(f'expl{i}.png', (i*15 + 30, i*15 + 30))
                if img.get_width() > 0: 
                    self.explosion_anim['lg'].append(img)
                    img_sm = pygame.transform.scale(img, (i*8 + 15, i*8 + 15))
                    self.explosion_anim['sm'].append(img_sm)
                    found_expl_images = True
            if not found_expl_images: raise FileNotFoundError # 실제 이미지가 하나도 없으면 Fallback
        except FileNotFoundError:
            print("Warning: Explosion animation images not found. Using fallback shapes.")
            for i in range(9):
                img = pygame.Surface((i*15 + 30, i*15 + 30), pygame.SRCALPHA)
                pygame.draw.circle(img, YELLOW, (img.get_width()//2, img.get_height()//2), i*7 + 15)
                self.explosion_anim['lg'].append(img)
                img_sm = pygame.transform.scale(img, (i*8 + 15, i*8 + 15))
                self.explosion_anim['sm'].append(img_sm)
        
        # --- 사운드 로드 ---
        # 사운드 파일이 없으면 더미 사운드 객체로 대체하여 오류 방지
        class DummySound:
            def play(self): pass

        try: self.shoot_sound = pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'shoot.wav'))
        except: self.shoot_sound = DummySound(); print("Warning: 'shoot.wav' not found.")
        try: self.powerup_sound = pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'powerup.wav'))
        except: self.powerup_sound = DummySound(); print("Warning: 'powerup.wav' not found.")
        try: self.expl_sounds = [pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'expl1.wav')), pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'expl2.wav'))]
        except: self.expl_sounds = [DummySound(), DummySound()]; print("Warning: Explosion sounds not found.")
        try: self.enemy_shoot_sound = pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'enemy_shoot.wav'))
        except: self.enemy_shoot_sound = DummySound(); print("Warning: 'enemy_shoot.wav' not found.")
        try: self.player_hit_sound = pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'player_hit.wav'))
        except: self.player_hit_sound = DummySound(); print("Warning: 'player_hit.wav' not found.")
        try: self.bomb_sound = pygame.mixer.Sound(os.path.join(IMAGE_FOLDER, 'bomb.wav'))
        except: self.bomb_sound = DummySound(); print("Warning: 'bomb.wav' not found.")
        
        # BGM 로드 (bgm.ogg, menu_bgm.ogg는 제공됨)
        self.bgm_loaded = False; self.menu_bgm_loaded = False
        try: pygame.mixer.music.load(os.path.join(IMAGE_FOLDER, 'bgm.ogg')); self.bgm_loaded = True
        except: print("Warning: 'bgm.ogg' not found. Game will run without game BGM.")
        try: 
            pygame.mixer.music.load(os.path.join(IMAGE_FOLDER, 'menu_bgm.ogg')); self.menu_bgm_loaded = True
            pygame.mixer.music.stop() # Ensure menu_bgm is not playing initially
        except: print("Warning: 'menu_bgm.ogg' not found. Menu will run without menu BGM.")

    def new(self):
        self.score, self.stage = 0, 1 # 스테이지는 일단 단순화
        # 모든 스프라이트 그룹 초기화
        self.all_sprites = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.mob_bullets = pygame.sprite.Group() # 적 총알 그룹 (보스 활성화 시 사용)
        self.boss_group = pygame.sprite.Group() # 보스 전용 그룹 추가 (선택 사항이지만 명확성을 위해 추가)

        self.powerups = pygame.sprite.Group()

        self.player = Player(self) # Player 객체 생성 시 game 인스턴스 전달
        self.all_sprites.add(self.player)

        # 몹 스폰 로직 단순화
        self.max_mobs = 8 # 한 화면에 최대로 나올 몹 수
        self.mob_spawn_delay = 1000 # 몹 스폰 간격 (ms)
        self.last_mob_spawn_time = pygame.time.get_ticks()

        self.player_has_bomb = False # 게임 시작 시 폭탄 아이템 초기화
        self.boss = None # 보스 객체 초기화
        self.boss_spawned = False # 보스가 이미 스폰되었는지 확인하는 플래그 (new 게임 시작 시 초기화)

        self.player_has_bomb = False # 게임 시작 시 폭탄 아이템 초기화

        if self.bgm_loaded: 
            pygame.mixer.music.load(os.path.join(IMAGE_FOLDER, 'bgm.ogg'))
            pygame.mixer.music.play(loops=-1)
        self.run()

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events() # 이벤트 처리
            if not self.paused: # 일시정지 상태가 아닐 때만 업데이트
                self.update()
            self.draw() # 화면 그리기
        if self.bgm_loaded: pygame.mixer.music.fadeout(500) # 게임 오버 시 BGM 페이드아웃
    
    def player_hit(self):
        if not self.player.hidden: # 플레이어가 숨겨진(무적) 상태가 아닐 때만
            self.player_hit_sound.play()
            if self.player.shield > 0: # 쉴드가 있다면 쉴드 먼저 감소
                self.player.shield -= 1
                self.player.show_pop_up("쉴드 파괴!")
            else: # 쉴드가 없다면 생명 감소
                self.player.lives -= 1
                self.player.show_pop_up("피격!")
            if self.player.lives <= 0: # 생명이 0 이하면 게임 오버
                self.playing = False
            else: # 생명이 남아있으면 잠시 무적 상태로 숨김
                self.player.hide()

    def activate_bomb(self):
        self.bomb_sound.play() # 폭탄 사운드
        self.player.show_pop_up("폭탄 사용!")
        for mob in self.mobs: # 모든 몹 제거
            self.all_sprites.add(Explosion(self, mob.rect.center, 'sm'))
            random.choice(self.expl_sounds).play()
            self.score += 50
            mob.kill()
        for bullet in self.mob_bullets: bullet.kill() # 모든 적 총알 제거

    def update(self):
        self.all_sprites.update()
        
        # 몹 스폰 로직 (수정됨: 보스가 활성화되지 않았고, 특정 점수(예: 2000점)에 도달하지 않았으면 일반 몹 스폰)
        now = pygame.time.get_ticks()
        if not self.boss_spawned and self.score < 2000 and now - self.last_mob_spawn_time > self.mob_spawn_delay and len(self.mobs) < self.max_mobs:
            self.last_mob_spawn_time = now
            self.spawn_mob()

        # 보스 스폰 조건 (수정됨: 특정 점수 도달 시 보스 스폰)
        if self.score >= 2000 and not self.boss_spawned: # 2000점 도달 시 보스 스폰
            self.spawn_boss()
            self.boss_spawned = True # 보스 스폰 플래그 설정
            for mob in self.mobs: mob.kill() # 보스 등장 시 기존 몹 제거 (화면 정리)

        # 플레이어 총알과 몹 충돌 (보스와 일반 몹 모두) (수정됨: 보스 체력 처리 추가)
        hits = pygame.sprite.groupcollide(self.mobs, self.bullets, False, True) # 몹 제거는 체력 감소 후 결정
        for mob_hit in hits:
            if mob_hit == self.boss: # 충돌한 것이 보스라면
                self.boss.hp -= 10 # 보스 체력 감소 (총알 피해)
                if self.player_has_bomb: # 플레이어가 폭탄 아이템을 가지고 있으면 더 큰 피해
                    self.boss.hp -= 30 # 폭탄 총알 효과 (기본 총알보다 강함)
                if self.boss.hp <= 0: # 보스 사망
                    self.all_sprites.add(Explosion(self, self.boss.rect.center, 'lg')) # 큰 폭발
                    if random.choice(self.expl_sounds): random.choice(self.expl_sounds).play()
                    self.score += 1000 # 보스 처치 점수
                    self.boss.kill() # 보스 제거
                    self.boss = None
                    self.boss_spawned = False # 다음 게임을 위해 리셋
                    self.player.show_pop_up("보스 처치!")
                    # 보스가 죽으면 화면의 모든 적 총알 제거
                    for bullet in self.mob_bullets: bullet.kill()
                else:
                    if self.game_hit_sound: self.game_hit_sound.play() # 보스 피격 사운드 (선택 사항)
            else: # 일반 몹 사망 처리
                mob_hit.kill() # 일반 몹은 바로 제거
                if random.choice(self.expl_sounds): random.choice(self.expl_sounds).play()
                self.all_sprites.add(Explosion(self, mob_hit.rect.center, 'sm'))
                self.score += 50
                if random.random() > 0.9: 
                    powerup = Powerup(self, mob_hit.rect.center)
                    self.all_sprites.add(powerup)
                    self.powerups.add(powerup)
                if not self.boss: self.spawn_mob() # 보스가 살아있지 않을 때만 일반 몹 스폰


        # 몹 총알과 플레이어 충돌 (수정됨: mob_bullets 그룹 활성화 및 보스 총알 처리)
        # 보스 총알과 일반 몹 총알이 모두 이 그룹에 들어갑니다.
        hits = pygame.sprite.spritecollide(self.player, self.mob_bullets, True, pygame.sprite.collide_circle)
        if hits: self.player_hit()

        # 몹과 플레이어 충돌 (수정됨: 보스 포함)
        hits = pygame.sprite.spritecollide(self.player, self.mobs, False, pygame.sprite.collide_circle) # 몹 제거는 체력 감소 후 결정
        for mob_hit in hits:
            if mob_hit == self.boss: # 보스와 충돌
                self.player_hit()
                # 보스는 플레이어와 충돌해도 사라지지 않고 체력만 깎이도록 (선택 사항)
                self.boss.hp -= 20 # 플레이어와 충돌 시 보스 체력 감소
                if self.boss.hp <= 0:
                    self.all_sprites.add(Explosion(self, self.boss.rect.center, 'lg'))
                    if random.choice(self.expl_sounds): random.choice(self.expl_sounds).play()
                    self.score += 1000
                    self.boss.kill()
                    self.boss = None
                    self.boss_spawned = False
                    self.player.show_pop_up("보스 처치!")
                    for bullet in self.mob_bullets: bullet.kill()
                else:
                    if self.game_hit_sound: self.game_hit_sound.play()
            else: # 일반 몹과 충돌
                mob_hit.kill() # 일반 몹은 바로 제거
                self.all_sprites.add(Explosion(self, mob_hit.rect.center, 'sm'))
                if random.choice(self.expl_sounds): random.choice(self.expl_sounds).play()
                self.player_hit()
                if not self.boss: self.spawn_mob()

        # 파워업 아이템과 플레이어 충돌
        hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup_item in hits: # powerup_item은 충돌한 Powerup 객체
            self.player.powerup(powerup_item.type)

        if self.score > self.highscore: self.highscore = self.score

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing, self.running = False, False
            if event.type == pygame.KEYUP and event.key == pygame.K_p:
                self.paused = not self.paused
                if self.paused:
                    if pygame.mixer.music.get_busy(): pygame.mixer.music.pause()
                    self.show_pause_menu() # 일시정지 메뉴 표시
                else:
                    pygame.mixer.music.unpause()
            
            # 마우스 이벤트 처리 - 시작 화면, 게임 오버 화면, 퍼즈 메뉴, 게임 방법, 크레딧 화면
            mouse_pos = pygame.mouse.get_pos()
            
            # 시작 화면 버튼의 색상 업데이트 (게임이 실행 중이 아닐 때)
            if hasattr(self, 'start_buttons') and not self.playing:
                for button in self.start_buttons: button.update_color(mouse_pos)
                if hasattr(self, 'credits_button'): self.credits_button.update_color(mouse_pos)
            
            # 게임 오버 화면 버튼의 색상 업데이트 (게임이 실행 중이 아니고, 플레이어 생명이 없을 때)
            if hasattr(self, 'go_buttons') and not self.playing and self.player and not self.player.lives > 0:
                for button in self.go_buttons: button.update_color(mouse_pos)
            
            # 일시정지 메뉴 버튼의 색상 업데이트 (일시정지 상태일 때)
            if self.paused and hasattr(self, 'pause_buttons'):
                for button in self.pause_buttons: button.update_color(mouse_pos)
            
            # 게임 방법 화면 버튼의 색상 업데이트
            if hasattr(self, '_how_to_play_active') and self._how_to_play_active and hasattr(self, 'how_to_play_buttons'):
                for button in self.how_to_play_buttons: button.update_color(mouse_pos)
            
            # 크레딧 화면 버튼의 색상 업데이트
            if hasattr(self, '_credits_active') and self._credits_active and hasattr(self, 'credits_buttons'):
                for button in self.credits_buttons: button.update_color(mouse_pos)


            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 시작 화면 버튼 클릭
                if hasattr(self, 'start_buttons') and not self.playing:
                    for button in self.start_buttons:
                        if button.handle_event(event, button.callback): break
                    if hasattr(self, 'credits_button') and self.credits_button.handle_event(event, self.credits_button.callback):
                        pass
                # 게임 오버 화면 버튼 클릭
                if hasattr(self, 'go_buttons') and not self.playing and self.player and not self.player.lives > 0:
                    for button in self.go_buttons:
                        if button.handle_event(event, button.callback): break
                # 일시정지 메뉴 버튼 클릭
                if self.paused and hasattr(self, 'pause_buttons'):
                    for button in self.pause_buttons:
                        if button.handle_event(event, button.callback): break
                # 게임 방법 화면 버튼 클릭
                if hasattr(self, '_how_to_play_active') and self._how_to_play_active and hasattr(self, 'how_to_play_buttons'):
                    for button in self.how_to_play_buttons:
                        if button.handle_event(event, button.callback): break
                # 크레딧 화면 버튼 클릭
                if hasattr(self, '_credits_active') and self._credits_active and hasattr(self, 'credits_buttons'):
                    for button in self.credits_buttons:
                        if button.handle_event(event, button.callback): break


    def draw(self):
        # 배경 그리기
        self.background.update_and_draw(self.screen)
        self.all_sprites.draw(self.screen)
        self.player.draw_magnet_aura(self.screen) # 자석 아우라 그리기
        # 보스 체력 바 그리기 (수정됨)
        if self.boss and self.boss.is_active: # 보스가 존재하고 활성화 상태일 때만 그립니다.
            self.draw_boss_hp_bar(self.screen, self.boss)

        # UI 텍스트 그리기 (수정됨: 우측 정렬 및 X좌표 조정)
        self.draw_text(self.screen, f"생명: {self.player.lives}", 24, 60, 10, WHITE, align="topleft")
        self.draw_text(self.screen, f"점수: {self.score}", 24, SCREEN_WIDTH / 2, 10, WHITE, shadow=True)
        self.draw_text(self.screen, f"최고 점수: {self.highscore}", 24, SCREEN_WIDTH / 2, 40, WHITE, shadow=True)

        ui_right_margin = SCREEN_WIDTH - 20 # 화면 오른쪽 끝에서 20픽셀 안쪽
        self.draw_text(self.screen, f"쉴드: {self.player.shield}", 24, ui_right_margin, 10, WHITE, align="topright")
        self.draw_text(self.screen, f"총알: {self.player.power}", 24, ui_right_margin, 40, WHITE, align="topright")
        if self.player_has_bomb: # 폭탄 아이템 보유 시 UI 표시
            self.draw_text(self.screen, "폭탄 보유 (Space)", 24, ui_right_margin, 70, ORANGE, align="topright", shadow=True)

        if self.player.pop_up_message: # 팝업 메시지 표시
            self.draw_text(self.screen, self.player.pop_up_message, 30, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50, CYAN, align="center", shadow=True)

        pygame.display.flip() # 화면 업데이트
    
    def spawn_mob(self):
        self.all_sprites.add(Mob(self)) # Mob 객체 생성 시 game 인스턴스 전달
        self.mobs.add(self.all_sprites.sprites()[-1])

    def spawn_bullet(self, x, y, color, angle_offset=0):
        self.all_sprites.add(Bullet(x,y,color,angle_offset))
        self.bullets.add(self.all_sprites.sprites()[-1])
    
    # Game 클래스 내부에 추가 (기존 주석 처리된 부분 교체)
    def spawn_mob_bullet(self, x, y, target=None, speed=6):
        bullet = MobBullet(self, x, y, target, speed) # MobBullet 생성 시 game 인스턴스 전달
        self.all_sprites.add(bullet)
        self.mob_bullets.add(bullet)

    # Game 클래스 내부에 추가 (보스 스폰 함수)
    def spawn_boss(self):
        self.boss = Boss(self) # 보스 객체 생성
        self.all_sprites.add(self.boss)
        self.mobs.add(self.boss) # 보스도 몹 그룹에 넣어 충돌 감지에 활용
        self.boss_group.add(self.boss) # 보스 전용 그룹에도 추가 (선택 사항)
        # BGM 변경 또는 보스 등장 효과음 재생 등 추가할 수 있습니다.
        self.player.show_pop_up("보스 등장!")

    def show_start_screen(self):
        self.background = Background(self) # 배경 업데이트를 위해 Background 인스턴스 사용

        if self.menu_bgm_loaded: 
            try: pygame.mixer.music.load(os.path.join(IMAGE_FOLDER, 'menu_bgm.ogg'))
            except: pass
            pygame.mixer.music.play(loops=-1)

        # --- 버튼들을 while 루프 밖에서 미리 생성합니다. ---
        button_width, button_height = 220, 60
        button_font = pygame.font.Font(self.font_name, 32)
        
        start_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT * 0.60, button_width, button_height, "새로운 게임", button_font, BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        how_to_play_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT * 0.72, button_width, button_height, "게임 방법", button_font, BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        exit_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT * 0.84, button_width, button_height, "게임 종료", button_font, BUTTON_NORMAL, BUTTON_HOVER, WHITE)

        self.start_buttons = [start_button, how_to_play_button, exit_button]
        start_button.callback = lambda: setattr(self, 'playing', True)
        how_to_play_button.callback = self.show_how_to_play_screen
        exit_button.callback = lambda: setattr(self, 'running', False)

        # 크레딧 버튼도 이 시점에 생성합니다.
        credits_button_size = (100, 30)
        self.credits_button = Button(SCREEN_WIDTH - credits_button_size[0] - 10, SCREEN_HEIGHT - credits_button_size[1] - 10, credits_button_size[0], credits_button_size[1], "Credits", pygame.font.Font(self.font_name, 18), (80,80,80), (120,120,120), WHITE, border_radius=5)
        self.credits_button.callback = self.show_credits_screen # 크레딧 화면 표시 함수 연결
        # ----------------------------------------------------------------------------------

        waiting = True
        while waiting:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: waiting, self.running = False, False
                if event.type == pygame.MOUSEMOTION:
                    for btn in self.start_buttons: btn.update_color(mouse_pos)
                    self.credits_button.update_color(mouse_pos) 
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    is_button_clicked = False
                    for btn in self.start_buttons:
                        if btn.handle_event(event, btn.callback):
                            if btn == start_button: # "새로운 게임" 버튼
                                if self.bgm_loaded: pygame.mixer.music.fadeout(500)
                                waiting = False
                            elif btn == exit_button: # "게임 종료" 버튼
                                waiting = False
                                self.running = False
                            is_button_clicked = True
                            break
                    if not is_button_clicked and self.credits_button.handle_event(event, self.credits_button.callback):
                        pass
            
            self.background.update_and_draw(self.screen) # 별/구름 배경 그리기
            
            # 메인 제목
            self.draw_text(self.screen, "FLY DRAGON", 72, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 - 50, YELLOW, shadow=True) # 제목을 더 위로
            self.draw_text(self.screen, "우주로 날아오른 용의 전설", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 + 20, WHITE, shadow=True) # 소제목 위치 조정
            self.draw_text(self.screen, f"최고 점수: {self.highscore}", 24, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20, WHITE)

            # 미리 생성된 버튼들을 그리기만 합니다.
            for btn in self.start_buttons: btn.draw(self.screen)
            self.credits_button.draw(self.screen) # 크레딧 버튼 그리기
            
            pygame.display.flip()

    def show_go_screen(self):
        if not self.running: return # 게임이 이미 종료 중이면 실행하지 않음

        if self.score > self.highscore:
            self.highscore = self.score
            with open(HIGHSCORE_FILE, 'w') as f: f.write(str(self.highscore))

        # 배경을 다시 그리기
        self.background.update_and_draw(self.screen)
        
        # 반투명 오버레이
        go_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        go_overlay.fill(DARK_GREY)
        self.screen.blit(go_overlay, (0,0))

        self.draw_text(self.screen, "게임 오버", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED, shadow=True)
        self.draw_text(self.screen, f"점수: {self.score}", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE)
        self.draw_text(self.screen, f"최고 점수: {self.highscore}", 24, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 - 30, WHITE)
        
        button_width, button_height = 180, 50
        restart_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT * 0.75, button_width, button_height, "재시작", pygame.font.Font(self.font_name, 30), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        main_menu_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT * 0.85, button_width, button_height, "메인 메뉴", pygame.font.Font(self.font_name, 30), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        
        self.go_buttons = [restart_button, main_menu_button]
        restart_button.callback = lambda: setattr(self, 'playing', True) # 재시작 콜백
        main_menu_button.callback = self.show_start_screen # 메인 메뉴 콜백

        if self.menu_bgm_loaded: 
            try: pygame.mixer.music.load(os.path.join(IMAGE_FOLDER, 'menu_bgm.ogg'))
            except: pass
            pygame.mixer.music.play(loops=-1)

        waiting = True
        while waiting:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: waiting, self.running = False, False
                if event.type == pygame.KEYUP and event.key == pygame.K_SPACE: # 스페이스바 재시작
                    if self.bgm_loaded: pygame.mixer.music.fadeout(500)
                    waiting = False
                if event.type == pygame.MOUSEMOTION:
                    for btn in self.go_buttons: btn.update_color(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.go_buttons:
                        if btn.handle_event(event, btn.callback):
                            if btn == restart_button: # 재시작
                                if self.bgm_loaded: pygame.mixer.music.fadeout(500)
                            elif btn == main_menu_button: # 메인 메뉴로
                                pass # show_start_screen에서 음악 처리
                            waiting = False
                            break
            
            # 여기서 배경과 오버레이를 다시 그려야 버튼 위에 다른 UI가 겹치지 않음
            self.background.update_and_draw(self.screen)
            self.screen.blit(go_overlay, (0,0))
            self.draw_text(self.screen, "게임 오버", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED, shadow=True)
            self.draw_text(self.screen, f"점수: {self.score}", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE)
            self.draw_text(self.screen, f"최고 점수: {self.highscore}", 24, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 - 30, WHITE)

            for btn in self.go_buttons: btn.draw(self.screen)
            pygame.display.flip()

    def show_pause_menu(self):
        self._paused_flag = True
        
        pause_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pause_overlay.fill(DARK_GREY) # 반투명 회색 오버레이

        button_width, button_height = 200, 60
        resume_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT / 2 - 100, button_width, button_height, "계속하기", pygame.font.Font(self.font_name, 35), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        restart_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT / 2, button_width, button_height, "재시작", pygame.font.Font(self.font_name, 35), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        main_menu_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT / 2 + 100, button_width, button_height, "메인 메뉴", pygame.font.Font(self.font_name, 35), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        
        self.pause_buttons = [resume_button, restart_button, main_menu_button]

        # 콜백 함수 정의
        def resume_game(): self.paused, self._paused_flag = False, False
        def restart_game(): 
            self.paused, self.playing, self._paused_flag = False, False, False 
            if self.bgm_loaded: pygame.mixer.music.fadeout(500)
        def go_to_main_menu(): 
            self.paused, self.playing, self.running, self._paused_flag = False, False, False, False 
            if self.bgm_loaded: pygame.mixer.music.fadeout(500)

        resume_button.callback = resume_game
        restart_button.callback = restart_game
        main_menu_button.callback = go_to_main_menu

        while self._paused_flag and self.paused:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running, self.playing, self._paused_flag = False, False, False
                if event.type == pygame.KEYUP and event.key == pygame.K_p: # P키로 일시정지 해제
                    resume_game()
                    break
                if event.type == pygame.MOUSEMOTION:
                    for btn in self.pause_buttons: btn.update_color(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.pause_buttons:
                        if btn.handle_event(event, btn.callback):
                            break
            
            self.draw() # 기존 게임 화면 그리기
            self.screen.blit(pause_overlay, (0, 0)) # 반투명 오버레이 덮기
            self.draw_text(self.screen, "PAUSED", 72, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 200, WHITE, shadow=True)
            for btn in self.pause_buttons: btn.draw(self.screen)
            pygame.display.flip()
        
        if not self.paused and self.bgm_loaded:
             pygame.mixer.music.unpause()


    def show_how_to_play_screen(self):
        self._how_to_play_active = True # 상태 플래그
        
        button_width, button_height = 150, 50
        back_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT - 70, button_width, button_height, "뒤로 가기", pygame.font.Font(self.font_name, 25), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        self.how_to_play_buttons = [back_button]
        back_button.callback = lambda: setattr(self, '_how_to_play_active', False)
        
        while self._how_to_play_active:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running, self._how_to_play_active = False, False
                if event.type == pygame.MOUSEMOTION:
                    for btn in self.how_to_play_buttons: btn.update_color(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.how_to_play_buttons:
                        if btn.handle_event(event, btn.callback): break
            
            self.screen.fill(BLACK)
            self.draw_text(self.screen, "게임 방법", 60, SCREEN_WIDTH / 2, 40, WHITE, shadow=True)

            text_start_x_left = 50 # 왼쪽 섹션 시작 X 좌표
            text_start_x_right = SCREEN_WIDTH * 0.5 + 50 # 오른쪽 섹션 시작 X 좌표
    

            # 조작법 (왼쪽 정렬)
            self.draw_text(self.screen, "--- 조작법 ---", 32, text_start_x_left, 120, YELLOW, align="topleft", shadow=True)
            self.draw_text(self.screen, "이동: ← → ↑ ↓ (방향키)", 25, text_start_x_left, 170, WHITE, align="topleft")
            self.draw_text(self.screen, "총알 발사: 자동", 25, text_start_x_left, 200, WHITE, align="topleft")
            self.draw_text(self.screen, "일시정지: P", 25, text_start_x_left, 230, WHITE, align="topleft")
            self.draw_text(self.screen, "폭탄 사용: Space Bar (아이템 획득 시)", 25, text_start_x_left, 260, WHITE, align="topleft")


            # 아이템 설명 (오른쪽 정렬)
            self.draw_text(self.screen, "--- 아이템 ---", 32, text_start_x_right, 120, YELLOW, align="topleft", shadow=True)

            item_y_start = 170
            item_line_height = 40 # 간격 좀 더 넓게
            item_icon_size = (30, 30) # 아이콘 크기 통일

            items_info = [
                ('shield', "쉴드: 피격 방어 (최대 3회)", GREEN),
                ('gun', "총알 강화: 총알 파워 증가 (최대 3단계)", BLUE),
                ('speed', "속도 증가: 플레이어 이동 속도 증가", CYAN),
                ('hp', "HP: 생명 1 증가 (최대 5)", RED),
                ('bomb', "폭탄: 모든 적, 총알 제거 (보스에게 큰 피해)", ORANGE),
                ('magnet', "자석: 주변 아이템 자동 획득", PURPLE)
            ]
            
            # 아이템 설명 그리기
            for item_type, desc, text_color in items_info:
                # Powerup 클래스의 generate_fallback_image 메서드를 사용하여 이미지 생성
                temp_powerup = Powerup(self, (0,0)) # game 인스턴스 전달 (임시용)
                temp_powerup.type = item_type 
                icon_image = temp_powerup.generate_fallback_image(item_icon_size)
                
                # 단, 제공된 이미지가 있을 경우 해당 이미지를 사용하도록 다시 로직 추가
                if item_type == 'bomb' and self.bomb_img.get_width() > 0: icon_image = self.bomb_img
                elif item_type == 'magnet' and self.magnet_img.get_width() > 0: icon_image = self.magnet_img
                elif item_type == 'shield' and self.shield_img.get_width() > 0: icon_image = self.shield_img
                elif item_type == 'gun' and self.twin_shot_img.get_width() > 0: icon_image = self.twin_shot_img
                elif item_type == 'speed' and self.speed_img.get_width() > 0: icon_image = self.speed_img
                elif item_type == 'hp' and self.hp_img.get_width() > 0: icon_image = self.hp_img

                icon_rect = icon_image.get_rect(midleft=(text_start_x_right, item_y_start + item_line_height / 2)) # X 위치 조정
                self.screen.blit(icon_image, icon_rect)
                self.draw_text(self.screen, desc, 20, text_start_x_right + item_icon_size[0] + 10, item_y_start + 5, text_color, align="topleft") # 텍스트 X 위치 조정
                item_y_start += item_line_height


            for btn in self.how_to_play_buttons: btn.draw(self.screen)
            pygame.display.flip()

    def show_credits_screen(self):
        self._credits_active = True
        
        button_width, button_height = 150, 50
        back_button = Button(SCREEN_WIDTH / 2 - button_width / 2, SCREEN_HEIGHT - 70, button_width, button_height, "뒤로 가기", pygame.font.Font(self.font_name, 25), BUTTON_NORMAL, BUTTON_HOVER, WHITE)
        self.credits_buttons = [back_button] # 이 화면 전용 버튼 리스트
        back_button.callback = lambda: setattr(self, '_credits_active', False)
        
        while self._credits_active:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running, self._credits_active = False, False
                if event.type == pygame.MOUSEMOTION:
                    for btn in self.credits_buttons: btn.update_color(mouse_pos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for btn in self.credits_buttons:
                        if btn.handle_event(event, btn.callback): break
            
            self.screen.fill(BLACK)
            self.draw_text(self.screen, "Credits", 60, SCREEN_WIDTH / 2, 80, WHITE, shadow=True)

            # 크레딧 내용
            credit_y = 200
            line_height = 35
            self.draw_text(self.screen, "개발:", 30, SCREEN_WIDTH / 2, credit_y, YELLOW, shadow=True)
            self.draw_text(self.screen, "김민철", 25, SCREEN_WIDTH / 2, credit_y + line_height, WHITE)
            
            credit_y += line_height * 2
            self.draw_text(self.screen, "코드 및 이미지 생성 도움:", 30, SCREEN_WIDTH / 2, credit_y, YELLOW, shadow=True)
            self.draw_text(self.screen, "ChatGPT (Python Code)", 25, SCREEN_WIDTH / 2, credit_y + line_height, WHITE)
            self.draw_text(self.screen, "DALL-E (Image Generation)", 25, SCREEN_WIDTH / 2, credit_y + line_height * 2, WHITE)

            credit_y += line_height * 3.5
            self.draw_text(self.screen, "음악 및 효과음:", 30, SCREEN_WIDTH / 2, credit_y, YELLOW, shadow=True)
            self.draw_text(self.screen, "OpenGameArt.org (비상업적 용도)", 25, SCREEN_WIDTH / 2, credit_y + line_height, WHITE)

            for btn in self.credits_buttons: btn.draw(self.screen)
            pygame.display.flip()
    # Game 클래스 내부에 추가 (보스 체력 바 그리는 유틸리티 함수)
    def draw_boss_hp_bar(self, surf, boss):
        if boss.hp < 0: boss.hp = 0 # 체력이 0보다 낮아지지 않도록
        bar_length = 150
        bar_height = 15
        fill = (boss.hp / boss.max_hp) * bar_length
        outline_rect = pygame.Rect(boss.rect.centerx - bar_length // 2, boss.rect.top - 20, bar_length, bar_height)
        fill_rect = pygame.Rect(boss.rect.centerx - bar_length // 2, boss.rect.top - 20, fill, bar_height)
        pygame.draw.rect(surf, RED, fill_rect)
        pygame.draw.rect(surf, WHITE, outline_rect, 2)
        self.draw_text(surf, f"BOSS HP: {boss.hp}", 18, boss.rect.centerx, boss.rect.top - 28, WHITE, shadow=True)
        
# --- 게임 실행 ---
g = Game()
g.show_start_screen()
while g.running:
    g.new() # 게임 시작 (new() 안에서 run()을 호출)
    if not g.playing and g.running: # 게임 오버 후 메인 메뉴로 돌아가지 않고 실행 중일 때만
        g.show_go_screen()
        
pygame.quit(); sys.exit()