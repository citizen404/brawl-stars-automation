import time, os, random, cv2, numpy as np
from appium import webdriver
from appium.options.android import UiAutomator2Options
from dotenv import load_dotenv

options = UiAutomator2Options()
options.platform_name = "Android"
options.automation_name = "UiAutomator2"

load_dotenv()

GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
APPIUM_SERVER = os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723")
DEVICE_UDID = os.getenv("DEVICE_UDID", "127.0.0.1:26625")

options.device_name = "Remote Device"
options.udid = DEVICE_UDID
options.set_capability("noReset", True) 
options.set_capability("gpsEnabled", True)
options.set_capability("disableIdLocatorAutocompletion", True)
options.set_capability("adbExecTimeout", 60000)
options.set_capability("appium:skipDeviceInitialization", True)
options.set_capability("appium:ignoreUnimportantViews", True)


driver = webdriver.Remote(APPIUM_SERVER, options=options)
bundle_id = "com.android.vending"
app_id = "com.supercell.brawlstars"


def find_element_multi(driver, xpaths):
    """Find element using multiple XPATH locators"""
    for xp in xpaths:
        try:
            driver.implicitly_wait(1) 
            return driver.find_element("xpath", xp)
        except:
            continue
    raise Exception(f"Element not found: {xpaths}")


