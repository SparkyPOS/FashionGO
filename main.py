import re
import urllib.request
from utils import *
from urllib.parse import urlparse

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

clicker = "arguments[0].click();"


def product_details_scrap(driver, urls, key, fixed_price=None, keyword=None):
    for url in urls:
        try:
            driver.get(url)
            p_title = ''
            try:
                p_title = driver.find_element(By.XPATH, '//h1[@class="product-title-name"]').text 
                print("Title: ", p_title)
            except:
                pass 
            p_sku = ''
            try:
                p_sku = driver.find_element(By.XPATH, '//span[@class="product-title-sku-text"]').text 
                print("SKU: ", p_sku)
            except:
                pass 
            p_price = ''
            try:
                p_price = driver.execute_script("""return document.querySelector('span[class="product-price-current"]').innerText;""")
                print("Unit Price: ", p_price)
            except:
                pass
            p_size = ''
            try:
                si = driver.execute_script("""
                    const allSpans = Array.from(document.querySelectorAll("thead span"));
                    const spansWithoutClass = allSpans.filter(span => !span.hasAttribute("class") || span.classList.contains("small-text"));
                    const textArray = [];
                    spansWithoutClass.forEach(span => {
                        textArray.push(span.textContent.trim());
                    });
                    return textArray;                      
                """)
                si.remove('EST. SHIP')
                p_size = ' | '.join(i for i in si if len(i) > 0)
                print(p_size)
            except Exception as e:
                pass  
            p_colors = ''
            try:
                colors = driver.execute_script("return document.querySelectorAll('tbody span.span_item_colorname');")
                p_colors = ' | '.join(i.text for i in colors)
            except Exception as e:
                pass
            p_details = ''
            try:
                p_details = driver.execute_script("return document.querySelector('div.detail_cont pre').innerText;")
            except Exception as e:
                pass
            febric_contents = ''
            try:
                febric_contents = driver.execute_script("return document.querySelector('div.extra-description').innerText;").replace('Fabric Contents', '').strip()
                print(febric_contents)
            except Exception as e:
                pass
            p_images = ''
            try:
                elem = driver.find_element(By.XPATH, '//div[@class="pdt_img"]').find_elements(By.TAG_NAME, 'img')
                elems = [i.get_attribute('src') for i in elem]
                p_images = ', '.join(i.replace('large', 'original') for i in elems)
                # print(p_images)
            except Exception as e:
                pass 

            if fixed_price:
                p_price = fixed_price

            data = [p_title, p_sku, p_price, p_size, p_colors, p_details, febric_contents, p_images]
            if keyword and keyword.lower() not in ' '.join(str(i) for i in data).lower():
                print('Skipped (keyword not found): ', p_title)
                continue
            csvWriter(data, key)
            
        except Exception as e:
            pass 

def get_vendor(driver):
    vendor_url_list = []
    try:
        vendors = driver.find_element(By.ID, 'item-found').find_elements(By.XPATH, './/div[@data-nclick-name="cate.list.vlink"]')
        print('Total Vendor found: ', len(vendors))
        if len(vendors) < 1:
            return vendor_url_list
        for vendor in vendors:
            vendor_url = vendor.find_element(By.TAG_NAME, 'a').get_attribute('href')
            vendor_url_list.append(vendor_url)
    except Exception as e:
        pass 
    return vendor_url_list

def scraper(driver, vendors, number, key, scrap_driver):
    if number == 1:
        for vendor in vendors:
            try:
                driver.execute_script(f"window.open('{vendor}')")
                driver.switch_to.window(driver.window_handles[1])
                sleep(5)
                products_all = driver.find_element(By.XPATH, '//a[@data-nclick-name="vendor.new.viewmore"]').get_attribute('href')
                print(products_all)
                driver.get(products_all)
                items_checker = False
                while True:
                    product_url_list = []
                    try:
                        items = driver.find_elements(By.XPATH, '//a[@data-nclick-name="vendor.new.item"]')
                        print('Total Items: ', len(items))
                        if len(items) < 1:
                            break
                        for item in items[::2]:
                            try:
                                item_url = item.get_attribute('href')
                                print(item_url)
                                product_url_list.append(item_url)
                            except:
                                pass 
                        product_details_scrap(scrap_driver, product_url_list, key)
                    except Exception as e:
                        print(e)
                        items_checker = True
                        break
                    try:
                        next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                        driver.execute_script(clicker, next)
                        sleep(6)
                    except:
                        break

                # pagination 
                if items_checker:
                    try:
                        next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                        while True:
                            # scraping part here
                            vendors = get_vendor(driver)
                            scraper(driver, vendors, number, key, scrap_driver) 
                            try:
                                next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                                driver.execute_script(clicker, next)
                                sleep(6)
                            except:
                                break
                    except Exception as e:
                        pass 

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                pass 

    else:
        try:
            items = driver.find_elements(By.XPATH, '//a[@data-nclick-name="catal.list.item"]')
            print('Total Items: ', len(items))
            for item in items:
                item_url = item.get_attribute('href')
                print(item_url)

        except Exception as e:
            print(e)


def login(driver):
    driver.get('https://www.fashiongo.net/login')
    driver.find_element(By.ID, "email-inp").send_keys('owner@shawnsfleamarket.com')
    driver.find_element(By.ID, "pwd_inp").send_keys('Cassie1999!')
    submit = driver.find_element(By.ID, "btn-signin")
    driver.execute_script(clicker, submit)
    sleep(3)

    cookies = driver.get_cookies()
    with open(COOKIES_PATH, 'wb') as f:
        pickle.dump(cookies, f)

    driver.quit() 


def sign_in(driver):
    driver.get('https://www.fashiongo.net')
    with open(COOKIES_PATH, 'rb') as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    sleep(3)
    return driver 


def duke_is_logged_in(driver):
    try:
        return bool(driver.execute_script(r"""
            const links = Array.from(document.querySelectorAll('a'));
            return links.some(link => {
                const href = (link.getAttribute('href') || '').toLowerCase();
                const text = (link.textContent || '').toLowerCase();
                return href.includes('logout') || href.includes('logoff') || text.includes('log out') || text.includes('logout') || text.includes('sign out') || text.includes('log off') || text.includes('logoff');
            });
        """))
    except Exception:
        return False


def duke_login_error_message(driver):
    try:
        return (driver.execute_script(r"""
            const selectors = ['.error', '.errors', '.message-error', '.loginError', '.alert-danger', 'font[color="red"]', '.red'];
            for (const selector of selectors) {
                for (const el of document.querySelectorAll(selector)) {
                    const text = (el.textContent || '').trim();
                    if (text) return text;
                }
            }
            const body = document.body ? document.body.innerText : '';
            const match = body.match(/[^\n]*(invalid|incorrect|failed|not\s+recognized|does\s+not\s+match)[^\n]*(username|password|login|credentials)[^\n]*/i)
                || body.match(/[^\n]*(username|password|login|credentials)[^\n]*(invalid|incorrect|failed|not\s+recognized|does\s+not\s+match)[^\n]*/i);
            return match ? match[0].trim() : '';
        """) or '').strip()
    except Exception:
        return ''


def duke_find_login_fields(driver):
    """Locate the Duke login form by its password field, then resolve the
    username field and submit button inside that same form. Scoping to the
    form avoids typing credentials into unrelated forms (search box,
    newsletter signup) that appear earlier in the page DOM."""
    password_field = None
    for selector in [
        'input[name="password"]',
        'input[name="j_password"]',
        '#password',
        'input[name="login[password]"]',
        'input[name="pass"]',
        '#pass',
        'input[type="password"]',
    ]:
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if password_field is None:
        return None, None, None, None

    form = None
    try:
        form = password_field.find_element(By.XPATH, 'ancestor::form[1]')
    except Exception:
        pass

    scope = form if form is not None else driver
    email_field = None
    for selector in [
        'input[name="username"]',
        'input[name="j_username"]',
        '#username',
        'input[name="login[username]"]',
        'input[name="email"]',
        '#email',
        'input[type="email"]',
        'input[type="text"]',
    ]:
        try:
            email_field = scope.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    submit_btn = None
    for selector in [
        'button[type="submit"]', 'input[type="submit"]', 'input[type="image"]',
        'button[title="Login"]', 'button[title="Sign In"]', 'button',
    ]:
        try:
            submit_btn = scope.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    return form, email_field, password_field, submit_btn


def duke_fill_field(driver, field, value):
    field.clear()
    field.send_keys(value)
    try:
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            field,
        )
    except Exception:
        pass


