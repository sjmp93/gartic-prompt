from flask import Flask, jsonify, request, send_from_directory
import random
import os
import json
from Levenshtein import distance as levenshtein_distance
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# LLM Scoring Configuration
ENABLE_LLM_SCORING = os.getenv('ENABLE_LLM_SCORING', 'false').lower() == 'true'
LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'paraphrase-multilingual-MiniLM-L12-v2')
llm_model = None
# Placeholders SentenceTransformer = None and util = None are removed as direct imports are used.
# Conditional import logic is removed.

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
    
    lev_score = score # Preserve Levenshtein score

    llm_similarity_score = None # Initialize
    final_score = lev_score # Default to Levenshtein score

    if ENABLE_LLM_SCORING and llm_model:
        try:
            # Generate embeddings
            prompt_embedding = llm_model.encode(correct_prompt_norm, convert_to_tensor=True)
            guess_embedding = llm_model.encode(user_guess_norm, convert_to_tensor=True)

            # Calculate cosine similarity
            cosine_scores = util.cos_sim(prompt_embedding, guess_embedding)
            similarity = cosine_scores[0][0].item() # Get the single similarity score (float)
            
            similarity = max(0.0, min(similarity, 1.0)) 

            llm_similarity_score = round(similarity * 100) # Scale to 0-100

            if llm_similarity_score >= 0: 
                final_score = round((lev_score + llm_similarity_score) / 2)
            else: 
                final_score = lev_score 
            
            print(f"LLM scoring active. Levenshtein: {lev_score}, LLM raw sim: {similarity:.4f}, LLM score: {llm_similarity_score}, Final: {final_score}")

        except Exception as e:
            print(f"Error during LLM scoring: {e}")
            final_score = lev_score 
    
    score = int(final_score) 
    is_correct = (score == 100) 

    response_data = {
        "correct": is_correct,
        "score": score,
        "correct_prompt": correct_prompt_orig
    }
    if ENABLE_LLM_SCORING and llm_model and llm_similarity_score is not None:
        response_data["llm_score"] = llm_similarity_score
        response_data["levenshtein_score"] = lev_score
    
    return jsonify(response_data)

@app.route('/api/submit_score', methods=['POST'])
def submit_score():
    data = request.get_json()
    if not data or 'name' not in data or 'score' not in data:
        return jsonify({"error": "Missing name or score"}), 400

    name = data['name'].strip()
    score = data['score']

    if not name:
        return jsonify({"error": "Name cannot be empty"}), 400
    if not isinstance(score, (int, float)): 
        return jsonify({"error": "Score must be a number"}), 400

    leaderboard = load_leaderboard()
    leaderboard.append({"name": name, "score": score})
    save_leaderboard(leaderboard) 

    return jsonify({"message": "Score submitted successfully"}), 201

def load_llm_model():
    global llm_model
    if ENABLE_LLM_SCORING: # Original intended logic
        try:
            print(f"Attempting to load LLM model: {LLM_MODEL_NAME}...")
            llm_model = SentenceTransformer(LLM_MODEL_NAME) # Assumes SentenceTransformer is directly imported
            print(f"LLM model {LLM_MODEL_NAME} loaded successfully.")
        except Exception as e:
            print(f"Error loading LLM model {LLM_MODEL_NAME}: {e}")
            # llm_model remains None; app can run without it if loading fails.

@app.route('/api/get_leaderboard', methods=['GET'])
def get_leaderboard():
    leaderboard = load_leaderboard()
    return jsonify(leaderboard[:LEADERBOARD_MAX_SIZE])

# Original unconditional call to load_llm_model.
# The function itself checks ENABLE_LLM_SCORING.
load_llm_model()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
