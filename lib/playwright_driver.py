import time

from playwright.sync_api import sync_playwright

from lib import bit_api


class Driver:
    def __init__(self, browser_id):
        self.browser_id = browser_id
        self.manager = None
        self.ctx = self.open_browser()
        self.page = self.ctx.new_page()

    # 打开浏览器
    def open_browser(self):
        res = bit_api.openBrowser(self.browser_id)
        # 指纹浏览器的WS调试接口
        ws_address = res['data']['ws']

        playwright_context_manager = sync_playwright()
        self.manager = playwright_context_manager
        playwright = playwright_context_manager.start()

        browser = playwright.chromium.connect_over_cdp(ws_address)
        ctx = browser.contexts[0]
        return ctx

    # 退出浏览器
    def quit_browser(self):
        self.close_window()
        self.manager.__exit__()
        bit_api.closeBrowser(self.browser_id)

    # 关闭窗口
    def close_window(self):
        self.page.close()

    # 获取网页某个元素
    def find_element(self, selector):
        return self.page.locator(selector)

    # 打开网页
    def open_webpage(self, url):
        self.page.goto(url=url, timeout=0)

    # 点击按钮
    def click_btn(self, selector):
        search_btn = self.find_element(selector)
        search_btn.dispatch_event("click")

    def set_check(self, selector):
        self.find_element(selector).set_checked(checked=True)

    def is_visible(self, selector):
        self.page.is_visible(selector)

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
            print("trigger filechooser")
            time.sleep(1)
            self.page.locator(selector).dispatch_event("click")
        file_info.value.set_files(file_path)

    def upload_file_with_dom(self, selector, file_path):
        cdp_session = self.page.context.new_cdp_session(self.page)
        file_input_handle = self.page.query_selector(selector)
        if not file_input_handle:
            print("File input element not found!")
            return False

        dom_snapshot = cdp_session.send("DOM.getDocument")
        node_id = cdp_session.send("DOM.querySelector", {
            "nodeId": dom_snapshot["root"]["nodeId"],
            "selector": selector
        })

        cdp_session.send("DOM.setFileInputFiles", {
            "nodeId": node_id["nodeId"],
            "files": [file_path]
        })

    # 鼠标悬停
    def hover(self, selector):
        search_box = self.find_element(selector)
        search_box.hover()

    # 新建tab
    def create_tab(self):
        self.page = self.ctx.new_page()
