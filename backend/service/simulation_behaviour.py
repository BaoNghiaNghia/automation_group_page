import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.utils.index import get_all_game_fanpages
from backend.constants import FB_DEFAULT_URL, FB_DEFAULT_URL, SHARE_COMMENT_IN_POST, logger


# =========================
# Utility helpers
# =========================

def random_sleep(a, b):
    time.sleep(random.uniform(a, b))


def scroll_window(browser, min_px=200, max_px=800):
    browser.execute_script(f"window.scrollBy(0, {random.randint(min_px, max_px)});")


# =========================
# SHARE LOGIC
# =========================

def maybe_share_post(browser):
    if random.random() > 0.1:
        return

    try:
        share_buttons = browser.find_elements(
            By.XPATH,
            "//div[@aria-label='Share' or contains(@aria-label, 'share')]"
        )

        if not share_buttons:
            return

        btn = random.choice(share_buttons)
        browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", btn
        )
        random_sleep(0.8, 1.5)
        btn.click()
        random_sleep(2, 3)

        handle_share_dialog(browser)

    except Exception:
        pass


def handle_share_dialog(browser):
    try:
        dialog = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
        )

        try:
            textbox = dialog.find_element(
                By.XPATH,
                ".//div[@contenteditable='true' or @role='textbox']"
            )

            text = random.choice(SHARE_COMMENT_IN_POST)
            for c in text:
                textbox.send_keys(c)
                time.sleep(random.uniform(0.05, 0.15))

        except Exception:
            pass

        share_btn = dialog.find_element(
            By.XPATH,
            ".//div[@role='button' and (contains(text(),'Share') or contains(text(),'Post'))]"
        )
        share_btn.click()

        WebDriverWait(browser, 10).until_not(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
        )

    except Exception:
        ActionChains(browser).send_keys(Keys.ESCAPE).perform()


# =========================
# REACTION LOGIC
# =========================

def maybe_react(browser):
    if random.random() > 0.4:
        return

    try:
        buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Like']")
        if not buttons:
            return

        btn = random.choice(buttons)
        ActionChains(browser).move_to_element(btn).perform()
        random_sleep(1, 2)

        if random.random() < 0.5:
            btn.click()
            random_sleep(2, 4)

    except Exception:
        pass


# =========================
# VIDEO LOGIC
# =========================

def maybe_watch_video(browser):
    if random.random() > 0.15:
        return

    try:
        videos = browser.find_elements(
            By.XPATH,
            "//a[contains(@href,'/watch/')]"
        )
        if not videos:
            return

        vid = random.choice(videos)
        browser.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", vid
        )
        random_sleep(1, 2)
        vid.click()

        random_sleep(15, 45)
        browser.back()
        random_sleep(2, 4)

    except Exception:
        pass


# =========================
# SEARCH LOGIC
# =========================

def maybe_search(browser, group_search_names):
    if random.random() > 0.4:
        return

    try:
        search_box = browser.find_element(
            By.XPATH, "//input[@placeholder='Search Facebook']"
        )

        queries = [
            "mobile game tips",
            "game strategies",
            "new game releases",
        ] + group_search_names

        query = random.choice(queries)

        search_box.click()
        search_box.clear()

        for c in query:
            search_box.send_keys(c)
            time.sleep(random.uniform(0.05, 0.25))

        search_box.send_keys(Keys.ENTER)
        random_sleep(5, 10)

    except Exception:
        pass


# =========================
# MAIN FUNCTION
# =========================

def simulate_human_behavior_when_scraping_game(browser, environment):
    logger.info("Start human simulation")

    game_fanpages = get_all_game_fanpages(environment, {"page": 1, "limit": 300})
    group_search_names = [
        g["group_search_name"]
        for g in game_fanpages
        if "group_search_name" in g
    ]

    # -------- WATCH --------
    browser.get(f"{FB_DEFAULT_URL}/watch")

    start = time.time()
    duration = random.randint(150, 210)

    while time.time() - start < duration:
        scroll_window(browser)
        random_sleep(2, 5)

        maybe_share_post(browser)
        maybe_react(browser)
        maybe_watch_video(browser)

    # -------- HOME --------
    browser.get(FB_DEFAULT_URL)

    start = time.time()
    duration = random.randint(160, 230)

    while time.time() - start < duration:
        scroll_window(browser)
        random_sleep(2, 6)

        maybe_share_post(browser)
        maybe_react(browser)
        maybe_search(browser, group_search_names)

    logger.info("Human simulation completed")



