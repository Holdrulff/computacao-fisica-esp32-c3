"""
Tic-Tac-Toe game logic with AI opponent.
"""
from core.logger import get_logger

logger = get_logger('TicTacToe')

# Game state (module-level singleton)
game_state = {
    'board': ['', '', '', '', '', '', '', '', ''],
    'current_player': 'X',
    'game_active': True,
    'winner': None,
    'winning_line': None
}

# Win conditions: rows, columns, diagonals (tuples for immutability and memory efficiency)
WIN_CONDITIONS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
    (0, 4, 8), (2, 4, 6)              # Diagonals
)


def get_game_state():
    """
    Get current game state.

    Returns:
        dict: Current game state with board, current player, winner, etc.
    """
    return {
        'success': True,
        'board': game_state['board'][:],  # Return copy
        'current_player': game_state['current_player'],
        'game_active': game_state['game_active'],
        'winner': game_state['winner'],
        'winning_line': game_state['winning_line']
    }


def reset_game():
    """
    Reset game to initial state.

    Returns:
        dict: New game state
    """
    game_state['board'] = ['', '', '', '', '', '', '', '', '']
    game_state['current_player'] = 'X'
    game_state['game_active'] = True
    game_state['winner'] = None
    game_state['winning_line'] = None

    logger.info("Game reset")
    return get_game_state()


def check_winner():
    """
    Check if there's a winner.

    Returns:
        tuple: (winner, winning_line) or (None, None) if no winner
    """
    board = game_state['board']

    for line in WIN_CONDITIONS:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return (board[a], line)

    return (None, None)


def check_draw():
    """
    Check if game is a draw (board full with no winner).

    Returns:
        bool: True if draw, False otherwise
    """
    return all(cell != '' for cell in game_state['board'])


def make_move(position, player):
    """
    Make a move on the board with validation.

    Args:
        position: Board position (0-8)
        player: Player making the move ('X' or 'O')

    Returns:
        dict: Result with success status and updated game state
    """
    # Validate game is active
    if not game_state['game_active']:
        return {
            'success': False,
            'error': 'Game is not active'
        }

    # Validate position
    try:
        position = int(position)
        if position < 0 or position > 8:
            return {
                'success': False,
                'error': 'Invalid position (must be 0-8)'
            }
    except (ValueError, TypeError):
        return {
            'success': False,
            'error': 'Invalid position'
        }

    # Validate player
    if player not in ['X', 'O']:
        return {
            'success': False,
            'error': 'Invalid player (must be X or O)'
        }

    # Validate it's the correct player's turn
    if player != game_state['current_player']:
        return {
            'success': False,
            'error': f'Not {player} turn'
        }

    # Validate cell is empty
    if game_state['board'][position] != '':
        return {
            'success': False,
            'error': 'Cell already occupied'
        }

    # Make the move
    game_state['board'][position] = player
    logger.info(f"Player {player} moved to position {position}")

    # Check for winner
    winner, winning_line = check_winner()
    if winner:
        game_state['game_active'] = False
        game_state['winner'] = winner
        game_state['winning_line'] = winning_line
        logger.info(f"Player {winner} wins! Line: {winning_line}")
    elif check_draw():
        game_state['game_active'] = False
        game_state['winner'] = 'draw'
        logger.info("Game is a draw")
    else:
        # Switch player
        game_state['current_player'] = 'O' if player == 'X' else 'X'

    return get_game_state()


def get_computer_move():
    """
    Get computer's move using strategic AI.
    OPTIMIZED: Uses tuples for immutable position lists, reduced iterations.

    Strategy:
    1. Win if possible
    2. Block player from winning
    3. Take center if available
    4. Take corner
    5. Take edge

    Returns:
        dict: Result with success status and move position
    """
    if not game_state['game_active']:
        return {
            'success': False,
            'error': 'Game is not active'
        }

    if game_state['current_player'] != 'O':
        return {
            'success': False,
            'error': 'Not computer turn'
        }

    board = game_state['board']

    # Strategy 1: Win if possible
    move = _find_winning_move('O')
    if move is not None:
        logger.info(f"Computer winning move: {move}")
        return _execute_computer_move(move)

    # Strategy 2: Block player from winning
    move = _find_winning_move('X')
    if move is not None:
        logger.info(f"Computer blocking move: {move}")
        return _execute_computer_move(move)

    # Strategy 3: Take center
    if board[4] == '':
        logger.info("Computer taking center: 4")
        return _execute_computer_move(4)

    # Strategy 4: Take corner (tuple instead of list - more memory efficient)
    for pos in (0, 2, 6, 8):
        if board[pos] == '':
            logger.info(f"Computer taking corner: {pos}")
            return _execute_computer_move(pos)

    # Strategy 5: Take edge (tuple instead of list)
    for pos in (1, 3, 5, 7):
        if board[pos] == '':
            logger.info(f"Computer taking edge: {pos}")
            return _execute_computer_move(pos)

    # No moves available (should not happen)
    return {
        'success': False,
        'error': 'No moves available'
    }


def _find_winning_move(player):
    """
    Find a position that would win for the given player.
    OPTIMIZED: Uses tuples instead of lists, single-pass algorithm.

    Args:
        player: Player to check winning moves for ('X' or 'O')

    Returns:
        int or None: Winning position or None if no winning move
    """
    board = game_state['board']

    for condition in WIN_CONDITIONS:
        a, b, c = condition
        # Use tuple instead of list - more memory efficient
        cells = (board[a], board[b], board[c])

        # Check if two cells are the player and one is empty
        if cells.count(player) == 2 and cells.count('') == 1:
            # Find the empty position (single pass)
            if board[a] == '':
                return a
            if board[b] == '':
                return b
            if board[c] == '':
                return c

    return None


def _execute_computer_move(position):
    """
    Execute computer's move at given position.

    Args:
        position: Board position (0-8)

    Returns:
        dict: Result with move position and updated game state
    """
    result = make_move(position, 'O')
    if result.get('success'):
        result['move'] = position
    return result
