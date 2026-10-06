import re
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


def duke_login(driver):
    login_url = 'https://www.dukeimports.com/login.jhtm'
    driver.get(login_url)
    sleep(3)

    email_locators = [
        'input[name="username"]',
        '#username',
        'input[name="login[username]"]',
        'input[name="email"]',
        '#email',
        'input[type="email"]',
        'form[action*="login"] input[type="text"]'
    ]
    password_locators = [
        'input[name="password"]',
        '#password',
        'input[name="login[password]"]',
        'input[name="pass"]',
        '#pass',
        'input[type="password"]'
    ]

    if not duke_email or not duke_password:
        raise RuntimeError(
            'Duke credentials are not configured. Add DUKE_EMAIL and DUKE_PASSWORD '
            'or fill duke_email/duke_password in Config.json.'
        )

    email_field = None
    for selector in email_locators:
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
    for selector in password_locators:
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

    if submit_btn is None:
        try:
            submit_btn = driver.find_element(By.XPATH, '//button[@type="submit"] | //button[contains(., "Sign In")] | //button[contains(., "Login")] | //input[@type="submit"]')
        except Exception:
            pass

    if submit_btn is not None:
        driver.execute_script(clicker, submit_btn)
        sleep(4)
    else:
        password_field.submit()
        sleep(4)

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
    for attempt in range(3):
        try:
            price_cell_text = driver.execute_script("""
                const selectors = [
                    '.price_cell', 'td.price_cell', '.priceCell', '.price-cell',
                    '[class*="price_cell"]', '[class*="priceCell"]',
                    '.price', 'span.price', 'td.price', 'div.price',
                    '.price-box', '.price-box .price', '.price-container',
                    '.product-info-price .price', '.product-pricing .price',
                    '.regular-price', '.special-price', '.old-price', '.final-price',
                    '.product-info-main .price', '[data-price-amount]', '[data-price]',
                    '[itemprop="price"]', 'meta[itemprop="price"]',
                    '.product-info-main [itemprop="price"]'
                ];
                const parts = [];
                const seen = new Set();
                for (const selector of selectors) {
                    document.querySelectorAll(selector).forEach((cell) => {
                        const text = (cell.innerText || cell.textContent || '').trim();
                        const amount = (cell.getAttribute('data-price-amount') || cell.getAttribute('data-price') || '').trim();
                        const itemPrice = (cell.getAttribute('content') || '').trim();
                        const candidates = [amount, itemPrice, text].filter(Boolean);
                        candidates.forEach((candidate) => {
                            if (!seen.has(candidate)) {
                                seen.add(candidate);
                                parts.push(candidate);
                            }
                        });
                    });
                }
                return parts.slice(0, 40).join('\\n');
            """) or ''
            match = re.search(price_pattern, price_cell_text)
            if match:
                price = match.group(0).strip()
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

    description = ''
    for selector in ['.product.attribute.description .value', '.description .value', '[data-role="description"]', '.product-info-main .description', '.product.description']:
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

    images = []
    try:
        images = driver.execute_script(r"""
            const seen = new Set();
            const selectors = ['img[src]', 'img[data-src]', 'img[data-zoom-image]'];
            const results = [];
            for (const selector of selectors) {
                document.querySelectorAll(selector).forEach((img) => {
                    const src = img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-zoom-image') || img.getAttribute('data-original');
                    if (!src) return;
                    const lower = src.toLowerCase();
                    if (!/\.(jpe?g|png|gif|webp|avif)(\?.*)?$/i.test(lower)) return;
                    if (lower.includes('placeholder') || lower.includes('logo') || lower.includes('sprite')) return;
                    if (!seen.has(src)) {
                        seen.add(src);
                        results.push(src);
                    }
                });
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
    """))
    main(driver, number, scrap_driver)
    # product_details_scrap(driver, ['https://www.fashiongo.net/Item/21638783?paKey=202405152c85431acbb0b1e8a2aaeeed7b29cb38&listkey=097a92c8-fcdf-4bb4-bbcc-cdf71b3ed01b'], 'test')
