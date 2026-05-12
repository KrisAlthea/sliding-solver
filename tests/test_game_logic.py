from game_logic import GameLogic


def setup_game(size, board):
    game = GameLogic(size=size)
    game.board = [row[:] for row in board]
    for i, row in enumerate(game.board):
        for j, value in enumerate(row):
            if value == 0:
                game.empty_pos = (i, j)
                return game
    raise ValueError("Board must contain 0 as the empty tile.")


def apply_moves(game, moves):
    for move in moves:
        moved = game.move(GameLogic.directions[move])
        assert moved is True


def test_move_swaps_empty_with_neighbor_for_valid_direction():
    game = setup_game(
        size=3,
        board=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 0, 8],
        ],
    )

    success = game.move((0, 1))

    assert success is True
    assert game.board == [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 0],
    ]
    assert game.empty_pos == (2, 2)


def test_move_returns_false_when_direction_goes_out_of_bounds():
    game = setup_game(
        size=3,
        board=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 0],
        ],
    )
    original_board = [row[:] for row in game.board]
    original_empty = game.empty_pos

    success = game.move((1, 0))

    assert success is False
    assert game.board == original_board
    assert game.empty_pos == original_empty


def test_is_solvable_returns_true_for_solved_3x3():
    game = setup_game(
        size=3,
        board=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 0],
        ],
    )

    assert game.is_solvable() is True


def test_is_solvable_returns_false_for_unsolvable_3x3():
    game = setup_game(
        size=3,
        board=[
            [1, 2, 3],
            [4, 5, 6],
            [8, 7, 0],
        ],
    )

    assert game.is_solvable() is False


def test_is_solvable_returns_true_for_solved_4x4():
    game = setup_game(
        size=4,
        board=[
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 0],
        ],
    )

    assert game.is_solvable() is True


def test_is_solvable_returns_false_for_unsolvable_4x4():
    game = setup_game(
        size=4,
        board=[
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 15, 14, 0],
        ],
    )

    assert game.is_solvable() is False


def test_solve_returns_empty_moves_when_board_already_solved():
    game = setup_game(
        size=3,
        board=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 0],
        ],
    )

    assert game.solve() == []


def test_solve_returns_valid_moves_that_reach_goal_state():
    game = setup_game(
        size=3,
        board=[
            [1, 2, 3],
            [4, 5, 6],
            [7, 0, 8],
        ],
    )

    moves = game.solve()

    assert moves == ["right"]
    apply_moves(game, moves)
    assert game.is_solved() is True


def test_set_size_recomputes_goal_state_for_new_size():
    game = GameLogic(size=3)

    game.set_size(4)
    game.board = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 0],
    ]
    game.empty_pos = (3, 3)

    assert len(game.goal_state) == 16
    assert game.goal_state[-1] == 0
    assert game.is_solved() is True