def duke_login(driver):
    login_url = 'https://www.dukeimports.com/login.jhtm'
    driver.get(login_url)
    sleep(3)

    if duke_is_logged_in(driver):
        print('Duke session already logged in.')
        return driver

    if not duke_email or not duke_password:
        raise RuntimeError(
            'Duke credentials are not configured. Add DUKE_EMAIL and DUKE_PASSWORD '
            'or fill duke_email/duke_password in Config.json.'
        )

    form, email_field, password_field, submit_btn = duke_find_login_fields(driver)

    if password_field is None:
        raise RuntimeError('Could not find Duke password field')
    if email_field is None:
        raise RuntimeError('Could not find Duke email field')

    duke_fill_field(driver, email_field, duke_email)
    duke_fill_field(driver, password_field, duke_password)

    if submit_btn is not None:
        driver.execute_script(clicker, submit_btn)
    elif form is not None:
        driver.execute_script(
            'if (arguments[0].requestSubmit) { arguments[0].requestSubmit(); } '
            'else { arguments[0].submit(); }',
            form,
        )
    else:
        password_field.submit()
    sleep(4)

    if duke_is_logged_in(driver):
        print('Duke login successful.')
        return driver

    error_message = duke_login_error_message(driver)
    still_on_login = False
    try:
        driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        still_on_login = True
    except Exception:
        pass

    if error_message:
        raise RuntimeError(f'Duke login rejected: {error_message}')
    if still_on_login:
        raise RuntimeError('Duke login did not complete (still on the login page). Check duke_email/duke_password in Config.json.')

    # Some pages after login lack a logout link; confirm from the homepage.
    try:
        driver.get('https://www.dukeimports.com/')
        sleep(3)
        if duke_is_logged_in(driver):
            print('Duke login successful.')
            return driver
    except Exception:
        pass

    print('Duke login submitted; could not confirm a logout link, continuing.')
    return driver


def duke_get_product_links(driver):
    try:
        hrefs = driver.execute_script(r"""
            const seen = new Set();
            return Array.from(document.querySelectorAll('a'))
                .map(link => link.href)
                .filter(href => {
                    if (!href || href.startsWith('javascript:')) return false;
                    const lower = href.toLowerCase();
                    if (lower.includes('/category/') || lower.includes('/customer/') || lower.includes('/search/') || lower.includes('/checkout/') || lower.includes('/cart/')) return false;
                    return lower.includes('/product/') || lower.includes('/products/') || lower.includes('/p/') || /\/[^/]+\.html?/i.test(href.replace(/https?:\/\//, ''));
                })
                .filter(href => {
                    if (seen.has(href)) return false;
                    seen.add(href);
                    return true;
                });
        """)
        return [href for href in hrefs if urlparse(href).netloc.lower() == 'www.dukeimports.com']
    except Exception:
        return []


def duke_scrape_product_page(driver, product_url):
    driver.get(product_url)
    sleep(3)

    body_text = driver.execute_script("return document.body ? document.body.innerText : ''") or ''
    lower_text = body_text.lower()
    if 'out of stock' in lower_text or 'sold out' in lower_text:
        return None

    title = ''
    for selector in ['h1.product-title', 'h1.page-title', '.product-info-main h1', 'h1']:
        try:
            title = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            break
        except Exception:
            pass

    sku = ''
    for selector in ['.product.attribute.sku .value', '.sku', '[data-role="sku"]', '.product-info-main .sku', '.product-info-main .product.attribute.sku']:
        try:
            sku = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if sku:
                break
        except Exception:
            pass
    if not sku:
        match = re.search(r'(?:SKU|Item\s*#|Model\s*#)\s*[:#]?\s*([A-Za-z0-9\-]+)', body_text, re.I)
        if match:
            sku = match.group(1).strip()

    price = ''
    price_pattern = r'[$€£]\s*\d[\d,]*(?:\.\d+)?'
    bare_number_pattern = r'\d[\d,]*(?:\.\d+)?'
    prioritized_selectors = [
        '.price_cell', 'td.price_cell', '.priceCell', '.price-cell',
        '.price', 'span.price', 'td.price', 'div.price',
        '.price-box', '.price-box .price', '.price-container',
        '.product-info-price .price', '.product-pricing .price',
        '.regular-price', '.special-price', '.old-price', '.final-price',
        '.product-info-main .price', '[itemprop="price"]', 'meta[itemprop="price"]',
        '.product-info-main [itemprop="price"]', '[data-price-amount]', '[data-price]'
    ]
    for attempt in range(3):
        try:
            for selector in prioritized_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                except Exception:
                    elements = []
                for element in elements:
                    text_candidates = [
                        element.text,
                        element.get_attribute('innerText'),
                        element.get_attribute('textContent'),
                    ]
                    attribute_candidates = [
                        element.get_attribute('data-price-amount'),
                        element.get_attribute('data-price'),
                        element.get_attribute('content'),
                    ]
                    for candidate in text_candidates:
                        if not candidate:
                            continue
                        match = re.search(price_pattern, candidate)
                        if match:
                            price = match.group(0).strip()
                            break
                    if not price:
                        # Attribute values are bare numbers (e.g. "12.9900")
                        # without a currency symbol.
                        for candidate in attribute_candidates:
                            if not candidate:
                                continue
                            match = re.search(bare_number_pattern, candidate)
                            if match:
                                price = '$' + match.group(0).strip()
                                break
                    if price:
                        break
                if price:
                    break
        except Exception:
            pass
        if price:
            break
        sleep(2)
        body_text = driver.execute_script("return document.body ? document.body.innerText : ''") or body_text
    if not price:
        match = re.search(r'Price\s*[:=]\s*(' + price_pattern + r')', body_text, re.I)
        if not match:
            match = re.search(price_pattern, body_text)
        if match:
            price = match.group(match.lastindex or 0).strip()
    if not price and re.search(r'(?:log\s*in|login|sign\s*in)[^\n]{0,40}(?:price|pricing)|(?:price|pricing)[^\n]{0,40}(?:log\s*in|login|sign\s*in)', body_text, re.I):
        print('Price appears hidden behind login on this page; check your Duke credentials/session.')

    description = ''
    for selector in ['#details_long_desc', '.details_long_desc', '[id*="long_desc"]', '.product.attribute.description .value', '.description .value', '[data-role="description"]', '.product-info-main .description', '.product.description']:
        try:
            description = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if description:
                break
        except Exception:
            pass
    if not description:
        match = re.search(r'(?:Description|Details)\s*[:\n\r]+\s*(.*)', body_text, re.I | re.S)
        if match:
            description = re.sub(r'\s+', ' ', match.group(1)).strip()
    if description:
        # Remove inline script/jQuery snippets that leak into page text
        # (e.g. $( "div.ribbon..." ).css(...); }); blocks).
        description = re.sub(r'\$\(.*?;', '', description, flags=re.S)
        description = re.sub(r'\}\s*\)\s*;?', '', description)
        # Drop footer boilerplate from the platform.
        description = re.sub(r'Powered\s+By\s+WebJaguar.*', '', description, flags=re.I | re.S)
        description = re.sub(r'\s+', ' ', description).strip()

        # Duke pages sometimes start with the site footer/address block instead of
        # the actual product content, so strip those lead-in boilerplate phrases.
        description = re.sub(r'^\s*1105\s+Williams\s+Street.*?(?:46703|IN\s*46703)\s*', '', description, flags=re.I | re.S)
        description = re.sub(r'^\s*Phone\s*:\s*.*?\bEmail\s*:\s*[^\s]+\s*', '', description, flags=re.I | re.S)
        description = re.sub(
            r'^\s*(?:COMPANY\s+INFO\s+)?(?:About\s+Us\s+Contact\s+Us\s+FAQ\s+SUPPORT\s+Login/Register\s+My\s+Account\s+Sales\s+Rep\s+Login\s+POLICIES\s+Terms?\s*&?\s*Conditions\s+Shipping\s+Policy\s+Privacy\s+Policy\s+FOLLOW\s+US\s+©?\s*Webjaguar.*?All\s+rights\s+reserved\.)\s*',
            '',
            description,
            flags=re.I | re.S,
        )
        description = description.strip()

        # Drop the tab labels (Specifications / Notification / Agent) that can
        # appear before the description text, and the store address/contact
        # block wherever it occurs.
        description = re.sub(r'^\s*(?:(?:Specifications?|Notification|Agent)\s+)+', '', description, flags=re.I)
        description = re.sub(r'1105\s+Williams\s+Street[^$]*?(?:IN\s*)?46703\s*', '', description, flags=re.I)
        description = re.sub(r'Phone\s*:\s*\(?\d{3}\)?[\s.-]*\d{3}[\s.-]*\d{4}\s*', '', description, flags=re.I)
        description = re.sub(r'Email\s*:\s*\S+@\S+\s*', '', description, flags=re.I)
        description = description.strip()

        footer_patterns = [
            r'(?i)\b(?:COMPANY\s+INFO|About\s+Us|Contact\s+Us|FAQ|SUPPORT|Login/Register|My\s+Account|Sales\s+Rep\s+Login|Terms?\s*&?\s*Conditions|Shipping\s+Policy|Privacy\s+Policy|FOLLOW\s+US)\b',
            r'(?i)\bPhone\s*:\b',
            r'(?i)\bEmail\s*:\b',
            r'©\s*Webjaguar',
        ]
        footer_start = -1
        for pattern in footer_patterns:
            match = re.search(pattern, description)
            if match and (footer_start == -1 or match.start() < footer_start):
                footer_start = match.start()
        if footer_start > 0:
            description = description[:footer_start].strip(' :-\u2013')

        # Trim trailing page sections that follow the description block
        # (e.g. Specifications / Notification / Agent tabs on Duke pages).
        stop_match = re.search(r'\b(?:Specifications?|Notification|Agent|Reviews?|Related\s+Products?|You\s+may\s+also\s+like)\b', description, re.I)
        if stop_match and stop_match.start() > 0:
            description = description[:stop_match.start()].strip(' :-\u2013')

    images = []
    try:
        images = driver.execute_script(r"""
            const seen = new Set();
            const results = [];
            const containerSelectors = [
                '.product.media', '.product-media', '.fotorama', '.gallery',
                '.product-image-gallery', '.product-images', '.product-image',
                '.product-img-box', '.product-info-media', '.main-image',
                '#product-image', '.item_image', '.product_image'
            ];
            let scopes = [];
            for (const selector of containerSelectors) {
                const found = document.querySelectorAll(selector);
                if (found.length) {
                    scopes = Array.from(found);
                    break;
                }
            }
            if (!scopes.length) scopes = [document];
            const MIN_DIM = 300;
            const largestFromSrcset = (img) => {
                const srcset = img.getAttribute('data-srcset') || img.getAttribute('srcset');
                if (!srcset) return null;
                let best = null, bestW = 0;
                for (const part of srcset.split(',')) {
                    const bits = part.trim().split(/\s+/);
                    if (!bits[0]) continue;
                    const w = bits[1] && /^\d+w$/.test(bits[1]) ? parseInt(bits[1]) : 0;
                    if (w >= bestW) { bestW = w; best = bits[0]; }
                }
                return best;
            };
            const collect = (img) => {
                let src = img.getAttribute('data-zoom-image') || img.getAttribute('data-original') || largestFromSrcset(img) || img.getAttribute('data-src') || img.getAttribute('src');
                if (!src) return;
                const highRes = !!(img.getAttribute('data-zoom-image') || img.getAttribute('data-original') || largestFromSrcset(img));
                try {
                    src = new URL(src, document.baseURI).href;
                } catch (e) {
                    return;
                }
                const lower = src.toLowerCase();
                if (!/\.(jpe?g|png|gif|webp|avif)(\?.*)?$/i.test(lower)) return;
                if (/(^|[\/_.-])(thumb|thumbnail|thumbs|tiny|mini|small|sm)([\/_.-]|$)/.test(lower)) return;
                const dimMatch = lower.match(/(^|[^0-9])(\d{2,4})x(\d{2,4})([^0-9]|$)/);
                if (dimMatch && (parseInt(dimMatch[2]) < MIN_DIM || parseInt(dimMatch[3]) < MIN_DIM)) return;
                if (!highRes) {
                    const nw = img.naturalWidth || 0, nh = img.naturalHeight || 0;
                    if (nw && nh && (nw < MIN_DIM || nh < MIN_DIM)) return;
                    if (!nw && !nh) {
                        const r = img.getBoundingClientRect();
                        if (r.width && r.height && (r.width < 150 || r.height < 150)) return;
                    }
                }
                let decoded = lower;
                try { decoded = decodeURIComponent(lower); } catch (e) {}
                const blockedFiles = ['star_0.gif', 'fullcasecloseoutsquare.jpg', 'solar icon.png'];
                const fileName = decoded.split('?')[0].split('/').pop();
                if (blockedFiles.includes(fileName)) return;
                if (/placeholder|logo|sprite|star|rating|review|banner|icon|badge|button|closeout|solar/.test(decoded)) return;
                const alt = (img.getAttribute('alt') || '').toLowerCase();
                const cls = (img.className || '').toString().toLowerCase();
                if (/star|rating|review|banner|icon|badge/.test(alt + ' ' + cls)) return;
                if (img.closest('.review, .reviews, .rating, .ratings, [class*="review"], [class*="rating"], header, footer, nav')) return;
                if (!seen.has(src)) {
                    seen.add(src);
                    results.push(src);
                }
            };
            for (const scope of scopes) {
                scope.querySelectorAll('img').forEach(collect);
            }
            return results.slice(0, 20);
        """)
    except Exception:
        images = []

    if not title and not sku and not price and not description:
        return None

    return [title, sku, price, '', '', description, '', ', '.join(images)]


