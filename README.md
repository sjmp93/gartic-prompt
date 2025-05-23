# Genie GuessR - AI Image Prompt Game

## Overview
Genie GuessR is an interactive web game where players are shown an AI-generated-style image and must guess the prompt that could have created it. The game tests your creativity and understanding of how AI image generation prompts work. Players aim for a high score by matching their guess as closely as possible to the actual prompt.

## Features
*   Guess the prompt for unique AI-themed images.
*   Engaging gameplay with 7 turns per game.
*   Advanced scoring system using Levenshtein distance, with an optional enhancement via a local Sentence Transformer model for semantic similarity.
*   Optional LLM-powered semantic scoring: If enabled, uses a sentence transformer model to provide a more nuanced understanding of prompt similarity, complementing the Levenshtein score.
*   Persistent leaderboard to track top players.
*   Clean, responsive user interface.

## How to Play
1.  A random AI-generated-style image is displayed on the screen.
2.  Enter your guess for the prompt that you think generated the image in the text box.
3.  Submit your guess. You'll receive a score from 0 to 100 based on how similar your guess is to the actual prompt. A perfect match (score 100) is considered "Correct!".
4.  You have 7 turns to guess prompts for different images.
5.  After 7 turns, your game ends, and you can submit your total score to the leaderboard.
6.  Try to get the highest score and make your mark on the leaderboard!

## Local Setup and Installation

### Prerequisites
*   Python 3.7 or newer
*   pip (Python package installer)

### Steps
1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder-name>
    ```

2.  **Create and activate a virtual environment:**

    *   **Unix-like systems (Linux, macOS):**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

    *   **Windows (Command Prompt/PowerShell):**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python genie_app/app.py
    ```

5.  **Open your browser:**
    Navigate to `http://127.0.0.1:5000/`.

### LLM Scoring (Optional)

This application supports an optional, more advanced scoring mechanism using a locally-run Sentence Transformer model (a type of Large Language Model or LLM) to assess semantic similarity between your guess and the actual prompt. This can provide a more nuanced score than Levenshtein distance alone, as it understands the meaning of the words rather than just character-level differences.

**How it Works:**
When enabled, the application loads a specified Sentence Transformer model. Upon submitting a guess, this model generates embeddings (numerical representations) for both your guess and the target prompt. The cosine similarity between these embeddings is calculated, resulting in a score from 0 to 100. This "LLM score" is then averaged with the traditional Levenshtein distance score to produce the final score for your guess.

**Configuration via Environment Variables:**

*   **`ENABLE_LLM_SCORING`**:
    *   Set to `true` to activate LLM-based semantic scoring.
    *   Defaults to `false` (LLM scoring disabled).
    *   Example: `export ENABLE_LLM_SCORING=true`

*   **`LLM_MODEL_NAME`**:
    *   Specifies the Sentence Transformer model to be used.
    *   Defaults to `paraphrase-multilingual-MiniLM-L12-v2`.
    *   You can choose other pre-trained models from the `sentence-transformers` library that are suitable for semantic similarity tasks (e.g., `all-MiniLM-L6-v2`, `stsb-roberta-base`).
    *   Example: `export LLM_MODEL_NAME=all-MiniLM-L6-v2`

**Important Note on Model Downloading:**
When LLM scoring is enabled for the first time (or if the `LLM_MODEL_NAME` is changed), the application will download the specified sentence transformer model. This is a one-time process per model and may take a few minutes depending on your internet connection and the model size. The model files will be cached locally by the `sentence-transformers` library (typically in your user's `~/.cache/torch/sentence_transformers` directory if running locally, or within the Docker container's corresponding cache path if using Docker).

**Impact on Scoring and API Response:**
*   **Final Score**: If LLM scoring is active and successful, the final score reported to the user is an average of the Levenshtein score and the LLM-derived semantic similarity score.
*   **API Response**: The JSON response from the `/api/submit_guess` endpoint will include additional fields when LLM scoring is active:
    *   `llm_score`: The semantic similarity score (0-100) from the LLM.
    *   `levenshtein_score`: The original Levenshtein distance score (0-100).
    *   `score`: The final combined score.

