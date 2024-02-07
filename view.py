import pygame
WIDTH = HEIGHT = 512 # 400 is another option
SIDEBAR_WIDTH = 256
DIMENSION = 8 # dimension of a chess board
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15


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
        # display promotion box
        if user_info.promotion:
            self.display_promotion_box(user_info.game_state.whiteToMove)
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
        self.display_game_result(user_info.game_state)
        
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
    
    def display_promotion_box(self, whiteToMove):
        if whiteToMove:
            turn = "w"
        else:
            turn = "b"
        # set parameters
        w_margin = 4
        h_margin = 10
        w = 5*w_margin+w_margin*64
        h = 64+2*h_margin
        tlc = (WIDTH/2 - w/2, HEIGHT/2 - h/2)
        # draw a rect in the middle as the choice box
        box = pygame.Rect(WIDTH/2 - w/2, HEIGHT/2 - h/2, w, h)
        pygame.draw.rect(self.board_screen, "gray", box)
        # blit pieces choice in the box
        pieces_list = ["N", "B", "R", "Q"]
        left_corners = []
        right_corners = []
        top_height = tlc[1] + h_margin
        bot_height = tlc[1] + 2 * h_margin + 64
        for i in range(4):
            pieces_list[i] = turn + pieces_list[i]
            left_corners.append(tlc[0]+(1+i)*w_margin)
            right_corners.append(tlc[0]+(1+i)*w_margin+(i+1)*64)
        for i in range(4):
            self.board_screen.blit(self.images[pieces_list[i]], (tlc[0] + (1 + i) * w_margin + i * 64, tlc[1] + h_margin))
        # clock.tick(MAX_FPS)
        # pygame.display.flip()
        # get events until a mouse click is on a piece
    
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
        
    def draw_text(self, text):
        # select font
        font = pygame.font.SysFont("Helvitca", 32, True, False)
        # select the words for text and color using the font
        text_object = font.render(text, False, pygame.Color("gray"))
        # center the text requires moving from top left corner to the tlc of the mid-point
        text_location = pygame.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - text_object.get_width()/2, HEIGHT/2 -
                                                        text_object.get_height()/2)
        self.board_screen.blit(text_object, text_location)
        # double text for shadow effect
        text_object = font.render(text, False, pygame.Color("black"))
        self.board_screen.blit(text_object, text_location.move(2, 2))
        
    def display_game_result(self, game_state):
        if game_state.checkmate:
            if game_state.whiteToMove:
                self.draw_text("game concluded with a black win")
            else:
                self.draw_text("game concluded with a white win")
        if game_state.stalemate:
            self.draw_text(self.board_screen, "game concluded with a stalemate")