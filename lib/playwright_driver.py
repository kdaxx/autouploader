from playwright.sync_api import sync_playwright

from lib import bit_api


class Driver:
    def __init__(self, browser_id):
        self.browser_id = browser_id
        self.ctx = self.open_browser()
        self.page = self.ctx.pages[0]

    # 打开浏览器
    def open_browser(self):
        res = bit_api.openBrowser(self.browser_id)
        # 指纹浏览器的WS调试接口
        ws_address = res['data']['ws']

        playwright = sync_playwright().start()

        browser = playwright.chromium.connect_over_cdp(ws_address)
        ctx = browser.contexts[0]
        return ctx

    # 退出浏览器
    def quit_browser(self):
        bit_api.closeBrowser(self.browser_id)

    # 关闭窗口
    def close_window(self):
        self.page.close()

    # 获取网页某个元素
    def find_element(self, selector):
        return self.page.locator(selector)

    # 打开网页
    def open_webpage(self, url):
        self.page.goto(url)

    # 点击按钮
    def click_btn(self, selector):
        search_btn = self.find_element(selector)
        search_btn.click()

    # 输入内容
    def input_text(self, selector, text):
        search_box = self.find_element(selector)
        search_box.type(text)

    # 文件路径
    def upload_file(self, selector, file_path):
        search_box = self.find_element(selector)
        search_box.set_input_files(file_path)

    # 上传文件
    def upload_file_with_filechooser(self, selector, file_path):
        with self.page.expect_file_chooser() as file_info:
            # 此处不能使用 click, 而是通过dispatch分发事件
            self.page.locator(selector).dispatch_event("click")
        file_info.value.set_files(file_path)

    # 鼠标悬停
    def hover(self, selector):
        search_box = self.find_element(selector)
        search_box.hover()

    # 新建tab
    def create_tab(self):
        self.page = self.ctx.new_page()