## Detailed Documentation
For more details on project structure and API, see [genie_app/docs.md](genie_app/docs.md).

## Running with Docker (Recommended for Development)

If you have Docker and Docker Compose installed, you can easily run the application in a containerized environment.

**Prerequisites:**
- Docker (refer to [Docker's official website](https://docs.docker.com/get-docker/) for installation instructions)
- Docker Compose (usually included with Docker Desktop, or see [Docker's documentation](https://docs.docker.com/compose/install/) for installation)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Ensure `leaderboard.json` exists:**
    The Docker Compose setup mounts the local `leaderboard.json` file. If it doesn't exist, create an empty one:
    ```bash
    echo "[]" > leaderboard.json
    ```
    (This step might have already been done if you followed previous Docker setup, but it's good to reiterate for users who jump straight to Docker.)
3.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up
    ```
    To rebuild the image if you've made changes to `Dockerfile` or `requirements.txt`, use:
    ```bash
    docker-compose up --build
    ```
4.  **Access the application:**
    Open your web browser and navigate to `http://localhost:5000`.

This setup uses volumes to map your local `genie_app` code into the container, so changes you make to the Python code should be reflected live (due to Flask's debug mode). For changes to `requirements.txt` or the `Dockerfile` itself, you'll need to rebuild the image.

**Configuring LLM Scoring with Docker:**

To enable or configure LLM scoring when running with Docker, you can set the environment variables in your `docker-compose.yml` file.

Example `docker-compose.yml` `web` service definition:
```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./genie_app:/app/genie_app
      - ./leaderboard.json:/app/leaderboard.json 
    environment:
      - FLASK_DEBUG=1 # Already present, for development
      - ENABLE_LLM_SCORING=true # Set to true to enable LLM scoring
      - LLM_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2 # Optional: change if you want a different model
```
After modifying `docker-compose.yml`, rebuild and restart your containers if they are already running:
```bash
docker-compose up --build
```

If you are running the Docker container directly using `docker run` (without Docker Compose), you can pass environment variables using the `-e` flag:
```bash
docker run -p 5000:5000 \
  -v $(pwd)/genie_app:/app/genie_app \
  -v $(pwd)/leaderboard.json:/app/leaderboard.json \
  -e ENABLE_LLM_SCORING=true \
  -e LLM_MODEL_NAME=all-MiniLM-L6-v2 \
  your_image_name_here 
```
Remember to replace `your_image_name_here` with the actual name of your built Docker image.

## Production/Staging Deployment

For deploying Genie GuessR to a production or staging environment, it's crucial to use a production-grade WSGI server instead of Flask's built-in development server. The development server is not designed for the performance, security, and stability requirements of a live application.

**Recommended WSGI Server: Gunicorn**

Gunicorn ('Green Unicorn') is a popular Python WSGI HTTP server for UNIX.

**Example Gunicorn command:**
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 "genie_app.app:app"
```
*   `--workers 4`: Adjust the number of worker processes based on your server's CPU cores. A common starting point is `(2 * number_of_cores) + 1`.
*   `--bind 0.0.0.0:5000`: Replace `5000` with your desired port if needed. `0.0.0.0` makes the app accessible externally.
*   `"genie_app.app:app"`: This tells Gunicorn where to find your Flask application instance. It means "in the `genie_app.app` module, the Flask app is named `app`".

**Important: Disable Debug Mode**

Ensure that `DEBUG` is set to `False` in a production environment. The `app.run(debug=True)` line in `genie_app/app.py` is intended for local development only. When you use a WSGI server like Gunicorn, it takes over serving the application, and Flask's debug mode should be off. Your application code might have logic to set `DEBUG` based on an environment variable (e.g., `app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1'`).

**Docker Considerations for Production:**

*   **Code Deployment:** For production Docker images, it's best practice to `COPY` the application code into the image (as the current `Dockerfile` does with `COPY genie_app/ ./genie_app/`) rather than using source code volumes (e.g., `./genie_app:/app/genie_app` in `docker-compose.yml`). Volumes are great for development for live reloading but can introduce inconsistencies in production.
*   **Environment Variables:** Ensure that environment variables like `FLASK_DEBUG=0` (or ensuring it's not set to `1`) are configured for your production Docker environment. This can be done through your `docker-compose.prod.yml` file, Kubernetes manifests, or other deployment tools.

## Running Tests

This project uses [pytest](https://docs.pytest.org/) for automated unit testing.

### Prerequisites

1.  Ensure you have completed the local setup and installed dependencies as described in the "Local Setup and Installation" section (this includes creating a virtual environment and running `pip install -r requirements.txt`). `pytest` and `pytest-flask` should now be installed.

### Running Unit Tests

1.  **Activate your virtual environment** (if not already active):
    *   Unix-like systems (Linux, macOS): `source venv/bin/activate`
    *   Windows: `.\venv\Scripts\activate`

2.  **Navigate to the project root directory** (the directory containing `README.md` and the `tests/` folder).

3.  **Run pytest:**
    ```bash
    pytest
    ```
    Pytest will automatically discover and run all tests in the `tests` directory. You should see output indicating the number of tests passed.

    For more verbose output, you can use:
    ```bash
    pytest -v
    ```

    To run specific test files or tests:
    ```bash
    pytest tests/test_app.py  # Run all tests in test_app.py
    pytest tests/test_app.py::test_home_page  # Run a specific test function
    ```

### Running End-to-End (E2E) Tests

End-to-End (E2E) tests are designed to test the application flow from the user's perspective, interacting with the UI in a browser. This project uses Selenium with pytest for E2E testing.

**Prerequisites for E2E Tests:**

1.  **WebDriver Installation**:
    *   E2E tests require a WebDriver compatible with your browser. For Chrome, this is ChromeDriver.
    *   Download ChromeDriver from the [official site](https://chromedriver.chromium.org/downloads). Ensure the version matches your installed Chrome browser version.
    *   Place the `chromedriver` executable in a directory that is part of your system's `PATH` environment variable.
    *   Alternatively, you can modify `tests/test_e2e.py` to specify the path to `chromedriver` directly if you prefer not to add it to your PATH. The `test_e2e.py` file contains comments on how to do this.

2.  **Dependencies**:
    *   Ensure you have installed all project dependencies, including `selenium`, by running `pip install -r requirements.txt` within your activated virtual environment.

**Running E2E Tests:**

1.  **Activate your virtual environment** (if not already active):
    *   Unix-like systems (Linux, macOS): `source venv/bin/activate`
    *   Windows: `.\venv\Scripts\activate`

2.  **Navigate to the project root directory.**

3.  **Run the E2E tests using pytest:**
    ```bash
    pytest tests/test_e2e.py
    ```
    *   The E2E tests will automatically start a local instance of the Flask application on `http://127.0.0.1:5000/` for testing purposes and attempt to shut it down afterwards.
    *   If ChromeDriver is not found or there's a setup issue, the tests will be skipped with a message.
    *   You should see browser windows open and close (unless running in headless mode, which is the default configuration in `test_e2e.py`).

**Important Notes for E2E Tests:**

*   **Speed and Stability**: E2E tests interact with a live browser and application, so they are generally slower than unit tests. They can also be more prone to intermittent failures due to timing issues, network conditions, or environmental differences.
*   **Port Usage**: The tests run the Flask app on port 5000. Ensure this port is free before running E2E tests. The test setup attempts to detect if the port is in use, but manual verification might be needed if issues arise.
*   **Headless Mode**: By default, the E2E tests are configured to run Chrome in headless mode (no visible UI). You can change this in `tests/test_e2e.py` by modifying the Chrome options if you want to observe the browser interaction.
