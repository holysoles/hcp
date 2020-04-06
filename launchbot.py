import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

# Setting options to hide selenium
opts = Options()
opts.add_argument("user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, "
                  "like Gecko) Chrome/80.0.3987.132 Mobile Safari/537.36")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option('useAutomationExtension', False)
opts.add_argument("start-maximized")
opts.add_argument("disable-infobars")  # hides "chrome is being controlled by automated test software
opts.add_argument("--disable-extensions")
opts.add_argument("--disable-gpu")
opts.add_argument("--headless")
opts.add_argument("--log-level=OFF")  # disable logging on cmd window



def runbot(link, size, proxy, q, row, kill):
    if proxy != 0:
        opts.add_argument('--proxy-server=%s' % proxy)

    chromedriver_autoinstaller.install()

    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
    })
    driver.execute_cdp_cmd("Network.enable", {})
    driver.get(link)
    # time.sleep(0) wait to begin actions

    # check for error popups and network issues here
    # 403 forbidden check
    forbiddenerror = driver.find_elements_by_tag_name("H1")
    if len(forbiddenerror) > 0:
        if forbiddenerror[0].get_attribute('innerText') == "Access Denied":
            error = 'forbidden'
            result = [row, error]
            q.put(result)
            driver.quit()
            return

    # session error popup
    sessionerror = driver.find_element_by_id("sessionErrorModalHeading")
    if sessionerror:
        print(sessionerror)
        time.sleep(1)
        # close button, classname:c-modal__close
        # how to handle this error? refresh page and check again?, close and continue?

    # check for countdown timer
    prelaunch = driver.find_elements_by_class_name("PreLaunch")
    while prelaunch:
        time.sleep(0.1)  # is this necessary to wait?
        prelaunch = driver.find_elements_by_class_name("PreLaunch")

    # check cart items
    cartcount = driver.find_elements_by_class_name("CartCount-badge")
    while not cartcount:
        #listen for kill event
        if kill.is_set():
            driver.quit()
            kill.clear()
            return

        # check if size is in stock
        sizeelement = driver.find_element_by_id('input_radio_size_' + size)
        if sizeelement:
            outofstock = sizeelement.get_attribute('disabled') == 'true'
            if outofstock:
                error = 'oos'
                result = [row, error]
                q.put(result)
                driver.quit()
                return

        # select and click size button
        clicksizestr = "document.getElementById('input_radio_size_" + size + "').click()"
        driver.execute_script(clicksizestr)

        # select and click add to cart button
        pagebuttons = driver.find_elements_by_class_name("ProductDetails-form__action")
        for button in pagebuttons:
            global addtocartbutton
            if button.get_attribute('innerText') == "ADD TO CART":
                addtocartbutton = button
                addtocartbutton.click()
                # wait for item to load to cart
                loading = driver.find_elements_by_class_name("global-loading")
                while loading:
                    loading = driver.find_elements_by_class_name("global-loading")

        cartcount = driver.find_elements_by_class_name("CartCount-badge")
    if cartcount:
        # check if specified product is in cart

        cookies = driver.get_cookies()
        result = [row, cookies]

        q.put(result)

        driver.quit()
        return
