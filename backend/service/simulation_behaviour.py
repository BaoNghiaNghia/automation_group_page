import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from backend.utils.index import get_all_game_fanpages
from backend.constants import FB_DEFAULT_URL, FB_DEFAULT_URL, SHARE_COMMENT_IN_POST, logger

def simulate_human_behavior_when_scraping_game(browser, environment):
    try:
        logger.info("Simulating human behavior...")

        game_fanpages = get_all_game_fanpages(environment, {
            "page": 1,
            "limit": 300
        })
        if not game_fanpages:
            logger.error("No game URLs found from get_game_fanpages_unique")
            raise Exception("No game URLs found from get_game_fanpages_unique")
        
        group_search_names = [game["group_search_name"] for game in game_fanpages if "group_search_name" in game]
        
        # Navigate to Facebook Watch
        logger.info("Navigating to Facebook Watch...")
        browser.get(f"{FB_DEFAULT_URL}/watch")
        
        # Scroll on Watch page for 2-3 minutes
        watch_duration = random.randint(150, 210)  # 2-3 minutes
        logger.info(f"Scrolling on Watch page for {watch_duration} seconds...")
        start_time = time.time()
        
        # Use more natural scrolling patterns with variable speeds and distances
        while time.time() - start_time < watch_duration:
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
                engagement_time = random.uniform(8.0, 18.0)
                logger.info(f"Engaging with content for {engagement_time:.1f} seconds...")
                time.sleep(engagement_time)
                
                # SHARE A POST
                if random.random() < 0.1:  # 10% chance to share a post
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
                            
                            # Sometimes click on a reaction
                            if random.random() < 0.5:  # 50% chance to click a reaction
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
                                    
                                    # Wait for reaction panel to appear
                                    try:
                                        # Use a more reliable XPath for the reaction panel
                                        reaction_panel = WebDriverWait(browser, 5).until(
                                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'reactions-panel') or contains(@style, 'opacity') or @role='dialog']"))
                                        )
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
                                                
                                                # Wait after clicking
                                                time.sleep(random.uniform(2.0, 4.0))
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
                    except Exception as e:
                        logger.debug(f"Failed to simulate reaction")

            # Occasionally click on videos that look interesting
            if random.random() < 0.15:  # 15% chance
                try:
                    videos = browser.find_elements(By.XPATH, "//div[contains(@class, 'watch')]//a[contains(@href, '/watch/')]")
                    if videos:
                        video = random.choice(videos)
                        # Scroll to make video visible
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", video)
                        time.sleep(random.uniform(1.0, 2.0))
                        video.click()
                        logger.info("Clicked on a video to watch")
                        # Watch for a variable amount of time
                        watch_time = random.uniform(15.0, 45.0)
                        logger.info(f"Watching video for {watch_time:.1f} seconds")
                        time.sleep(watch_time)
                        browser.back()
                        time.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger.debug(f"Failed to interact with video")
        
        # Navigate to Facebook homepage with natural browsing pattern
        logger.info("Navigating to Facebook homepage...")
        browser.get(FB_DEFAULT_URL)
        
        # Scroll on homepage with more natural reading patterns
        homepage_duration = random.randint(160, 230)  # 1.5-2.5 minutes
        logger.info(f"Browsing homepage for {homepage_duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < homepage_duration:
            # Implement variable scrolling speeds and distances
            scroll_speed = random.choice(["slow", "medium", "fast"])
            
            if scroll_speed == "slow":
                # Slow careful reading
                scroll_amount = random.randint(100, 300)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(4.0, 8.0))  # Longer time reading
            elif scroll_speed == "medium":
                # Normal browsing
                scroll_amount = random.randint(300, 600)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(2.5, 5.0))
            else:  # fast
                # Scanning quickly
                scroll_amount = random.randint(600, 900)
                browser.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1.0, 2.5))
                
            # SHARE A POST
            if random.random() < 0.1:  # 10% chance to share a post
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
            
            # Simulate interest in specific content
            if random.random() < 0.25:  # 25% chance to show interest
                try:
                    # Find interactive elements like posts, images, or comments
                    interactive_elements = browser.find_elements(By.XPATH, 
                        "//div[contains(@class, 'feed')]/div | //div[contains(@class, 'post')] | //div[contains(@class, 'story')]")
                    
                    if interactive_elements:
                        element = random.choice(interactive_elements)
                        # Scroll element into view with natural movement
                        browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Hover over the element to show interest
                        ActionChains(browser).move_to_element(element).perform()
                        logger.info("Showing interest in a post")
                        
                        # Longer pause to simulate reading
                        reading_time = random.uniform(8.0, 20.0)
                        logger.info(f"Reading content for {reading_time:.1f} seconds")
                        time.sleep(reading_time)
                        
                        # Sometimes expand comments or click on images
                        if random.random() < 0.3:
                            try:
                                comment_buttons = element.find_elements(By.XPATH, ".//span[contains(text(), 'comment') or contains(text(), 'Comment')]")
                                if comment_buttons:
                                    comment_buttons[0].click()
                                    logger.info("Expanded comments section")
                                    time.sleep(random.uniform(5.0, 12.0))
                            except Exception:
                                pass
                except Exception as e:
                    logger.debug(f"Failed to interact with content")

            # Occasionally search for topics related to games (more targeted)
            if random.random() < 0.4:
                try:
                    search_box = browser.find_element(By.XPATH, "//input[@placeholder='Search Facebook']")
                    
                    search_queries = [
                        "mobile game tips", "new game releases", "game strategies", "popular mobile games", 
                        "game recommendations", "gaming community", "best mobile games 2023", 
                        "free mobile games", "mobile game cheats", "mobile game updates", 
                        "upcoming game releases", "mobile game events", "mobile game giveaways",
                        "mobile game tournaments", "mobile game reviews", "mobile game guides",
                        "trending mobile games", "mobile game hacks", "mobile game mods",
                        "mobile game communities", "mobile game news", "mobile game forums"
                    ]
                    
                    # Extend search_queries with group_search_names
                    search_queries.extend(group_search_names)

                    search_query = random.choice(search_queries)
                    
                    # Type like a human with variable speed
                    search_box.click()
                    search_box.clear()
                    for char in search_query:
                        search_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.25))  # Variable typing speed
                    
                    time.sleep(random.uniform(0.5, 1.5))  # Pause before hitting enter
                    search_box.send_keys(Keys.ENTER)
                    logger.info(f"Searching for game-related topic: {search_query}")
                    
                    # Browse search results
                    time.sleep(random.uniform(5.0, 12.0))
                    
                    # Scroll through results with variable speed
                    for _ in range(random.randint(2, 5)):
                        browser.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
                        time.sleep(random.uniform(2.0, 5.0))
                    
                    # Return to homepage
                    browser.get(FB_DEFAULT_URL)
                    time.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger.debug(f"Search simulation failed")
        
        logger.info("Human behavior simulation completed")
        
    except Exception as e:
        logger.error(f"Error during human behavior simulation")


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

