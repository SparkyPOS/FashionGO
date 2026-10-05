from utils import *


def login(driver):
    driver.get('https://www.fashiongo.net/login')
    driver.find_element(By.ID, "email-inp").send_keys(email)
    driver.find_element(By.ID, "pwd_inp").send_keys(pasw)
    submit = driver.find_element(By.ID, "btn-signin")
    driver.execute_script(clicker, submit)
    sleep(3)

    cookies = driver.get_cookies()
    with open('cookies.pkl', 'wb') as f:
        pickle.dump(cookies, f)

    return driver


def duke_login(driver):
    if not duke_email or not duke_password:
        print('Duke credentials not configured. Skipping Duke login.')
        return driver

    driver.get('https://www.dukeimports.com/customer/account/login/')
    sleep(3)

    email_field = None
    for selector in ['input[name="login[username]"]', 'input[name="email"]', '#email', 'input[type="email"]']:
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if email_field is None:
        raise RuntimeError('Could not find Duke email field')

    email_field.clear()
    email_field.send_keys(duke_email)

    password_field = None
    for selector in ['input[name="login[password]"]', 'input[name="pass"]', '#pass', 'input[type="password"]']:
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if password_field is None:
        raise RuntimeError('Could not find Duke password field')

    password_field.clear()
    password_field.send_keys(duke_password)

    submit_btn = None
    for selector in ['button[type="submit"]', 'button[title="Login"]', 'button[title="Sign In"]']:
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if submit_btn is not None:
        driver.execute_script(clicker, submit_btn)
        sleep(4)

    return driver


if __name__ == "__main__":
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