def duke_scrape_category(driver, category_url, key):
    # The selector-fallback loops used for Duke probe many locators; with a long
    # implicit wait every miss blocks for seconds, which makes the bot look stuck.
    driver.implicitly_wait(0)
    try:
        try:
            duke_login(driver)
        except Exception as exc:
            print(f'Duke login failed: {exc}')
            print('Continuing without login; prices may be hidden for guest visitors.')
        print(f'Opening category page: {category_url}')
        driver.get(category_url)
        sleep(5)

        seen_products = set()
        page_number = 0
        current_page_url = driver.current_url
        while True:
            product_links = duke_get_product_links(driver)
            print(f'Page {page_number + 1}: found {len(product_links)} product link(s).')
            if not product_links and page_number == 0:
                print('No product links found on the category page. Check the URL or your Duke login.')
            new_products = 0
            for product_url in product_links:
                normalized_url = product_url.split('#')[0].split('?')[0]
                if normalized_url in seen_products:
                    continue
                seen_products.add(normalized_url)
                new_products += 1
                print(f'Scraping {normalized_url}')
                try:
                    row = duke_scrape_product_page(driver, normalized_url)
                    if row:
                        csvWriter(row, key)
                    else:
                        print('Skipped (out of stock or no product data found).')
                except Exception as exc:
                    print(f'Failed to scrape {normalized_url}: {exc}')

            if page_number > 0 and new_products == 0:
                print('No new products found on this page; stopping.')
                break

            # Scraping product pages navigated away; go back to the category
            # page so the next-page link can actually be found.
            driver.get(current_page_url)
            sleep(3)

            next_page = None
            for selector in ['a.pageNavNext', '.pageNavLink.pageNavNext', 'a.pageNavLink[rel="next"]', 'a[rel="next"]', '.next', '.pagination-next', '.action.next', 'li.next a', 'a.next', '.pageNavNext a', 'a[href*="p="]']:
                try:
                    next_page = driver.find_element(By.CSS_SELECTOR, selector)
                    if next_page:
                        break
                except Exception:
                    pass

            if next_page is None:
                for xpath in [
                    '//a[contains(translate(normalize-space(.), "NEXT", "next"), "next")]',
                    '//a[.//img[contains(translate(@alt, "NEXT", "next"), "next")]]',
                    '//a[contains(translate(@title, "NEXT", "next"), "next")]',
                    '//a[normalize-space(text())=">" or normalize-space(text())=">>"]',
                ]:
                    try:
                        next_page = driver.find_element(By.XPATH, xpath)
                        if next_page:
                            break
                    except Exception:
                        pass

            if next_page is None:
                print('No next-page link found; finished paging.')
                break

            try:
                driver.execute_script(clicker, next_page)
                sleep(4)
            except Exception:
                break
            current_page_url = driver.current_url
            page_number += 1
        print(f'Duke scraping finished. Visited {len(seen_products)} product page(s). Results saved to the "{key}" CSV.')
    finally:
        driver.implicitly_wait(10)


CROSSROADS_BASE_URL = 'https://wholesale.crossroadsfamily.com'


def crossroads_is_logged_in(driver):
    try:
        return bool(driver.execute_script(r"""
            const links = Array.from(document.querySelectorAll('a, button'));
            return links.some(el => {
                const href = (el.getAttribute('href') || '').toLowerCase();
                const text = (el.textContent || '').toLowerCase();
                const onclick = (el.getAttribute('onclick') || '').toLowerCase();
                return href.includes('logout') || href.includes('signout') || onclick.includes('logout')
                    || text.includes('log out') || text.includes('logout') || text.includes('sign out');
            });
        """))
    except Exception:
        return False


def crossroads_base_url(category_url=None):
    # Category URLs may live on a subdomain (e.g. fragrance.wholesale.crossroadsfamily.com);
    # log in and filter links on that same host.
    try:
        parsed = urlparse(category_url or '')
        host = parsed.netloc.lower()
        if host == 'crossroadsfamily.com' or host.endswith('.crossroadsfamily.com'):
            return f'{parsed.scheme or "https"}://{parsed.netloc}'
    except Exception:
        pass
    return CROSSROADS_BASE_URL


def crossroads_login(driver, base_url=None):
    base_url = base_url or CROSSROADS_BASE_URL
    driver.get(base_url + '/shop/?context=shop')
    sleep(5)

    if crossroads_is_logged_in(driver):
        print('CrossRoads session already logged in.')
        return driver

    if not crossroads_email or not crossroads_password:
        raise RuntimeError(
            'CrossRoads credentials are not configured. Add CROSSROADS_EMAIL and CROSSROADS_PASSWORD '
            'or fill crossroads_email/crossroads_password in Config.json.'
        )

    # The login form is a popup opened through the site's navbar helper.
    try:
        driver.execute_script("navbar.login({authProvider:'emun'});")
    except Exception:
        # Fallback: click any visible login/sign-in trigger in the navbar.
        try:
            trigger = driver.find_element(
                By.XPATH,
                '//a[contains(translate(normalize-space(.), "LOGIN", "login"), "login") or '
                'contains(translate(normalize-space(.), "SIGN IN", "sign in"), "sign in")]'
            )
            driver.execute_script(clicker, trigger)
        except Exception:
            raise RuntimeError('Could not open the CrossRoads login popup (navbar.login failed).')
    sleep(4)

    # The popup may open in a new window/tab; switch to it if so.
    main_handle = driver.current_window_handle
    popup_handle = None
    for handle in driver.window_handles:
        if handle != main_handle:
            popup_handle = handle
            driver.switch_to.window(handle)
            break

    email_field = None
    password_field = None
    for selector in ['input[type="password"]', 'input[name="password"]', '#password']:
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if password_field is None:
        # The popup may be rendered inside an iframe on the same page.
        for frame in driver.find_elements(By.TAG_NAME, 'iframe'):
            try:
                driver.switch_to.frame(frame)
                password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                break
            except Exception:
                driver.switch_to.default_content()

    if password_field is None:
        raise RuntimeError('Could not find the CrossRoads login popup password field.')

    scope = driver
    try:
        scope = password_field.find_element(By.XPATH, 'ancestor::form[1]')
    except Exception:
        pass
    for selector in ['input[type="email"]', 'input[name="email"]', 'input[name="username"]', '#email', '#username', 'input[type="text"]']:
        try:
            email_field = scope.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass

    if email_field is None:
        raise RuntimeError('Could not find the CrossRoads login popup email field.')

    email_field.clear()
    email_field.send_keys(crossroads_email)
    password_field.clear()
    password_field.send_keys(crossroads_password)

    submit_btn = None
    for selector in ['button[type="submit"]', 'input[type="submit"]', 'button']:
        try:
            submit_btn = scope.find_element(By.CSS_SELECTOR, selector)
            break
        except Exception:
            pass
    if submit_btn is not None:
        driver.execute_script(clicker, submit_btn)
    else:
        password_field.submit()
    sleep(5)

    # Return to the main window/content after the popup closes.
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    if popup_handle is not None:
        try:
            if popup_handle not in driver.window_handles:
                driver.switch_to.window(main_handle)
            elif driver.current_window_handle != main_handle:
                driver.switch_to.window(main_handle)
        except Exception:
            pass
    try:
        driver.refresh()
        sleep(4)
    except Exception:
        pass

    if crossroads_is_logged_in(driver):
        print('CrossRoads login successful.')
    else:
        print('CrossRoads login submitted; could not confirm a logout link, continuing.')
    return driver


