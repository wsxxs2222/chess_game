import pygame
import ChessEngine
WIDTH = HEIGHT = 512 # 400 is another option
SIDEBAR_WIDTH = 256
DIMENSION = 8 # dimension of a chess board
SQ_SIZE = HEIGHT // DIMENSION
BOARD_SCREEN = 1
MENU_SCREEN = 2
class UserInfo:
    def __init__(self) -> None:
        self.game_state = ChessEngine.GameState()
        self.is_selected = False # see if we have already selected a square as a starting position
        self.square_selected = (-1, -1)
        self.start_and_endsquare = [] # record the start and end position to keep track of moves
        self.menu_state = None
        self.move_made = False # telling us whether to get new possible moves
        self.valid_moves = self.game_state.get_valid_moves()
        self.clock = pygame.time.Clock()
        self.promotion = False
        self.promotion_move = None
        # load functions correspond to each button
        self.menu_button_functions = {}
        self.load_button_functions()
        pass
    
    # determine which screen the mouse is on
    def identify_screen(self, pos):
        if pos[0] > WIDTH:
            return MENU_SCREEN
        else:
            return BOARD_SCREEN
    
    # handle click of mouse
    def handle_mouseclick(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            screen_pos = self.identify_screen(pos)
            if self.promotion:
                self.get_promotion_choice(pos)
                return
            if screen_pos == BOARD_SCREEN:
                self.get_move(pos)
            elif screen_pos == MENU_SCREEN:
                self.get_menu_order(pos)
        
    # handle user clicks on the board
    def get_move(self, pos):
        col = pos[0] // SQ_SIZE
        row = pos[1] // SQ_SIZE
        move_made = False
        if self.game_state.whiteToMove:
            color = "w"
        else:
            color = "b"
        # see if we are getting start or end position
        # if get start pos, see if the clicked square has a piece of correct color
        if not self.is_selected:
            if self.game_state.board[row][col] != "--" and self.game_state.board[row][col][0] == color:
                self.square_selected = (row, col)
                self.start_and_endsquare.append((row, col))
                self.is_selected = True
            pass
        # if get end pos
        else:
            # check if the selected square is ally piece
            if (self.game_state.whiteToMove and self.game_state.board[row][col][0] == "w") or \
                                    (not self.game_state.whiteToMove and self.game_state.board[row][col][0] == "b"):
                # check if the same square is clicked twice, if so, undo click
                if (row, col) == self.start_and_endsquare[0]:
                    self.start_and_endsquare = []
                    self.is_selected = False
                else:
                    self.start_and_endsquare = [(row, col)]
                    self.square_selected = (row, col)
            #  if we clicked empty square or enemy pieces, move it only if it is valid
            else:
                self.start_and_endsquare.append((row, col))
                # make a move
                move = ChessEngine.Move(self.start_and_endsquare[0], self.start_and_endsquare[1], self.game_state.board)
                for i in range(len(self.valid_moves)):
                    if move == self.valid_moves[i]:
                        # handle pawn promotion choice
                        if self.valid_moves[i].promoted_piece != "--":
                            self.promotion = True
                            self.promotion_move = self.valid_moves[i]
                            return
                        else:
                            # use the engine generated move since it has additional info to it
                            self.game_state.make_move(self.valid_moves[i])
                        # generate notation (only played moves generate notation
                        # imaginary moves that are for validating another move don't trigger notation)
                        move_made = True
                        # if we made a move, reset is_selected, start and end square and valid moves 
                        self.after_move(self.valid_moves[i])
                        break
                # if this move is not valid, clear piece selection
                if not move_made:
                    self.start_and_endsquare = []
                    self.is_selected = False
                
    def get_promotion_choice(self, pos):
        if self.game_state.whiteToMove:
            turn = "w"
        else:
            turn = "b"
        w_margin = 4
        h_margin = 10
        w = 5*w_margin+w_margin*64
        h = 64+2*h_margin
        tlc = (WIDTH/2 - w/2, HEIGHT/2 - h/2)
        left_corners = []
        right_corners = []
        top_height = tlc[1] + h_margin
        bot_height = tlc[1] + 2 * h_margin + 64
        pieces_list = ["N", "B", "R", "Q"]
        for i in range(4):
            pieces_list[i] = turn + pieces_list[i]
            left_corners.append(tlc[0]+(1+i)*w_margin)
            right_corners.append(tlc[0]+(1+i)*w_margin+(i+1)*64)
        for j in range(4):
            if (left_corners[j] <= pos[0] < right_corners[j]) and (top_height <=
            pos[1] <= bot_height):
                self.promotion_move.promoted_piece =  self.promotion_move.promoted_piece[0] + pieces_list[j][1]
                self.game_state.make_move(self.promotion_move)
                self.promotion = False
                self.after_move(self.promotion_move)
        pass
    
    # record the function correspond to each button press
    def load_button_functions(self):
        self.menu_button_functions["undo"]               = self.make_unmove
        self.menu_button_functions["reset"]              = self.reset_board
        self.menu_button_functions["change perspective"] = self.change_perspective
        self.menu_button_functions["export game"]        = self.export_game
        self.menu_button_functions["import game"]        = self.import_game
        self.menu_button_functions["play online"]        = self.play_online
        pass
    
    # handle the things needed to be done after a move is made
    def after_move(self, move=None):
        self.valid_moves = self.game_state.get_valid_moves()
        self.is_selected = False
        self.start_and_endsquare = []
        # clear notation is unmove, notation if move
        if move:
            self.game_state.notation(move)
        else:
            pass
    
    def button_click(self, key):
        self.menu_button_functions[key]()
        
    def make_unmove(self):
        self.game_state.unmove()
        self.after_move()
        
    def reset_board(self):
        self.game_state = ChessEngine.GameState()
        self.after_move()
    
    def change_perspective(self):
        pass
    def export_game(self):
        pass
    def import_game(self):
        pass
    def play_online(self):
        pass
        
    def get_menu_order(self, pos):
        pass