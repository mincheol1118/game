import pygame
import random
from settings import * # settings.py의 상수들을 사용합니다.

class Background:
    def __init__(self, game): # game 인자 추가
        self.game = game
        # game.load_data에서 로드된 이미지들을 참조
        self.cloud_images = [self.game.cloud_img1, self.game.cloud_img2, self.game.cloud_img3] 
        
        # 실제 로드된 구름 이미지가 있는지 확인 (어떤 이미지든 폭이 0보다 크면 유효하다고 판단)
        if any(img.get_width() > 0 for img in self.cloud_images):
            self.use_clouds = True
            self.clouds = []
            for _ in range(10): self.spawn_cloud()
        else: # 구름 이미지가 없으면 별 배경 사용
            print("Warning: Cloud images not found. Using starfield background.")
            self.use_clouds = False
            self.stars = [[random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.1, 5)] for _ in range(200)]

    def spawn_cloud(self):
        if self.use_clouds:
            # 실제로 유효한 구름 이미지만 선택
            valid_clouds = [c for c in self.cloud_images if c.get_width() > 0]
            if valid_clouds:
                img = random.choice(valid_clouds)
                # 구름 이미지의 크기는 이미 로드 시 결정되었으므로 그대로 사용
                self.clouds.append({'image': img, 'rect': img.get_rect(topleft=(random.randrange(-img.get_width(), SCREEN_WIDTH), random.randrange(-img.get_height()*2, -img.get_height()//2))), 'speed': random.randrange(1, 3)})

    def update_and_draw(self, surf):
        surf.fill(BLACK) # 배경색을 블랙으로 변경하여 별이 잘 보이도록

        if self.use_clouds:
            for cloud in self.clouds[:]: # 리스트를 순회하면서 수정할 때는 슬라이싱 사용
                cloud['rect'].y += cloud['speed']
                surf.blit(cloud['image'], cloud['rect'])
                if cloud['rect'].top > SCREEN_HEIGHT:
                    self.clouds.remove(cloud)
                    self.spawn_cloud()
        else:
            # Starfield fallback (별 배경)
            center_x, center_y = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
            for star in self.stars:
                star[2] -= 0.03 # 별이 플레이어에게 다가오는 듯한 효과 (깊이 값 감소)
                if star[2] <= 0: # 별이 화면을 벗어나면 다시 맨 뒤에서 생성
                    star[0], star[1], star[2] = random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(4, 5)
                
                # 원근감 계산
                k = 128.0 / star[2]
                screen_x, screen_y = star[0] * k + center_x, star[1] * k + center_y
                
                # 별의 크기와 밝기 조절
                size = (5 - star[2]) * 0.8
                shade = int((5 - star[2]) * 50)
                
                if 0 < shade < 255 and 0 < screen_x < SCREEN_WIDTH and 0 < screen_y < SCREEN_HEIGHT:
                    pygame.draw.rect(surf, (shade, shade, shade), (screen_x, screen_y, size, size))