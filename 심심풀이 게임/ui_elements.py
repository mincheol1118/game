import pygame
from settings import * # settings.py에서 정의된 색상 상수를 사용합니다.

# --- UI 버튼 클래스 (디자인 개선) ---
class Button:
    def __init__(self, x, y, width, height, text, font, normal_color, hover_color, text_color, border_radius=12, shadow_offset=4):
        self.rect = pygame.Rect(x, y, width, height)
        self.text, self.font = text, font
        self.normal_color, self.hover_color, self.text_color = normal_color, hover_color, text_color
        self.current_color = normal_color
        self.border_radius = border_radius
        self.shadow_offset = shadow_offset
        self.shadow_color = (30, 30, 30, 150) # 버튼 그림자 색상 (투명도 추가)

    def draw(self, surf):
        # 버튼 본체 그리기
        pygame.draw.rect(surf, self.current_color, self.rect, border_radius=self.border_radius)
        
        # 텍스트 그림자
        text_surf = self.font.render(self.text, True, SHADOW) # settings.py의 SHADOW 사용
        text_rect = text_surf.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2))
        surf.blit(text_surf, text_rect)
        
        # 텍스트
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surf.blit(text_surf, text_rect)

    def is_hovered(self, mouse_pos): return self.rect.collidepoint(mouse_pos)
    def update_color(self, mouse_pos): self.current_color = self.hover_color if self.is_hovered(mouse_pos) else self.normal_color
    def handle_event(self, event, callback):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered(event.pos):
            callback(); return True
        return False