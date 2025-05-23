import pytest
import json
from genie_app.app import app as flask_app # Adjusted import
from unittest.mock import patch

@pytest.fixture
def app():
    # Configure the app for testing
    flask_app.config.update({
        "TESTING": True,
    })
    # You can also set other configurations here if needed, e.g., mock database
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page(client):
    # Test the home page
    response = client.get('/')
    assert response.status_code == 200
    assert b"<h1>Guess the Prompt!</h1>" in response.data # Check for the main heading

def test_get_image_data_success(client):
    # Test the /api/get_image_data endpoint for successful response
    response = client.get('/api/get_image_data')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "id" in data
    assert "path" in data
    # Check if the path looks like a static image path
    assert data["path"].startswith("static/images/")

# Optional: Test for empty sample_images_data if straightforward to mock
def test_get_image_data_no_images(client):
    with patch('genie_app.app.sample_images_data', []):
        response = client.get('/api/get_image_data')
        # App should return 404 if sample_images_data is empty
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "No images available"

# Tests for /api/submit_guess
MOCKED_IMAGES_DATA = [
    {
        "id": "imgTest001",
        "path": "static/images/test_image.jpg", # Path doesn't need to exist for this test
        "prompt": "A test prompt for precise matching"
    },
    {
        "id": "imgTest002",
        "path": "static/images/test_image2.jpg",
        "prompt": "Another example prompt"
    }
]

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_success_perfect_match(client):
    response = client.post('/api/submit_guess', json={
        "image_id": "imgTest001",
        "user_guess": "A test prompt for precise matching"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["correct"] is True
    assert data["score"] == 100
    assert data["correct_prompt"] == "A test prompt for precise matching"

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_success_partial_match(client):
    response = client.post('/api/submit_guess', json={
        "image_id": "imgTest002",
        "user_guess": "Another example prumpt" # Small typo "prumpt" vs "prompt"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["correct"] is False
    # Expected score: Levenshtein distance is 1. Length of "Another example prompt" is 22.
    # Score = (1 - (1/22)) * 100 = (21/22) * 100 = 95.45... -> rounds to 95
    assert data["score"] == 95 
    assert data["correct_prompt"] == "Another example prompt"

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_success_case_insensitivity_and_whitespace(client):
    response = client.post('/api/submit_guess', json={
        "image_id": "imgTest001",
        "user_guess": "  A TEST prompt FOR precise matching  " # Extra spaces and different case
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["correct"] is True # Normalization should handle this
    assert data["score"] == 100
    assert data["correct_prompt"] == "A test prompt for precise matching"

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_success_complete_mismatch(client):
    response = client.post('/api/submit_guess', json={
        "image_id": "imgTest001",
        "user_guess": "Completely different phrase"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["correct"] is False
    assert data["score"] < 50 # Expect a low score, exact value depends on Levenshtein
    assert data["correct_prompt"] == "A test prompt for precise matching"

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_missing_parameters(client):
    response = client.post('/api/submit_guess', json={"image_id": "imgTest001"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert response.get_json()["error"] == "Missing image_id or user_guess"

    response = client.post('/api/submit_guess', json={"user_guess": "some guess"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert response.get_json()["error"] == "Missing image_id or user_guess"

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_invalid_image_id(client):
    response = client.post('/api/submit_guess', json={
        "image_id": "invalidId123",
        "user_guess": "any guess"
    })
    assert response.status_code == 404
    assert "error" in response.get_json()
    assert response.get_json()["error"] == "Image not found"

@patch('genie_app.app.sample_images_data', MOCKED_IMAGES_DATA)
def test_submit_guess_empty_user_guess(client):
    response = client.post('/api/submit_guess', json={
        "image_id": "imgTest001",
        "user_guess": "   " # Whitespace only
    })
    assert response.status_code == 200 # The app handles this as a valid (but incorrect) guess
    data = response.get_json()
    assert data["correct"] is False
    assert data["score"] == 0
    assert data["correct_prompt"] == "A test prompt for precise matching"

import os
from unittest.mock import patch, MagicMock
# import torch # Will import if absolutely necessary for tensor simulation

# Need to import the app module itself for monkeypatching if not already done in a suitable way
from genie_app import app as main_app_module # Alias for clarity in monkeypatching


# Fixture for sample image data, similar to MOCKED_IMAGES_DATA but as a fixture
@pytest.fixture
def sample_image_data_fixture():
    return [
        {
            "id": "llmTest001",
            "path": "static/images/llm_test_image.jpg",
            "prompt": "A curious cat observes a butterfly"
        },
        {
            "id": "llmTest002",
            "path": "static/images/llm_test_image2.jpg",
            "prompt": "Robots playing chess in space"
        }
    ]

# Tests for /api/submit_score and /api/get_leaderboard

@pytest.fixture
def temp_leaderboard(tmp_path, monkeypatch):
    temp_file = tmp_path / "leaderboard.json"
    temp_file.write_text("[]") # Start with an empty leaderboard
    monkeypatch.setattr(main_app_module, 'LEADERBOARD_FILE', str(temp_file))
    return str(temp_file)

# LLM Scoring Tests
# Using main_app_module (alias for genie_app.app) for monkeypatching module-level variables

def test_llm_scoring_disabled_by_default(client, monkeypatch, sample_image_data_fixture):
    # Ensure sample_images_data is patched for this test
    monkeypatch.setattr(main_app_module, 'sample_images_data', sample_image_data_fixture)
    
    # By default, ENABLE_LLM_SCORING is False (or from env var, but we can override for test)
    monkeypatch.setattr(main_app_module, 'ENABLE_LLM_SCORING', False)
    monkeypatch.setattr(main_app_module, 'llm_model', None) # Ensure model is None

    response = client.post('/api/submit_guess', json={
        "image_id": sample_image_data_fixture[0]["id"],
        "user_guess": "A curious cat observes a butterfly" # Perfect match
    })
    assert response.status_code == 200
    data = response.get_json()
    
    assert "llm_score" not in data
    assert "levenshtein_score" not in data
    assert data["score"] == 100 # Should be pure Levenshtein score
    assert data["correct_prompt"] == sample_image_data_fixture[0]["prompt"]

# This test simulates the scenario where ENABLE_LLM_SCORING is True, 
# and a model is successfully loaded (mocked).
# @patch('genie_app.app.util.cos_sim') # Removed direct patch, will handle with monkeypatch
@patch('genie_app.app.SentenceTransformer') # Mock SentenceTransformer
def test_llm_scoring_active_and_model_loaded(mock_st_class, client, monkeypatch, sample_image_data_fixture):
    monkeypatch.setattr(main_app_module, 'ENABLE_LLM_SCORING', True)
    monkeypatch.setattr(main_app_module, 'sample_images_data', sample_image_data_fixture)

    # Mock the SentenceTransformer class and its instance's encode method
    mock_st_instance = MagicMock()
    mock_st_instance.encode.return_value = "dummy_embedding" 
    # Ensure that when SentenceTransformer(model_name) is called, it returns our mock_st_instance
    # This is relevant if load_llm_model is called. If llm_model is directly set, this mock_st_class might not be directly used.
    # For this test, we directly set llm_model, so mock_st_class is mostly to satisfy the decorator.
    monkeypatch.setattr(main_app_module, 'SentenceTransformer', mock_st_class)
    # Simulate that llm_model is this successfully loaded mock instance
    monkeypatch.setattr(main_app_module, 'llm_model', mock_st_instance)

    # Mock genie_app.app.util and its cos_sim method
    mock_util = MagicMock()
    mock_similarity_tensor_behavior = MagicMock()
    mock_similarity_tensor_behavior[0][0].item.return_value = 0.80 # Mocked raw similarity
    mock_util.cos_sim.return_value = mock_similarity_tensor_behavior
    monkeypatch.setattr(main_app_module, 'util', mock_util)
    
    user_guess = "A cat watching a butterfly"
    expected_image_id = sample_image_data_fixture[0]["id"]
    expected_prompt = sample_image_data_fixture[0]["prompt"] # "A curious cat observes a butterfly"

    response = client.post('/api/submit_guess', json={
        "image_id": expected_image_id,
        "user_guess": user_guess
    })
    
    assert response.status_code == 200
    data = response.get_json()

    # Calculate expected Levenshtein score for "A cat watching a butterfly" vs "A curious cat observes a butterfly"
    # lev_dist = levenshtein_distance(user_guess.lower(), expected_prompt.lower()) -> levenshtein_distance("a cat watching a butterfly", "a curious cat observes a butterfly")
    # "a cat watching a butterfly" (28)
    # "a curious cat observes a butterfly" (34)
    # dist = 16 (observed from levenshtein_distance in this environment)
    # max_len = 34
    # lev_score = round((1 - (16/34)) * 100) = round((18/34)*100) = round(0.5294 * 100) = 53
    expected_lev_score = 53

    assert data["levenshtein_score"] == expected_lev_score
    assert data["llm_score"] == 80 # Mocked similarity 0.80 * 100
    # Expected final score: round((53 + 80) / 2) = round(133 / 2) = round(66.5) = 66 (Python rounds .5 to nearest even)
    assert data["score"] == 66
    assert data["correct_prompt"] == expected_prompt
    
    # Check that the global SentenceTransformer class mock (mock_st_class) was NOT called to create a new instance
    # because we directly set main_app_module.llm_model.
    # If load_llm_model were called AND main_app_module.SentenceTransformer was this mock_st_class, then it would be called.
    mock_st_class.assert_not_called() 
    # Check that the mocked model's encode was called twice
    assert mock_st_instance.encode.call_count == 2
    # Check that util.cos_sim was called once
    main_app_module.util.cos_sim.assert_called_once()

# This test specifically checks the call to SentenceTransformer, including model name logic
# @patch('genie_app.app.util.cos_sim') # Removed direct patch
@patch('genie_app.app.SentenceTransformer') # Mock SentenceTransformer class
def test_llm_model_loading_and_name_config(mock_st_class_runtime, client, monkeypatch, sample_image_data_fixture):
    monkeypatch.setattr(main_app_module, 'ENABLE_LLM_SCORING', True)
    monkeypatch.setattr(main_app_module, 'sample_images_data', sample_image_data_fixture)

    # This mock_st_class_runtime is the one provided by @patch for genie_app.app.SentenceTransformer
    # It will be used by load_llm_model if SentenceTransformer is not None in app.py
    mock_st_instance_runtime = MagicMock()
    mock_st_instance_runtime.encode.return_value = "dummy_embedding"
    mock_st_class_runtime.return_value = mock_st_instance_runtime
    
    # Crucially, ensure that main_app_module.SentenceTransformer points to our mock *class*
    # This is what load_llm_model will use if the conditional import in app.py didn't already set it
    # or if we want to override what the conditional import might have set (e.g. if sentence_transformers *is* installed)
    monkeypatch.setattr(main_app_module, 'SentenceTransformer', mock_st_class_runtime)

    # Mock genie_app.app.util and its cos_sim method
    mock_util_runtime = MagicMock()
    mock_similarity_tensor_behavior = MagicMock()
    mock_similarity_tensor_behavior[0][0].item.return_value = 0.90 # Mocked raw similarity
    mock_util_runtime.cos_sim.return_value = mock_similarity_tensor_behavior
    monkeypatch.setattr(main_app_module, 'util', mock_util_runtime)

    # Scenario 1: Default model name
    monkeypatch.setattr(main_app_module, 'LLM_MODEL_NAME', 'paraphrase-multilingual-MiniLM-L12-v2') # Ensure default
    main_app_module.llm_model = None # Reset llm_model before calling load_llm_model
    
    # Call load_llm_model. This will use the monkeypatched main_app_module.SentenceTransformer (which is mock_st_class_runtime)
    main_app_module.load_llm_model() 
    
    mock_st_class_runtime.assert_called_with('paraphrase-multilingual-MiniLM-L12-v2')
    assert main_app_module.llm_model is mock_st_instance_runtime

    client.post('/api/submit_guess', json={
        "image_id": sample_image_data_fixture[0]["id"],
        "user_guess": "Some guess"
    })
    # Assertions for this part were covered in test_llm_scoring_active_and_model_loaded,
    # main focus here is the SentenceTransformer call.

    # Scenario 2: Custom model name
    mock_st_class_runtime.reset_mock() 
    mock_st_instance_runtime.encode.reset_mock()
    main_app_module.util.cos_sim.reset_mock() # Reset the mock on the monkeypatched util

    custom_model_name = "test-custom-model-xyz"
    monkeypatch.setattr(main_app_module, 'LLM_MODEL_NAME', custom_model_name)
    main_app_module.llm_model = None # Reset
    main_app_module.load_llm_model() # Call again with new model name

    mock_st_class_runtime.assert_called_with(custom_model_name)
    assert main_app_module.llm_model is mock_st_instance_runtime

    # Re-configure cos_sim for another call
    mock_similarity_tensor_behavior_2 = MagicMock()
    mock_similarity_tensor_behavior_2[0][0].item.return_value = 0.70
    main_app_module.util.cos_sim.return_value = mock_similarity_tensor_behavior_2

    client.post('/api/submit_guess', json={
        "image_id": sample_image_data_fixture[1]["id"],
        "user_guess": "Another guess"
    })
    # Again, focus is on SentenceTransformer call.

def test_llm_scoring_fallback_on_error(client, monkeypatch, sample_image_data_fixture):
    monkeypatch.setattr(main_app_module, 'ENABLE_LLM_SCORING', True)
    monkeypatch.setattr(main_app_module, 'sample_images_data', sample_image_data_fixture)

    # Mock the llm_model to have an encode method that raises an exception
    mock_model_with_error = MagicMock()
    mock_model_with_error.encode.side_effect = Exception("LLM Model Error")
    monkeypatch.setattr(main_app_module, 'llm_model', mock_model_with_error)

    user_guess = "A cat watching a butterfly" # Levenshtein score: 74
    expected_image_id = sample_image_data_fixture[0]["id"]
    expected_prompt = sample_image_data_fixture[0]["prompt"]
    
    response = client.post('/api/submit_guess', json={
        "image_id": expected_image_id,
        "user_guess": user_guess
    })
    
    assert response.status_code == 200 # Should still succeed
    data = response.get_json()
    
    # Verify it falls back to Levenshtein score
    # The Levenshtein score observed from the library for these inputs is 53.
    assert data["score"] == 53 
    # llm_score and levenshtein_score should not be in response if LLM processing failed before they are set
    assert "llm_score" not in data 
    assert "levenshtein_score" not in data
    assert data["correct_prompt"] == expected_prompt


def test_submit_score_success(client, temp_leaderboard):
    response = client.post('/api/submit_score', json={"name": "Player1", "score": 100})
    assert response.status_code == 201
    assert response.get_json()["message"] == "Score submitted successfully"

    with open(temp_leaderboard, 'r') as f:
        leaderboard_data = json.load(f)
    assert len(leaderboard_data) == 1
    assert leaderboard_data[0]["name"] == "Player1"
    assert leaderboard_data[0]["score"] == 100

def test_submit_score_missing_params(client, temp_leaderboard):
    response = client.post('/api/submit_score', json={"name": "Player1"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing name or score"

    response = client.post('/api/submit_score', json={"score": 100})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing name or score"

def test_submit_score_empty_name(client, temp_leaderboard):
    response = client.post('/api/submit_score', json={"name": "  ", "score": 100})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Name cannot be empty"

def test_submit_score_invalid_score_type(client, temp_leaderboard):
    response = client.post('/api/submit_score', json={"name": "Player1", "score": "not_a_number"})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Score must be a number"

def test_submit_score_sorting_and_limiting(client, temp_leaderboard):
    # LEADERBOARD_MAX_SIZE is 10 in app.py
    for i in range(12):
        name = f"Player{i+1}"
        score = (i + 1) * 10
        client.post('/api/submit_score', json={"name": name, "score": score})

    with open(temp_leaderboard, 'r') as f:
        leaderboard_data = json.load(f)
    
    assert len(leaderboard_data) == 10 # Check limiting
    assert leaderboard_data[0]["name"] == "Player12" # Check sorting (highest score first)
    assert leaderboard_data[0]["score"] == 120
    assert leaderboard_data[9]["name"] == "Player3"
    assert leaderboard_data[9]["score"] == 30

    # Test tie-breaking (name ascending for same score) - if implemented in app
    # For now, app sorts by score then name. Let's test this behavior.
    client.post('/api/submit_score', json={"name": "Alpha", "score": 120})
    client.post('/api/submit_score', json={"name": "Beta", "score": 120}) # Same as Player12 and Alpha

    with open(temp_leaderboard, 'r') as f:
        leaderboard_data_updated = json.load(f)

    assert len(leaderboard_data_updated) == 10
    # Expected order for top scores (120): Alpha, Beta, Player12 (if name is tie breaker)
    # Current app.py sorts by score desc, then name asc.
    names_with_120 = [entry["name"] for entry in leaderboard_data_updated if entry["score"] == 120]
    assert sorted(names_with_120) == ["Alpha", "Beta", "Player12"]
    # Verify they are at the top
    assert leaderboard_data_updated[0]["name"] == "Alpha" # or Beta, depends on insertion if stable sort
    assert leaderboard_data_updated[1]["name"] == "Beta" # or Alpha
    assert leaderboard_data_updated[2]["name"] == "Player12"
    # And the lowest score among the top 10 should be 50 (Player5)
    assert leaderboard_data_updated[-1]["score"] == 50 # Player5 is now the last in the top 10

def test_get_leaderboard_empty(client, temp_leaderboard):
    response = client.get('/api/get_leaderboard')
    assert response.status_code == 200
    leaderboard = response.get_json()
    assert leaderboard == []

def test_get_leaderboard_populated(client, temp_leaderboard):
    # Populate the leaderboard directly for this test
    scores = [
        {"name": "PlayerA", "score": 150},
        {"name": "PlayerB", "score": 200},
        {"name": "PlayerC", "score": 100}
    ]
    # The app's save_leaderboard function sorts and limits.
    # We can simulate this by calling the submit_score endpoint or by manually writing
    # to the temp_leaderboard file respecting the app's logic.
    # For simplicity, let's use the submit_score endpoint as it uses the app's logic.
    client.post('/api/submit_score', json={"name": "PlayerA", "score": 150})
    client.post('/api/submit_score', json={"name": "PlayerB", "score": 200})
    client.post('/api/submit_score', json={"name": "PlayerC", "score": 100})

    response = client.get('/api/get_leaderboard')
    assert response.status_code == 200
    leaderboard = response.get_json()
    
    assert len(leaderboard) == 3
    assert leaderboard[0]["name"] == "PlayerB"
    assert leaderboard[0]["score"] == 200
    assert leaderboard[1]["name"] == "PlayerA"
    assert leaderboard[1]["score"] == 150
    assert leaderboard[2]["name"] == "PlayerC"
    assert leaderboard[2]["score"] == 100

def test_get_leaderboard_respects_max_size(client, temp_leaderboard):
    # LEADERBOARD_MAX_SIZE is 10
    for i in range(12): # Submit 12 scores
        client.post('/api/submit_score', json={"name": f"User{i}", "score": (i+1)*10})
    
    response = client.get('/api/get_leaderboard')
    assert response.status_code == 200
    leaderboard = response.get_json()
    
    assert len(leaderboard) == 10 # Should be limited
    assert leaderboard[0]["score"] == 120 # Highest score
    assert leaderboard[9]["score"] == 30 # 10th highest score
