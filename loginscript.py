from utils import *

def login(driver):
    driver.get('https://www.fashiongo.net/login')
    driver.find_element(By.ID, "email-inp").send_keys('owner@shawnsfleamarket.com')
    driver.find_element(By.ID, "pwd_inp").send_keys('Cassie1999!')
    submit = driver.find_element(By.ID, "btn-signin")
    driver.execute_script(clicker, submit)
    sleep(3)

    cookies = driver.get_cookies()
    with open('cookies.pkl', 'wb') as f:
        pickle.dump(cookies, f)

    driver.quit()


if __name__ == "__main__":
    driver = get_browser()
    login(driver)