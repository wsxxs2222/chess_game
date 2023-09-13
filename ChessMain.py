"""
This class is responsible for sharing all the info about the current state of a chess game. It will be responsible for
determining the valid moves at the current state. It will also keep a move log.
"""

import pygame as p
import ChessEngine


WIDTH = HEIGHT = 512 # 400 is another option
DIMENSION = 8 # dimension of a chess board
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15 # for animations
IMAGES = {}
colors = [p.Color("white"), p.Color("gray")]
ENABLE_ANIMATION = False

'''
initialize a global dict of images. This will be called exactly once in the main
'''
def loadImages():
    pieces = ['wP','wR','wN','wB','wK','wQ','bP','bR','bN','bB','bK','bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("./pictures/" + piece + ".png"), (SQ_SIZE,SQ_SIZE))
    IMAGES['selected'] = p.transform.scale(p.image.load("./pictures/selected.png"), (SQ_SIZE, SQ_SIZE))
    # Note we can access an img by saying 'IMAGES['wP']'

'''
The main driver for our code. This will handle user input and updating the graphics
'''
def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()
    #print(gs.board)
    loadImages() #only do it once before the while loop
    running = True
    # get the square currently selected
    sqSelected = ()
    # get the start and end position for a move
    start_to_end = []
    # variable that controls whether to compute possible moves
    move_made = False
    # control animation
    do_animation = False
    valid_moves = []
    valid_moves = gs.get_valid_moves()
    # the position of selected square
    select_square = (-1, -1)
    # perspective in fog of war
    persp_list = ('n', 'e', 'w', 'b')
    persp_count = 0
    persp = persp_list[persp_count]
    while running:
        for e in p.event.get():
            # quit the program
            if e.type == p.QUIT:
                running = False
            # handle mouse clicks (moves)
            elif e.type == p.MOUSEBUTTONDOWN:
                # get position where the mouse clicked
                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                # if this is the first click
                if len(start_to_end) == 0:
                    if gs.whiteToMove:
                        color = "w"
                    else:
                        color = "b"
                    # only a valid move if a square with piece is clicked
                    if gs.board[row][col] != "--" and gs.board[row][col][0] == color:
                        start_to_end.append((row, col))
                        select_square = (row, col)
                # if this is the second click
                else:
                    # check if the same square is clicked twice
                    if (row, col) == start_to_end[0]:
                        start_to_end = []
                        select_square = (-1, -1)
                    else:
                        start_to_end.append((row, col))
                        # make a move
                        move = ChessEngine.Move(start_to_end[0], start_to_end[1], gs.board)
                        # switch to another piece if we click another piece
                        if (gs.whiteToMove and gs.board[row][col][0] == "w") or \
                                (not gs.whiteToMove and gs.board[row][col][0] == "b"):
                            select_square = (row, col)
                            start_to_end = [(row, col)]
                        # if not selected another piece, then check if this move is valid
                        else:
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    # handle pawn promotion choice
                                    if valid_moves[i].promoted_piece != "--":
                                        promotion_choice(screen, gs, clock, valid_moves[i])
                                    else:
                                        # use the engine generated move since it has additional info to it
                                        gs.make_move(valid_moves[i])
                                    # generate notation (only played moves generate notation
                                    # imaginary moves that are for validating another move don't trigger notation)
                                    gs.notation(valid_moves[i])
                                    move_made = True
                                    do_animation = True
                                    start_to_end = []
                                    select_square = (row, col)
                                    break
                            # if this move is not valid, clear piece selection
                            if not move_made:
                                start_to_end = []
                                select_square = (-1, -1)

            # handle un-moves
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.unmove()
                    do_animation = False
                    select_square = (-1, -1)
                    move_made = True
                # handle reset
                elif e.key == p.K_r:
                    # get new game state object
                    gs = ChessEngine.GameState()
                    # reset parameters
                    move_made = False
                    select_square = (-1, -1)
                    start_to_end = []
                    do_animation = False
                    valid_moves = gs.get_valid_moves()
                elif e.key == p.K_f:
                    persp_count += 1
                    persp_count = persp_count % 4
                    persp = persp_list[persp_count]
        if move_made:
            if do_animation and ENABLE_ANIMATION:
                draw_animation(screen, gs, gs.moveLog[-1], clock)
            valid_moves = gs.get_valid_moves()
            move_made = False
        draw_game_state(screen, gs, valid_moves, select_square, persp)
        draw_selected(screen, select_square)
        # determine the game result
        if gs.checkmate:
            if gs.whiteToMove:
                draw_text(screen, gs, "game concluded with a black win")
            else:
                draw_text(screen, gs, "game concluded with a white win")
        if gs.stalemate:
            draw_text(screen, gs, "game concluded with a stalemate")
        clock.tick(MAX_FPS)
        p.display.flip()


'''
responsible for all the graphics within a current game state.
'''


def draw_game_state(screen, gs, valid_moves, select_square, persp):
    # draw squares on the board
    draw_board(screen)
    draw_highlight(screen, gs, valid_moves, select_square)
    # add in move highlights or move suggestions
    draw_pieces(screen, gs, persp)  # draw pieces on those squares


def draw_board(screen):

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def promotion_choice(screen, gs, clock, move):
    piece_choice = promotion_box(screen, gs.whiteToMove, clock)
    move.promoted_piece = move.promoted_piece[0] + piece_choice
    gs.make_move(move)
    pass


def promotion_box(screen, whiteToMove, clock):
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
    box = p.Rect(WIDTH/2 - w/2, HEIGHT/2 - h/2, w, h)
    p.draw.rect(screen, "gray", box)
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
    while True:
        for i in range(4):
            screen.blit(IMAGES[pieces_list[i]], (tlc[0] + (1 + i) * w_margin + i * 64, tlc[1] + h_margin))
        for e in p.event.get():
            if e.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()
                for j in range(4):
                    if (left_corners[j] <= mouse_pos[0] < right_corners[j]) and (top_height <=
                       mouse_pos[1] <= bot_height):
                        return pieces_list[j][1]
        clock.tick(MAX_FPS)
        p.display.flip()
    # get events until a mouse click is on a piece


'''
draw the pieces using gs.board
'''


def draw_pieces(screen, gs, persp):
    # empty board
    if persp == 'e':
        return
    # normal board
    if persp == 'n':
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                piece = gs.board[r][c]
                if piece != "--":  # if not empty square
                    screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
    else:
        # if it is white's move, display white pieces, display all the pieces in the possible move list
        # (that they are the end row, end col of one of the possible moves) display fog in other squares
        if gs.whiteToMove:
            color = 'w'
        else:
            color = 'b'
        # record if we changed the move order to find correspond possible squares
        order_swapped = False
        if persp != color:
            gs.whiteToMove = not gs.whiteToMove
            order_swapped = True
        # initialize a list correspond to all 64 squares
        display_fog = [[True for j in range(8)] for i in range(8)]
        # determine whether to put fog on them
        moves = gs.get_possible_moves()
        # if the square is in move list, display the piece and do not display fog
        for move in moves:
            visible_row = move.eRow
            visible_col = move.eCol
            display_fog[visible_row][visible_col] = False
            # blit any enemy piece in attack range
            piece = gs.board[visible_row][visible_col]
            if piece[0] != '-':
                screen.blit(IMAGES[piece], (visible_col*SQ_SIZE, visible_row*SQ_SIZE))
        # create a half transparent black square to act as fog of war
        fog = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
        fog.fill((0, 0, 0, 128))
        # choose to not blit anything or blit grey square or to blit a piece
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                if gs.board[r][c][0] == persp:
                    screen.blit(IMAGES[gs.board[r][c]], (c*SQ_SIZE, r*SQ_SIZE))
                else:
                    if display_fog[r][c]:
                        screen.blit(fog, (c*SQ_SIZE, r*SQ_SIZE))
        # swap back order if needed
        if order_swapped:
            gs.whiteToMove = not gs.whiteToMove



def draw_selected(screen, pair):
    if pair != (-1, -1):
        screen.blit(IMAGES['selected'], (pair[1] * SQ_SIZE, pair[0] * SQ_SIZE))


def draw_highlight(screen, gs, valid_moves, select_square):
    # create a new surface for the highlight square
    s = p.Surface((SQ_SIZE, SQ_SIZE))
    # set the opacity
    s.set_alpha(100)
    # set color
    s.fill(p.Color("blue"))
    row, col = select_square
    if not (row == -1 and col == -1):
        # blit the square at the right position on the screen
        screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
        # change color to highlight possible squares
        s.fill(p.Color("yellow"))
        # if highlight all the valid moves involving this piece
        for move in valid_moves:
            if (move.sRow == row) and (move.sCol == col):
                screen.blit(s, (SQ_SIZE * move.eCol, SQ_SIZE * move.eRow))


def draw_animation(screen, gs, move, clock):
    # set speed
    frames_per_square = 10
    # determine the row and col distance
    # determine the total frames to travel from start to end square
    row_dist = move.eRow - move.sRow
    col_dist = move.eCol - move.sCol
    # the direction with the longer distance should be traveled at max speed
    frames = max(abs(row_dist), abs(col_dist)) * frames_per_square
    row_delta = row_dist / frames
    col_delta = col_dist / frames
    for i in range(frames + 1):
        draw_board(screen)
        draw_pieces(screen, gs.board)
        # erase the moved piece from the end position
        color = colors[(move.eRow+move.eCol) % 2]
        p.draw.rect(screen, color, p.Rect(move.eCol*SQ_SIZE, move.eRow*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        # put the piece captured back at the end square
        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], (move.eCol*SQ_SIZE, move.eRow*SQ_SIZE))
        # blit the piece in the in-between position
        screen.blit(IMAGES[move.pieceMoved], ((move.sCol+col_delta*i)*SQ_SIZE,(move.sRow+row_delta*i)*SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def draw_text(screen, gs, text):
    # select font
    font = p.font.SysFont("Helvitca", 32, True, False)
    # select the words for text and color using the font
    text_object = font.render(text, False, p.Color("gray"))
    # center the text requires moving from top left corner to the tlc of the mid-point
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - text_object.get_width()/2, HEIGHT/2 -
                                                     text_object.get_height()/2)
    screen.blit(text_object, text_location)
    # double text for shadow effect
    text_object = font.render(text, False, p.Color("black"))
    screen.blit(text_object, text_location.move(2, 2))
    pass


if __name__ == '__main__':
    main()
