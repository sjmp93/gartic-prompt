import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager # Alternative for driver management
import threading
import time
import requests # For a cleaner shutdown, if implemented
from genie_app.app import app as flask_app
import socket

# Flag to control Flask app thread
flask_thread = None
# Using a global for the app instance to allow shutdown.
# In a more complex setup, you might pass the app instance around or use a class.
server_props = {'app_instance': None, 'thread': None}


def run_flask_app():
    # The app.run host must be 127.0.0.1 for Selenium to access it
    # Using a specific port for E2E tests to avoid conflict if main app is running.
    # However, the prompt implies using 5000, so we'll stick to that.
    # For robust shutdown, Flask app needs a shutdown route.
    # Adding a simple one here for test purposes.
    @flask_app.route('/shutdown_test_server', methods=['POST'])
    def shutdown_test_server():
        print("Shutdown signal received...")
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            print('Werkzeug server not running or shutdown function not available.')
            return 'Not a Werkzeug server.'
        func()
        return 'Server shutting down...'

    print("Starting Flask app for E2E tests on 127.0.0.1:5000...")
    try:
        flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask app failed to start or run: {e}")
    finally:
        print("Flask app for E2E tests has stopped.")

@pytest.fixture(scope="session", autouse=True)
def start_flask_server_session(request):
    # Check if Flask app is already running on port 5000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()

    if result == 0: # Port is already in use
        print("Port 5000 is already in use. Assuming external server or previous run.")
        yield
        return # Do not attempt to start/stop if already running

    print("Setting up Flask server for E2E session...")
    server_props['thread'] = threading.Thread(target=run_flask_app, daemon=True)
    server_props['thread'].start()
    time.sleep(3) # Give the server a moment to start

    def fin():
        print("Tearing down Flask server for E2E session...")
        try:
            # Attempt graceful shutdown
            requests.post('http://127.0.0.1:5000/shutdown_test_server', timeout=1)
            server_props['thread'].join(timeout=5) # Wait for thread to finish
            if server_props['thread'].is_alive():
                print("Flask app thread did not shut down gracefully.")
        except Exception as e:
            print(f"Error shutting down Flask app: {e}. Relying on daemon thread exit.")
        
    request.addfinalizer(fin)
    yield


@pytest.fixture(scope="function")
def browser():
    # IMPORTANT: ChromeDriver must be installed and in the system's PATH,
    # or use ChromeDriverManager or specify service path.
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Example for explicit path (uncomment and modify if needed):
        # service = ChromeService(executable_path='/usr/local/bin/chromedriver') 
        # driver = webdriver.Chrome(service=service, options=options)
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        pytest.skip(f"Skipping E2E tests: WebDriver setup failed. Error: {e} "
                    "Ensure ChromeDriver is installed and in PATH, or path is specified in test_e2e.py.")
    
    yield driver
    if driver:
        driver.quit()

def test_load_page_and_submit_guess(browser):
    try:
        browser.get("http://127.0.0.1:5000/")
    except Exception as e:
        pytest.fail(f"Failed to load page http://127.0.0.1:5000/. Error: {e}")

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    # Check title or a prominent header
    page_title = browser.title
    header_text = browser.find_element(By.TAG_NAME, "h1").text
    assert "Genie GuessR" in page_title or "Genie GuessR" in header_text, \
        f"Page title was '{page_title}' and header was '{header_text}'"


    # Check for initial image (ID: game-image)
    image_element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "game-image"))
    )
    assert image_element.get_attribute("src") != "", "Image source is empty."
    assert "placeholder" in image_element.get_attribute("src"), "Initial image src doesn't seem to be a placeholder."


    guess_input = browser.find_element(By.ID, "guess-input")
    # Assuming the button ID is 'submit-guess-button'
    submit_button = browser.find_element(By.ID, "submit-guess-button")
    
    # Assuming turn counter has ID 'turns-left' and score 'score-value'
    initial_turns_left_text = browser.find_element(By.ID, "turns-left").text
    assert "7" in initial_turns_left_text, f"Initial turns left was '{initial_turns_left_text}'"

    guess_input.send_keys("a test guess")
    submit_button.click()

    # Wait for score to update. Assuming score is in an element with ID 'score-value'
    # And it's not the initial "0" or placeholder.
    WebDriverWait(browser, 10).until(
        EC.text_to_be_present_in_element_value((By.ID, "score-value"), "") # Wait for score to not be empty or 0
    )
    # More robust: wait until the score is NOT the initial score.
    # This implies we need to know the initial score text. Let's assume it's "0".
    WebDriverWait(browser, 10).until(
        lambda d: d.find_element(By.ID, "score-value").text != "0"
    )
    score_value_text = browser.find_element(By.ID, "score-value").text
    assert score_value_text.isdigit(), f"Score value '{score_value_text}' is not a digit."
    assert int(score_value_text) >= 0, f"Score value '{score_value_text}' is not >= 0."

    # Check if turns updated
    WebDriverWait(browser, 10).until(
        lambda d: d.find_element(By.ID, "turns-left").text != initial_turns_left_text
    )
    current_turns_left_text = browser.find_element(By.ID, "turns-left").text
    assert "6" in current_turns_left_text, f"Turns left was '{current_turns_left_text}', expected 6."

    # (Optional: test_play_few_turns can be added here if time permits)
    # Example of playing one more turn:
    # initial_image_src = image_element.get_attribute("src")
    # guess_input.clear()
    # guess_input.send_keys("another guess")
    # submit_button.click()
    # WebDriverWait(browser, 10).until(
    #     lambda d: d.find_element(By.ID, "game-image").get_attribute("src") != initial_image_src
    # )
    # WebDriverWait(browser, 10).until(
    #     lambda d: "5" in d.find_element(By.ID, "turns-left").text
    # )
    # assert "5" in browser.find_element(By.ID, "turns-left").text
    # new_score_value_text = browser.find_element(By.ID, "score-value").text
    # assert new_score_value_text.isdigit()
    # assert int(new_score_value_text) >= 0
    # print(f"Score after 2nd guess: {new_score_value_text}")
```
