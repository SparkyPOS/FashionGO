from utils import *

if not os.path.exists('Data'):
    os.mkdir('Data')

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
    with open('cookies.pkl', 'wb') as f:
        pickle.dump(cookies, f)

    driver.quit() 


def sign_in(driver):
    driver.get('https://www.fashiongo.net')
    with open('cookies.pkl', 'rb') as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    sleep(3)
    return driver 


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



    except Exception as e:
        pass 
            
       
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
"""))
    main(driver, number, scrap_driver)
    # product_details_scrap(driver, ['https://www.fashiongo.net/Item/21638783?paKey=202405152c85431acbb0b1e8a2aaeeed7b29cb38&listkey=097a92c8-fcdf-4bb4-bbcc-cdf71b3ed01b'], 'test')
    