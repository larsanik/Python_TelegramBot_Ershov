from colorama import Fore, Back, Style
import copy


def draw_board(clone_board, sze):
    # делаем клон доски
    # запустить цикл, который проходит по всем  строкам доски
    for i in range(sze):
        # разукращиваем символы в строке
        for ii in range(sze):
            if clone_board[i][ii] == ' ':
                clone_board[i][ii] = Back.MAGENTA + clone_board[i][ii] + Style.RESET_ALL
            if clone_board[i][ii] == '0':
                clone_board[i][ii] = Fore.LIGHTGREEN_EX + Back.BLACK + clone_board[i][ii] + Style.RESET_ALL
            if clone_board[i][ii] == 'X':
                clone_board[i][ii] = Fore.BLACK + Back.LIGHTGREEN_EX + clone_board[i][ii] + Style.RESET_ALL

        # поставить разделители значений в строке
        print(" | ".join(clone_board[i]))
        # print((Back.MAGENTA + " " + Style.RESET_ALL + "| ").join(board[i]))

        # поставить разделители строк
        print("---" * sze + "-" * (sze - 3))


def ask_move(player, board):
    # определяем размер доски
    sze = len(board)
    # дать игроку возможность сделать ход, то есть ввести координаты
    x, y = input(f"{player}, Введите x (0 - {sze - 1}) и y (0 - {sze - 1}) координаты (пример 0 0): ").strip().split()
    # преобразовать координаты в целые числа
    x, y = int(x), int(y)
    # задать условие, которое проверяет,
    # находится ли координата в пределах поля и свободно ли место
    if (0 <= x <= (sze - 1)) and (0 <= y <= (sze - 1)) and (board[y][x] == " "):
        # если свободно, вернуть координаты
        return (x, y)
    else:
        print(f"Клетка {x} {y} занята. Попробуйте еще раз.")
        return ask_move(player, board)


def make_move(player, board, x, y):
    # записать ход
    board[y][x] = player


def ask_and_make_move(player, board):
    x, y = ask_move(player, board)
    # координаты x, y взять из функции ask_move(player, board) и записать ход
    make_move(player, board, x, y)


def check_win(player, board):
    # проверяем не стал ли очередной ход выигрышным
    # определяем размер доски
    sze = len(board)
    # проверяем строки
    for i in range(sze):
        str = ''
        for ii in range(sze):
            str = str + board[i][ii]
        if str == player * sze:
            return True
    # проверяем столбцы
    for i in range(sze):
        str = ''
        for ii in range(sze):
            str = str + board[ii][i]
        if str == player * sze:
            return True
    # проверяем диогональ лв-пн
    str = ''
    for i in range(sze):
        str = str + board[i][i]
    if str == player * sze:
        return True
    # проверяем диогональ лн-пв
    str = ''
    for i in range(sze):
        str = str + board[(sze - 1) - i][i]
    if str == player * sze:
        return True


def tic_tac_toe(sze):
    # бесконечный цикл игры
    while True:
        # создание доски с заданным размером
        board = [[" " for i in range(sze)] for j in range(sze)]
        player = 'X'

        # бесконечный цикл раунда
        while True:
            #  делаем клон доски для разукращивания в цвета
            clone_board = copy.deepcopy(board)

            # рисуем игровое поле
            draw_board(clone_board, sze)

            # запросить ход
            ask_and_make_move(player, board)

            # проверка выигрыша
            if check_win(player, board):
                print(f"{player} выиграл!")
                break

            # проверка состояния ничья
            let_play = False
            for row in board:
                for cell in row:
                    if cell == " ":
                        let_play = True
            # если произошла ничья, завершаем цикл
            if not let_play:
                print("Ничья!")
                break
            # переход хода к другому игроку
            player = "0" if player == "X" else "X"
        # запрос продолжения игры
        restart = input("Хотите сыграть еще раз? (y/n)")
        if restart.lower() != "y":
            break


# запускаем игру для поля 3х3
tic_tac_toe(3)
