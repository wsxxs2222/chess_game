import pygame
class Button:
    def __init__(self, left, top, width, height, text, size) -> None:
        self.rect = pygame.Rect(left, top, width, height)
        self.font = pygame.font.SysFont("Helvitca", size, False, False)
        self.text_object = self.font.render(text, False, pygame.Color(255, 255, 255, 255))
        self.text_location = pygame.Rect(left + int((width-self.text_object.get_width())/2), top + int((height-self.text_object.get_height())/2), self.text_object.get_width(), self.text_object.get_height())
        self.clicked = False
        pass
    
    def draw(self, screen):
        pygame.draw.rect(screen, pygame.Color(51, 204, 51, 255), self.rect)
        screen.blit(self.text_object, self.text_location)
        event = False
        pos = pygame.mouse.get_pos()
        pos1 = (pos[0]-512, pos[1])
        # check if mouse is hovering over button
        if self.rect.collidepoint(pos1):
            # check if mouse button is down for the first time after last button up
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                # trigger event
                event = True
                self.clicked = True
            if pygame.mouse.get_pressed()[0] == 0 and self.clicked:
                self.clicked = False
        return event
    