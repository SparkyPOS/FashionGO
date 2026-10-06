from utils import *


def login(driver):
    if not email or not pasw:
        print('FashionGO credentials not configured. Set FASHIONGO_EMAIL/FASHIONGO_PASSWORD or Config.json values before running.')
        return driver

    driver.get('https://www.fashiongo.net/login')
    sleep(3)

    try:
        driver.find_element(By.ID, "email-inp").send_keys(email)
        driver.find_element(By.ID, "pwd_inp").send_keys(pasw)
        submit = driver.find_element(By.ID, "btn-signin")
        driver.execute_script(clicker, submit)
        sleep(3)
    except Exception as exc:
        print(f'Failed to sign in to FashionGO: {exc}')
        return driver

    cookies = driver.get_cookies()
    with open(COOKIES_PATH, 'wb') as f:
        pickle.dump(cookies, f)

    return driver


def duke_login(driver):
    if not duke_email or not duke_password:
        print('Duke credentials not configured. Skipping Duke login.')
        return driver

    driver.get('https://www.dukeimports.com/login.jhtm')
    sleep(3)

    email_field = None
    for selector in ['input[name="username"]', '#username', 'input[name="login[username]"]', 'input[name="email"]', '#email', 'input[type="email"]', 'form[action*="login"] input[type="text"]']:
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if email_field is None:
        print('Could not find Duke email field. Skipping Duke login.')
        return driver

    email_field.clear()
    email_field.send_keys(duke_email)

    password_field = None
    for selector in ['input[name="password"]', '#password', 'input[name="login[password]"]', 'input[name="pass"]', '#pass', 'input[type="password"]']:
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if password_field is None:
        print('Could not find Duke password field. Skipping Duke login.')
        return driver

    password_field.clear()
    password_field.send_keys(duke_password)

    submit_btn = None
    for selector in ['button[type="submit"]', 'input[type="submit"]', 'button[title="Login"]', 'button[title="Sign In"]']:
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if submit_btn is not None:
        driver.execute_script(clicker, submit_btn)
        sleep(4)
    else:
        password_field.submit()
        sleep(4)

    return driver


if __name__ == "__main__":
    try:
        fashiongo_driver = get_browser()
        try:
            login(fashiongo_driver)
        finally:
            fashiongo_driver.quit()

        if duke_email and duke_password:
            duke_driver = get_browser()
            try:
                duke_login(duke_driver)
            finally:
                duke_driver.quit()
    except Exception as exc:
        print(f'Login script failed: {exc}')
        raise SystemExit(1)