def crossroads_get_product_links(driver, allowed_host=None):
    try:
        hrefs = driver.execute_script(r"""
            const seen = new Set();
            return Array.from(document.querySelectorAll('a'))
                .map(link => link.href)
                .filter(href => {
                    if (!href || href.startsWith('javascript:')) return false;
                    const lower = href.toLowerCase();
                    if (lower.includes('/cart') || lower.includes('/checkout') || lower.includes('/login')) return false;
                    return lower.includes('/shop/product') || lower.includes('/product/') || lower.includes('/productdetail')
                        || lower.includes('itemid=') || lower.includes('productid=') || lower.includes('/item/');
                })
                .filter(href => {
                    if (seen.has(href)) return false;
                    seen.add(href);
                    return true;
                });
        """) or []
        allowed = (allowed_host or '').lower()
        def host_ok(href):
            host = urlparse(href).netloc.lower()
            if allowed and host == allowed:
                return True
            return host == 'wholesale.crossroadsfamily.com' or host.endswith('.crossroadsfamily.com')
        links = [href for href in hrefs if host_ok(href)]
        if links:
            return links
        # Fallback: anchors inside product card/tile containers (emun shop grids).
        hrefs = driver.execute_script(r"""
            const seen = new Set();
            const selectors = '[class*="product-card"] a, [class*="productCard"] a, ' +
                '[class*="product-tile"] a, [class*="product-item"] a, ' +
                '.card a, [class*="grid-item"] a, [class*="item-card"] a';
            return Array.from(document.querySelectorAll(selectors))
                .map(link => link.href)
                .filter(href => {
                    if (!href || href.startsWith('javascript:')) return false;
                    const lower = href.toLowerCase();
                    if (lower.includes('/cart') || lower.includes('/checkout') || lower.includes('/login')
                        || lower.includes('/shop/?') || lower.endsWith('/shop/')) return false;
                    if (seen.has(href)) return false;
                    seen.add(href);
                    return true;
                });
        """) or []
        return [href for href in hrefs if host_ok(href)]
    except Exception:
        return []


CROSSROADS_LISTING_PRICES_JS = r"""
    // Map each product link on a category/listing page to the price displayed
    // in its tile. The listing tile shows the real shopper-facing price (e.g.
    // $6.25), so it beats any tier/variant price buried in the product page.
    const currency = /[$€£]\s*\d[\d,]*(?:\.\d+)?/;
    // Tier/qty-break fallback lines (e.g. "As low as $5.20", "12+ $5.20")
    // show a bulk price, not the shopper-facing tile price.
    const TIER_LINE = /as\s+low\s+as|starting\s+at|from\s*\$|tier|per\s*(?:case|dozen)|\bcase\b|\bdozen\b|\bbulk\b|qty|quantity|\d+\s*\+/i;
    const tilePrice = (node) => {
        for (const line of ((node.innerText || '')).split('\n')) {
            const text = line.trim();
            if (!text || TIER_LINE.test(text)) continue;
            const match = text.match(currency);
            if (match) return match[0].trim();
        }
        return '';
    };
    const looksLikeProduct = (href) => {
        if (!href || href.startsWith('javascript:')) return false;
        const lower = href.toLowerCase();
        if (lower.includes('/cart') || lower.includes('/checkout') || lower.includes('/login')) return false;
        return lower.includes('/shop/product') || lower.includes('/product/') || lower.includes('/productdetail')
            || lower.includes('itemid=') || lower.includes('productid=') || lower.includes('/item/');
    };
    const result = {};
    for (const anchor of document.querySelectorAll('a')) {
        if (!looksLikeProduct(anchor.href)) continue;
        const key = anchor.href.split('#')[0];
        if (result[key]) continue;
        let node = anchor;
        for (let depth = 0; node && depth < 6; depth++) {
            // Stop climbing once the container holds other products' links:
            // any price found there could belong to a different tile.
            const links = new Set();
            for (const inner of node.querySelectorAll('a')) {
                if (looksLikeProduct(inner.href)) links.add(inner.href.split('#')[0]);
            }
            if (links.size > 1) break;
            const price = tilePrice(node);
            if (price) {
                result[key] = price;
                break;
            }
            node = node.parentElement;
        }
    }
    return result;
"""


def crossroads_get_listing_prices(driver):
    try:
        prices = driver.execute_script(CROSSROADS_LISTING_PRICES_JS) or {}
        prices = {url: price for url, price in prices.items() if price}
        # A page-wide banner (e.g. a stale "as low as $5.20" element) can leak
        # the SAME value into every tile. A real category rarely prices every
        # product identically, so treat a uniform map as unreliable.
        if len(prices) >= 3 and len(set(prices.values())) == 1:
            print(f'Ignoring listing prices: every tile shows {next(iter(prices.values()))}, likely a shared banner.')
            return {}
        return prices
    except Exception:
        return {}


CROSSROADS_PRICE_SWEEP_JS = r"""
    const texts = [];
    const relatedTexts = [];
    // Elements inside related/recommended product tiles, carousels or listing
    // grids carry OTHER products' prices and must not override the main price.
    const RELATED_SELECTOR = '[class*="related" i],[id*="related" i],[class*="recommend" i],[id*="recommend" i],' +
        '[class*="carousel" i],[class*="slider" i],[class*="upsell" i],[class*="cross-sell" i],' +
        '[class*="also-" i],[class*="similar" i],[class*="you-may" i],[class*="product-list" i],' +
        '[class*="product-grid" i],[class*="listing" i],[class*="suggest" i]';
    const inRelated = (el) => {
        try { return !!el.closest(RELATED_SELECTOR); } catch (e) { return false; }
    };
    // Tier/qty-break fallback values (e.g. a stale "$5.20" bulk price) must
    // never beat the displayed price; demote them to the fallback list.
    const TIER_CONTEXT = /as\s+low\s+as|starting\s+at|from\s*\$|tier|per\s*(?:case|dozen)|\bcase\b|\bdozen\b|\bbulk\b|qty|quantity|variant|size-option|swatch|\d+\s*\+/i;
    const inTier = (el, value) => {
        try {
            const context = ((el.className || '').toString() + ' ' + (el.id || '') + ' ' +
                (el.closest('[class]') ? el.closest('[class]').className.toString() : '') + ' ' + (value || '')).toLowerCase();
            return TIER_CONTEXT.test(context);
        } catch (e) { return false; }
    };
    // Hidden elements (variant templates, collapsed tier tables) carry prices
    // the shopper never sees; demote them to the fallback list.
    const isHidden = (el) => {
        try {
            const rect = el.getBoundingClientRect();
            if (!rect.width || !rect.height) return true;
            const style = getComputedStyle(el);
            return style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0';
        } catch (e) { return false; }
    };
    const push = (el, value) => {
        if (!value) return;
        ((inRelated(el) || isHidden(el) || inTier(el, value)) ? relatedTexts : texts).push(value);
    };
    const addAttributeText = (el) => {
        for (const key of ['data-title', 'title', 'aria-label']) {
            const value = (el.getAttribute(key) || '').trim();
            if (value) push(el, value);
        }
    };
    const visit = (root) => {
        for (const el of root.querySelectorAll('*')) {
            const cls = ((el.className || '').toString() + ' ' + (el.id || '')).toLowerCase();
            if (cls.includes('price')) {
                push(el, (el.textContent || '').trim());
                push(el, el.getAttribute('data-price') || el.getAttribute('content'));
            }
            addAttributeText(el);
            if (el.shadowRoot) visit(el.shadowRoot);
        }
    };
    // Second pass: leaf elements (e.g. <strong>$6.25</strong>) that carry a
    // currency amount but no price-related class/id.
    const currency = /[$€£]\s*\d[\d,]*(?:\.\d+)?/;
    const visitCurrency = (root) => {
        for (const el of root.querySelectorAll('strong, b, span, em, h1, h2, h3, h4, h5, h6, p, td, div, label')) {
            if (el.children.length) continue;
            const text = (el.textContent || '').trim();
            if (!text || text.length > 60 || !currency.test(text)) continue;
            const context = ((el.className || '').toString() + ' ' + (el.id || '') + ' ' +
                (el.closest('[class]') ? el.closest('[class]').className.toString() : '')).toLowerCase();
            if (/cart|checkout|shipping|total|subtotal|minimum|nav|footer|header/.test(context)) continue;
            push(el, text);
            if (el.shadowRoot) visitCurrency(el.shadowRoot);
        }
    };
    visit(document);
    visitCurrency(document);
    for (const frame of document.querySelectorAll('iframe')) {
        try {
            if (frame.contentDocument) {
                visit(frame.contentDocument);
                visitCurrency(frame.contentDocument);
            }
        } catch (e) {}
    }
    return texts.concat(relatedTexts).slice(0, 50);
"""


