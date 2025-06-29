import pygame


class Cell:
    def __init__(self, rect, color, text):
        self.rect:pygame.Rect = rect
        self.color = color
        self.text = text

        self.mine = False
        self.opened = False
        self.flagged = False