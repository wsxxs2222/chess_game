"""
This is our driver file. It will be respnosible for handling user input and displaying the current gamestate
"""


class GameState:
    def __init__(self):
        # 8*8 board, rep by 2d list
        # each piece rep by 2 chars string, first rep the color, second rep the type
        # 'bQ' -> black queen
        # "--" means empty square
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        # keep track of who's move is it
        self.whiteToMove = True
        # keep track of all previous moves
        self.moveLog = []
        # construct notation table
        self.row_to_rank = {}
        self.col_to_file = {}
        self.notation_table()
        # map pieces to functions that check the squares this piece can go
        self.move_functions = {'P': self.p_moves, 'R': self.r_moves, 'N': self.n_moves, 'B': self.b_moves,
                               'Q': self.q_moves,  'K':self.k_moves}

        # keep track of the king position
        self.wk_pos = (7, 4)
        self.bk_pos = (0, 4)
        # game result
        self.checkmate = False
        self.stalemate = False
        # track the en passant square
        self.enp_sq = ()
        # determine which kind of castle we can do at the present move
        self.cur_castle_rights = CastleRights(True, True, True, True)
        self.cr_log = [CastleRights(True, True, True, True)]

    def notation_table(self):
        # ascii number for a is 97
        # construct dict to look up the rank and file correspond
        # to row and col
        for row in range(10):
            str_row = str(row)
            self.row_to_rank[str_row] = 8-row
        for col in range(9):
            a_code = 97 + col
            self.col_to_file[str(col)] = chr(a_code)


    # fix me
    def notation(self, move):
        rank = self.row_to_rank[str(move.eRow)]
        file = self.col_to_file[str(move.eCol)]
        out_str = move.pieceMoved[1] + file + str(rank)
        # if there is capture
        if move.pieceCaptured != "--":
            # muti symbol code is 215
            out_str = out_str[0] + chr(215) + out_str[1:]
            if move.pieceMoved[1] == 'P':
                out_str = self.col_to_file[str(move.sCol)] + out_str[1:]
        # if the piece moved is pawn
        else:
            if move.pieceMoved[1] == 'P':
                out_str = out_str[1:]
        print(out_str)
    # make a move
    def make_move(self, move):
        # track king position
        if move.pieceMoved == "wK":
            self.wk_pos = (move.eRow, move.eCol)
        elif move.pieceMoved == "bK":
            self.bk_pos = (move.eRow, move.eCol)
        # change board situation
        self.board[move.sRow][move.sCol] = "--"
        self.board[move.eRow][move.eCol] = move.pieceMoved
        # handle pawn promotion
        # auto promo queen at this time
        if move.is_promotion:
            self.board[move.eRow][move.eCol] = move.promoted_piece

        self.moveLog.append(move)
        # self.notation(move)
        self.whiteToMove = not self.whiteToMove
        # if it is two square pawn move, then set enp_sq
        if move.pieceMoved[1] == "P" and abs(move.eRow - move.sRow) == 2:
            self.enp_sq = ((move.sRow + move.eRow)//2, move.sCol)
        # other moves make enp square vanish
        else:
            self.enp_sq = ()
        # if the move is enp capture
        if move.is_enp:
            # clear the captured pawn
            self.board[move.sRow][move.eCol] = "--"
        # move the rook to the right location if this is a castle move
        if move.is_castle:
            # if long castle
            if move.sCol - move.eCol == 2:
                # add a rook in new position
                self.board[move.eRow][move.eCol + 1] = move.pieceMoved[0] + "R"
                # erase a rook in old position
                self.board[move.eRow][move.eCol - 2] = "--"
            elif move.sCol - move.eCol == -2:
                # add a rook in new position
                self.board[move.eRow][move.eCol - 1] = move.pieceMoved[0] + "R"
                # erase a rook in old position
                self.board[move.eRow][move.eCol + 1] = "--"
        # determine if castling rights have been broken
        self.update_cr(move)


    # undo a move
    def unmove(self):
        # only can un-move when it is not starting pos
        if len(self.moveLog) == 0:
            return
        # get the last move and clear it from the movelog
        last_move = self.moveLog.pop()
        # update board back to last position
        self.board[last_move.sRow][last_move.sCol] = last_move.pieceMoved
        self.board[last_move.eRow][last_move.eCol] = last_move.pieceCaptured
        if last_move.pieceMoved == "wK":
            self.wk_pos = (last_move.sRow, last_move.sCol)
        elif last_move.pieceMoved == "bK":
            self.bk_pos = (last_move.sRow, last_move.sCol)
        self.whiteToMove = not self.whiteToMove
        # clear game conclusions
        self.checkmate = False
        self.stalemate = False
        # clear enp_sq if undo a two square pawn move
        if last_move.pieceMoved[1] == "P" and abs(last_move.sRow - last_move.eRow) == 2:
            self.enp_sq = ()
        # if last move is enp, revive the pawn two squares back rather than 1
        if last_move.is_enp:
            self.board[last_move.eRow][last_move.eCol] = "--"
            self.board[last_move.sRow][last_move.eCol] = last_move.pieceCaptured
        # if it is castle move, undo the rook correctly
        if last_move.is_castle:
            # if long castle
            if last_move.sCol - last_move.eCol == 2:
                # add a rook in new position
                self.board[last_move.eRow][last_move.eCol + 1] = "--"
                # erase a rook in old position
                self.board[last_move.eRow][last_move.eCol - 2] = last_move.pieceMoved[0] + "R"
            elif last_move.sCol - last_move.eCol == -2:
                # add a rook in new position
                self.board[last_move.eRow][last_move.eCol - 1] = "--"
                # erase a rook in old position
                self.board[last_move.eRow][last_move.eCol + 1] = last_move.pieceMoved[0] + "R"

        # if the move on the top after clearing the last move is two square p move
        # then restore its enp_sq
        if len(self.moveLog) != 0:
            prev_move = self.moveLog[-1]
            if prev_move.pieceMoved[1] == "P" and abs(prev_move.sRow - prev_move.eRow) == 2:
                self.enp_sq = ((prev_move.sRow + prev_move.eRow)//2, prev_move.sCol)
        # restore the castle right state on the last move
        self.cr_log.pop()
        last_cr = self.cr_log[-1]
        self.cur_castle_rights = CastleRights(last_cr.wcl, last_cr.wcs, last_cr.bcl, last_cr.bcs)
        # print()

    def get_possible_moves(self):
        moves = []
        for row in range(8):
            for col in range(8):
                if (self.board[row][col][0] == "w" and self.whiteToMove) or \
                (self.board[row][col][0] == "b" and not self.whiteToMove):
                    piece = self.board[row][col][1]
                    self.move_functions[piece](row, col, moves)
                    # continue other cases

        return moves


    def in_between(self, four_tuple):
        # first is row of the checking piece, second is col
        # third is the checking row dir, fourth is col dir
        between_list = []
        # negative because the direction of attack is
        # opposite to the dir coming from the king
        row = four_tuple[0]
        col = four_tuple[1]
        direction = (-four_tuple[2], -four_tuple[3])
        # if knight check, no blocking
        # initialize to -3, -3 since -1, -1 is used
        if direction == (3, 3):
            return between_list
        for squares in range(1, 8):
            if self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "K":
                break
            else:
                between_list.append((row + squares * direction[0], col + squares * direction[1]))
        return between_list

    def get_valid_moves(self):
        # for status in self.cr_log:
        #     print(f"{status.wcl}, {status.wcs}, {status.bcl}, {status.bcs}",end=",")
        valid_moves = self.get_possible_moves()
        in_check, checking_pieces, pinned_pieces = self.checks_and_pins()
        # first two tuples are row and col, second tuple are attack dir row and col
        #print(f"checking_pieces: {checking_pieces}")
        #print(f"pinned pieces: {pinned_pieces}")
        # in check
        if in_check:
            # single check
            if len(checking_pieces) == 1:
                between_list = self.in_between(checking_pieces[0])
                attacker_pos = (checking_pieces[0][0], checking_pieces[0][1])
                for i in range(len(valid_moves)-1, -1, -1):
                    # block
                    if valid_moves[i].pieceMoved[1] != "K" \
                            and (valid_moves[i].eRow, valid_moves[i].eCol) in between_list:
                        continue
                        # enp capture checking pawn
                    elif valid_moves[i].is_enp == True:
                        if (checking_pieces[0][0], checking_pieces[0][1]) == (valid_moves[i].sRow, valid_moves[i].eCol):
                        # print("can enp")
                            continue
                    # attack
                    elif (valid_moves[i].eRow, valid_moves[i].eCol) == attacker_pos:
                        if valid_moves[i].pieceMoved[1] != "K":
                            # can't capture with the pinned piece
                            for four_tuple in pinned_pieces:
                                if (valid_moves[i].sRow, valid_moves[i].sCol) == (four_tuple[0], four_tuple[1]):
                                    valid_moves.remove(valid_moves[i])
                            continue
                        else:
                            if self.expose_king(valid_moves[i]):
                                valid_moves.remove(valid_moves[i])
                    # run
                    elif valid_moves[i].pieceMoved[1] == "K":
                        # attempt the move
                        if self.expose_king(valid_moves[i]):
                            valid_moves.remove(valid_moves[i])
                    else:
                        valid_moves.remove(valid_moves[i])
            elif len(checking_pieces) == 2:
                for i in range(len(valid_moves)-1, -1, -1):
                    if valid_moves[i].pieceMoved[1] != "K":
                        valid_moves.remove(valid_moves[i])
                    else:
                        if self.expose_king(valid_moves[i]):
                            valid_moves.remove(valid_moves[i])
        # not in check
        else:
            for i in range(len(valid_moves) - 1, -1, -1):
                # check if king moves expose the king
                if valid_moves[i].pieceMoved[1] == "K":
                # attempt the move
                    if self.expose_king(valid_moves[i]):
                        valid_moves.remove(valid_moves[i])
                else:
                    # en passant move special row check
                    if valid_moves[i].is_enp == True:
                        # check if expose king in the row
                        # ptr goes to both dirs until hitting a piece
                        # go dir 1 (startCol - endCol)
                        piece_in_dir1 = "--"
                        piece_in_dir2 = "--"
                        dir1 = valid_moves[i].sCol - valid_moves[i].eCol
                        for m in range(1,7):
                            if (valid_moves[i].sCol + m * dir1 >= 0) and (valid_moves[i].sCol + m * dir1 < 8):
                                if self.board[valid_moves[i].sRow][valid_moves[i].sCol + m * dir1] != "--":
                                    piece_in_dir1 = self.board[valid_moves[i].sRow][valid_moves[i].sCol + m * dir1]
                                    break
                            else:
                                break
                        # go dir 2
                        dir2 = -dir1
                        for m in range(1, 7):
                            if (valid_moves[i].eCol + m * dir2 >= 0) and (valid_moves[i].eCol + m * dir2 < 8):
                                if self.board[valid_moves[i].sRow][valid_moves[i].eCol + m * dir2] != "--":
                                    piece_in_dir2 = self.board[valid_moves[i].sRow][valid_moves[i].eCol + m * dir2]
                                    break
                            else:
                                break
                        # check if one of the two pieces is king and the other is Q or R
                        # the two pieces have to be different color and the king has to be ally king
                        if self.whiteToMove:
                            if piece_in_dir1 == "wK":
                                if piece_in_dir2 == "bQ" or piece_in_dir2 == "bR":
                                    valid_moves.remove(valid_moves[i])
                                    continue
                            if piece_in_dir2 == "wK":
                                if piece_in_dir1 == "bQ" or piece_in_dir1 == "bR":
                                    valid_moves.remove(valid_moves[i])
                                    continue
                        else:
                            if piece_in_dir1 == "bK":
                                if piece_in_dir2 == "wQ" or piece_in_dir2 == "wR":
                                    valid_moves.remove(valid_moves[i])
                                    continue
                            if piece_in_dir2 == "bK":
                                if piece_in_dir1 == "wQ" or piece_in_dir1 == "wR":
                                    valid_moves.remove(valid_moves[i])
                                    continue

                    # restrict the pinned pieces, let them only move along the pinned direction
                    for four_tuple in pinned_pieces:
                        #print(f"valid move {(valid_moves[i].sRow, valid_moves[i].sCol)}")
                        #print(f"pinned tuple {(four_tuple[0], four_tuple[1])}")
                        # if the piece is pinned, it can only move in pinned direction
                        if (valid_moves[i].sRow, valid_moves[i].sCol) == (four_tuple[0], four_tuple[1]):
                            # use normalized end pos - start pos to determine direction

                            # if the piece is n then it can't move (its abs(valid_moves[i].sRow - valid_moves[i].eRow)
                            # != abs(valid_moves[i].sCol - valid_moves[i].eCol))
                            if (abs(valid_moves[i].sRow - valid_moves[i].eRow) == 2 and \
                                abs(valid_moves[i].sCol - valid_moves[i].eCol) == 1) or \
                                (abs(valid_moves[i].sRow - valid_moves[i].eRow) == 1 and \
                                 abs(valid_moves[i].sCol - valid_moves[i].eCol) == 2):
                                valid_moves.remove(valid_moves[i])
                            # otherwise check its moving dir, compare it with pinned dir
                            else:
                                move_dir = []
                                if valid_moves[i].eRow - valid_moves[i].sRow == 0:
                                    move_dir.append(0)
                                else:
                                    move_dir.append((valid_moves[i].eRow - valid_moves[i].sRow) //
                                            abs(valid_moves[i].eRow - valid_moves[i].sRow))
                                if valid_moves[i].eCol - valid_moves[i].sCol == 0:
                                    move_dir.append(0)
                                else:
                                    move_dir.append((valid_moves[i].eCol - valid_moves[i].sCol) //
                                            abs(valid_moves[i].eCol - valid_moves[i].sCol))
                                # can move along or opposite to the pinned dir
                                if ((move_dir[0], move_dir[1]) != (four_tuple[2], four_tuple[3])) and \
                                   ((-move_dir[0], -move_dir[1]) != (four_tuple[2], four_tuple[3])):
                                    valid_moves.remove(valid_moves[i])
        # add in valid castle moves
        self.get_cr_moves(valid_moves)
        # if ended up with no valid moves, check if the game is checkmate or stalemate
        if len(valid_moves) == 0:
            if in_check:
                self.checkmate = True
                # print("checkmate")
            else:
                self.stalemate = True
                # print("stalemate")
        return valid_moves

    # check if a square is on the board
    def on_board(self, row, col):
        if (row < 0) or (row > 7):
            return False
        if (col < 0) or (col > 7):
            return False
        return True

    def get_cr_moves(self, moves):
        # short castle
        if (self.whiteToMove and self.cur_castle_rights.wcs) \
           or (not self.whiteToMove and self.cur_castle_rights.bcs):
            self.short_castle_move(moves)
        if (self.whiteToMove and self.cur_castle_rights.wcl) \
           or (not self.whiteToMove and self.cur_castle_rights.bcl):
            self.long_castle_move(moves)

    def short_castle_move(self, moves):
        if self.whiteToMove:
            row = 7
            col = 4
        else:
            row = 0
            col = 4
        # check if squares between k and r are clean
        if (self.board[row][col+1] != "--") or (self.board[row][col+2] != "--"):
            return
        # check if any of the three key squares are under attack
        if (self.square_under_attack(row, col)) or (self.square_under_attack(row, col + 1)) \
           or (self.square_under_attack(row, col + 2)):
            return
        moves.append(Move((row, col), (row, col + 2), self.board, is_castle=True))
        pass

    def long_castle_move(self, moves):
        if self.whiteToMove:
            row = 7
            col = 4
        else:
            row = 0
            col = 4
        if (self.board[row][col - 1] != "--") or (self.board[row][col - 2] != "--") or \
           (self.board[row][col - 3] != "--"):
            return
        # check if any of the three key squares are under attack
        if (self.square_under_attack(row, col)) or (self.square_under_attack(row, col - 1)) \
           or (self.square_under_attack(row, col - 2)):
            return
        moves.append(Move((row, col), (row, col - 2), self.board, is_castle=True))

        pass

    # pass in moves as reference
    def p_moves(self, row, col, moves):
        # diff cases for white and black
        if self.whiteToMove:
            # check if p can move 1 forward
            if self.board[row - 1][col] == "--":
                self.promotion_moves_generator((row, col), (row - 1, col), moves)
                # check if p can move 2 forward
                if row == 6:
                    if self.board[row - 2][col] == "--":
                        moves.append(Move((row, col), (row - 2, col), self.board))
            # L captures
            # enp capture
            if col > 0:
                if self.board[row - 1][col - 1][0] == "b":
                    self.promotion_moves_generator((row, col), (row - 1, col - 1), moves)
                if (row - 1, col - 1) == self.enp_sq:
                    moves.append(Move((row, col), (row - 1, col - 1), self.board, is_enp=True))
            # R captures
            # enp capture
            if col < 7:
                if self.board[row - 1][col + 1][0] == "b":
                    self.promotion_moves_generator((row, col), (row - 1, col + 1), moves)
                if (row - 1, col + 1) == self.enp_sq:
                    moves.append(Move((row, col), (row - 1, col + 1), self.board, is_enp=True))
        else:
            # check if p can move 1 forward
            if self.board[row + 1][col] == "--":
                self.promotion_moves_generator((row, col), (row + 1, col), moves)
                # check if p can move 2 forward
                if row == 1:
                    if self.board[row + 2][col] == "--":
                        moves.append(Move((row, col), (row + 2, col), self.board))
            # L captures
            if col > 0:
                if self.board[row + 1][col - 1][0] == "w":
                    self.promotion_moves_generator((row, col), (row + 1, col - 1), moves)
                if (row + 1, col - 1) == self.enp_sq:
                    moves.append(Move((row, col), (row + 1, col - 1), self.board, is_enp=True))
            # R captures
            if col < 7:
                if self.board[row + 1][col + 1][0] == "w":
                    self.promotion_moves_generator((row, col), (row + 1, col + 1), moves)
                if (row + 1, col + 1) == self.enp_sq:
                    moves.append(Move((row, col), (row + 1, col + 1), self.board, is_enp=True))

    def r_moves(self, row, col, moves):
        if self.whiteToMove:
            color = "w"
        else:
            color = "b"
        dirs = [(0, 1), (-1, 0), (0, -1), (1, 0)]
        for direction in dirs:
            for squares in range(1,8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == color:
                    break
                # if the square is empty
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == "-":
                    moves.append(Move((row, col), (row + squares * direction[0], col + squares * direction[1]),
                                      self.board))
                # if the square is enemy piece
                else:
                    moves.append(Move((row, col), (row + squares * direction[0], col + squares * direction[1]),
                                      self.board))
                    break

    def n_moves(self, row, col, moves):
        if self.whiteToMove:
            color = "w"
        else:
            color = "b"
        # whether move long first, left or right, up or down
        considerables = [(row - 1, col +2), (row - 2, col + 1), (row - 2, col -1), (row -1 , col - 2),
                         (row + 1, col - 2), (row + 2, col - 1), (row + 2, col + 1), (row + 1, col + 2)]
        for pair in considerables:
            # check if it is on board
            # check if self piece is there
            if self.on_board(pair[0], pair[1]):
                if not (self.board[pair[0]][pair[1]][0] == color):
                    moves.append(Move((row, col), (pair[0], pair[1]), self.board))
        pass

    def b_moves(self, row, col, moves):
        if self.whiteToMove:
            color = "w"
        else:
            color = "b"
        dirs = [(-1, 1), (-1, -1), (1, -1), (1, 1)]
        for direction in dirs:
            for squares in range(1, 8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == color:
                    break
                # if the square is empty
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == "-":
                    moves.append(Move((row, col), (row + squares * direction[0], col + squares * direction[1]),
                                      self.board))
                # if the square is enemy piece
                else:
                    moves.append(Move((row, col), (row + squares * direction[0], col + squares * direction[1]),
                                      self.board))
                    break

    def q_moves(self, row, col, moves):
        if self.whiteToMove:
            color = "w"
        else:
            color = "b"
        dirs = [(0, 1), (-1, 0), (0, -1), (1, 0), (-1, 1), (-1, -1), (1, -1), (1, 1)]
        for direction in dirs:
            for squares in range(1, 8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == color:
                    break
                # if the square is empty
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == "-":
                    moves.append(Move((row, col), (row + squares * direction[0], col + squares * direction[1]),
                                      self.board))
                # if the square is enemy piece
                else:
                    moves.append(Move((row, col), (row + squares * direction[0], col + squares * direction[1]),
                                      self.board))
                    break

    def k_moves(self, row, col, moves):
        if self.whiteToMove:
            color = "w"
        else:
            color = "b"
        # whether move long first, left or right, up or down
        considerables = [(row - 1, col +1), (row - 1, col -1), (row - 1, col), (row + 1, col),
                         (row + 1, col - 1), (row + 1, col + 1), (row, col -1), (row, col + 1)]
        for pair in considerables:
            # check if it is on board
            # check if self piece is there
            if self.on_board(pair[0], pair[1]):
                if not (self.board[pair[0]][pair[1]][0] == color):
                    moves.append(Move((row, col), (pair[0], pair[1]), self.board))
        pass

    # find if the king is in check, find all squares of checking pieces, pinned pieces
    def checks_and_pins(self):
        # clear lists
        in_check = False
        checking_pieces = []
        pinned_pieces = []
        if self.whiteToMove:
            row = self.wk_pos[0]
            col = self.wk_pos[1]
            ally = "w"
            enemy = "b"
        else:
            row = self.bk_pos[0]
            col = self.bk_pos[1]
            ally = "b"
            enemy = "w"
        # from the position of the king search 8 dirs for enemy attack pieces

        # check straight line checks
        lines = [(0, 1), (-1, 0), (0, -1), (1, 0)]
        for direction in lines:
            check_pin = False
            possible_pin = (-1, -1)
            for squares in range(1, 8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == ally:
                    if not check_pin:
                        check_pin = True
                        possible_pin = (row + squares * direction[0], col + squares * direction[1])
                    else:
                        break
                # if the square is enemy piece
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == enemy:
                    # if it is a attacking piece
                    if self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "Q" \
                       or self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "R":
                        if not check_pin:
                            checking_pieces.append((row + squares * direction[0], col + squares * direction[1],
                                                         direction[0], direction[1]))
                            in_check = True
                        else:
                            pinned_pieces.append((possible_pin[0], possible_pin[1],
                                                         direction[0], direction[1]))
                    elif self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "K":
                        if squares == 1:
                            checking_pieces.append((row + squares * direction[0], col + squares * direction[1],
                                                         direction[0], direction[1]))
                            # print("checked by king")
                            in_check = True
                    # if it is not a attacking piece
                    break
        # check for diag checks
        diags = [(-1, 1), (-1, -1), (1, -1), (1, 1)]
        for direction in diags:
            check_pin = False
            possible_pin = (-1, -1)
            for squares in range(1, 8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == ally:
                    if not check_pin:
                        check_pin = True
                        possible_pin = (row + squares * direction[0], col + squares * direction[1])
                    else:
                        break
                # if the square is enemy piece
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == enemy:
                    # if it is a attacking piece
                    if self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "Q" \
                            or self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "B":
                        if not check_pin:
                            checking_pieces.append((row + squares * direction[0], col + squares * direction[1],
                                                         direction[0], direction[1]))
                            in_check = True
                        else:
                            pinned_pieces.append((possible_pin[0], possible_pin[1],
                                                       direction[0], direction[1]))
                    elif self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "K":
                        # print("see a king")
                        if squares == 1:
                            checking_pieces.append((row + squares * direction[0], col + squares * direction[1],
                                                         direction[0], direction[1]))
                            #print("checked by king")
                            in_check = True
                    elif self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "P":
                        # if new_row = row - 1 and it is white to move
                        # if new_row = row + 1 and it is black to move
                        if (row + squares * direction[0] == row - 1 and self.whiteToMove) \
                           or (row + squares * direction[0] == row + 1 and not self.whiteToMove):
                            checking_pieces.append((row + squares * direction[0], col + squares * direction[1],
                                                         direction[0], direction[1]))
                            #print("checked by pawn")
                            in_check = True
                    # if it is not a attacking piece
                    break
        # check for knight checks
        considerables = [(row - 1, col + 2), (row - 2, col + 1), (row - 2, col - 1), (row - 1, col - 2),
                         (row + 1, col - 2), (row + 2, col - 1), (row + 2, col + 1), (row + 1, col + 2)]
        for pair in considerables:
            if self.on_board(pair[0], pair[1]):
                if (self.board[pair[0]][pair[1]][0] == enemy) and (self.board[pair[0]][pair[1]][1] == "N"):
                    checking_pieces.append((pair[0], pair[1], -3, -3))
                    in_check = True
        return in_check, checking_pieces, pinned_pieces

    def square_under_attack(self, row, col):
        is_attacked = False
        if self.whiteToMove:
            ally = "w"
            enemy = "b"
        else:
            ally = "b"
            enemy = "w"
        # from the position of the king search 8 dirs for enemy attack pieces

        # check straight line checks
        lines = [(0, 1), (-1, 0), (0, -1), (1, 0)]
        for direction in lines:
            for squares in range(1, 8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == ally:
                    break
                # if the square is enemy piece
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == enemy:
                    # if it is a attacking piece
                    if self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "Q" \
                            or self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "R":
                        is_attacked = True
                    elif self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "K":
                        if squares == 1:
                            is_attacked = True
                    # if it is not a attacking piece
                    break
        # check for diag checks
        diags = [(-1, 1), (-1, -1), (1, -1), (1, 1)]
        for direction in diags:
            for squares in range(1, 8):
                # check if the square is on board
                if not self.on_board(row + squares * direction[0], col + squares * direction[1]):
                    break
                # if ally piece is there
                if self.board[row + squares * direction[0]][col + squares * direction[1]][0] == ally:
                    break
                # if the square is enemy piece
                elif self.board[row + squares * direction[0]][col + squares * direction[1]][0] == enemy:
                    # if it is a attacking piece
                    if self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "Q" \
                            or self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "B":
                        is_attacked = True
                    elif self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "K":
                        # print("see a king")
                        if squares == 1:
                            is_attacked = True
                    elif self.board[row + squares * direction[0]][col + squares * direction[1]][1] == "P":
                        # if new_row = row - 1 and it is white to move
                        # if new_row = row + 1 and it is black to move
                        if (row + squares * direction[0] == row - 1 and self.whiteToMove) \
                                or (row + squares * direction[0] == row + 1 and not self.whiteToMove):
                            is_attacked = True
                    # if it is not a attacking piece
                    break
        # check for knight checks
        considerables = [(row - 1, col + 2), (row - 2, col + 1), (row - 2, col - 1), (row - 1, col - 2),
                         (row + 1, col - 2), (row + 2, col - 1), (row + 2, col + 1), (row + 1, col + 2)]
        for pair in considerables:
            if self.on_board(pair[0], pair[1]):
                if (self.board[pair[0]][pair[1]][0] == enemy) and (self.board[pair[0]][pair[1]][1] == "N"):
                    is_attacked = True
        return is_attacked

    # see if a move expose the king in check
    def expose_king(self, move):
        exposed = False
        self.make_move(move)
        # look if in check
        # in order to see if ally side is in check, need to swap back move order
        self.whiteToMove = not self.whiteToMove
        checked, l1, l2 = self.checks_and_pins()
        if checked:
            exposed = True
        self.whiteToMove = not self.whiteToMove
        self.unmove()
        return exposed


    def update_cr(self, move):
        # move wK, bK, wR, bR
        if move.pieceMoved == "wK":
            self.cur_castle_rights.wcl = False
            self.cur_castle_rights.wcs = False
        elif move.pieceMoved == "bK":
            self.cur_castle_rights.bcl = False
            self.cur_castle_rights.bcs = False

        elif move.pieceMoved == "wR":
            if move.sRow == 7:
                if move.sCol == 0:
                    self.cur_castle_rights.wcl = False
                elif move.sCol == 7:
                    self.cur_castle_rights.wcs = False
        elif move.pieceMoved == "bR":
            if move.sRow == 0:
                if move.sCol == 0:
                    self.cur_castle_rights.bcl = False
                elif move.sCol == 7:
                    self.cur_castle_rights.bcs = False
        self.cr_log.append(CastleRights(self.cur_castle_rights.wcl, self.cur_castle_rights.wcs
                                        , self.cur_castle_rights.bcl, self.cur_castle_rights.bcs))

    def promotion_moves_generator(self, sPos, ePos, moves):
        if self.whiteToMove and ePos[0] == 0:
            moves.append(Move(sPos, ePos, self.board, promoted_piece="wN"))
            moves.append(Move(sPos, ePos, self.board, promoted_piece="wB"))
            moves.append(Move(sPos, ePos, self.board, promoted_piece="wR"))
            moves.append(Move(sPos, ePos, self.board, promoted_piece="wQ"))
        elif not self.whiteToMove and ePos[0] == 7:
            moves.append(Move(sPos, ePos, self.board, promoted_piece="bN"))
            moves.append(Move(sPos, ePos, self.board, promoted_piece="bB"))
            moves.append(Move(sPos, ePos, self.board, promoted_piece="bR"))
            moves.append(Move(sPos, ePos, self.board, promoted_piece="bQ"))
        else:
            moves.append(Move(sPos, ePos, self.board))


class Move:
    def __init__(self, sPos, ePos, board, is_enp=False, is_castle=False, promoted_piece="--"):
        self.sRow = sPos[0]
        self.sCol = sPos[1]
        self.eRow = ePos[0]
        self.eCol = ePos[1]
        self.pieceMoved = board[sPos[0]][sPos[1]]
        self.pieceCaptured = board[ePos[0]][ePos[1]]
        self.is_pawn_pro = False
        # if the move is white pawn get to 8th rank or black
        self.promoted_piece = promoted_piece
        self.is_promotion = False
        if promoted_piece != "--":
            self.is_promotion = True
        self.ID = 1000 * self.sRow + 100 * self.sCol + 10 * self.eRow + self.eCol
        self.is_enp = is_enp
        # set piece captured to the right piece if it is enp capture
        if self.is_enp:
            self.pieceCaptured = board[self.sRow][self.eCol]
        self.is_castle = is_castle

    def __eq__(self, other):
        # check if the other object is type 'move'
        if isinstance(other, Move):
            return self.ID == other.ID
        return False


class CastleRights:
    def __init__(self, wcl, wcs, bcl, bcs):
        self.wcl = wcl
        self.wcs = wcs
        self.bcl = bcl
        self.bcs = bcs