def crossroads_price_matches(text, price_pattern=r'[$€£]\s*\d[\d,]*(?:\.\d+)?'):
    tier_context = r'(?:as\s+low\s+as|starting\s+at|from\s*\$|related\s+products|recommended\s+products|similar\s+products|you\s+may\s+also\s+like|tier|case\s+price|per\s*(?:case|dozen)|\bcase\b|\bdozen\b|\bbulk\b|qty|quantity|variant|size-option|swatch|\d+\s*\+)'

    def product_hint(fragment):
        if not fragment:
            return False
        if re.search(tier_context, fragment, re.I):
            return False
        return bool(re.search(r'(?:^|[^\w])(?:product|our\s+price|unit\s+price|wholesale|price)\b', fragment, re.I))

    matches = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line or re.search(r'log\s*in|sign\s*in|login', line, re.I):
            continue
        if re.search(tier_context, line, re.I) and not product_hint(line):
            continue
        for match in re.finditer(price_pattern, line):
            start, end = match.span()
            prefix = (line[max(0, start - 40):start] or '').lower()
            suffix = (line[end:min(len(line), end + 16)] or '').lower()
            prefix_hint = product_hint(prefix)
            suffix_hint = product_hint(suffix)
            if re.search(tier_context, prefix, re.I) and not prefix_hint:
                continue
            if not prefix_hint and re.search(tier_context, suffix, re.I):
                continue
            if suffix_hint and not prefix_hint:
                continue
            value = match.group(0).strip()
            if value:
                matches.append(value)
    return matches


def crossroads_extract_price(driver):
    price_pattern = r'[$€£]\s*\d[\d,]*(?:\.\d+)?'
    bare_number_pattern = r'\d[\d,]*(?:\.\d+)?'
    tier_context = r'(?:as\s+low\s+as|starting\s+at|from\s*\$|related\s+products|recommended\s+products|similar\s+products|you\s+may\s+also\s+like|tier|case\s+price|per\s*(?:case|dozen)|\bcase\b|\bdozen\b|\bbulk\b|qty|quantity|variant|size-option|swatch|\d+\s*\+)'

    def product_hint(fragment):
        if not fragment:
            return False
        if re.search(tier_context, fragment, re.I):
            return False
        return bool(re.search(r'(?:^|[^\w])(?:product|our\s+price|unit\s+price|wholesale|price)\b', fragment, re.I))

    def price_matches(text, pattern):
        if 'crossroads_price_matches' in globals():
            return crossroads_price_matches(text, pattern)
        matches = []
        for line in (text or '').splitlines():
            line = line.strip()
            if not line or re.search(r'log\s*in|sign\s*in|login', line, re.I):
                continue
            if re.search(tier_context, line, re.I) and not product_hint(line):
                continue
            for match in re.finditer(pattern, line):
                start, end = match.span()
                prefix = (line[max(0, start - 40):start] or '').lower()
                suffix = (line[end:min(len(line), end + 16)] or '').lower()
                prefix_hint = product_hint(prefix)
                suffix_hint = product_hint(suffix)
                if re.search(tier_context, prefix, re.I) and not prefix_hint:
                    continue
                if not prefix_hint and re.search(tier_context, suffix, re.I):
                    continue
                if suffix_hint and not prefix_hint:
                    continue
                value = match.group(0).strip()
                if value:
                    matches.append(value)
        return matches

    def highest_price(prices):
        best = ''
        best_value = None
        for price in prices:
            value = re.search(r'\d[\d,]*(?:\.\d+)?', str(price))
            if not value:
                continue
            amount = float(value.group(0).replace(',', ''))
            if best_value is None or amount > best_value:
                best = str(price).strip()
                best_value = amount
        return best

    # Sweep every element whose class/id mentions "price", including shadow DOM
    # and same-origin iframes (the emun shop renders price via JS components).
    try:
        texts = driver.execute_script(CROSSROADS_PRICE_SWEEP_JS) or []
    except Exception:
        texts = []
    if isinstance(texts, str):
        texts = [texts]
    elif not isinstance(texts, (list, tuple, set)):
        texts = [texts]
    normalized = []
    for item in texts:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        normalized.extend(line.strip() for line in text.splitlines() if line.strip())
    texts = normalized
    # A single JavaScript value can be returned as one string; iterating that as a
    # sequence of characters truncates prices like "$6.25" to "$6" and makes
    # tier-only values like "Case price $5.20" look like a real product price.
    candidates = []
    for text in texts:
        if re.search(r'log\s*in|sign\s*in|login', text, re.I):
            continue
        candidates.extend(price_matches(text, price_pattern))
    if candidates:
        return highest_price(candidates)
    for text in texts:
        if re.search(r'log\s*in|sign\s*in|login', text, re.I):
            continue
        if re.search(tier_context, text, re.I):
            continue
        match = re.search(price_pattern, text)
        if match:
            return match.group(0).strip()
    for text in texts:
        if re.search(r'log\s*in|sign\s*in|login', text, re.I):
            continue
        match = re.search(bare_number_pattern, text)
        if match:
            return '$' + match.group(0).strip()
    # Last resort: product JSON embedded in scripts/state objects.
    try:
        html = driver.execute_script('return document.documentElement.outerHTML') or ''
    except Exception:
        html = ''
    match = re.search(
        r'"(?:wholesalePrice|unitPrice|price|Price|WholesalePrice|UnitPrice)"\s*:\s*"?(\d[\d,]*(?:\.\d+)?)"?',
        html,
    )
    if match:
        return '$' + match.group(1).strip()
    return ''


CROSSROADS_MAIN_PRICE_JS = r"""
    // Find the price actually displayed next to the product title: climb the
    // title's ancestors and return the most prominent VISIBLE currency amount,
    // skipping retail/compare/struck prices, hidden elements and
    // related-product tiles, and demoting tier/case/variant contexts.
    // Picking the first match in DOM order is wrong:
    // emun pages render quantity-break/variant prices (e.g. $5.20) before the
    // big displayed price (e.g. $6.25), and hidden variant templates also
    // carry other prices.
    const currency = /[$€£]\s*\d[\d,]*(?:\.\d+)?/;
    const RELATED_SELECTOR = '[class*="related" i],[id*="related" i],[class*="recommend" i],[id*="recommend" i],' +
        '[class*="carousel" i],[class*="slider" i],[class*="upsell" i],[class*="cross-sell" i],' +
        '[class*="also-" i],[class*="similar" i],[class*="you-may" i],[class*="product-list" i],' +
        '[class*="product-grid" i],[class*="listing" i],[class*="suggest" i]';
    // HARD contexts are never the displayed wholesale price. SOFT contexts
    // (tier/qty/case tables) usually aren't either, but emun pages sometimes
    // render the main displayed price (e.g. <strong>$6.25</strong>) inside the
    // quantity-break area, so soft matches are demoted rather than dropped.
    const HARD_BAD_CONTEXT = /retail|msrp|srp|compare|\bwas\b|save|strike|\bold\b|cart|checkout|shipping|total|subtotal|minimum|nav|footer|header/;
    const SOFT_BAD_CONTEXT = /as\s+low\s+as|starting\s+at|from\s*\$|tier|case|pack|dozen|bulk|qty|quantity|variant|size-option|swatch|per\s*(?:case|dozen)|\d+\s*\+/;
    let title = null;
    for (const sel of ['h1.product-title', '.product-title', '.product-name', 'h1.item-name', '.item-title', 'h1']) {
        title = document.querySelector(sel);
        if (title && (title.textContent || '').trim()) break;
        title = null;
    }
    if (!title) return '';
    const titleRect = title.getBoundingClientRect();
    const isStruck = (el) => {
        try {
            if (el.closest('s, del, strike')) return true;
            return getComputedStyle(el).textDecorationLine.includes('line-through');
        } catch (e) { return false; }
    };
    const isVisible = (el) => {
        try {
            const rect = el.getBoundingClientRect();
            if (!rect.width || !rect.height) return false;
            const style = getComputedStyle(el);
            return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        } catch (e) { return true; }
    };
    const collectElements = (scope, out) => {
        for (const el of scope.querySelectorAll('*')) {
            out.push(el);
            if (el.shadowRoot) collectElements(el.shadowRoot, out);
        }
    };
    const candidatesIn = (scope) => {
        const found = [];
        const elements = [];
        collectElements(scope, elements);
        for (const el of elements) {
            if (el.children.length) continue;
            const text = (el.textContent || '').trim();
            if (!text || text.length > 60 || !currency.test(text)) continue;
            if (el.closest(RELATED_SELECTOR)) continue;
            const context = ((el.className || '').toString() + ' ' + (el.id || '') + ' ' +
                (el.closest('[class]') ? el.closest('[class]').className.toString() : '') + ' ' + text).toLowerCase();
            if (HARD_BAD_CONTEXT.test(context)) continue;
            if (isStruck(el) || !isVisible(el)) continue;
            const soft = SOFT_BAD_CONTEXT.test(context) ? 1 : 0;
            let fontSize = 0, fontWeight = 0;
            try {
                const style = getComputedStyle(el);
                fontSize = parseFloat(style.fontSize) || 0;
                fontWeight = parseInt(style.fontWeight, 10) || 0;
            } catch (e) {}
            // Bold tags (<strong>/<b>) or heavy computed weight mark the
            // displayed price even when a secondary price uses a larger font.
            const bold = (/^(strong|b)$/i.test(el.tagName) || fontWeight >= 600 ||
                !!el.closest('strong, b')) ? 1 : 0;
            const rect = el.getBoundingClientRect();
            const distance = Math.abs(rect.top - titleRect.bottom) + Math.abs(rect.left - titleRect.left);
            found.push({ text, soft, bold, fontSize, fontWeight, distance });
        }
        return found;
    };
    let node = title.parentElement;
    // Returning the first depth's candidates is how stale tier fallback values
    // (e.g. $5.20) win: a tier row near the title gets returned before the
    // climb reaches the container holding the real displayed price. Only
    // return tier/qty (soft) candidates after the whole climb finds nothing
    // better, preferring bold soft prices (emun sometimes renders the main
    // <strong> price inside the quantity-break area).
    const byProminence = (a, b) => (b.bold - a.bold) || (b.fontSize - a.fontSize) ||
        (b.fontWeight - a.fontWeight) || (a.distance - b.distance);
    let softFallback = null;
    for (let depth = 0; node && depth < 8; depth++) {
        const found = candidatesIn(node);
        const clean = found.filter(c => !c.soft);
        if (clean.length) {
            clean.sort(byProminence);
            return clean[0].text;
        }
        if (!softFallback && found.length) {
            found.sort(byProminence);
            softFallback = found[0];
        }
        node = node.parentElement;
    }
    return softFallback ? softFallback.text : '';
"""


