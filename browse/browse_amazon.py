import json
import time

import requests

from lib import bit_api, playwright_driver


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


class AmazonBrowser:
    def __init__(self, window_id):
        self.chrome = playwright_driver.Driver(window_id)

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
        # 新建tab页面
        self.chrome.create_tab()
        # 打开亚马逊
        self.chrome.open_webpage(url)
        print("打开商品链接")

    def close_window(self):
        # 关闭窗口并退出浏览器
        self.chrome.close_window()
        print("关闭页面")

    def quit_browser(self):
        # 关闭窗口并退出浏览器
        self.chrome.close_window()
        time.sleep(1)
        self.chrome.quit_browser()
        print("窗口已退出")


def iter_windows(ws, url):
    for w in ws:
        browser_window = AmazonBrowser(w["id"])
        print(f"{w['name']} 正在打开，浏览:{url}")
        # 根据keyword浏览
        # browser_window.browse_by_keyword(keyword)
        # 根据网址直接浏览
        browser_window.browse_direct(url)
        print(f"{w['name']} 浏览完成！")
        browser_window.quit_browser()


if __name__ == '__main__':
    group = bit_api.get_group_by_name("测试")
    gid = group['id']
    keyword = "Snake Eye Tactical Two ToneFinish Fantasy Desgin NinjaSword Comes with " \
              "Nylon Sheath(Red)"
    url = "https://www.amazon.com/Snake-Eye-Tactical-Martial-Throwing/dp/B07DP5PCZ6"

    page = 0
    while True:
        windows = get_window_by_gid(gid, page, 50)
        if windows:
            iter_windows(windows["list"], url)
        if page * 50 + 50 >= windows["totalNum"] - 1:
            break
        page += 1
