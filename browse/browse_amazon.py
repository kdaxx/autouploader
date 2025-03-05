import json
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import requests

from browse.upload_action import Recorder
from lib import bit_api, playwright_driver, util


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

    def randon_browse(self):
        href = \
        self.chrome.page.query_selector_all("div.product-shoveler")[0].query_selector_all("span.a-list-item a")[
            0].get_attribute("href")
        self.chrome.page.goto(f"https://www.amazon.com{href}",timeout=0)

    def close_window(self):
        # 关闭窗口并退出浏览器
        self.chrome.close_window()
        print("关闭页面")

    def quit_browser(self):
        self.chrome.quit_browser()


def iter_windows(w, url, rd, plan):
    browser_window = None
    try:
        browser_window = AmazonBrowser(w["window"]["id"])
        print(f"{w["window"]['name']} 正在打开，浏览:{url}")
        # 根据keyword浏览
        # browser_window.browse_by_keyword(keyword)
        # 根据网址直接浏览
        browser_window.browse_direct(url)
        browser_window.randon_browse()
        print(f"{w["window"]['name']} 浏览完成！")
        browser_window.quit_browser()
        w["is_browsed"] = True
        rd.record(plan)
    except Exception as e:
        traceback.print_exc()
        print("出现错误，本次操作中止")
    finally:
        pass
        browser_window.quit_browser()


def get_config():
    cfg = None
    config_path = "./browse_amazon.json"
    if os.path.exists(config_path):
        print(f"使用[{config_path}]中的程序配置文件")
        return util.read_json_file(config_path)
    # 默认配置
    if cfg is None:
        print("使用默认程序配置文件")
        cfg = {
            "group_name": "lx15905044834-默认分组",
            "parallel": 1,
            "browse_plan": "./browse_plan.json",
            "url": "https://www.amazon.com/"
        }
        util.write_json_file(config_path, cfg)
    return cfg


def create_plan(c):
    browse_plan = c["browse_plan"]
    if not os.path.exists(browse_plan):
        group = bit_api.get_group_by_name(c["group_name"])
        if group is None:
            print(f"[{c["group_name"]}]组不存在")
            exit(1)
        group_id = group["id"]
        windows = bit_api.iter_windows(group_id)
        sp = []
        for index, w in enumerate(windows):
            sp.append({
                "index": index + 1,
                "is_browsed": False,
                "window": {
                    "id": w["id"],
                    "seq": w["seq"],
                    "groupId": w["groupId"],
                    "name": w["name"],
                    "lastIp": w["lastIp"],
                    "lastCountry": w["lastCountry"],
                }
            })
        util.write_json_file(c["browse_plan"], sp)
        print("已生成计划")
    else:
        print(f"[{c["browse_plan"]}] 已经生成，跳过")


if __name__ == '__main__':
    config = get_config()
    print("=========生成计划===========")
    create_plan(config)
    print("=========开始浏览计划===========")
    recorder = Recorder(config["browse_plan"])
    s_windows = recorder.read()
    with ThreadPoolExecutor(max_workers=config["parallel"]) as executor:
        for window in s_windows:
            if window["is_browsed"]:
                print(f"[{window["window"]["name"]}]已经浏览过, 本次跳过")
                continue
            executor.submit(iter_windows, window, config["url"], recorder, s_windows)
