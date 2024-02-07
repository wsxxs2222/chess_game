import pygame
WIDTH = HEIGHT = 512 # 400 is another option
SIDEBAR_WIDTH = 256
DIMENSION = 8 # dimension of a chess board
SQ_SIZE = HEIGHT // DIMENSION


class Game_display:
    def __init__(self) -> None:
        # create main screen, board screen, menu screen
        self.main_screen = pygame.display.set_mode((WIDTH + SIDEBAR_WIDTH, HEIGHT))
        self.board_screen = pygame.surface.Surface((WIDTH, HEIGHT))
        self.menu_screen = pygame.surface.Surface((SIDEBAR_WIDTH, HEIGHT))
        # dictionary to store images
        self.images = {}
        self.load_images()
        pass
    
    def load_images(self):
        pieces = ['wP','wR','wN','wB','wK','wQ','bP','bR','bN','bB','bK','bQ']
        for piece in pieces:
            self.images[piece] = pygame.transform.scale(pygame.image.load("./pictures/" + piece + ".png"), (SQ_SIZE,SQ_SIZE))
            self.images['selected'] = pygame.transform.scale(pygame.image.load("./pictures/selected.png"), (SQ_SIZE, SQ_SIZE))
        # Note we can access an img by saying 'IMAGES['wP']'
    
    def draw_interface(self, user_info):
        # draw board and menu on main screen
        self.draw_game_state(user_info)
        self.draw_menu()
        self.main_screen.blit(self.board_screen, (0, 0))
        self.main_screen.blit(self.menu_screen, (512, 0))
    
    # def draw_game_state(gs, valid_moves, select_square, persp):
    def draw_game_state(self, user_info):
        # draw squares on the board
        self.draw_board()
        self.draw_pieces(user_info.game_state)
        if user_info.if_selected:
            self.draw_highlight(user_info.valid_moves, user_info.square_selected)
            self.draw_selected(user_info.square_selected)
        
        # draw_highlight(screen, gs, valid_moves, select_square)
        # add in move highlights or move suggestions
        # draw_pieces(screen, gs, persp)  # draw pieces on those squares
        
    def draw_menu(self):
        self.menu_screen.fill(pygame.Color((234, 221, 202, 50)))
        
    
    def draw_board(self):
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                if (r+c)%2 == 0:
                    color = pygame.Color("white")
                else:
                    color = pygame.Color("gray")
                pygame.draw.rect(self.board_screen, color, pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                
    def draw_pieces(self, gs):
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                piece = gs.board[r][c]
                if piece != "--":  # if not empty square
                    self.board_screen.blit(self.images[piece], pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        # implement fog of war see reference code
    
    def draw_highlight(self, valid_moves, square_selected):
        # create a new surface for the highlight square
        s = pygame.Surface((SQ_SIZE, SQ_SIZE))
        # set the opacity
        s.set_alpha(100)
        # set color
        s.fill(pygame.Color("blue"))
        row, col = square_selected
        # blit the square at the right position on the screen
        self.board_screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
        # change color to highlight possible squares
        s.fill(pygame.Color("yellow"))
        # if highlight all the valid moves involving this piece
        for move in valid_moves:
            if (move.sRow == row) and (move.sCol == col):
                self.board_screen.blit(s, (SQ_SIZE * move.eCol, SQ_SIZE * move.eRow))
                
    def draw_selected(self, sqare_selected):
        self.board_screen.blit(self.images['selected'], (sqare_selected[1] * SQ_SIZE, sqare_selected[0] * SQ_SIZE))