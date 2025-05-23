# Detailed Documentation for Genie GuessR

## Project Structure
The Genie GuessR application is organized as follows:

*   `genie_app/`: Main application directory.
    *   `app.py`: The core Flask application. This file contains all the backend logic, including:
        *   Serving the main `index.html` page.
        *   Handling API requests for game data, guess submissions, and leaderboard management.
        *   Implementing game rules, such as scoring based on Levenshtein distance.
        *   Managing the `leaderboard.json` file.
    *   `index.html`: The single HTML page that serves as the main user interface for the game. It's located in this directory to be served directly by Flask.
    *   `static/`: Contains all static assets.
        *   `css/style.css`: Provides all the styling for the application, ensuring a responsive and visually appealing experience.
        *   `js/script.js`: Contains all client-side JavaScript. This script handles:
            *   Fetching game data from the backend.
            *   Submitting user guesses and scores.
            *   Updating the UI dynamically based on game state and API responses.
            *   Managing game turns and game over conditions.
        *   `images/`: Stores the placeholder images used in the game (e.g., `placeholder1.jpg`, `placeholder2.jpg`).
    *   `leaderboard.json`: A JSON file that stores player names and their scores. It's created and updated by `app.py`.
    *   `templates/`: (Currently unused) This directory is typically used for Flask templates if `render_template` was used more extensively. For this app, `index.html` is served directly from the `genie_app` directory.
    *   `docs.md`: This file, providing detailed documentation.
*   `README.md`: Located at the project root, this file provides an overview of the project, setup instructions, and how to play.
*   `requirements.txt`: Located at the project root, this file lists all necessary Python dependencies for the project.
*   `venv/`: (If created by the user following setup instructions) Directory for the Python virtual environment.

## API Endpoints
The application provides the following API endpoints:

### `/api/get_image_data`
*   **Method:** `GET`
*   **Description:** Fetches a random image path and its unique ID for the current game turn.
*   **Response Body (JSON):**
    ```json
    {
        "id": "img001",
        "path": "static/images/placeholder1.jpg"
    }
    ```
    *   `id`: A unique identifier for the image.
    *   `path`: The server-relative path to the image file.

### `/api/submit_guess`
*   **Method:** `POST`
*   **Description:** Submits a user's guess for a given image. The backend calculates the score based on the Levenshtein distance between the normalized user guess and the normalized correct prompt.
*   **Request Body (JSON):**
    ```json
    {
        "image_id": "img001",
        "user_guess": "A feline wearing a small hat"
    }
    ```
*   **Response Body (JSON):**
    ```json
    {
        "correct": false,
        "score": 85,
        "correct_prompt": "A cat wearing a tiny hat"
    }
    ```
    *   `correct`: A boolean indicating if the score was 100 (perfect match).
    *   `score`: An integer score from 0 to 100.
    *   `correct_prompt`: The actual prompt for the image.

### `/api/submit_score`
*   **Method:** `POST`
*   **Description:** Submits the player's name and their total score at the end of a game to be saved on the leaderboard. The leaderboard keeps the top 10 scores.
*   **Request Body (JSON):**
    ```json
    {
        "name": "PlayerOne",
        "score": 550
    }
    ```
*   **Response Body (JSON):**
    *   **Success (201 Created):**
        ```json
        {
            "message": "Score submitted successfully"
        }
        ```
    *   **Failure (e.g., 400 Bad Request for missing data):**
        ```json
        {
            "error": "Missing name or score"
        }
        ```

### `/api/get_leaderboard`
*   **Method:** `GET`
*   **Description:** Retrieves the top 10 scores from the leaderboard. Scores are sorted in descending order.
*   **Response Body (JSON):**
    ```json
    [
        {
            "name": "PlayerOne",
            "score": 550
        },
        {
            "name": "PlayerTwo",
            "score": 490
        }
    ]
    ```
    (The list will contain up to 10 entries, or be empty if no scores are submitted.)

## Future Enhancements
Potential future improvements for Genie GuessR include:

*   **User Image Uploads:** Allow users to upload their own AI-generated images and prompts. This would require a moderation system.
*   **Diverse Image Sets:** Integrate with APIs or databases to provide a wider and more dynamic range of images and prompts.
*   **User Accounts:** Implement user registration and login to track scores and game history per user.
*   **Difficulty Levels:** Introduce difficulty levels based on prompt complexity or image ambiguity.
*   **Hints System:** Provide optional hints for players who are stuck.
*   **Themed Rounds:** Offer themed rounds (e.g., "fantasy creatures," "sci-fi landscapes") for specialized guessing challenges.
*   **Real-time Multiplayer:** Allow multiple players to compete simultaneously.
