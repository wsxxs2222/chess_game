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
        self.if_selected = False # see if we have already selected a square as a starting position
        self.square_selected = (-1, -1)
        self.start_and_endsquare = [] # record the start and end position to keep track of moves
        self.menu_state = None
        self.move_made = False # telling us whether to get new possible moves
        self.valid_moves = self.game_state.get_valid_moves()
        self.clock = pygame.time.Clock()
        self.promotion = False
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
        if not self.if_selected:
            if self.game_state.board[row][col] != "--" and self.game_state.board[row][col][0] == color:
                self.square_selected = (row, col)
                self.start_and_endsquare.append((row, col))
                self.if_selected = True
            pass
        # if get end pos
        else:
            # check if the selected square is ally piece
            if (self.game_state.whiteToMove and self.game_state.board[row][col][0] == "w") or \
                                    (not self.game_state.whiteToMove and self.game_state.board[row][col][0] == "b"):
                # check if the same square is clicked twice, if so, undo click
                if (row, col) == self.start_and_endsquare[0]:
                    self.start_and_endsquare = []
                    self.if_selected = False
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
                        else:
                            # use the engine generated move since it has additional info to it
                            self.game_state.make_move(self.valid_moves[i])
                        # generate notation (only played moves generate notation
                        # imaginary moves that are for validating another move don't trigger notation)
                        self.game_state.notation(self.valid_moves[i])
                        move_made = True
                        # if we made a move, reset if_selected, start and end square and valid moves 
                        self.start_and_endsquare = []
                        self.if_selected = False
                        self.valid_moves = self.game_state.get_valid_moves()
                        break
                # if this move is not valid, clear piece selection
                if not move_made:
                    self.start_and_endsquare = []
                    self.if_selected = False
                
                    
    def get_menu_order(self, pos):
        pass