CROSSROADS_TIER_PRICES_JS = r"""
    // Collect currency amounts that appear in tier/qty-break/variant contexts
    // (including hidden templates). Used to detect when a captured listing
    // price is really a stale tier fallback value.
    const currency = /[$€£]\s*\d[\d,]*(?:\.\d+)?/g;
    const TIER_CONTEXT = /as\s+low\s+as|starting\s+at|from\s*\$|tier|per\s*(?:case|dozen)|\bcase\b|\bdozen\b|\bbulk\b|qty|quantity|variant|size-option|swatch|\d+\s*\+/i;
    const out = new Set();
    const visit = (root) => {
        for (const el of root.querySelectorAll('*')) {
            if (!el.children.length) {
                const text = (el.textContent || '').trim();
                if (text && text.length <= 120 && currency.test(text)) {
                    currency.lastIndex = 0;
                    const context = ((el.className || '').toString() + ' ' + (el.id || '') + ' ' +
                        (el.closest('[class]') ? el.closest('[class]').className.toString() : '') + ' ' + text).toLowerCase();
                    let hidden = false;
                    try {
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        hidden = !rect.width || !rect.height || style.display === 'none' ||
                            style.visibility === 'hidden' || style.opacity === '0';
                    } catch (e) {}
                    if (hidden || TIER_CONTEXT.test(context)) {
                        for (const match of text.match(currency) || []) out.add(match.trim());
                        currency.lastIndex = 0;
                    }
                }
            }
            if (el.shadowRoot) visit(el.shadowRoot);
        }
    };
    visit(document);
    return Array.from(out).slice(0, 50);
"""


def crossroads_normalize_price(value):
    return re.sub(r'\s+', '', (value or '')).strip()


def crossroads_tier_prices(driver):
    try:
        return {crossroads_normalize_price(p) for p in (driver.execute_script(CROSSROADS_TIER_PRICES_JS) or []) if p}
    except Exception:
        return set()


CROSSROADS_RELATED_CONTEXT_JS = """
    const RELATED_SELECTOR = '[class*="related" i],[id*="related" i],[class*="recommend" i],[id*="recommend" i],' +
        '[class*="carousel" i],[class*="slider" i],[class*="upsell" i],[class*="cross-sell" i],' +
        '[class*="also-" i],[class*="similar" i],[class*="you-may" i],[class*="product-list" i],' +
        '[class*="product-grid" i],[class*="listing" i],[class*="suggest" i]';
    try { return !!arguments[0].closest(RELATED_SELECTOR); } catch (e) { return false; }
"""


def crossroads_element_in_related(driver, element):
    try:
        return bool(driver.execute_script(CROSSROADS_RELATED_CONTEXT_JS, element))
    except Exception:
        return False


def crossroads_price_hidden_by_login(body_text):
    return bool(re.search(
        r'(?:log\s*in|login|sign\s*in)[^\n]{0,40}(?:price|pricing)|(?:price|pricing)[^\n]{0,40}(?:log\s*in|login|sign\s*in)',
        body_text, re.I,
    ))


def crossroads_extract_product_metadata(body_text):
    text = (body_text or '').replace('\r\n', '\n').replace('\r', '\n')
    labels = (
        ('ITEM #', r'(?:ITEM\s*#|ITEM\s*NO\.?|ITEM\s*NUMBER|ITEM)\b'),
        ('MINIMUM QTY', r'(?:MINIMUM\s*QTY|MINIMUM\s*QUANTITY|MIN\s*QTY|QTY\s*MINIMUM)\b'),
        ('DIMENSIONS', r'(?:DIMENSIONS?|DIMENSION)\b'),
        ('DESIGNER', r'DESIGNER\b'),
    )
    metadata = {}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for label, pattern in labels:
            match = re.search(rf'^{pattern}\s*[:#\-]?\s*(.+)$', line, re.I)
            if match:
                value = re.sub(r'\s+', ' ', match.group(1)).strip(' :;,-')
                if value and value.lower() not in {'n/a', 'na', 'none', 'not available'}:
                    metadata[label] = value
                break

    if len(metadata) < 4:
        for label, pattern in labels:
            if label in metadata:
                continue
            match = re.search(
                rf'{pattern}\s*[:#\-]?\s*(.+?)(?=(?:\s*(?:ITEM\s*#|ITEM\s*NO\.?|ITEM\s*NUMBER|ITEM|MINIMUM\s*QTY|MINIMUM\s*QUANTITY|MIN\s*QTY|QTY\s*MINIMUM|DIMENSIONS?|DIMENSION|DESIGNER)\s*[:#\-]?|$))',
                text,
                re.I | re.S,
            )
            if match:
                value = re.sub(r'\s+', ' ', match.group(1)).strip(' :;,-')
                if value and value.lower() not in {'n/a', 'na', 'none', 'not available'}:
                    metadata[label] = value

    return metadata


def crossroads_price_after_sku(body_text, sku):
    sku = re.sub(r'^(?:SKU|Item\s*(?:#|No\.?|Number))\s*[:#]?\s*', '', sku.strip(), flags=re.I)
    if not sku:
        return ''
    tier_context = r'(?:as\s+low\s+as|starting\s+at|from\s*\$|tier|case\s+price|per\s*(?:case|dozen)|\bcase\b|\bdozen\b|\bbulk\b|qty|quantity|variant|size-option|swatch|\d+\s*\+)'
    sku_pattern = re.escape(sku) + r'(?![\w-])'
    match = re.search(
        r'\b(?:SKU|Item\s*(?:#|No\.?|Number))\s*[:#]?\s*' + sku_pattern,
        body_text, re.I,
    )
    if not match:
        match = re.search(r'^\s*' + sku_pattern, body_text, re.M)
    if not match:
        return ''
    def non_tier_prices(block):
        prices = []
        for line in (block or '').splitlines():
            line = line.strip()
            if not line or re.search(r'log\s*in|sign\s*in|login', line, re.I):
                continue
            if re.search(tier_context, line, re.I):
                continue
            price = re.search(r'\$\s*\d[\d,]*(?:\.\d+)?', line)
            if price:
                prices.append(price.group(0).strip())
        return prices
    after_sku = body_text[match.end():]
    # Do not borrow a price from another product when this SKU has no price.
    after_sku = re.split(
        r'\n\s*(?:SKU\b|Item\s*(?:#|No\.?|Number)(?=\s|:|$)|'
        r'(?:Related|Recommended|Similar)\s+Products\b|'
        r'You\s+May\s+Also\s+Like\b)',
        after_sku, maxsplit=1, flags=re.I,
    )[0]
    prices = non_tier_prices(after_sku)
    if prices:
        return prices[-1]
    # Emun product pages often render the displayed price ABOVE the SKU line.
    # Look back within the same product block (bounded by the previous SKU or
    # related-products marker) and take the price closest to this SKU.
    before_sku = body_text[:match.start()]
    before_sku = re.split(
        r'(?:\n|\A)\s*(?:SKU\b|Item\s*(?:#|No\.?|Number)(?=\s|:|$)|'
        r'(?:Related|Recommended|Similar)\s+Products\b|'
        r'You\s+May\s+Also\s+Like\b)',
        before_sku, flags=re.I,
    )[-1]
    prices = non_tier_prices(before_sku)
    return prices[-1] if prices else ''


