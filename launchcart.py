import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

def opencart(site, cookies, proxy):
    global driver  # window wont get garbage collected on finish

    # set options to hide selenium/webdriver characteristics
    opts = Options()
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Mobile Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument("disable-infobars")
    opts.add_argument("start-maximized")
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

    # launch new browser window, add cookies and load cart
    driver.get(site)
    for cookie in cookies:
        if 'expiry' in cookie:
            cookie['expiry'] = int(cookie['expiry'])
        driver.add_cookie(cookie)
    cartlink = site + "cart"
    driver.get(cartlink)

    # close cookie agreement
    time.sleep(1)
    if driver.find_element_by_id('ccpaClose'):
        driver.execute_script("document.getElementById('ccpaClose').click()")

    return
