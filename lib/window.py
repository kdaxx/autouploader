import json
import time

import requests

from lib import bit_api, tools


# 根据组ID获取窗口
def get_window_by_gid(group_id, page, page_size):
    json_data = {
        "page": page,
        "pageSize": page_size,
        "groupId": group_id
    }
    res = requests.post(f"{bit_api.url}/browser/list",
                        data=json.dumps(json_data), headers=bit_api.headers).json()
    return res['data']


class Window:
    def __init__(self, window_id):
        self.chrome = tools.Driver(window_id)

    # 根据关键词浏览
    def browse_by_keyword(self, keyword):
        # 新建tab页面
        self.chrome.create_tab()

        # 打开亚马逊
        self.chrome.open_webpage('https://www.amazon.com/')
        print("打开亚马逊")

        # 输入
        self.chrome.input_text("#twotabsearchtextbox", keyword)
        print("输入链接关键词")
        time.sleep(1)

        # 点击
        self.chrome.click_btn("#nav-search-submit-button")
        print("点击搜索")

        # 点击第一个
        self.chrome.click_btn("[data-index='3']  [data-cy=image-container]")
        print("点击第一个")

    # 根据商品链接浏览
    def browse_direct(self, url):
        # 打开亚马逊
        self.chrome.open_webpage(url)
        print("打开商品链接")

    def close_window(self):
        # 关闭窗口并退出浏览器
        self.chrome.close_window()
        time.sleep(1)
        self.chrome.quit_browser()
        print("quit")