CROSSROADS_IMAGES_JS = r"""
    // Collect product images, including ones rendered inside shadow DOM by the
    // emun shop components. Two tiers: "strict" (clearly product gallery images)
    // and "relaxed" (anything plausible) so that over-filtering can never leave
    // a product with zero images when the page has some.
    const seen = new Set();
    const strict = [];
    const relaxed = [];
    const BAD_URL = /placeholder|logo|sprite|spinner|loading|star|rating|review|banner|icon|badge|button|favicon|captcha|\.svg(\?|$)/;
    const BAD_CTX = /star|rating|review|banner|icon|badge|logo|avatar/;
    const BAD_ZONE = 'header, footer, nav, .navbar, [class*="related" i], [class*="recommend" i], ' +
        '[class*="upsell" i], [class*="cross-sell" i], [class*="you-may" i], [class*="similar" i]';
    const GALLERY = '[class*="product-image" i], [class*="product-gallery" i], [class*="product-media" i], ' +
        '[class*="main-image" i], [class*="item-image" i], [class*="gallery" i], [class*="carousel" i], ' +
        '[class*="pdp" i], [id*="gallery" i], [id*="product-image" i]';
    const resolve = (src) => {
        if (!src) return null;
        try { return new URL(src, document.baseURI).href; } catch (e) { return null; }
    };
    const pushUrl = (href, area, preferred) => {
        if (!href || href.startsWith('data:') || href.startsWith('javascript:')) return;
        if (BAD_URL.test(href.toLowerCase())) return;
        if (seen.has(href)) return;
        seen.add(href);
        (preferred ? strict : relaxed).push({ src: href, area: area || 0 });
    };
    const largestFromSrcset = (el) => {
        const srcset = el.getAttribute('data-srcset') || el.getAttribute('srcset');
        if (!srcset) return null;
        let best = null, bestW = 0;
        for (const part of srcset.split(',')) {
            const bits = part.trim().split(/\s+/);
            if (!bits[0]) continue;
            const w = bits[1] && /^\d+w$/.test(bits[1]) ? parseInt(bits[1]) : 0;
            if (w >= bestW) { bestW = w; best = bits[0]; }
        }
        return best;
    };
    const inZone = (el, selector) => {
        let node = el;
        while (node) {
            try { if (node.closest && node.closest(selector)) return true; } catch (e) {}
            const root = node.getRootNode ? node.getRootNode() : null;
            node = (root && root.host) ? root.host : null;
        }
        return false;
    };
    const collectImg = (img) => {
        const highRes = img.getAttribute('data-zoom-image') || img.getAttribute('data-original') || largestFromSrcset(img);
        const src = resolve(highRes || img.getAttribute('data-src') || img.currentSrc || img.getAttribute('src'));
        if (!src) return;
        const alt = (img.getAttribute('alt') || '').toLowerCase();
        const cls = (img.className || '').toString().toLowerCase();
        if (BAD_CTX.test(alt + ' ' + cls)) return;
        if (inZone(img, BAD_ZONE)) return;
        const nw = img.naturalWidth || 0, nh = img.naturalHeight || 0;
        let area = nw * nh;
        if (!area) {
            const r = img.getBoundingClientRect();
            area = (r.width || 0) * (r.height || 0);
        }
        const preferred = !!highRes || inZone(img, GALLERY) || area >= 200 * 200;
        pushUrl(src, area, preferred && !(area && area < 80 * 80));
    };
    const collectAnchor = (a) => {
        const href = resolve(a.getAttribute('href') || '');
        if (!href || !/\.(jpe?g|png|gif|webp|avif)(\?|$)/i.test(href)) return;
        if (inZone(a, BAD_ZONE)) return;
        pushUrl(href, 0, inZone(a, GALLERY));
    };
    const collectBackground = (el) => {
        if (!inZone(el, GALLERY) || inZone(el, BAD_ZONE)) return;
        let bg = '';
        try { bg = getComputedStyle(el).backgroundImage || ''; } catch (e) {}
        const match = bg.match(/url\((['"]?)(.*?)\1\)/);
        if (!match || !match[2]) return;
        const r = el.getBoundingClientRect();
        pushUrl(resolve(match[2]), (r.width || 0) * (r.height || 0), true);
    };
    const visit = (root) => {
        for (const el of root.querySelectorAll('*')) {
            const tag = el.tagName ? el.tagName.toLowerCase() : '';
            if (tag === 'img') collectImg(el);
            else if (tag === 'a') collectAnchor(el);
            else collectBackground(el);
            if (el.shadowRoot) visit(el.shadowRoot);
        }
    };
    visit(document);
    for (const frame of document.querySelectorAll('iframe')) {
        try { if (frame.contentDocument) visit(frame.contentDocument); } catch (e) {}
    }
    const picked = strict.length ? strict : relaxed;
    picked.sort((a, b) => b.area - a.area);
    return picked.slice(0, 20).map(item => item.src);
"""


