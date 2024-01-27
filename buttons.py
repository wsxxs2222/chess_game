import pygame
class Button:
    def __init__(self, left, top, width, height, text) -> None:
        self.rect = pygame.Rect(left, top, width, height)
        self.font = pygame.font.SysFont("Helvitca", 48, True, False)
        self.text_object = self.font.render(text, False, pygame.Color("black"))
        self.text_location = pygame.Rect(64+int((width-self.text_object.get_width())/2), 50+int((height-self.text_object.get_height())/2), self.text_object.get_width(), self.text_object.get_height())
        self.clicked = False
        pass
    
    def draw(self, screen):
        pygame.draw.rect(screen, "green", self.rect)
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
    