def simulate_scrolling_behavior_when_init_facebook(browser):
    """
    Simulates natural human scrolling behavior in the browser
    
    Args:
        browser (webdriver.Chrome): The browser instance used for Selenium automation
        
    Returns:
        float: The final pause time in seconds
    """
    try:
        # Use more natural scrolling patterns with variable speeds and distances
        scroll_duration = random.randint(180, 240)
        start_time = time.time()
        
        while time.time() - start_time < scroll_duration:
            # Natural scrolling with acceleration and deceleration
            scroll_pattern = random.choice(["smooth", "quick", "pause_heavy"])
            
            if scroll_pattern == "smooth":
                # Smooth scrolling with gradual acceleration
                for i in range(3, 8):
                    scroll_amount = i * 100  # Gradually increasing scroll amount
                    browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    time.sleep(random.uniform(0.3, 0.7))
            elif scroll_pattern == "quick":
                # Quick scroll followed by pause (like finding something interesting)
                scroll_amount = random.randint(500, 1200)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
            else:  # pause_heavy
                # Small scroll with longer pause (like reading content)
                scroll_amount = random.randint(200, 400)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            # Variable pauses between scrolling actions
            if random.random() < 0.7:  # 70% chance for normal pause
                time.sleep(random.uniform(2.0, 5.5))
            else:  # 30% chance for longer engagement
                engagement_time = random.uniform(9.0, 17.0)
                logger.info(f"Engaging with content for {engagement_time:.1f} seconds...")
                time.sleep(engagement_time)
                
                # Simulate reactions during longer engagement (like, comment hover)
                if random.random() < 0.4:  # 40% chance to interact
                    try:
                        reaction_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Like' or @aria-label='React' or contains(@aria-label, 'reaction')]")
                        if reaction_buttons:
                            button = random.choice(reaction_buttons)
                            # Hover over but don't click (just showing interest)
                            ActionChains(browser).move_to_element(button).perform()
                            logger.info("Hovering over reaction button")
                            time.sleep(random.uniform(1.0, 2.5))
                    except Exception as e:
                        logger.debug(f"Failed to simulate reaction")
                        
            # SHARE A POST
            if random.random() < 0.1:
                try:
                    logger.info("Attempting to share a post...")
                    # Find share buttons using multiple possible selectors
                    share_buttons = browser.find_elements(By.XPATH, 
                        "//div[@aria-label='Share' or contains(@aria-label, 'share') or contains(@role, 'button')][.//span[text()='Share' or contains(text(), 'Share')]]")
                    
                    if share_buttons:
                        share_button = random.choice(share_buttons)
                        # Scroll to make the share button visible
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", share_button)
                        time.sleep(random.uniform(0.8, 1.5))
                        
                        # Click the share button
                        share_button.click()
                        logger.info("Clicked share button")
                        time.sleep(random.uniform(2.0, 3.5))
                        
                        # Handle the share dialog
                        try:
                            # First try to add some text to the share
                            try:
                                # Look for text input field in the share dialog
                                text_input = WebDriverWait(browser, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@contenteditable='true' or @role='textbox']"))
                                )
                                
                                share_text = random.choice(SHARE_COMMENT_IN_POST)
                                
                                # Type the text with human-like timing
                                for char in share_text:
                                    text_input.send_keys(char)
                                    time.sleep(random.uniform(0.05, 0.15))  # Realistic typing speed
                                
                                logger.info(f"Added text to share: '{share_text}'")
                                time.sleep(random.uniform(1.0, 2.0))
                            except Exception as text_error:
                                logger.info(f"Could not add text to share: {str(text_error)}")
                            
                            # Look for "Share now" or similar option
                            share_options = WebDriverWait(browser, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@aria-label='Share now' and @role='button'] | //div[@role='dialog']//div[text()='Share now' or contains(text(), 'Share now') or text()='Post' or contains(text(), 'Share')]"))
                            )
                            
                            share_options.click()
                            logger.info("Shared post with text")
                            
                            # Wait until share action is completed
                            time.sleep(random.uniform(5.0, 8.0))
                            
                            # Look for confirmation elements that indicate sharing is complete
                            try:
                                WebDriverWait(browser, 10).until_not(
                                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
                                )
                                logger.info("Share dialog closed, sharing completed")
                            except Exception as wait_error:
                                logger.info(f"Waiting for share completion: {str(wait_error)}")
                                time.sleep(random.uniform(3.0, 5.0))  # Additional wait time
                        except Exception as e:
                            logger.info(f"Could not complete share action: {str(e)}")
                            # Try to close the share dialog
                            try:
                                close_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Close' or @role='button'][.//i]")
                                if close_buttons:
                                    close_buttons[0].click()
                                    logger.info("Closed share dialog")
                                    time.sleep(random.uniform(1.0, 2.0))
                                else:
                                    # Try to press Escape key to close any open dialogs
                                    ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(1.0)
                            except Exception as close_error:
                                logger.info(f"Could not close share dialog: {str(close_error)}")
                                # Try to press Escape key as a last resort
                                try:
                                    ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(1.0)
                                except:
                                    pass
                    else:
                        logger.info("No share buttons found")
                except Exception as share_error:
                    logger.info(f"Error while attempting to share post: {str(share_error)}")
                        
            # Decide whether to hover over reactions
            if random.random() < 0.5:
                emotions = ["like", "love", "care", "haha", "wow", "sad", "angry"]
                selected_emotion = random.choice(emotions)
                logger.info(f"Considering reaction: {selected_emotion}")
                
                try:
                    # Different XPaths for different emotions
                    emotion_xpath_map = {
                        "like": "//div[@role='button' and @aria-label='Like']",
                        "love": "//div[@role='button' and @aria-label='Love']",
                        "care": "//div[@role='button' and @aria-label='Care']",
                        "haha": "//div[@role='button' and @aria-label='Haha']",
                        "wow": "//div[@role='button' and @aria-label='Wow']",
                        "sad": "//div[@role='button' and @aria-label='Sad']",
                        "angry": "//div[@role='button' and @aria-label='Angry']"
                    }
                    
                    # Find Like buttons
                    like_buttons = browser.find_elements(By.XPATH, "//div[@aria-label='Like' or @aria-label='React' or contains(@aria-label, 'reaction')]")
                    if like_buttons:
                        # Select a random Like button
                        like_button = random.choice(like_buttons)
                        
                        # First hover over the Like button
                        ActionChains(browser).move_to_element(like_button).perform()
                        logger.info("Hovering over Like button")
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Wait for reaction panel to appear
                        try:
                            logger.info("Reaction panel appeared")
                            time.sleep(random.uniform(0.5, 1.0))  # Short pause after panel appears
                            
                            # Try to find the specific emotion using multiple possible selectors
                            try:
                                # Try different approaches to find the emotion element
                                emotion_xpaths = [
                                    emotion_xpath_map[selected_emotion],  # Original xpath
                                    f"//div[@aria-label='{selected_emotion.capitalize()}']",  # Alternative format
                                    f"//div[contains(@aria-label, '{selected_emotion}')]",  # Partial match
                                    f"//div[@data-reaction-type='{selected_emotion}']"  # Data attribute
                                ]
                                
                                # Try each xpath until one works
                                emotion_element = None
                                for xpath in emotion_xpaths:
                                    try:
                                        emotion_element = WebDriverWait(browser, 1).until(
                                            EC.presence_of_element_located((By.XPATH, xpath))
                                        )
                                        if emotion_element:
                                            break
                                    except:
                                        continue
                                
                                if emotion_element:
                                    # Move to the emotion and click it
                                    ActionChains(browser).move_to_element(emotion_element).perform()
                                    logger.info(f"Hovering over {selected_emotion} reaction")
                                    
                                    # Variable wait time before clicking
                                    time.sleep(random.uniform(0.5, 1.5))
                                    
                                    # Click the emotion element
                                    emotion_element.click()
                                    logger.info(f"Clicked on {selected_emotion} reaction")
                                    
                                    # Wait after clicking to ensure the reaction is registered
                                    time.sleep(random.uniform(2.0, 4.0))
                                    
                                    # Verify the reaction was registered before continuing
                                    try:
                                        # Look for confirmation that reaction was applied
                                        WebDriverWait(browser, 3).until(
                                            EC.presence_of_element_located((By.XPATH, f"//div[contains(@aria-label, '{selected_emotion}') and contains(@aria-label, 'ed')]"))
                                        )
                                        logger.info(f"Confirmed {selected_emotion} reaction was registered")
                                    except Exception as e:
                                        logger.debug(f"Could not confirm reaction was registered")
                                        # Additional wait to ensure reaction processing
                                        time.sleep(random.uniform(1.0, 2.0))
                                    
                                    # Continue only after ensuring reaction was processed
                                    continue
                                else:
                                    logger.debug(f"Could not find {selected_emotion} reaction with any selector")
                                
                                # Move away from the reaction panel without clicking
                                ActionChains(browser).move_by_offset(200, 200).perform()
                                logger.info("Moving away from reaction panel")
                            except Exception as e:
                                logger.debug(f"Could not find or interact with emotion element")
                                # Move away to close the reaction panel
                                ActionChains(browser).move_by_offset(200, 200).perform()
                        except Exception as e:
                            logger.debug(f"Reaction panel did not appear or could not be interacted with")
                            # Try to move mouse away anyway to ensure we don't get stuck
                            ActionChains(browser).move_by_offset(200, 200).perform()
                except Exception as e:
                    logger.debug(f"Failed to interact with reactions")
        
        # Occasionally navigate to a different section before returning to main task
        if random.random() < 0.3:  # 30% chance
            try:
                sections = ["watch", "marketplace", "groups"]
                section = random.choice(sections)
                logger.info(f"Briefly visiting {section} section...")
                browser.get(f"{FB_DEFAULT_URL}/{section}")
                time.sleep(random.uniform(5.0, 10.0))
                browser.get(FB_DEFAULT_URL)  # Return to homepage
            except Exception as e:
                logger.debug(f"Failed to visit section")
        
        # Final pause before starting the actual scraping
        final_pause = random.uniform(5, 8)
        logger.info(f"Finished human-like browsing behavior, pausing for {final_pause:.1f} seconds before scraping...")
        return final_pause
    except Exception as e:
        logger.error(f"Error during scrolling behavior simulation")
        return random.uniform(3, 5)  # Fallback pause time

