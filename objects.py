import pygame


class Cell:
    def __init__(self, rect, color, text):
        self.rect:pygame.Rect = rect
        self.color = color
        self.text = text

        self.mine = False
        self.opened = False
        self.flagged = False

class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image:pygame.image = image
        self.rect = image.get_rect()
        self.rect.x = x
        self.rect.y = y