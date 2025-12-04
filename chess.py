class ChessGame:
    def __init__(self):
        self.board = self.initialize_board()
        self.current_player = 'white'
        self.move_count = 0
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.game_over = False

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

    def print_board(self):
        """Вывод доски на экран"""
        print("\n  A B C D E F G H")
        for i in range(8):
            row_num = 8 - i
            print(f"{row_num} ", end="")
            for j in range(8):
                piece = self.board[i][j]
                print(piece if piece != ' ' else '.', end=" ")
            print(f"{row_num}")
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

    def get_piece_at(self, pos):
        """Получить фигуру на позиции"""
        return self.board[pos[0]][pos[1]]

    def is_white_piece(self, piece):
        """Проверка, является ли фигура белой"""
        return piece.isupper()

    def is_black_piece(self, piece):
        """Проверка, является ли фигура черной"""
        return piece.islower()

    def is_valid_pawn_move(self, from_pos, to_pos, piece):
        """Проверка корректности хода пешки"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        target = self.get_piece_at(to_pos)

        if self.is_white_piece(piece):
            direction = -1
            start_row = 6
        else:
            direction = 1
            start_row = 1

        # Движение вперед на одну клетку
        if from_col == to_col and to_row == from_row + direction and target == ' ':
            return True

        # Движение вперед на две клетки с начальной позиции
        if (from_col == to_col and from_row == start_row and
                to_row == from_row + 2 * direction and
                target == ' ' and self.board[from_row + direction][from_col] == ' '):
            return True

        # Взятие по диагонали
        if (abs(from_col - to_col) == 1 and to_row == from_row + direction and
                target != ' ' and self.is_white_piece(piece) != self.is_white_piece(target)):
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
        """Проверка корректности хода короля"""
        row_diff = abs(from_pos[0] - to_pos[0])
        col_diff = abs(from_pos[1] - to_pos[1])
        return row_diff <= 1 and col_diff <= 1

    def is_valid_move(self, from_pos, to_pos):
        """Проверка корректности хода"""
        piece = self.get_piece_at(from_pos)
        target = self.get_piece_at(to_pos)

        # Проверка, что фигура принадлежит текущему игроку
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
            if not self.is_valid_king_move(from_pos, to_pos):
                return False, "Неверный ход для короля!"

        # Проверка, не приводит ли ход к шаху своему королю
        if self.would_be_in_check(from_pos, to_pos):
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

                # Временно проверяем, может ли фигура атаковать позицию
                from_pos = (row, col)
                piece_lower = piece.lower()

                if piece_lower == 'p':
                    # Пешка атакует по диагонали
                    direction = -1 if self.is_white_piece(piece) else 1
                    if (pos[0] == row + direction and
                            abs(pos[1] - col) == 1):
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
        # Сохраняем состояние
        piece = self.board[from_pos[0]][from_pos[1]]
        target = self.board[to_pos[0]][to_pos[1]]

        # Делаем временный ход
        self.board[to_pos[0]][to_pos[1]] = piece
        self.board[from_pos[0]][from_pos[1]] = ' '

        # Находим позицию короля
        if piece.lower() == 'k':
            king_pos = to_pos
        else:
            king_pos = self.white_king_pos if self.current_player == 'white' else self.black_king_pos

        # Проверяем, атакован ли король
        enemy_color = 'black' if self.current_player == 'white' else 'white'
        in_check = self.is_square_attacked(king_pos, enemy_color)

        # Восстанавливаем состояние
        self.board[from_pos[0]][from_pos[1]] = piece
        self.board[to_pos[0]][to_pos[1]] = target

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

                # Проверяем, принадлежит ли фигура нужному цвету
                if color == 'white' and not self.is_white_piece(piece):
                    continue
                if color == 'black' and not self.is_black_piece(piece):
                    continue

                from_pos = (from_row, from_col)

                # Проверяем все возможные позиции на доске
                for to_row in range(8):
                    for to_col in range(8):
                        to_pos = (to_row, to_col)

                        if from_pos == to_pos:
                            continue

                        # Временно переключаем игрока для проверки
                        original_player = self.current_player
                        self.current_player = color

                        valid, _ = self.is_valid_move(from_pos, to_pos)

                        self.current_player = original_player

                        if valid:
                            legal_moves.append((from_pos, to_pos))

        return legal_moves

    def is_checkmate(self, color):
        """
        Проверка мата для указанного цвета.
        Мат - это когда:
        1. Король находится под шахом
        2. Нет ни одного легального хода, который бы спас короля от шаха
        """
        # Проверяем, находится ли король под шахом
        if not self.is_in_check(color):
            return False

        # Проверяем, есть ли хотя бы один легальный ход
        legal_moves = self.get_all_legal_moves(color)

        # Если нет легальных ходов и король под шахом - это мат
        return len(legal_moves) == 0

    def is_stalemate(self, color):
        """
        Проверка пата для указанного цвета.
        Пат - это когда:
        1. Король НЕ находится под шахом
        2. Нет ни одного легального хода
        """
        # Проверяем, что король НЕ под шахом
        if self.is_in_check(color):
            return False

        # Проверяем, есть ли хотя бы один легальный ход
        legal_moves = self.get_all_legal_moves(color)

        # Если нет легальных ходов и король не под шахом - это пат
        return len(legal_moves) == 0

    def make_move(self, from_pos, to_pos):
        """Выполнить ход"""
        piece = self.board[from_pos[0]][from_pos[1]]

        # Обновляем позицию короля
        if piece.lower() == 'k':
            if self.current_player == 'white':
                self.white_king_pos = to_pos
            else:
                self.black_king_pos = to_pos

        self.board[to_pos[0]][to_pos[1]] = piece
        self.board[from_pos[0]][from_pos[1]] = ' '

        self.move_count += 1
        self.current_player = 'black' if self.current_player == 'white' else 'white'

        # Проверяем мат или пат после хода
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

    def play(self):
        """Основной игровой цикл"""
        print("=" * 40)
        print("ШАХМАТНЫЙ СИМУЛЯТОР")
        print("=" * 40)
        print("\nОбозначения фигур:")
        print("Белые (заглавные): K-король, Q-ферзь, R-ладья, B-слон, N-конь, P-пешка")
        print("Черные (строчные): k-король, q-ферзь, r-ладья, b-слон, n-конь, p-пешка")
        print("\nФормат хода: e2 e4 (из позиции в позицию)")
        print("Для выхода введите: quit\n")

        while not self.game_over:
            self.print_board()
            print(f"Ход #{self.move_count + 1}")
            print(f"Ходят {'БЕЛЫЕ' if self.current_player == 'white' else 'ЧЕРНЫЕ'}")

            move_input = input("\nВведите ход (например, e2 e4): ").strip().lower()

            if move_input == 'quit':
                print("Игра завершена!")
                break

            parts = move_input.split()
            if len(parts) != 2:
                print("Ошибка! Введите ход в формате: e2 e4")
                continue

            from_pos = self.parse_position(parts[0])
            to_pos = self.parse_position(parts[1])

            if from_pos is None or to_pos is None:
                print("Ошибка! Неверный формат позиции. Используйте формат a1-h8.")
                continue

            piece = self.get_piece_at(from_pos)
            if piece == ' ':
                print("Ошибка! На указанной клетке нет фигуры.")
                continue

            valid, message = self.is_valid_move(from_pos, to_pos)
            if not valid:
                print(f"Ошибка! {message}")
                continue

            self.make_move(from_pos, to_pos)

        self.print_board()
        print(f"Всего сделано ходов: {self.move_count}")


# Функции для тестирования
def test_initial_board():
    """Тест инициализации доски"""
    print("Тест 1: Инициализация доски")
    game = ChessGame()
    assert game.board[0][0] == 'r', "Ошибка: левая черная ладья"
    assert game.board[0][4] == 'k', "Ошибка: черный король"
    assert game.board[7][4] == 'K', "Ошибка: белый король"
    assert game.board[1][0] == 'p', "Ошибка: черная пешка"
    assert game.board[6][0] == 'P', "Ошибка: белая пешка"
    print("✓ Доска инициализирована корректно\n")


def test_pawn_moves():
    """Тест ходов пешки"""
    print("Тест 2: Ходы пешки")
    game = ChessGame()

    # Тест хода пешки на одну клетку
    from_pos = (6, 4)  # e2
    to_pos = (5, 4)  # e3
    valid, _ = game.is_valid_move(from_pos, to_pos)
    assert valid, "Ошибка: пешка должна ходить на одну клетку вперед"

    # Тест хода пешки на две клетки с начальной позиции
    to_pos = (4, 4)  # e4
    valid, _ = game.is_valid_move(from_pos, to_pos)
    assert valid, "Ошибка: пешка должна ходить на две клетки с начальной позиции"

    print("✓ Ходы пешки работают корректно\n")


def test_knight_moves():
    """Тест ходов коня"""
    print("Тест 3: Ходы коня")
    game = ChessGame()

    # Тест хода коня буквой "Г"
    from_pos = (7, 1)  # b1
    to_pos = (5, 2)  # c3
    valid, _ = game.is_valid_move(from_pos, to_pos)
    assert valid, "Ошибка: конь должен ходить буквой Г"

    print("✓ Ходы коня работают корректно\n")


def test_checkmate_detection():
    """Тест определения мата (дурацкий мат)"""
    print("Тест 4: Определение мата (дурацкий мат)")
    game = ChessGame()

    # Имитируем дурацкий мат за 2 хода
    # 1. f3
    game.board[6][5] = ' '
    game.board[5][5] = 'P'
    game.current_player = 'black'

    # 1... e5
    game.board[1][4] = ' '
    game.board[3][4] = 'p'
    game.current_player = 'white'

    # 2. g4
    game.board[6][6] = ' '
    game.board[4][6] = 'P'
    game.current_player = 'black'

    # 2... Qh4# (мат)
    game.board[0][3] = ' '
    game.board[4][7] = 'q'
    game.white_king_pos = (7, 4)

    is_mate = game.is_checkmate('white')
    assert is_mate, "Ошибка: должен быть обнаружен мат"

    print("✓ Мат определяется корректно\n")


def test_stalemate_detection():
    """Тест определения пата"""
    print("Тест 5: Определение пата")
    game = ChessGame()

    # Создаем патовую позицию
    game.board = [[' ' for _ in range(8)] for _ in range(8)]
    game.board[0][0] = 'k'  # Черный король в углу
    game.board[1][1] = 'Q'  # Белый ферзь контролирует поля
    game.board[2][0] = 'K'  # Белый король

    game.black_king_pos = (0, 0)
    game.white_king_pos = (2, 0)

    is_stalemate = game.is_stalemate('black')
    assert is_stalemate, "Ошибка: должен быть обнаружен пат"

    print("✓ Пат определяется корректно\n")


def test_check_detection():
    """Тест определения шаха"""
    print("Тест 6: Определение шаха")
    game = ChessGame()

    # Создаем позицию с шахом
    game.board[1][4] = ' '
    game.board[3][4] = 'q'  # Черный ферзь дает шах белому королю

    is_check = game.is_in_check('white')
    assert is_check, "Ошибка: должен быть обнаружен шах"

    print("✓ Шах определяется корректно\n")


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "=" * 50)
    print("ЗАПУСК ТЕСТОВ ШАХМАТНОГО СИМУЛЯТОРА")
    print("=" * 50 + "\n")

    try:
        test_initial_board()
        test_pawn_moves()
        test_knight_moves()
        test_checkmate_detection()
        test_stalemate_detection()
        test_check_detection()

        print("=" * 50)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 50 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: {e}\n")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":  #  python chess.py --test
        # Режим тестирования
        run_all_tests()
    else:
        # Обычная игра
        game = ChessGame()
        game.play()