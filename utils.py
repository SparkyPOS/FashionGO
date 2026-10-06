import csv, json, os, sys, pickle, subprocess, site, importlib, shutil
from time import sleep


def ensure_dependencies():
    missing = []
    for module_name in ('selenium', 'webdriver_manager'):
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)

    if not missing:
        return

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'selenium', 'webdriver-manager'])

    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
    importlib.invalidate_caches()


ensure_dependencies()

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

clicker = "arguments[0].click();"

with open('Config.json', 'r') as cfile:
    config = json.load(cfile)

email = os.getenv('FASHIONGO_EMAIL') or config.get('email', '')
pasw = os.getenv('FASHIONGO_PASSWORD') or config.get('password', '')
duke_email = os.getenv('DUKE_EMAIL') or config.get('duke_email', '')
duke_password = os.getenv('DUKE_PASSWORD') or config.get('duke_password', '')
set_time = config.get('time', ['', ''])



def csvMaker(filename):
    if not os.path.exists('Data/' + filename + '_.csv'):
        with open('Data/' + filename + '_.csv', 'w', newline='', errors='ignore', encoding='utf-8-sig') as f:
            wr = csv.writer(f)
            wr.writerow([
                'Title',
                'SKU',
                'Price',
                'Sizes',
                'Colors',
                'Product Details',
                'Febric Contents',
                'Images',
                ])


def csvWriter(data,filename):
    with open('Data/' + filename + '_.csv', 'a', newline='', errors='ignore', encoding='utf-8-sig') as f:
        wr = csv.writer(f)
        wr.writerow(data)


def _resolve_local_driver_path(driver_name):
    candidates = []
    system_path = shutil.which(driver_name)
    if system_path:
        candidates.append(system_path)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    local_candidates = [
        os.path.join(project_dir, driver_name),
        os.path.join(project_dir, f"{driver_name}.exe"),
        os.path.join(project_dir, 'chromedriver'),
        os.path.join(project_dir, 'geckodriver'),
    ]
    candidates.extend(local_candidates)

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def _install_chromedriver_fallback():
    try:
        return ChromeDriverManager().install()
    except Exception:
        return _resolve_local_driver_path('chromedriver')


def _install_geckodriver_fallback():
    try:
        return GeckoDriverManager().install()
    except Exception:
        return _resolve_local_driver_path('geckodriver')


def get_browser(headless=False, sel=False):
    download_directory = os.path.join(os.getcwd(), "Data")
    agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/124.0.1216.0 Safari/537.2'
    driver_path = _install_chromedriver_fallback()
    if not driver_path:
        raise RuntimeError('ChromeDriver could not be resolved. Install chromedriver or place it in the project folder.')
    s = Service(executable_path=driver_path)
    chrome_option = webdriver.ChromeOptions()
    if headless:
        chrome_option.add_argument('--headless')
        chrome_option.add_argument("--no-sandbox")
        chrome_option.add_argument("--disable-dev-shm-usage")
        chrome_option.add_argument(f'user-agent={agent}')
    chrome_option.add_argument('--log-level=3')
    chrome_option.add_argument('--incognito')
    chrome_option.page_load_strategy = 'eager'
    chrome_option.add_argument('--ignore-certificate-errors')
    chrome_option.add_argument('--ignore-ssl-errors')
    chrome_option.add_argument('--ignore-certificate-errors-spki-list')
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_option.add_experimental_option("prefs", prefs)
    chrome_option.add_experimental_option("useAutomationExtension", False)
    chrome_option.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(service=s, options=chrome_option)
    return driver


def get_browser_firefox(headless=False):
    agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Firefox/116.0.1 Safari/537.2'  # You can adjust the user-agent as needed
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.set_preference("general.useragent.override", agent)
    if headless:
        firefox_options.headless = True
    driver_path = _install_geckodriver_fallback()
    if not driver_path:
        raise RuntimeError('GeckoDriver could not be resolved. Install geckodriver or place it in the project folder.')
    driver = webdriver.Firefox(executable_path=driver_path, options=firefox_options)

    return driver



