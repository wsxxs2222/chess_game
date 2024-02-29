import pygame
import ChessEngine
import socket
import threading
WIDTH = HEIGHT = 512 # 400 is another option
SIDEBAR_WIDTH = 256
DIMENSION = 8 # dimension of a chess board
SQ_SIZE = HEIGHT // DIMENSION
BOARD_SCREEN = 1
MENU_SCREEN = 2
FORMAT = "utf-8"
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
        self.mode_menu_functions = {}
        self.load_button_functions()
        # client socket to send moves for multiplayer
        self.client = None
        self.is_white = None
        # perspective
        self.perspective = "w"
        # state that user is in
        # [offline, select_mode, waiting, online]
        self.user_state = "offline"
        
        pass
    
    # determine which screen the mouse is on
    def identify_screen(self, pos):
        if pos[0] > WIDTH:
            return MENU_SCREEN
        else:
            return BOARD_SCREEN
    
    # handle click of mouse
    def handle_mouseclick(self, event):
        # if it's online and not our turn, we receive move
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            screen_pos = self.identify_screen(pos)
            # if online and opponent's turn, wait them to send move
            if self.promotion:
                self.get_promotion_choice(pos)
                return
            if screen_pos == BOARD_SCREEN:
                if self.user_state == "offline":
                    self.get_move(pos)
                # online and my move then get move
                elif self.user_state == "online" and self.game_state.ally_color == self.game_state.get_color():
                    if not self.game_state.checkmate:
                        self.get_move(pos)
                    
            elif screen_pos == MENU_SCREEN:
                # handle main menu or different menu depend on the state
                if self.user_state == "online":
                    pass
                elif self.user_state == "select_mode":
                    pass
                else:
                    pass
                    
    def handle_key_press(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.change_mode()
                
    def change_mode(self):
        if self.game_state.game_mode == "normal":
            self.game_state.game_mode = "fog of war"
        else:
            self.game_state.game_mode = "normal"
        
    # handle user clicks on the board
    def get_move(self, pos):
        col = pos[0] // SQ_SIZE
        row = pos[1] // SQ_SIZE
        # case where the perspective is on black side
        if self.perspective == "b":
            row, col = self.symmetric_mapping(row, col)
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
                move_made = self.handle_move(move)
                # if this move is not valid, clear piece selection
                if not move_made:
                    self.start_and_endsquare = []
                    self.is_selected = False
                    
    def handle_move(self, move):
        move_made = False
        for i in range(len(self.valid_moves)):
            if move == self.valid_moves[i]:
                # handle pawn promotion choice
                if self.valid_moves[i].promoted_piece != "--":
                    if move.promoted_piece == "--":
                        self.promotion = True
                        self.promotion_move = self.valid_moves[i]
                        return
                    # if we received the move and therefore know its promoted piece
                    else:
                        self.valid_moves[i].promoted_piece = move.promoted_piece
                        self.game_state.make_move(self.valid_moves[i])
                else:
                    # use the engine generated move since it has additional info to it
                    self.game_state.make_move(self.valid_moves[i])
                # generate notation (only played moves generate notation
                # imaginary moves that are for validating another move don't trigger notation)
                move_made = True
                # if we made a move, reset is_selected, start and end square and valid moves 
                self.after_move(self.valid_moves[i])
                break
        return move_made
    
    def receive_move(self):
        print("receiving move")
        message = self.client.recv(1024).decode(FORMAT)
        while not message:
            message = self.client.recv(1024).decode(FORMAT)
        if message:
            message_list = message.split(",")
        print(f"received {message}")
        # 3 parts, s_pos, e_pos, promo_piece
        s_pos = (int(message_list[0][0]), int(message_list[0][1]))
        e_pos = (int(message_list[1][0]), int(message_list[1][1]))
        move = ChessEngine.Move(s_pos, e_pos, self.game_state.board, promoted_piece=message[2])
        self.handle_move(move)
        pass
    
    def send_move(self, move):
        if self.game_state.checkmate or self.game_state.stalemate:
            game_res = "end"
        else:
            game_res = "--"
        string = str(move.sRow) + str(move.sCol) + "," + str(move.eRow) + str(move.eCol) + "," + move.promoted_piece + "," + game_res
        print(f"sending {string}")
        self.client.send(string.encode(FORMAT))
        pass
                
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
        # main menu buttons
        self.menu_button_functions["undo"]               = self.make_unmove
        self.menu_button_functions["reset"]              = self.reset_board
        self.menu_button_functions["change perspective"] = self.change_perspective
        self.menu_button_functions["export game"]        = self.export_game
        self.menu_button_functions["import game"]        = self.import_game
        self.menu_button_functions["play online"]        = self.play_online
        
        # select mode buttons
        self.mode_menu_functions["normal"] = self.send_normal
        self.mode_menu_functions["fog of war"] = self.send_fow
        pass
    
    
    
    # handle the things needed to be done after a move is made
    def after_move(self, move=None):
        self.valid_moves = self.game_state.get_valid_moves()
        self.is_selected = False
        self.start_and_endsquare = []
        # clear notation is unmove, notation if move
        if move:
            self.game_state.notation(move)
            # wins the game if we capture king in fog of war
            if move.pieceCaptured[1] == "K":
                self.game_state.checkmate = True
        else:
            pass
        
        # handle cases when we are online
        if self.user_state == "online":
            # send move if it was our turn and we were online
            if self.game_state.whiteToMove != self.is_white:
                self.send_move(move)
            # terminate connection when the game ended
            if self.game_state.checkmate or self.game_state.stalemate:
                self.client.close()
                self.user_state = "offline"
                print("game concluded, close client socket")
                # self.game_state = ChessEngine.GameState()
            # receive a move if it is not our turn
            if self.game_state.get_color() != self.game_state.ally_color:
                if not self.game_state.checkmate:
                    t1 = threading.Thread(target=self.receive_move, args=())
                    t1.start()

    def main_buttons_click(self, key):
        self.menu_button_functions[key]()
        
    def mode_buttons_click(self, key):
        self.mode_menu_functions[key]()
        
    def make_unmove(self):
        self.game_state.unmove()
        self.after_move()
        
    def reset_board(self):
        self.game_state = ChessEngine.GameState()
        self.after_move()
    
    def change_perspective(self):
        if self.perspective == "w":
            self.perspective = "b"
        else:
            self.perspective = "w"
        pass
    
    # map the row and column number from white perspective to black perspective
    def symmetric_mapping(self, row, col):
        return 7-row, 7-col
    
    def export_game(self):
        pass
    def import_game(self):
        pass
    def play_online(self):
        self.multiplayer()
        pass
    
    def send_normal(self):
        self.client.send("normal".encode(FORMAT))
        self.game_state.game_mode = "normal"
        print("normal mode selected")
        self.user_state = "waiting"
        
    def send_fow(self):
        self.client.send("fog of war".encode(FORMAT))
        self.game_state.game_mode = "fog of war"
        print("fog of war mode selected")
        self.user_state = "waiting"
        
    def get_mode(self, pos):
        pass
        
    def get_menu_order(self, pos):
        pass
    
    def init_client(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def connect_to_server(self):
        # reset board when we want to play online
        self.game_state = ChessEngine.GameState()
        self.valid_moves = self.game_state.get_valid_moves()
        self.user_state = "waiting"
        print("trying to connect")
        # HOST = '172.30.108.165'
        HOST = '172.26.28.223'
        PORT = 9090
        self.client.connect((HOST, PORT))
        print("connection successful, waiting for player 2")
        # stuck here when waiting for the other connectio
        message = self.client.recv(1024).decode(FORMAT)
        while not message:
                message = self.client.recv(1024).decode(FORMAT)
        if message == "select_mode":
            self.user_state = "select_mode"
            print("selecting mode")
            # assigned color message
            message = None
            message = self.client.recv(1024).decode(FORMAT)
            while not message:
                message = self.client.recv(1024).decode(FORMAT)
            color = message
        else:
            # game mode message
            self.game_state.game_mode = message
            print(f"received game mode {message}")
            # assigned color message
            message = None
            message = self.client.recv(1024).decode(FORMAT)
            while not message:
                message = self.client.recv(1024).decode(FORMAT)
            color = message
        print(f"got assigned color {color}")
        if color == "w":
            self.is_white = True
            self.game_state.ally_color = "w"
            self.perspective = "w"
        else:
            self.is_white = False
            self.game_state.ally_color = "b"
            self.perspective = "b"
        self.user_state = "online"
        # start to receive move if we are assigned black
        if self.game_state.ally_color == "b":
            t1 = threading.Thread(target=self.receive_move, args=())
            t1.start()

        
    def multiplayer(self):
        self.init_client()
        t1 = threading.Thread(target=self.connect_to_server, args=())
        t1.start()
        pass
    
    # ToDo: send move when we are online after we make a move
    # add a function to accept assigned color by the server
    # link multiplayer button to corresp function
    # test if the two player mode works