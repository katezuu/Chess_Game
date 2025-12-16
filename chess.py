import json
import re
from copy import deepcopy


class ChessGame:
    def __init__(self):
        self.board = self.initialize_board()
        self.current_player = 'white'
        self.move_count = 0
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.game_over = False

        # История для отката ходов
        self.move_history = []

        # Рокировка
        self.white_king_moved = False
        self.white_rook_a_moved = False
        self.white_rook_h_moved = False
        self.black_king_moved = False
        self.black_rook_a_moved = False
        self.black_rook_h_moved = False

        # Взятие на проходе
        self.en_passant_target = None

        # Режим просмотра партии
        self.replay_mode = False
        self.replay_moves = []
        self.replay_position = 0

    def initialize_board(self):
        """Инициализация шахматной доски"""
        board = [[' ' for _ in range(8)] for _ in range(8)]

        # Черные фигуры
        board[0] = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        board[1] = ['p'] * 8

        # Белые фигуры
        board[6] = ['P'] * 8
        board[7] = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']

        return board

    def print_board(self, highlighted_squares=None, threatened_pieces=None):
        """Вывод доски на экран с подсветкой"""
        if highlighted_squares is None:
            highlighted_squares = []
        if threatened_pieces is None:
            threatened_pieces = []

        print("\n  A B C D E F G H")
        for i in range(8):
            row_num = 8 - i
            print(f"{row_num} ", end="")
            for j in range(8):
                pos = (i, j)
                piece = self.board[i][j]
                display = piece if piece != ' ' else '.'

                # Подсветка угрожаемых фигур
                if pos in threatened_pieces:
                    display = f"[{display}]"[0:3]  # Ограничение длины
                # Подсветка доступных ходов
                elif pos in highlighted_squares:
                    display = f"*{display}*"[0:3]

                print(display.center(2), end="")
            print(f" {row_num}")
        print("  A B C D E F G H\n")

    def parse_position(self, pos):
        """Преобразование позиции из формата 'e2' в координаты"""
        if len(pos) != 2:
            return None
        col = pos[0].lower()
        row = pos[1]

        if col not in 'abcdefgh' or row not in '12345678':
            return None

        col_idx = ord(col) - ord('a')
        row_idx = 8 - int(row)

        return (row_idx, col_idx)

    def position_to_notation(self, pos):
        """Преобразование координат в нотацию"""
        row, col = pos
        return chr(ord('a') + col) + str(8 - row)

    def get_piece_at(self, pos):
        """Получить фигуру на позиции"""
        return self.board[pos[0]][pos[1]]

    def is_white_piece(self, piece):
        """Проверка, является ли фигура белой"""
        return piece.isupper()

    def is_black_piece(self, piece):
        """Проверка, является ли фигура черной"""
        return piece.islower()

    def is_valid_pawn_move(self, from_pos, to_pos, piece, check_capture=True):
        """Проверка корректности хода пешки"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        target = self.get_piece_at(to_pos)

        if self.is_white_piece(piece):
            direction = -1
            start_row = 6
            promotion_row = 0
        else:
            direction = 1
            start_row = 1
            promotion_row = 7

        # Движение вперед на одну клетку
        if from_col == to_col and to_row == from_row + direction and target == ' ':
            return True

        # Движение вперед на две клетки с начальной позиции
        if (from_col == to_col and from_row == start_row and
                to_row == from_row + 2 * direction and
                target == ' ' and self.board[from_row + direction][from_col] == ' '):
            return True

        # Взятие по диагонали
        if check_capture and (abs(from_col - to_col) == 1 and to_row == from_row + direction):
            if target != ' ' and self.is_white_piece(piece) != self.is_white_piece(target):
                return True
            # Взятие на проходе
            if to_pos == self.en_passant_target:
                return True

        return False

    def is_valid_rook_move(self, from_pos, to_pos):
        """Проверка корректности хода ладьи"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        if from_row != to_row and from_col != to_col:
            return False

        # Проверка пути
        if from_row == to_row:
            step = 1 if to_col > from_col else -1
            for col in range(from_col + step, to_col, step):
                if self.board[from_row][col] != ' ':
                    return False
        else:
            step = 1 if to_row > from_row else -1
            for row in range(from_row + step, to_row, step):
                if self.board[row][from_col] != ' ':
                    return False

        return True

    def is_valid_knight_move(self, from_pos, to_pos):
        """Проверка корректности хода коня"""
        row_diff = abs(from_pos[0] - to_pos[0])
        col_diff = abs(from_pos[1] - to_pos[1])
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)

    def is_valid_bishop_move(self, from_pos, to_pos):
        """Проверка корректности хода слона"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        if abs(from_row - to_row) != abs(from_col - to_col):
            return False

        row_step = 1 if to_row > from_row else -1
        col_step = 1 if to_col > from_col else -1

        row, col = from_row + row_step, from_col + col_step
        while row != to_row and col != to_col:
            if self.board[row][col] != ' ':
                return False
            row += row_step
            col += col_step

        return True

    def is_valid_queen_move(self, from_pos, to_pos):
        """Проверка корректности хода ферзя"""
        return self.is_valid_rook_move(from_pos, to_pos) or self.is_valid_bishop_move(from_pos, to_pos)

    def is_valid_king_move(self, from_pos, to_pos):
        """Проверка корректности хода короля (без рокировки)"""
        row_diff = abs(from_pos[0] - to_pos[0])
        col_diff = abs(from_pos[1] - to_pos[1])
        return row_diff <= 1 and col_diff <= 1

    def is_valid_castling(self, from_pos, to_pos):
        """Проверка возможности рокировки"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        # Проверяем, что это король
        piece = self.get_piece_at(from_pos)
        if piece.lower() != 'k':
            return False

        # Проверяем, что король движется на 2 клетки по горизонтали
        if from_row != to_row or abs(to_col - from_col) != 2:
            return False

        is_white = self.is_white_piece(piece)

        # Проверяем, что король не двигался
        if is_white and self.white_king_moved:
            return False
        if not is_white and self.black_king_moved:
            return False

        # Проверяем, что король не под шахом
        enemy_color = 'black' if is_white else 'white'
        if self.is_square_attacked(from_pos, enemy_color):
            return False

        # Короткая рокировка (O-O)
        if to_col > from_col:
            rook_col = 7
            if is_white and self.white_rook_h_moved:
                return False
            if not is_white and self.black_rook_h_moved:
                return False

            # Проверяем путь
            for col in range(from_col + 1, rook_col):
                if self.board[from_row][col] != ' ':
                    return False
                # Проверяем, что король не проходит через битое поле
                if col <= from_col + 2 and self.is_square_attacked((from_row, col), enemy_color):
                    return False
        # Длинная рокировка (O-O-O)
        else:
            rook_col = 0
            if is_white and self.white_rook_a_moved:
                return False
            if not is_white and self.black_rook_a_moved:
                return False

            # Проверяем путь
            for col in range(rook_col + 1, from_col):
                if self.board[from_row][col] != ' ':
                    return False
                # Проверяем, что король не проходит через битое поле
                if col >= from_col - 2 and self.is_square_attacked((from_row, col), enemy_color):
                    return False

        return True

    def is_valid_move(self, from_pos, to_pos, for_threat_check=False):
        """Проверка корректности хода"""
        piece = self.get_piece_at(from_pos)
        target = self.get_piece_at(to_pos)

        # Проверка, что фигура принадлежит текущему игроку
        if not for_threat_check:
            if self.current_player == 'white' and not self.is_white_piece(piece):
                return False, "Это не ваша фигура!"
            if self.current_player == 'black' and not self.is_black_piece(piece):
                return False, "Это не ваша фигура!"

        # Проверка, что целевая клетка не занята своей фигурой
        if target != ' ':
            if self.is_white_piece(piece) == self.is_white_piece(target):
                return False, "На целевой клетке стоит ваша фигура!"

        piece_lower = piece.lower()

        # Проверка правил для каждой фигуры
        if piece_lower == 'p':
            if not self.is_valid_pawn_move(from_pos, to_pos, piece):
                return False, "Неверный ход для пешки!"
        elif piece_lower == 'r':
            if not self.is_valid_rook_move(from_pos, to_pos):
                return False, "Неверный ход для ладьи!"
        elif piece_lower == 'n':
            if not self.is_valid_knight_move(from_pos, to_pos):
                return False, "Неверный ход для коня!"
        elif piece_lower == 'b':
            if not self.is_valid_bishop_move(from_pos, to_pos):
                return False, "Неверный ход для слона!"
        elif piece_lower == 'q':
            if not self.is_valid_queen_move(from_pos, to_pos):
                return False, "Неверный ход для ферзя!"
        elif piece_lower == 'k':
            # Проверяем рокировку
            if abs(to_pos[1] - from_pos[1]) == 2:
                if not self.is_valid_castling(from_pos, to_pos):
                    return False, "Рокировка невозможна!"
            elif not self.is_valid_king_move(from_pos, to_pos):
                return False, "Неверный ход для короля!"

        # Проверка, не приводит ли ход к шаху своему королю
        if not for_threat_check and self.would_be_in_check(from_pos, to_pos):
            return False, "Этот ход ставит вашего короля под шах!"

        return True, ""

    def is_square_attacked(self, pos, by_color):
        """Проверка, атакована ли клетка фигурами определенного цвета"""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == ' ':
                    continue

                if by_color == 'white' and not self.is_white_piece(piece):
                    continue
                if by_color == 'black' and not self.is_black_piece(piece):
                    continue

                from_pos = (row, col)
                piece_lower = piece.lower()

                if piece_lower == 'p':
                    direction = -1 if self.is_white_piece(piece) else 1
                    if (pos[0] == row + direction and abs(pos[1] - col) == 1):
                        return True
                elif piece_lower == 'n':
                    if self.is_valid_knight_move(from_pos, pos):
                        return True
                elif piece_lower == 'b':
                    if self.is_valid_bishop_move(from_pos, pos):
                        return True
                elif piece_lower == 'r':
                    if self.is_valid_rook_move(from_pos, pos):
                        return True
                elif piece_lower == 'q':
                    if self.is_valid_queen_move(from_pos, pos):
                        return True
                elif piece_lower == 'k':
                    if self.is_valid_king_move(from_pos, pos):
                        return True

        return False

    def would_be_in_check(self, from_pos, to_pos):
        """Проверка, будет ли король под шахом после хода"""
        piece = self.board[from_pos[0]][from_pos[1]]
        target = self.board[to_pos[0]][to_pos[1]]

        # Обработка взятия на проходе
        en_passant_capture = None
        if piece.lower() == 'p' and to_pos == self.en_passant_target:
            direction = 1 if self.is_white_piece(piece) else -1
            en_passant_capture = (to_pos[0] - direction, to_pos[1])
            captured_piece = self.board[en_passant_capture[0]][en_passant_capture[1]]
            self.board[en_passant_capture[0]][en_passant_capture[1]] = ' '

        self.board[to_pos[0]][to_pos[1]] = piece
        self.board[from_pos[0]][from_pos[1]] = ' '

        if piece.lower() == 'k':
            king_pos = to_pos
        else:
            king_pos = self.white_king_pos if self.current_player == 'white' else self.black_king_pos

        enemy_color = 'black' if self.current_player == 'white' else 'white'
        in_check = self.is_square_attacked(king_pos, enemy_color)

        self.board[from_pos[0]][from_pos[1]] = piece
        self.board[to_pos[0]][to_pos[1]] = target

        if en_passant_capture:
            self.board[en_passant_capture[0]][en_passant_capture[1]] = captured_piece

        return in_check

    def is_in_check(self, color):
        """Проверка, находится ли король указанного цвета под шахом"""
        king_pos = self.white_king_pos if color == 'white' else self.black_king_pos
        enemy_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(king_pos, enemy_color)

    def get_all_legal_moves(self, color):
        """Получить все возможные легальные ходы для указанного цвета"""
        legal_moves = []

        for from_row in range(8):
            for from_col in range(8):
                piece = self.board[from_row][from_col]
                if piece == ' ':
                    continue

                if color == 'white' and not self.is_white_piece(piece):
                    continue
                if color == 'black' and not self.is_black_piece(piece):
                    continue

                from_pos = (from_row, from_col)

                for to_row in range(8):
                    for to_col in range(8):
                        to_pos = (to_row, to_col)

                        if from_pos == to_pos:
                            continue

                        original_player = self.current_player
                        self.current_player = color

                        valid, _ = self.is_valid_move(from_pos, to_pos)

                        self.current_player = original_player

                        if valid:
                            legal_moves.append((from_pos, to_pos))

        return legal_moves

    def get_legal_moves_for_piece(self, pos):
        """Получить все легальные ходы для конкретной фигуры"""
        piece = self.get_piece_at(pos)
        if piece == ' ':
            return []

        legal_moves = []
        for to_row in range(8):
            for to_col in range(8):
                to_pos = (to_row, to_col)
                if pos == to_pos:
                    continue

                valid, _ = self.is_valid_move(pos, to_pos)
                if valid:
                    legal_moves.append(to_pos)

        return legal_moves

    def get_threatened_pieces(self, color):
        """Получить список угрожаемых фигур указанного цвета"""
        threatened = []
        enemy_color = 'black' if color == 'white' else 'white'

        for row in range(8):
            for col in range(8):
                pos = (row, col)
                piece = self.board[row][col]

                if piece == ' ':
                    continue

                if color == 'white' and not self.is_white_piece(piece):
                    continue
                if color == 'black' and not self.is_black_piece(piece):
                    continue

                if self.is_square_attacked(pos, enemy_color):
                    threatened.append(pos)

        return threatened

    def is_checkmate(self, color):
        """Проверка мата для указанного цвета"""
        if not self.is_in_check(color):
            return False

        legal_moves = self.get_all_legal_moves(color)
        return len(legal_moves) == 0

    def is_stalemate(self, color):
        """Проверка пата для указанного цвета"""
        if self.is_in_check(color):
            return False

        legal_moves = self.get_all_legal_moves(color)
        return len(legal_moves) == 0

    def save_state(self):
        """Сохранить текущее состояние игры"""
        return {
            'board': deepcopy(self.board),
            'current_player': self.current_player,
            'move_count': self.move_count,
            'white_king_pos': self.white_king_pos,
            'black_king_pos': self.black_king_pos,
            'white_king_moved': self.white_king_moved,
            'white_rook_a_moved': self.white_rook_a_moved,
            'white_rook_h_moved': self.white_rook_h_moved,
            'black_king_moved': self.black_king_moved,
            'black_rook_a_moved': self.black_rook_a_moved,
            'black_rook_h_moved': self.black_rook_h_moved,
            'en_passant_target': self.en_passant_target,
        }

    def restore_state(self, state):
        """Восстановить состояние игры"""
        self.board = deepcopy(state['board'])
        self.current_player = state['current_player']
        self.move_count = state['move_count']
        self.white_king_pos = state['white_king_pos']
        self.black_king_pos = state['black_king_pos']
        self.white_king_moved = state['white_king_moved']
        self.white_rook_a_moved = state['white_rook_a_moved']
        self.white_rook_h_moved = state['white_rook_h_moved']
        self.black_king_moved = state['black_king_moved']
        self.black_rook_a_moved = state['black_rook_a_moved']
        self.black_rook_h_moved = state['black_rook_h_moved']
        self.en_passant_target = state['en_passant_target']

    def make_move(self, from_pos, to_pos, promotion_piece='Q'):
        """Выполнить ход"""
        if self.replay_mode:
            return

        # Сохраняем состояние для истории
        state = self.save_state()
        state['from_pos'] = from_pos
        state['to_pos'] = to_pos
        state['captured_piece'] = self.get_piece_at(to_pos)

        piece = self.board[from_pos[0]][from_pos[1]]

        # Обработка взятия на проходе
        en_passant_capture = False
        if piece.lower() == 'p' and to_pos == self.en_passant_target:
            en_passant_capture = True
            direction = 1 if self.is_white_piece(piece) else -1
            capture_pos = (to_pos[0] - direction, to_pos[1])
            state['en_passant_captured'] = self.board[capture_pos[0]][capture_pos[1]]
            state['en_passant_capture_pos'] = capture_pos
            self.board[capture_pos[0]][capture_pos[1]] = ' '

        # Сброс цели взятия на проходе
        self.en_passant_target = None

        # Установка новой цели взятия на проходе
        if piece.lower() == 'p' and abs(to_pos[0] - from_pos[0]) == 2:
            direction = 1 if self.is_white_piece(piece) else -1
            self.en_passant_target = (from_pos[0] + direction, from_pos[1])

        # Обработка рокировки
        if piece.lower() == 'k' and abs(to_pos[1] - from_pos[1]) == 2:
            # Перемещаем ладью
            if to_pos[1] > from_pos[1]:  # Короткая рокировка
                rook_from = (from_pos[0], 7)
                rook_to = (from_pos[0], 5)
            else:  # Длинная рокировка
                rook_from = (from_pos[0], 0)
                rook_to = (from_pos[0], 3)

            self.board[rook_to[0]][rook_to[1]] = self.board[rook_from[0]][rook_from[1]]
            self.board[rook_from[0]][rook_from[1]] = ' '
            state['castling'] = True
            state['rook_from'] = rook_from
            state['rook_to'] = rook_to

        # Обновляем флаги перемещения для рокировки
        if piece == 'K':
            self.white_king_moved = True
        elif piece == 'k':
            self.black_king_moved = True
        elif piece == 'R':
            if from_pos == (7, 0):
                self.white_rook_a_moved = True
            elif from_pos == (7, 7):
                self.white_rook_h_moved = True
        elif piece == 'r':
            if from_pos == (0, 0):
                self.black_rook_a_moved = True
            elif from_pos == (0, 7):
                self.black_rook_h_moved = True

        # Обновляем позицию короля
        if piece.lower() == 'k':
            if self.current_player == 'white':
                self.white_king_pos = to_pos
            else:
                self.black_king_pos = to_pos

        # Выполняем ход
        self.board[to_pos[0]][to_pos[1]] = piece
        self.board[from_pos[0]][from_pos[1]] = ' '

        # Превращение пешки
        if piece.lower() == 'p':
            promotion_row = 0 if self.is_white_piece(piece) else 7
            if to_pos[0] == promotion_row:
                if self.is_white_piece(piece):
                    self.board[to_pos[0]][to_pos[1]] = promotion_piece.upper()
                else:
                    self.board[to_pos[0]][to_pos[1]] = promotion_piece.lower()
                state['promotion'] = promotion_piece

        self.move_history.append(state)
        self.move_count += 1
        self.current_player = 'black' if self.current_player == 'white' else 'white'

        # Проверяем окончание игры
        if self.is_checkmate(self.current_player):
            self.game_over = True
            winner = 'ЧЕРНЫЕ' if self.current_player == 'white' else 'БЕЛЫЕ'
            print(f"\n{'=' * 40}")
            print(f"МАТ! Победили {winner}!")
            print(f"{'=' * 40}\n")
        elif self.is_stalemate(self.current_player):
            self.game_over = True
            print(f"\n{'=' * 40}")
            print("ПАТ! Ничья!")
            print(f"{'=' * 40}\n")
        elif self.is_in_check(self.current_player):
            print(f"\nШАХ {'белому' if self.current_player == 'white' else 'черному'} королю!")

    def undo_move(self, steps=1):
        """Откатить ход(ы) назад"""
        if len(self.move_history) < steps:
            print(f"Недостаточно ходов для отката. Доступно: {len(self.move_history)}")
            return False

        for _ in range(steps):
            if not self.move_history:
                break

            state = self.move_history.pop()

            # Восстанавливаем рокировку
            if 'castling' in state and state['castling']:
                rook_from = state['rook_from']
                rook_to = state['rook_to']
                self.board[rook_from[0]][rook_from[1]] = self.board[rook_to[0]][rook_to[1]]
                self.board[rook_to[0]][rook_to[1]] = ' '

            # Восстанавливаем взятие на проходе
            if 'en_passant_captured' in state:
                capture_pos = state['en_passant_capture_pos']
                self.board[capture_pos[0]][capture_pos[1]] = state['en_passant_captured']

            # Восстанавливаем основное состояние
            self.restore_state(state)

        self.game_over = False
        print(f"Откачено {steps} ход(ов)")
        return True

    def move_to_notation(self, from_pos, to_pos, captured_piece='', check='', promotion=''):
        """Преобразовать ход в шахматную нотацию"""
        piece = self.get_piece_at(from_pos)
        piece_symbol = ''

        if piece.lower() != 'p':
            piece_symbols = {'k': 'K', 'q': 'Q', 'r': 'R', 'b': 'B', 'n': 'N'}
            piece_symbol = piece_symbols[piece.lower()]

        from_notation = self.position_to_notation(from_pos)
        to_notation = self.position_to_notation(to_pos)

        # Рокировка
        if piece.lower() == 'k' and abs(to_pos[1] - from_pos[1]) == 2:
            if to_pos[1] > from_pos[1]:
                return "O-O" + check
            else:
                return "O-O-O" + check

        capture_symbol = 'x' if captured_piece else ''

        # Для пешки при взятии указываем линию
        if piece.lower() == 'p' and captured_piece:
            piece_symbol = from_notation[0]

        return f"{piece_symbol}{capture_symbol}{to_notation}{promotion}{check}"

    def save_game_to_file(self, filename):
        """Сохранить партию в файл (полная нотация)"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                move_num = 1
                for i in range(0, len(self.move_history), 2):
                    white_state = self.move_history[i]

                    # Восстанавливаем состояние для определения нотации
                    temp_board = self.board
                    temp_player = self.current_player

                    self.board = white_state['board']
                    from_pos = white_state['from_pos']
                    to_pos = white_state['to_pos']
                    piece = self.board[from_pos[0]][from_pos[1]]
                    captured = white_state['captured_piece']

                    promotion = f"={white_state['promotion']}" if 'promotion' in white_state else ''

                    white_move = self.move_to_notation(from_pos, to_pos, captured, '', promotion)

                    line = f"{move_num}. {white_move}"

                    if i + 1 < len(self.move_history):
                        black_state = self.move_history[i + 1]
                        self.board = black_state['board']
                        from_pos = black_state['from_pos']
                        to_pos = black_state['to_pos']
                        captured = black_state['captured_piece']
                        promotion = f"={black_state['promotion']}" if 'promotion' in black_state else ''

                        black_move = self.move_to_notation(from_pos, to_pos, captured, '', promotion)
                        line += f" {black_move}"

                    f.write(line + "\n")
                    move_num += 1

                    self.board = temp_board
                    self.current_player = temp_player

            print(f"Партия сохранена в файл: {filename}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
            return False

    def parse_move_notation(self, notation, color):
        """Парсинг хода из шахматной нотации"""
        notation = notation.strip().replace('+', '').replace('#', '').replace('!', '').replace('?', '')

        # Рокировка
        if notation in ['O-O', '0-0']:
            row = 7 if color == 'white' else 0
            return ((row, 4), (row, 6))
        if notation in ['O-O-O', '0-0-0']:
            row = 7 if color == 'white' else 0
            return ((row, 4), (row, 2))

        # Превращение пешки
        promotion = None
        if '=' in notation:
            notation, promotion = notation.split('=')
            promotion = promotion[0]

        # Определяем фигуру
        piece_symbols = {'K': 'k', 'Q': 'q', 'R': 'r', 'B': 'b', 'N': 'n'}
        piece_type = None

        if notation[0] in piece_symbols:
            piece_type = piece_symbols[notation[0]]
            notation = notation[1:]
        else:
            piece_type = 'p'

        # Убираем символ взятия
        is_capture = 'x' in notation
        notation = notation.replace('x', '')

        # Последние два символа - целевая позиция
        if len(notation) >= 2:
            to_notation = notation[-2:]
            to_pos = self.parse_position(to_notation)

            if to_pos is None:
                return None

            # Определяем начальную позицию
            disambiguation = notation[:-2]

            # Ищем подходящую фигуру
            candidates = []
            for row in range(8):
                for col in range(8):
                    pos = (row, col)
                    piece = self.get_piece_at(pos)

                    if piece == ' ':
                        continue

                    if color == 'white' and not self.is_white_piece(piece):
                        continue
                    if color == 'black' and not self.is_black_piece(piece):
                        continue

                    if piece.lower() != piece_type:
                        continue

                    # Проверяем дизамбигуацию
                    if disambiguation:
                        pos_notation = self.position_to_notation(pos)
                        if disambiguation not in pos_notation:
                            continue

                    # Проверяем легальность хода
                    original_player = self.current_player
                    self.current_player = color
                    valid, _ = self.is_valid_move(pos, to_pos)
                    self.current_player = original_player

                    if valid:
                        candidates.append(pos)

            if len(candidates) == 1:
                return (candidates[0], to_pos, promotion)
            elif len(candidates) > 1:
                # Неоднозначность - берем первого кандидата
                return (candidates[0], to_pos, promotion)

        return None

    def load_game_from_file(self, filename):
        """Загрузить партию из файла (полная нотация)"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # Очищаем от комментариев и лишних символов
            content = re.sub(r'\{[^}]*\}', '', content)
            content = re.sub(r'\([^)]*\)', '', content)

            moves = []
            # Парсим ходы
            pattern = r'\d+\.\s*([^\s]+)(?:\s+([^\s]+))?'
            matches = re.findall(pattern, content)

            for white_move, black_move in matches:
                moves.append(white_move)
                if black_move:
                    moves.append(black_move)

            self.replay_moves = moves
            self.replay_position = 0
            self.replay_mode = True

            # Сбрасываем игру
            self.__init__()
            self.replay_moves = moves
            self.replay_mode = True

            print(f"Партия загружена: {len(moves)} ходов")
            return True

        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
            return False

    def replay_next(self):
        """Следующий ход в режиме просмотра"""
        if not self.replay_mode:
            print("Не в режиме просмотра")
            return False

        if self.replay_position >= len(self.replay_moves):
            print("Достигнут конец партии")
            return False

        move_notation = self.replay_moves[self.replay_position]
        color = 'white' if self.replay_position % 2 == 0 else 'black'

        parsed = self.parse_move_notation(move_notation, color)
        if parsed:
            if len(parsed) == 3:
                from_pos, to_pos, promotion = parsed
            else:
                from_pos, to_pos = parsed
                promotion = 'Q'

            self.replay_mode = False
            self.make_move(from_pos, to_pos, promotion or 'Q')
            self.replay_mode = True
            self.replay_position += 1

            move_num = (self.replay_position + 1) // 2
            print(f"Ход {move_num}: {move_notation}")
            return True
        else:
            print(f"Не удалось распознать ход: {move_notation}")
            return False

    def replay_prev(self):
        """Предыдущий ход в режиме просмотра"""
        if not self.replay_mode:
            print("Не в режиме просмотра")
            return False

        if self.replay_position == 0:
            print("Начало партии")
            return False

        self.replay_mode = False
        self.undo_move(1)
        self.replay_mode = True
        self.replay_position -= 1

        print(f"Возврат к ходу {(self.replay_position + 1) // 2}")
        return True

    def exit_replay_mode(self):
        """Выйти из режима просмотра и продолжить игру"""
        self.replay_mode = False
        self.replay_moves = []
        self.game_over = False
        print("Режим просмотра завершен. Продолжайте игру!")

    def show_help(self):
        """Показать справку по командам"""
        print("\n" + "=" * 50)
        print("СПРАВКА ПО КОМАНДАМ")
        print("=" * 50)
        print("Ходы: e2 e4 - формат хода")
        print("hint [позиция] - показать доступные ходы для фигуры")
        print("threats - показать угрожаемые фигуры")
        print("undo [N] - откатить N ходов назад (по умолчанию 1)")
        print("save [файл] - сохранить партию")
        print("load [файл] - загрузить партию")
        print("next - следующий ход (в режиме просмотра)")
        print("prev - предыдущий ход (в режиме просмотра)")
        print("play - выйти из просмотра и продолжить игру")
        print("help - показать эту справку")
        print("quit - выход")
        print("=" * 50 + "\n")

    def play(self):
        """Основной игровой цикл"""
        print("=" * 50)
        print("РАСШИРЕННЫЙ ШАХМАТНЫЙ СИМУЛЯТОР")
        print("=" * 50)
        print("\nОбозначения фигур:")
        print("Белые: K-король, Q-ферзь, R-ладья, B-слон, N-конь, P-пешка")
        print("Черные: k-король, q-ферзь, r-ладья, b-слон, n-конь, p-пешка")
        print("\nВведите 'help' для справки по командам\n")

        while not self.game_over:
            highlighted = []
            threatened = []

            self.print_board(highlighted, threatened)

            if self.replay_mode:
                print(f"РЕЖИМ ПРОСМОТРА - Ход {self.replay_position}/{len(self.replay_moves)}")
            else:
                print(f"Ход #{self.move_count + 1}")
                print(f"Ходят {'БЕЛЫЕ' if self.current_player == 'white' else 'ЧЕРНЫЕ'}")

            user_input = input("\nВведите команду: ").strip().lower()

            if user_input == 'quit':
                print("Игра завершена!")
                break

            elif user_input == 'help':
                self.show_help()
                continue

            elif user_input.startswith('hint'):
                parts = user_input.split()
                if len(parts) == 2:
                    pos = self.parse_position(parts[1])
                    if pos:
                        legal_moves = self.get_legal_moves_for_piece(pos)
                        self.print_board(legal_moves, [])
                        print(f"Доступно ходов: {len(legal_moves)}")
                    else:
                        print("Неверная позиция")
                else:
                    print("Использование: hint e2")
                continue

            elif user_input == 'threats':
                threatened = self.get_threatened_pieces(self.current_player)
                self.print_board([], threatened)
                print(f"Угрожаемых фигур: {len(threatened)}")
                if self.is_in_check(self.current_player):
                    print("⚠️  ШАХ КОРОЛЮ!")
                continue

            elif user_input.startswith('undo'):
                parts = user_input.split()
                steps = int(parts[1]) if len(parts) > 1 else 1
                self.undo_move(steps)
                continue

            elif user_input.startswith('save'):
                parts = user_input.split()
                filename = parts[1] if len(parts) > 1 else 'game.txt'
                self.save_game_to_file(filename)
                continue

            elif user_input.startswith('load'):
                parts = user_input.split()
                if len(parts) > 1:
                    self.load_game_from_file(parts[1])
                else:
                    print("Укажите имя файла")
                continue

            elif user_input == 'next' and self.replay_mode:
                self.replay_next()
                continue

            elif user_input == 'prev' and self.replay_mode:
                self.replay_prev()
                continue

            elif user_input == 'play' and self.replay_mode:
                self.exit_replay_mode()
                continue

            # Обработка хода
            parts = user_input.split()
            if len(parts) != 2:
                print("Ошибка! Введите ход в формате: e2 e4")
                continue

            from_pos = self.parse_position(parts[0])
            to_pos = self.parse_position(parts[1])

            if from_pos is None or to_pos is None:
                print("Ошибка! Неверный формат позиции.")
                continue

            piece = self.get_piece_at(from_pos)
            if piece == ' ':
                print("Ошибка! На указанной клетке нет фигуры.")
                continue

            valid, message = self.is_valid_move(from_pos, to_pos)
            if not valid:
                print(f"Ошибка! {message}")
                continue

            # Проверка превращения пешки
            promotion = 'Q'
            if piece.lower() == 'p':
                target_row = 0 if self.is_white_piece(piece) else 7
                if to_pos[0] == target_row:
                    promo_input = input("Превращение пешки (Q/R/B/N): ").upper()
                    if promo_input in ['Q', 'R', 'B', 'N']:
                        promotion = promo_input

            self.make_move(from_pos, to_pos, promotion)

        self.print_board()
        print(f"Всего сделано ходов: {self.move_count}")


