from flask import Flask, jsonify, request, send_from_directory
import random
import os
import json
from Levenshtein import distance as levenshtein_distance

app = Flask(__name__)

LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaderboard.json')
LEADERBOARD_MAX_SIZE = 10

sample_images_data = [
    {
        "id": "img001",
        "path": "static/images/placeholder1.jpg",
        "prompt": "A cat wearing a tiny hat"
    },
    {
        "id": "img002",
        "path": "static/images/placeholder2.jpg",
        "prompt": "A dog riding a skateboard"
    }
]

@app.route('/')
def home():
    # Serve index.html from the genie_app directory itself
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError):
        return []

def save_leaderboard(data):
    try:
        # Sort by score descending, then by name ascending as a tie-breaker (optional)
        data.sort(key=lambda x: (-x.get("score", 0), x.get("name", "")))
        # Limit the size of the leaderboard
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(data[:LEADERBOARD_MAX_SIZE], f, indent=4)
    except IOError:
        # Handle save error, e.g., log it
        print(f"Error saving leaderboard to {LEADERBOARD_FILE}")

@app.route('/api/get_image_data', methods=['GET'])
def get_image_data():
    if not sample_images_data:
        return jsonify({"error": "No images available"}), 404
    
    selected_image = random.choice(sample_images_data)
    return jsonify({
        "id": selected_image["id"],
        "path": selected_image["path"]
    })

@app.route('/api/submit_guess', methods=['POST'])
def submit_guess():
    data = request.get_json()
    if not data or 'image_id' not in data or 'user_guess' not in data:
        return jsonify({"error": "Missing image_id or user_guess"}), 400

    image_id = data['image_id']
    user_guess = data['user_guess']

    image_data = next((img for img in sample_images_data if img["id"] == image_id), None)

    if not image_data:
        return jsonify({"error": "Image not found"}), 404

    correct_prompt_orig = image_data["prompt"]
    
    # Normalize strings
    user_guess_norm = user_guess.lower().strip()
    correct_prompt_norm = correct_prompt_orig.lower().strip()

    if not user_guess_norm: # Handle empty guess after stripping
        return jsonify({
            "correct": False,
            "score": 0,
            "correct_prompt": correct_prompt_orig
        })

    lev_dist = levenshtein_distance(user_guess_norm, correct_prompt_norm)
    max_len = max(len(user_guess_norm), len(correct_prompt_norm))

    if max_len == 0: # Both strings are empty after normalization
        score = 100
    else:
        score = max(0, round((1 - (lev_dist / max_len)) * 100))
    
    is_correct = (score == 100) # Considered correct only on perfect score

    return jsonify({
        "correct": is_correct,
        "score": int(score), # Ensure score is an integer
        "correct_prompt": correct_prompt_orig
    })

@app.route('/api/submit_score', methods=['POST'])
def submit_score():
    data = request.get_json()
    if not data or 'name' not in data or 'score' not in data:
        return jsonify({"error": "Missing name or score"}), 400

    name = data['name'].strip()
    score = data['score']

    if not name:
        return jsonify({"error": "Name cannot be empty"}), 400
    if not isinstance(score, (int, float)): # Allow float scores just in case, though game logic gives int
        return jsonify({"error": "Score must be a number"}), 400

    leaderboard = load_leaderboard()
    leaderboard.append({"name": name, "score": score})
    save_leaderboard(leaderboard) # save_leaderboard handles sorting and limiting

    return jsonify({"message": "Score submitted successfully"}), 201

@app.route('/api/get_leaderboard', methods=['GET'])
def get_leaderboard():
    leaderboard = load_leaderboard()
    # load_leaderboard already returns sorted and potentially limited data if save_leaderboard is the only writer
    # However, if we want to be absolutely sure it's limited to N for this endpoint:
    return jsonify(leaderboard[:LEADERBOARD_MAX_SIZE])

if __name__ == '__main__':
    # Make sure the app runs on 0.0.0.0 to be accessible from Docker
    # and explicitly set the port. Debug should ideally be False for production.
    # For this project, keeping debug=True for simplicity as per earlier setup.
    app.run(host='0.0.0.0', port=5000, debug=True)