def crossroads_image_file_size(url, cookie_header='', timeout=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    if cookie_header:
        headers['Cookie'] = cookie_header
    try:
        request = urllib.request.Request(url, headers=headers, method='HEAD')
        with urllib.request.urlopen(request, timeout=timeout) as response:
            length = response.headers.get('Content-Length')
            if length and length.isdigit():
                return int(length)
    except Exception:
        pass
    try:
        request = urllib.request.Request(url, headers=dict(headers, Range='bytes=0-0'))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            match = re.search(r'/(\d+)\s*$', response.headers.get('Content-Range') or '')
            if match:
                return int(match.group(1))
            length = response.headers.get('Content-Length')
            if length and length.isdigit() and response.status != 206:
                return int(length)
    except Exception:
        pass
    return 0


def crossroads_sort_images_by_file_size(driver, urls):
    # Upload order matters downstream: the first image becomes the primary
    # product photo, so put the largest file (usually the highest quality
    # shot) first.
    urls = [u for u in urls if u]
    if len(urls) <= 1:
        return urls
    cookie_header = ''
    try:
        cookie_header = '; '.join(
            '{}={}'.format(c.get('name'), c.get('value'))
            for c in driver.get_cookies() if c.get('name')
        )
    except Exception:
        pass
    sized = [(crossroads_image_file_size(url, cookie_header), index, url) for index, url in enumerate(urls)]
    if not any(size for size, _, _ in sized):
        return urls
    sized.sort(key=lambda item: (-item[0], item[1]))
    return [url for _, _, url in sized]


def crossroads_scrape_product_page(driver, product_url, allow_relogin=True, listing_price=''):
    driver.get(product_url)
    sleep(4)

    body_text = driver.execute_script("return document.body ? document.body.innerText : ''") or ''

    title = ''
    for selector in ['h1.product-title', '.product-title', '.product-name', 'h1.item-name', '.item-title', 'h1', 'h2.product-title']:
        try:
            title = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if title:
                break
        except Exception:
            pass

    sku = ''
    for selector in ['.product-sku', '.sku', '.item-number', '.item-no', '[itemprop="sku"]']:
        try:
            sku = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if sku:
                break
        except Exception:
            pass
    if not sku:
        match = re.search(r'(?:SKU|Item\s*(?:#|No\.?|Number))\s*[:#]?\s*([A-Za-z0-9\-]+)', body_text, re.I)
        if match:
            sku = match.group(1).strip()

    price = (listing_price or '').strip()
    # The category listing tile shows the shopper-facing price for this exact
    # product; when we captured it there, it is authoritative.
    # The SKU/body-text regex is intentionally not used as a normal fallback:
    # it can grab stale tier/qty values like $5.20 before the actual product
    # price. Prefer the title-scoped visible price and the generic DOM sweep.
    try:
        main_price = (driver.execute_script(CROSSROADS_MAIN_PRICE_JS) or '').strip()
    except Exception:
        main_price = ''
    if price and main_price and crossroads_normalize_price(price) != crossroads_normalize_price(main_price):
        # A listing price that reappears on the product page only in a
        # tier/qty context is a stale tier fallback value, not the shopper
        # price; trust the displayed main price instead.
        if crossroads_normalize_price(price) in crossroads_tier_prices(driver):
            print(f'Listing price {price} matches a tier value on the product page; using displayed price {main_price}.')
            price = main_price
    if not price:
        price = main_price
    if not price:
        price = crossroads_extract_price(driver)
    if not price and crossroads_price_hidden_by_login(body_text):
        if allow_relogin:
            print('Price appears hidden behind login; re-logging into CrossRoads and retrying this product.')
            try:
                crossroads_login(driver, crossroads_base_url(product_url))
            except Exception as exc:
                print(f'CrossRoads re-login failed: {exc}')
            return crossroads_scrape_product_page(driver, product_url, allow_relogin=False, listing_price=listing_price)
        print('Price appears hidden behind login on this page; check your CrossRoads credentials/session.')
    print(f'CrossRoads selected price for {product_url}: {price or "<empty>"}')

    description = ''
    for selector in ['.product-description', '.description', '[itemprop="description"]', '.product-details-description', '.item-description']:
        try:
            description = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if description:
                break
        except Exception:
            pass
    if not description:
        match = re.search(r'Description\s*[:\n\r]+\s*(.*?)(?:\n\s*\n|$)', body_text, re.I | re.S)
        if match:
            description = re.sub(r'\s+', ' ', match.group(1)).strip()

    details = ''
    for selector in ['.product-details', '.details', '.product-specs', '.specifications', '.product-attributes', '.item-details']:
        try:
            details = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if details:
                break
        except Exception:
            pass
    if not details:
        match = re.search(r'Details\s*[:\n\r]+\s*(.*?)(?:\n\s*\n|$)', body_text, re.I | re.S)
        if match:
            details = re.sub(r'\s+', ' ', match.group(1)).strip()
    if details and details == description:
        details = ''

    metadata = crossroads_extract_product_metadata(body_text)
    metadata_block = ' | '.join(
        f'{label}: {value}'
        for label, value in [
            ('ITEM #', metadata.get('ITEM #', '')),
            ('MINIMUM QTY', metadata.get('MINIMUM QTY', '')),
            ('DIMENSIONS', metadata.get('DIMENSIONS', '')),
            ('DESIGNER', metadata.get('DESIGNER', '')),
        ]
        if value
    )
    description_text = ' | '.join(part for part in [description, details] if part)
    if metadata_block:
        description_text = ' | '.join(part for part in [description_text, metadata_block] if part)

    images = []
    try:
        images = driver.execute_script(CROSSROADS_IMAGES_JS) or []
    except Exception:
        images = []
    images = crossroads_sort_images_by_file_size(driver, images)

    if not title and not sku and not price and not description and not metadata_block:
        return None

    return [title, sku, price, '', '', description_text, '', ', '.join(images)]


def crossroads_set_page(url, page_number):
    if re.search(r'([?&])page=\d+', url):
        return re.sub(r'([?&])page=\d+', r'\g<1>page=' + str(page_number), url)
    separator = '&' if '?' in url else '?'
    return f'{url}{separator}page={page_number}'


def crossroads_scrape_category(driver, category_url, key):
    # Selector-fallback loops probe many locators; with a long implicit wait
    # every miss blocks for seconds, which makes the bot look stuck.
    driver.implicitly_wait(0)
    try:
        base_url = crossroads_base_url(category_url)
        allowed_host = urlparse(base_url).netloc.lower()
        try:
            crossroads_login(driver, base_url)
        except Exception as exc:
            print(f'CrossRoads login failed: {exc}')
            print('Continuing without login; prices may be hidden for guest visitors.')

        seen_products = set()
        page_number = 1
        while True:
            page_url = crossroads_set_page(category_url, page_number)
            print(f'Opening category page: {page_url}')
            driver.get(page_url)
            sleep(5)

            product_links = crossroads_get_product_links(driver, allowed_host)
            listing_prices = crossroads_get_listing_prices(driver)
            print(f'Page {page_number}: found {len(product_links)} product link(s).')
            if not product_links:
                if page_number == 1:
                    print('No product links found on the category page. Check the URL or your CrossRoads login.')
                break

            new_products = 0
            for product_url in product_links:
                normalized_url = product_url.split('#')[0]
                if normalized_url in seen_products:
                    continue
                seen_products.add(normalized_url)
                new_products += 1
                print(f'Scraping {normalized_url}')
                listing_price = listing_prices.get(normalized_url) or listing_prices.get(product_url, '')
                if listing_price:
                    print(f'Using listing price from category page: {listing_price}')
                try:
                    row = crossroads_scrape_product_page(driver, normalized_url, listing_price=listing_price)
                    if row:
                        csvWriter(row, key)
                    else:
                        print('Skipped (no product data found).')
                except Exception as exc:
                    print(f'Failed to scrape {normalized_url}: {exc}')

            if new_products == 0:
                print('No new products found on this page; stopping.')
                break
            page_number += 1
        print(f'CrossRoads scraping finished. Visited {len(seen_products)} product page(s). Results saved to the "{key}" CSV.')
    finally:
        driver.implicitly_wait(10)


def main(driver, number, scrap_driver):
    try:
        if number == 1:
            main_categories = driver.find_elements(By.XPATH, "//a[starts-with(@href, '/Category?')]")
            m_cat_list = {}
            for cat in main_categories:
                cat_name = driver.execute_script("return arguments[0].querySelector('span').innerText;", cat)
                cat_link = cat.get_attribute('href')
                m_cat_list[cat_name] = cat_link
            for index, item in enumerate(m_cat_list.keys()):
                print(index, '-> ', item) 
            
            select_cat = int(input('Select A Category\n'))
            key = list(m_cat_list.keys())[select_cat]
            csvMaker(key)
            get_url = m_cat_list.get(key)
            driver.get(get_url)
            sleep(10)
            # pagination 
            try:
                next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                while True:
                    # scraping part here
                    vendors = get_vendor(driver)
                    scraper(driver, vendors, number, key, scrap_driver) 
                    try:
                        next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                        driver.execute_script(clicker, next)
                        sleep(6)
                    except:
                        break
            except Exception as e:
                pass 
            


        if number == 2:
            sub_categories = driver.find_elements(By.XPATH, "//a[starts-with(@href, '/Catalog?')]")
            s_cat_list = {}
        
            for cat in sub_categories:
                cat_name = driver.execute_script("return arguments[0].querySelector('span').innerText;", cat)
                cat_link = cat.get_attribute('href')
                s_cat_list[cat_name] = cat_link

            for index, item in enumerate(s_cat_list.keys()):
                print(index, '-> ', item)  

              
            select_cat = int(input('Select A Catalog\n'))
            key = list(s_cat_list.keys())[select_cat]
            csvMaker(key)
            get_url = s_cat_list.get(key)
            driver.get(get_url)
            sleep(10)
            # pagination 
            try:
                next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                while True:
                    # scraping part here
                    scraper(driver, vendors, number, key, scrap_driver) 
                    try:
                        next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                        driver.execute_script(clicker, next)
                        sleep(6)
                    except:
                        break
            except Exception as e:
                pass

        if number == 3:
            v_link = input('Vendor Link: ')
            key = v_link.rsplit('/', 1)[-1]
            fixed_price = input('Enter a price to set for all items (leave empty to keep original prices): ').strip()
            if not fixed_price:
                fixed_price = None
            keyword = input('Enter a word to keep only entries containing it (leave empty to keep all): ').strip()
            if not keyword:
                keyword = None
            csvMaker(key)
            try:
                driver.get(v_link)
                products_all = driver.find_element(By.XPATH, '//a[@data-nclick-name="vendor.menu.allitems"]').get_attribute('href')
                print(products_all)
                driver.get(products_all)
                while True:
                    product_url_list = []
                    try:
                        items = driver.find_elements(By.XPATH, '//a[@data-nclick-name="vendor.allitems.item"]')
                        print('Total Items: ', len(items))
                        if len(items) < 1:
                            break
                        for item in items[::2]:
                            try:
                                item_url = item.get_attribute('href')
                                print(item_url)
                                product_url_list.append(item_url)
                            except:
                                pass 
                        product_details_scrap(scrap_driver, product_url_list, key, fixed_price, keyword)
                    except Exception as e:
                        pass 
                        items_checker = True
                        break
                    try:
                        next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                        driver.execute_script(clicker, next)
                        sleep(6)
                        is_visible = driver.execute_script("""
                        return (function () {
                        const el = document.querySelector(
                            'li.btn_next_paging.paging-button.paging-next'
                        );

                        if (!el) return false;

                        const style = window.getComputedStyle(el);
                        return (
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            style.opacity !== '0' &&
                            el.offsetWidth > 0 &&
                            el.offsetHeight > 0
                        );
                        })();
                        """)
                        if is_visible is False:
                            break
                    except:
                        break

                # pagination 
                # if items_checker:
                #     try:
                #         next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                #         while True:
                #             # scraping part here
                #             try:
                #                 next = driver.execute_script("return document.querySelector('li.btn_next_paging')")
                #                 driver.execute_script(clicker, next)
                #                 sleep(6)
                #             except:
                #                 break
                #     except Exception as e:
                #         pass
            except Exception as e:
                print(e)

        if number == 4:
            duke_url = input('Duke Imports category URL: ').strip()
            if not duke_url:
                print('No Duke URL provided.')
                return
            key = input('CSV name (leave blank to use category name): ').strip() or 'dukeimports'
            csvMaker(key)
            duke_scrape_category(driver, duke_url, key)

        if number == 5:
            crossroads_url = input('CrossRoads category URL: ').strip()
            if not crossroads_url:
                print('No CrossRoads URL provided.')
                return
            key = input('CSV name (leave blank to use "crossroads"): ').strip()
            if not key:
                match = re.search(r'[?&]Category=([^&]+)', crossroads_url, re.I)
                key = match.group(1) if match else 'crossroads'
            csvMaker(key)
            crossroads_scrape_category(driver, crossroads_url, key)

    except Exception as e:
        print(f'Scraping failed: {e}')


if __name__ == '__main__':
    driver = get_browser(headless=False)
    scrap_driver = get_browser(headless=False)
    driver = sign_in(driver)
    scrap_driver = sign_in(scrap_driver)
    driver.maximize_window()
    driver.implicitly_wait(10)
    scrap_driver.implicitly_wait(5)
    number = int(input("""
    1. -> Scrap by Category
    2. -> Scrap by Catalog
    3. -> Scrap by vendor link
    4. -> Scrap Duke Imports category URL
    5. -> Scrap CrossRoads category URL
    """))
    main(driver, number, scrap_driver)
    # product_details_scrap(driver, ['https://www.fashiongo.net/Item/21638783?paKey=202405152c85431acbb0b1e8a2aaeeed7b29cb38&listkey=097a92c8-fcdf-4bb4-bbcc-cdf71b3ed01b'], 'test')
