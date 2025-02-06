from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from lib import bit_api


class Driver:
    def __init__(self, browser_id):
        self.browser_id = browser_id
        self.driver = self.open_browser()
        self.driver.implicitly_wait(20)

    # 打开browser
    def open_browser(self):
        res = bit_api.openBrowser(self.browser_id)
        driver_path = res['data']['driver']
        debugger_address = res['data']['http']

        # selenium 连接代码
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)

        chrome_service = Service(driver_path)
        return webdriver.Chrome(service=chrome_service, options=chrome_options)

    def quit_browser(self):
        bit_api.closeBrowser(self.browser_id)

    # 获取网页某个元素
    def find_element(self, selector):
        return self.driver.find_element(By.CSS_SELECTOR, selector)

    # 打开网页
    def open_webpage(self, url):
        self.driver.get(url)

    # 点击按钮
    def click_btn(self, selector):
        search_btn = self.find_element(selector)
        search_btn.click()

    # 输入内容
    def input_text(self, selector, text):
        search_box = self.find_element(selector)
        search_box.send_keys(text)

    # 文件路径
    def upload_txt(self, selector, file_path):
        search_box = self.find_element(selector)
        search_box.send_keys(file_path)

    def hover(self, selector):
        search_box = self.find_element(selector)
        ActionChains(self.driver).move_to_element(search_box).perform()
