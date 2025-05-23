# Genie GuessR - AI Image Prompt Game

## Overview
Genie GuessR is an interactive web game where players are shown an AI-generated-style image and must guess the prompt that could have created it. The game tests your creativity and understanding of how AI image generation prompts work. Players aim for a high score by matching their guess as closely as possible to the actual prompt.

## Features
*   Guess the prompt for unique AI-themed images.
*   Engaging gameplay with 7 turns per game.
*   Advanced scoring system based on Levenshtein distance to measure guess accuracy.
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