def find_by_cv(driver, template_name):
    """Multiscale CV template matching"""
    try:
        base_path = os.path.dirname(__file__)
        template_path = os.path.join(base_path, template_name)
        screen_path = os.path.join(base_path, "assets/screen_debug.png")
        driver.save_screenshot(screen_path)
        
        img = cv2.imread(screen_path, 0)
        template = cv2.imread(template_path, 0)
        
        if img is None or template is None: return None

        for scale in [0.8, 1.0, 1.2]:
            width = int(template.shape[1] * scale)
            height = int(template.shape[0] * scale)
            resized = cv2.resize(template, (width, height), interpolation=cv2.INTER_AREA)
            
            res = cv2.matchTemplate(img, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if max_val > 0.75:
                h, w = resized.shape[:2]
                return int(max_loc[0] + w/2), int(max_loc[1] + h/2)
    except Exception as e:
        print(f"CV Multiscale Error: {e}")
    return None

def handle_google_auth(driver):
    """Automated Google Login sequence"""
    print("Starting Google Auth sequence...")
    time.sleep(4) 
    w, h = driver.get_window_size().values()
    
    try:
	# Step 1: Sign-in button
        for _ in range(3):
            driver.tap([(int(w * 0.5), int(h * 0.67))])
            time.sleep(0.4)

        time.sleep(10) 
        
        # Step 2: Email entry
        print(f"Entering email: {GOOGLE_EMAIL}")
        driver.tap([(int(w * 0.5), int(h * 0.33))]) 
        time.sleep(1.5)
        driver.execute_script('mobile: shell', {'command': 'input', 'args': ['text', GOOGLE_EMAIL]})
        time.sleep(0.5)
        driver.tap([(int(w * 0.88), int(h * 0.94))]) 
        time.sleep(5)

        # Step 3: Password entry
        print("Entering password...")
        driver.tap([(int(w * 0.5), int(h * 0.33))]) 
        time.sleep(2)
        driver.execute_script('mobile: shell', {'command': 'input', 'args': ['text', GOOGLE_PASSWORD]})
        time.sleep(1)
        driver.tap([(int(w * 0.88), int(h * 0.94))]) 
        time.sleep(10)
        
	# Step 4: 'I agree' screen
        print("Accepting Google Terms (I agree screen)...")
        time.sleep(5)
        for y_coord in [0.58, 0.60, 0.62]:
            for x_coord in [0.75, 0.80, 0.85]:
                driver.tap([(int(w * x_coord), int(h * y_coord))])
                time.sleep(0.2)
        time.sleep(6) 

        # Step 5: Google Services (Accept)
        print("Handling Google Services screen...")
        time.sleep(2)

        for _ in range(2):
            driver.swipe(int(w * 0.5), int(h * 0.8), int(w * 0.5), int(h * 0.2), 600)
            time.sleep(0.5)

        for y_coord in [0.88, 0.90, 0.92, 0.94]:
            for x_coord in [0.75, 0.85, 0.90]:
                driver.tap([(int(w * x_coord), int(h * y_coord))])
                time.sleep(0.2)

        time.sleep(15)         
        return True 
        
    except Exception as e:
        print(f"Auth error: {e}")
        return False

def smart_click(driver, xpaths, template_name):
    """Hybrid search: XPATH first, CV as fallback"""
    driver.implicitly_wait(0.5) # Reduced wait for faster cycling
    for xp in xpaths:
        try:
            el = driver.find_element("xpath", xp)
            el.click()
            print(f"Clicked via DOM: {xp}")
            return True
        except:
            continue
    
    print(f"DOM failed for {template_name}. Trying CV...")
    coords = find_by_cv(driver, template_name)
    if coords:
        driver.tap([coords])
        return True
    return False

def ensure_app_active(driver, package_id):
    """Restore app to foreground if lost"""
    if driver.current_package != package_id:
        print(f"Restoring {package_id} to foreground")
        driver.activate_app(package_id)
        time.sleep(1.5)

def safe_swipe(driver, x1, y1, x2, y2, duration=400):
    """Fault-tolerant swipe with retries"""
    for i in range(2): # for speed
        try:
            driver.swipe(x1, y1, x2, y2, duration)
            return True
        except Exception as e:
            print(f"Swipe retry (attempt {i+1}): {e}")
            time.sleep(0.5)
    return False

def safe_tap(driver, coords):
    """Fault-tolerant tap with retries"""
    for i in range(2):
        try:
            driver.tap(coords)
            return True
        except Exception as e:
            print(f"Tap retry (attempt {i+1}): {e}")
            time.sleep(0.5)
    return False


def save_debug_screenshot(driver, name):
    """Save screenshot for debugging and reporting"""
    try:
        base_path = os.path.dirname(__file__)
        debug_dir = os.path.join(base_path, "debug")
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = int(time.time())
        path = os.path.join(debug_dir, f"{timestamp}_{name}.png")

        driver.save_screenshot(path)
        print(f"Debug screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Failed to save debug screenshot: {e}")
        return None





#--------------------------0----------------------------

def handle_brawl_onboarding(driver):
    """Handle age slider and terms of service screens"""
    ensure_app_active(driver, app_id)
    print("Waiting for game load...")
    
    size = driver.get_window_size()
    w, h = size['width'], size['height']
    
    # Phase 1: Wait for initial assets
    time.sleep(4) 
    for attempt in range(15):
        ensure_app_active(driver, app_id)

        # Priority 0: Check if already in main menu
        if find_by_cv(driver, "assets/shop_btn.png"):
            print("Main menu detected during onboarding, skipping loading wait")
            return "main_menu"
    
        # Priority 1: Check if already in battle
        if find_by_cv(driver, "assets/level0_start.png"): 
            print("Battle detected, skipping onboarding")
            return "battle"
            
        # Priority 2: Age slider detection
        if find_by_cv(driver, "assets/age_slider.png"):
            print("Age screen detected")
            break

        # Priority 3: System buttons (Accept/OK)
        try:
            driver.implicitly_wait(0)
            if driver.find_elements("xpath", "//*[contains(@text, 'Accept') or contains(@text, 'OK')]"):
                print("Accept button detected via DOM")
                break
        except:
            pass
        
        print(f"Loading attempt {attempt}...")
        time.sleep(1.5)

    # Phase 2: Interaction sequence
    for i in range(10):
        # Button check (DOM)
        accepted = False
        for text in ["Confirm", "Accept", "Accept All", "Not now", "OK"]:
            try:
                driver.implicitly_wait(0)
                el = driver.find_element("xpath", f"//*[contains(@text, '{text}')]")
                el.click()
                print(f"Clicked: {text}")
                accepted = True
                break
            except:
                continue

        if accepted:
            time.sleep(2)
            return "ready"

        # Slider interaction (CV fallback)
        if find_by_cv(driver, "assets/age_slider.png"):
            print(f"Action {i}: Adjusting age slider")
            safe_swipe(driver, w * 0.3, h * 0.5, w * 0.7, h * 0.5, 400)
            time.sleep(0.5)
            
            off_x, off_y = random.randint(-10, 10), random.randint(-10, 10)
            safe_tap(driver, [(int(w * 0.5) + off_x, int(h * 0.72) + off_y)])
        else:
            if i > 1:
                print("Onboarding completed")
                return "ready"

        time.sleep(1)
    return "ready"

    
def handle_google_login(driver):
    """Google Play Sign-in check"""
    print("Checking Google Auth...")
    locators = ["//*[contains(@text, 'Sign in')]", "//*[contains(@text, 'Войти')]"]
    if smart_click(driver, locators, "assets/google_signin_btn.png"):
        print("Login initiated")
        time.sleep(4)

#--------------------------1----------------------------

def handle_shop_flow(driver):
    """Open shop and execute dry-run payment check"""
    ensure_app_active(driver, app_id)

    size = driver.get_window_size()
    w, h = size['width'], size['height']

    print("Opening SHOP...")
    shop_coords = find_by_cv(driver, "assets/shop_btn.png")

    if shop_coords:
        shop_x, shop_y = shop_coords
        print(f"Shop found via CV at {shop_x}, {shop_y}")
    else:
        print("Shop CV failed, using fallback")
        shop_x, shop_y = int(w * 0.07), int(h * 0.30)

    time.sleep(0.5)

    for _ in range(2):
        safe_tap(driver, [(shop_x, shop_y)])
        time.sleep(0.8)

    print("Loading Shop assets...")
    time.sleep(2)
    safe_tap(driver, [(int(w * 0.5), int(h * 0.5))])

    print("Navigating to offers...")
    time.sleep(1.5)
    safe_tap(driver, [(int(w * 0.1), int(h * 0.9))])

    print("Executing Dry Run: Payment trigger check...")
    offer_coords = find_by_cv(driver, "assets/offer_price.png")

    if offer_coords:
        print(f"DRY RUN SUCCESS: Offer detected at {offer_coords}")
    else:
        print("Dry run: Shop reached, no specific offer detected")

    print("Shop sequence completed")
    return True

def handle_gameplay(driver):
    ensure_app_active(driver, app_id)

    battle_start_time = time.time() # Фиксируем время начала
    start_activity = driver.current_activity
   
    print("Starting gameplay with ADB-native actions...")
    size = driver.get_window_size()
    w, h = size['width'], size['height']
    udid = driver.capabilities.get('udid', DEVICE_UDID)
    
    jx, jy = int(w * 0.2), int(h * 0.7)
    sx, sy = int(w * 0.8), int(h * 0.7)
    ux, uy = int(sx - 140), int(sy + 140)
    
    phases = ["left", "center_up", "right", "center_up", "deep_left"]
    phase_idx = 0
    stuck_frames = 0

    while driver.current_activity == start_activity: #True:

	# Waiting for PROCEED button and end of fight signs ---
        safe_tap(driver, [(int(w * 0.85), int(h * 0.88))])
        
        try:
            driver.implicitly_wait(0)
            finish_btns = driver.find_elements("xpath", "//*[contains(@text, 'PROCEED') or contains(@text, 'EXIT') or contains(@text, 'Claim') or contains(@text, 'OK')]")
            name_input = driver.find_elements("xpath", "//android.widget.EditText")
            
            if finish_btns or name_input:
                print("End of battle detected! Transitioning to exit logic...")
                break
        except:
            pass
        # -------------

        current_phase = phases[phase_idx]
        try:
            driver.implicitly_wait(0)
            print("Check buttons..")
            finish_btns = driver.find_elements("xpath", "//*[contains(@text, 'PROCEED') or contains(@text, 'EXIT') or contains(@text, 'Claim') or contains(@text, 'OK')]")
            if finish_btns:
                print("End of battle detected via UI elements!")
                break
        except:
            pass
        
        # 1. AIM COORDS
        if current_phase == "deep_left":
            tx, ty = 100, h - 100
            duration = 2000
        elif current_phase == "left":
            tx, ty = 100, random.randint(int(h * 0.3), int(h * 0.6))
            duration = 1500
        elif current_phase == "right":
            tx, ty = w - 100, random.randint(int(h * 0.3), int(h * 0.6))
            duration = 1500
        else: # center_up
            tx, ty = int(w * 0.5), int(h * 0.2)
            duration = 1200
            stuck_frames += 1 

        # 2. THroWBACK MECHANISM (ADB)
        if stuck_frames >= 3:
            print("CORNER DETECTED! Mirrored dash via ADB...")
            esc_x = w - 150 if tx < w/2 else 150
            safe_swipe(driver, jx, jy, int(esc_x), int(h - 150), 1000)
            stuck_frames = 0
            phase_idx = (phase_idx + 1) % len(phases)
            continue

        # 3. RUN AND ATTACK (ADB)
        # Movement
        safe_swipe(driver, jx, jy, int(tx), int(ty), duration)

        # Shooting
        for _ in range(3):
            atx = sx + random.randint(-50, 50)
            aty = sy + random.randint(-50, 50)
            safe_tap(driver, [(int(atx), int(aty))])
        
        # Ultra (by sectors)
        if random.random() < 0.4:
            print("SUPER ATTACK: Sweeping sectors...")
            offset = 180 
            sectors = [
                (ux, uy - offset),          # up
                (ux + offset, uy - offset), # up-right
                (ux - offset, uy - offset)  # up-left
            ]
            
            target_sx, target_sy = random.choice(sectors)
            # resrtict
            target_sx = max(10, min(target_sx, w - 10))
            target_sy = max(10, min(target_sy, h - 10))

            safe_swipe(driver, ux, uy, int(target_sx), int(target_sy), 300)
            time.sleep(0.2)

        phase_idx = (phase_idx + 1) % len(phases)
        time.sleep(0.01)


    # Stage 4: Post-Battle Navigation
    print("Battle finished! Handling exit...")
    for i in range(10):
        # Proceed / Exit area (bottom right)
        safe_tap(driver, [(int(w * 0.85), int(h * 0.88))])
        time.sleep(0.3)

    # Name Input handling
    print("Checking for Name screen (CV)...")
    time.sleep(1) 
    
    name_ok = find_by_cv(driver, "assets/name_ok_btn.png")
    if name_ok:
        print(f"Name OK found at {name_ok}")
        safe_tap(driver, [name_ok])
        time.sleep(0.5)
        safe_tap(driver, [name_ok])
    else:
        print("Name CV failed, using DOM/fallback...")
        try:
            driver.implicitly_wait(1)
            if driver.find_elements("xpath", "//android.widget.EditText"):
                safe_tap(driver, [(int(w * 0.68), int(h * 0.30))])
        except:
            print("Name screen skipped")

    # Stage 5: Shop Navigation
    handle_shop_flow(driver)
    
    print("Sequence completed")


#--------------------------2----------------------------
# Launch and play
try:
    installed = False
    if driver.is_app_installed(app_id):
        print("App already installed. Skipping Google Play...")
        installed = True
    else:
        # 0. Restart Google Play
        
        print("Restarting Google Play...")
        driver.terminate_app(bundle_id)
        time.sleep(1)
        
    
        # 1. Open Google Play
        
        driver.press_keycode(3)
        time.sleep(0.5)
        driver.activate_app(bundle_id)
        time.sleep(3)
        
        # Login only if Google Play actually asks for it.
        # handle_google_login() is kept as a safety click for the Sign in button.
        print("Checking Google Play login state...")
        
        google_auth_needed = False
        
        try:
            driver.implicitly_wait(2)
        
            login_markers = driver.find_elements(
                "xpath",
                "//*[contains(@text, 'Sign in') "
                "or contains(@text, 'Войти') "
                "or contains(@text, 'Use your Google Account') "
                "or contains(@text, 'Используйте аккаунт Google') "
                "or contains(@text, 'Email or phone') "
                "or contains(@text, 'Электронная почта или телефон')]"
            )
        
            search_markers = driver.find_elements(
                "xpath",
                "//*[@text='Search for apps & games' "
                "or @content-desc='Search for apps & games' "
                "or contains(@text, 'Search') "
                "or contains(@text, 'Поиск')]"
            )
        
            if login_markers and not search_markers:
                google_auth_needed = True
        
        except Exception as e:
            print(f"Google login state check error: {e}")
        
        if google_auth_needed:
            print("Google Play requires login. Trying Sign in safety click first...")
            handle_google_login(driver)
            time.sleep(3)
        
            print("Continuing full Google auth...")
            handle_google_auth(driver)
        else:
            print("Google Play already signed in. Skipping Google auth.")
        
        
        # 2. Find Search line
    
        search_locators = [
            "//*[@text='Search for apps & games']",
            "//*[@content-desc='Search for apps & games']",
            "//*[contains(@text, 'Search')]"
        ]
        search_trigger = find_element_multi(driver, search_locators)
        search_trigger.click()
        time.sleep(3)
        
        
        # 3. Enter text
        print("Entering text via ADB...")
        driver.execute_script('mobile: shell', {'command': 'input', 'args': ['text', 'Brawl%sStars']})
        time.sleep(1)
        driver.press_keycode(66) # Enter
        time.sleep(2) #
        
        
        # 4. Search and click Install button
        
        print("Opening Brawl Stars page...")
        app_locators = [
            "//android.view.View[contains(@content-desc, 'Brawl Stars')]",
            "//android.widget.TextView[contains(@text, 'Brawl Stars') and not(contains(@resource-id, 'search'))]/ancestor::*[@clickable='true'][1]",
            "//android.widget.Button[contains(@text, 'Install') or contains(@text, 'Установить')]",
            "(//android.widget.TextView[contains(@text, 'Brawl Stars')])[2]" 
        ]
        
        app = find_element_multi(driver, app_locators)
        print("Clicking app container, not text...")
        app.click()
        
        time.sleep(2)
        
        print("Searching for Install button (Smart)...")
        install_locs = [
            "//android.widget.Button[contains(@text, 'Install')]",
            "//*[@resource-id='com.android.vending:id/install_button']"
        ]
    
        if smart_click(driver, install_locs, "assets/install_btn.png"):
            print("INSTALL CLICKED!")
        else:
            print("Install button not found!")
            save_debug_screenshot(driver, "install_button_not_found")
            
        # 5. Waiting install
        print("Waiting for Brawl Stars to appear in system...")
        installed = False
        for i in range(24):
            if driver.is_app_installed(app_id):
                print(f"App {app_id} detected in system!")
                installed = True
                break
            if i % 6 == 0:
                print("Still installing...")
            time.sleep(5)
        
    # Launch and play
    if installed:
        print("Launching Brawl Stars...")
        driver.terminate_app(app_id)
        time.sleep(1)
        driver.activate_app(app_id)
        time.sleep(15)
    
        state = handle_brawl_onboarding(driver)
    
        if state == "main_menu":
            print("Main menu detected. Running shop flow directly...")
            handle_shop_flow(driver)
        
        elif state == "battle":
            print("Battle detected. Starting gameplay flow...")
            handle_gameplay(driver)
        
        else:
            print("Checking whether game is already in main menu...")
        
            if find_by_cv(driver, "assets/shop_btn.png"):
                print("Main menu detected after onboarding. Running shop flow directly...")
                handle_shop_flow(driver)
            else:
                print("Main menu shop button not detected. Starting gameplay flow...")
                handle_gameplay(driver)
    
    else:
        print("Installation failed or took too long.")
finally:    
    print("All steps finished!")
    driver.quit()