# Тесты
def run_tests():
    """Запуск всех тестов"""
    print("\n" + "=" * 50)
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 50 + "\n")

    tests_passed = 0
    tests_total = 0

    # Тест 1: Инициализация
    tests_total += 1
    try:
        game = ChessGame()
        assert game.board[0][0] == 'r'
        assert game.board[7][4] == 'K'
        print("✓ Тест 1: Инициализация")
        tests_passed += 1
    except:
        print("✗ Тест 1: Инициализация")

    # Тест 2: Ходы пешки
    tests_total += 1
    try:
        game = ChessGame()
        valid, _ = game.is_valid_move((6, 4), (5, 4))
        assert valid
        print("✓ Тест 2: Ходы пешки")
        tests_passed += 1
    except:
        print("✗ Тест 2: Ходы пешки")

    # Тест 3: Рокировка
    tests_total += 1
    try:
        game = ChessGame()
        # Освобождаем место для рокировки
        game.board[7][5] = ' '
        game.board[7][6] = ' '
        valid = game.is_valid_castling((7, 4), (7, 6))
        assert valid
        print("✓ Тест 3: Рокировка")
        tests_passed += 1
    except:
        print("✗ Тест 3: Рокировка")

    # Тест 4: Откат хода
    tests_total += 1
    try:
        game = ChessGame()
        game.make_move((6, 4), (4, 4))
        initial_count = game.move_count
        game.undo_move(1)
        assert game.move_count == initial_count - 1
        print("✓ Тест 4: Откат хода")
        tests_passed += 1
    except:
        print("✗ Тест 4: Откат хода")

    # Тест 5: Определение мата
    tests_total += 1
    try:
        game = ChessGame()
        # Дурацкий мат
        game.board[6][5] = ' '
        game.board[5][5] = 'P'
        game.current_player = 'black'
        game.board[1][4] = ' '
        game.board[3][4] = 'p'
        game.current_player = 'white'
        game.board[6][6] = ' '
        game.board[4][6] = 'P'
        game.current_player = 'black'
        game.board[0][3] = ' '
        game.board[4][7] = 'q'
        game.white_king_pos = (7, 4)
        is_mate = game.is_checkmate('white')
        assert is_mate
        print("✓ Тест 5: Определение мата")
        tests_passed += 1
    except:
        print("✗ Тест 5: Определение мата")

    # Тест 6: Взятие на проходе
    tests_total += 1
    try:
        game = ChessGame()
        # Настраиваем позицию для взятия на проходе
        game.board[6][4] = ' '
        game.board[3][4] = 'P'  # Белая пешка на e5
        game.board[1][3] = ' '
        game.board[3][3] = 'p'  # Черная пешка перемещается с d7 на d5
        game.en_passant_target = (2, 3)
        game.current_player = 'white'
        valid, _ = game.is_valid_move((3, 4), (2, 3))
        assert valid
        print("✓ Тест 6: Взятие на проходе")
        tests_passed += 1
    except:
        print("✗ Тест 6: Взятие на проходе")

    # Тест 7: Подсказки ходов
    tests_total += 1
    try:
        game = ChessGame()
        moves = game.get_legal_moves_for_piece((6, 4))
        assert len(moves) > 0
        print("✓ Тест 7: Подсказки ходов")
        tests_passed += 1
    except:
        print("✗ Тест 7: Подсказки ходов")

    # Тест 8: Угрожаемые фигуры
    tests_total += 1
    try:
        game = ChessGame()
        game.board[1][4] = ' '
        game.board[3][4] = 'q'
        threatened = game.get_threatened_pieces('white')
        assert len(threatened) > 0
        print("✓ Тест 8: Угрожаемые фигуры")
        tests_passed += 1
    except:
        print("✗ Тест 8: Угрожаемые фигуры")

    print("\n" + "=" * 50)
    print(f"РЕЗУЛЬТАТ: {tests_passed}/{tests_total} тестов пройдено")
    print("=" * 50 + "\n")

    return tests_passed == tests_total


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    else:
        game = ChessGame()
        game.play()