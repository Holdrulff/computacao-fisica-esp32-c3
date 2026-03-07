"""
Snake game leaderboard management with JSON persistence.
"""
import json
from core.logger import get_logger

logger = get_logger('SnakeLeaderboard')

LEADERBOARD_FILE = 'snake_scores.json'
MAX_ENTRIES = 10

def load_leaderboard():
    """Load leaderboard from JSON file."""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except:
        logger.info("Creating new leaderboard file")
        return []

def save_leaderboard(leaderboard):
    """Save leaderboard to JSON file."""
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f)
        logger.info(f"Leaderboard saved ({len(leaderboard)} entries)")
    except Exception as e:
        logger.error(f"Failed to save leaderboard: {e}")

def get_leaderboard():
    """Get current leaderboard."""
    leaderboard = load_leaderboard()
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return {
        'success': True,
        'leaderboard': leaderboard[:MAX_ENTRIES]
    }

def add_score(name, score):
    """
    Add score to leaderboard with idempotency check.

    Args:
        name: Player name (max 20 chars)
        score: Score value

    Returns:
        dict with success, rank, and updated leaderboard
    """
    leaderboard = load_leaderboard()
    normalized_name = name[:20].strip()

    # Check if this exact entry already exists (idempotency)
    if any(entry['name'] == normalized_name and entry['score'] == score
           for entry in leaderboard):
        logger.info(f"Score already exists: {normalized_name} - {score} (idempotent)")
        # Find rank without adding duplicate
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        rank = next((i+1 for i, e in enumerate(leaderboard)
                     if e['name'] == normalized_name and e['score'] == score), None)
        return {
            'success': True,
            'rank': rank,
            'leaderboard': leaderboard[:MAX_ENTRIES],
            'duplicate': True
        }

    # Add new entry
    new_entry = {'name': normalized_name, 'score': score}
    leaderboard.append(new_entry)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    leaderboard = leaderboard[:MAX_ENTRIES]

    # Find rank
    rank = next((i+1 for i, e in enumerate(leaderboard)
                 if e['name'] == normalized_name and e['score'] == score), None)

    save_leaderboard(leaderboard)
    logger.info(f"New score added: {normalized_name} - {score} (rank #{rank})")

    return {
        'success': True,
        'rank': rank,
        'leaderboard': leaderboard,
        'duplicate': False
    }
