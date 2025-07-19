from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import time

app = Flask(__name__)
CORS(app) # Enable CORS for communication with the frontend

# --- Global State (for simplicity, in-memory. For real app, use a DB) ---
# This dictionary will store player performance metrics to adapt difficulty
# Key: session_id (or user_id if implemented), Value: {'difficulty_level': float, 'correct_streak': int, 'avg_time': float, 'puzzle_count': int}
player_performance = {}

# --- Puzzle Generation Logic ---
def generate_arithmetic_sequence(difficulty_level):
    """
    Generates an arithmetic sequence puzzle based on difficulty.
    Difficulty influences sequence length, common difference range, and start number range.
    """
    # Adjust parameters based on difficulty_level
    # Difficulty levels are floats to allow for finer adjustments
    # 0.0 to 0.9: Very Easy
    # 1.0 to 1.9: Easy
    # 2.0 to 2.9: Medium
    # 3.0 to 3.9: Hard
    # 4.0 to 4.5: Very Hard (max difficulty)

    if difficulty_level < 1.0: # Very Easy
        start_num = random.randint(1, 10)
        common_diff = random.choice([1, 2, 5])
        length = 3
    elif difficulty_level < 2.0: # Easy
        start_num = random.randint(1, 20)
        common_diff = random.randint(1, 7)
        length = 4
    elif difficulty_level < 3.0: # Medium
        start_num = random.randint(1, 50)
        common_diff = random.randint(1, 10) * random.choice([-1, 1]) # Allow negative diff
        length = 5
    elif difficulty_level < 4.0: # Hard
        start_num = random.randint(1, 100)
        common_diff = random.randint(5, 20) * random.choice([-1, 1])
        length = 6
    else: # Very Hard (4.0 to 4.5)
        start_num = random.randint(1, 200)
        common_diff = random.randint(10, 30) * random.choice([-1, 1])
        length = 7

    sequence = [start_num + i * common_diff for i in range(length)]
    correct_answer = start_num + length * common_diff
    
    # Generate a unique puzzle ID (for tracking)
    puzzle_id = f"puzzle_{int(time.time())}_{random.randint(1000, 9999)}"

    return {
        'sequence': sequence,
        'correct_answer': correct_answer,
        'puzzle_id': puzzle_id,
        'difficulty_level': difficulty_level # For debugging/tracking
    }

# --- AI/ML Adaptive Logic ---
def update_player_performance(session_id, is_correct, time_taken):
    """
    Updates the player's performance profile based on the last puzzle result.
    Adjusts difficulty level, correct streak, and average time.
    """
    if session_id not in player_performance:
        player_performance[session_id] = {
            'difficulty_level': 0.0, # Start at easiest
            'correct_streak': 0,
            'avg_time': 0.0,
            'puzzle_count': 0
        }

    player_data = player_performance[session_id]
    
    # Update average time (moving average for simplicity)
    if player_data['puzzle_count'] == 0:
        player_data['avg_time'] = time_taken
    else:
        player_data['avg_time'] = (player_data['avg_time'] * player_data['puzzle_count'] + time_taken) / (player_data['puzzle_count'] + 1)
    
    player_data['puzzle_count'] += 1

    if is_correct:
        player_data['correct_streak'] += 1
        # Increase difficulty if player is consistently correct and fast enough
        if player_data['correct_streak'] >= 2 and player_data['avg_time'] < 15: # Solved 2 in a row quickly (adjust time threshold as needed)
            player_data['difficulty_level'] = min(player_data['difficulty_level'] + 0.5, 4.5) # Max difficulty 4.5
    else:
        player_data['correct_streak'] = 0
        # Decrease difficulty if player is incorrect or too slow
        if time_taken > 25: # Took too long (adjust time threshold as needed)
             player_data['difficulty_level'] = max(player_data['difficulty_level'] - 0.5, 0.0) # Min difficulty 0.0
        else: # Incorrect but not necessarily too slow
            player_data['difficulty_level'] = max(player_data['difficulty_level'] - 0.25, 0.0)

    print(f"Player {session_id} performance: {player_data}") # For server-side logging

# --- Flask Routes ---
@app.route('/get_puzzle', methods=['POST'])
def get_puzzle():
    """
    Generates and returns a new puzzle.
    Difficulty is adapted based on the last puzzle's result (if provided).
    """
    # Use remote_addr as a simple session ID for demonstration purposes.
    # In a real application, you'd use proper session management (e.g., Flask-Login, JWT).
    session_id = request.remote_addr 

    last_result = request.json.get('last_result')
    if last_result:
        # Update player performance before generating next puzzle
        update_player_performance(session_id, last_result['is_correct'], last_result['time_taken'])
    
    # Get current difficulty for this session, defaulting to 0.0 if new player
    current_difficulty = player_performance.get(session_id, {}).get('difficulty_level', 0.0)
    
    puzzle = generate_arithmetic_sequence(current_difficulty)
    return jsonify(puzzle)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """
    Receives user's answer and puzzle details, evaluates it,
    and updates player performance.
    """
    data = request.json
    # No direct logic here, just acknowledge receipt.
    # The actual difficulty adaptation happens in get_puzzle based on the 'last_result' sent from frontend.
    return jsonify({"status": "received", "message": "Answer processed."})

if __name__ == '__main__':
    # Run the Flask app on port 5002
    
    app.run(debug=True, port=5002, host='0.0.0.0')