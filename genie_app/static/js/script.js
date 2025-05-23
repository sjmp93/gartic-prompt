document.addEventListener('DOMContentLoaded', () => {
    const gameImage = document.getElementById('gameImage');
    const guessInput = document.getElementById('guessInput');
    const submitGuessButton = document.getElementById('submitGuess');
    const scoreDisplay = document.getElementById('scoreDisplay');
    const turnsDisplay = document.getElementById('turnsDisplay');
    const messageArea = document.getElementById('messageArea');
    // Leaderboard and Game Over elements
    const gameOverSection = document.getElementById('gameOverSection');
    const finalScoreDisplay = document.getElementById('finalScoreDisplay');
    const playerNameInput = document.getElementById('playerName');
    const submitScoreButton = document.getElementById('submitScoreButton');
    const submitMessageArea = document.getElementById('submitMessageArea');
    const leaderboardList = document.getElementById('leaderboardList');

    let currentImageId = null;
    let score = 0;
    let turns = 7;

    function updateScore(newScore) {
        score = newScore;
        scoreDisplay.textContent = score;
    }

    function updateTurns(turnsLeft) {
        turns = turnsLeft;
        turnsDisplay.textContent = turns;
    }

    function showMessage(message, type = 'info') {
        messageArea.textContent = message;
        messageArea.className = 'message-area'; // Reset classes
        if (type === 'success') {
            messageArea.classList.add('message-correct');
        } else if (type === 'error') {
            messageArea.classList.add('message-incorrect');
        } else {
            messageArea.classList.add('message-info');
        }
    }

    function showSubmitMessage(message, type = 'info') {
        submitMessageArea.textContent = message;
        submitMessageArea.className = 'submit-message-area'; // Reset classes
        if (type === 'success') {
            submitMessageArea.classList.add('message-correct');
        } else if (type === 'error') {
            submitMessageArea.classList.add('message-incorrect');
        } else {
            submitMessageArea.classList.add('message-info');
        }
    }


    async function fetchImage() {
        try {
            const response = await fetch('/api/get_image_data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.error) {
                showMessage(`Error: ${data.error}`, 'error');
                return;
            }
            gameImage.src = data.path; // Path is already correct e.g. "static/images/placeholder1.jpg"
            currentImageId = data.id;
            guessInput.value = ''; // Clear previous guess
            showMessage('', 'info'); // Clear previous messages, set to info
            guessInput.disabled = false;
            submitGuessButton.disabled = false;
        } catch (error) {
            showMessage(`Failed to fetch image: ${error.message}`, 'error');
            console.error('Fetch image error:', error);
        }
    }

    async function submitGuessHandler() {
        if (turns <= 0) return;

        const userGuess = guessInput.value.trim();
        if (!userGuess) {
            showMessage("Please enter a guess.", 'error');
            return;
        }
        if (!currentImageId) {
            showMessage("No image loaded to guess for. Please wait or refresh.", 'error');
            return;
        }

        guessInput.disabled = true;
        submitGuessButton.disabled = true;
        showMessage("Submitting...", 'info');

        try {
            const response = await fetch('/api/submit_guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_id: currentImageId,
                    user_guess: userGuess,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();

            if (result.error) {
                showMessage(`Error: ${result.error}`, 'error');
                guessInput.disabled = false; // Re-enable on error
                submitGuessButton.disabled = false;
                return;
            }

            updateScore(score + result.score);
            updateTurns(turns - 1);

            if (result.correct) {
                showMessage("Correct!", 'success');
            } else {
                showMessage(`Incorrect (Score: ${result.score}). The prompt was: "${result.correct_prompt}"`, 'error');
            }

            if (turns <= 0) {
                gameOver();
            } else {
                // Fetch the next image for the next turn
                setTimeout(fetchImage, 2000); // Wait 2 seconds before fetching next image
            }

        } catch (error) {
            showMessage(`Failed to submit guess: ${error.message}`, 'error');
            console.error('Submit guess error:', error);
            guessInput.disabled = false; // Re-enable on error
            submitGuessButton.disabled = false;
        }
    }

    function gameOver() {
        // Main messageArea is hidden in CSS when gameOverSection is visible,
        // so we use submitMessageArea for the "Game Over!" message.
        showSubmitMessage(`Game Over! Final Score: ${score}`, 'info'); 
        finalScoreDisplay.textContent = score; 
        gameOverSection.style.display = 'flex'; // Use flex as per CSS
        guessInput.style.display = 'none'; 
        submitGuessButton.style.display = 'none'; 
        messageArea.style.display = 'none'; 
    }

    async function submitScoreHandler() {
        const playerName = playerNameInput.value.trim();
        if (!playerName) {
            showSubmitMessage("Please enter your name.", 'error');
            return;
        }

        submitScoreButton.disabled = true;
        playerNameInput.disabled = true;
        showSubmitMessage("Submitting score...", 'info');

        try {
            const response = await fetch('/api/submit_score', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: playerName, score: score }),
            });

            const result = await response.json(); 

            if (!response.ok) {
                showSubmitMessage(`Error: ${result.error || 'Failed to submit score'}`, 'error');
                console.error("Submit score error:", result);
                submitScoreButton.disabled = false; 
                playerNameInput.disabled = false;  
                return;
            }
            
            showSubmitMessage("Score submitted successfully!", 'success');
            fetchLeaderboard(); 
            // Keep button and input disabled to prevent resubmission
        } catch (error) {
            showSubmitMessage(`Error: ${error.message}`, 'error');
            console.error('Submit score exception:', error);
            submitScoreButton.disabled = false; 
            playerNameInput.disabled = false;  
        }
    }

    async function fetchLeaderboard() {
        try {
            const response = await fetch('/api/get_leaderboard');
            if (!response.ok) {
                console.error(`HTTP error! status: ${response.status}`);
                leaderboardList.innerHTML = '<li>Failed to load leaderboard.</li>';
                return;
            }
            const leaderboard = await response.json();
            
            leaderboardList.innerHTML = ''; // Clear existing entries
            if (leaderboard.length === 0) {
                leaderboardList.innerHTML = '<li>No scores yet. Be the first!</li>';
            } else {
                leaderboard.forEach(entry => {
                    const li = document.createElement('li');
                    li.textContent = `${entry.name}: ${entry.score}`;
                    leaderboardList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Fetch leaderboard error:', error);
            leaderboardList.innerHTML = '<li>Error loading leaderboard.</li>';
        }
    }

    function resetGameUI() {
        updateScore(0);
        updateTurns(7);
        
        guessInput.style.display = 'inline-block';
        submitGuessButton.style.display = 'inline-block';
        messageArea.style.display = 'block';
        
        gameOverSection.style.display = 'none';
        playerNameInput.value = '';
        playerNameInput.disabled = false;
        submitScoreButton.disabled = false;
        showSubmitMessage('', 'info'); // Clear submit message area
        
        fetchImage(); // This will also clear the main messageArea
    }


    // Initial game setup
    resetGameUI(); 
    fetchLeaderboard(); 

    submitGuessButton.addEventListener('click', submitGuessHandler);
    submitScoreButton.addEventListener('click', submitScoreHandler); // Listener for new button
    guessInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            submitGuessHandler();
        }
    });
});
