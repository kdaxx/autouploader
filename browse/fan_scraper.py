import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from browse.upload_action import Recorder
from lib import playwright_driver, bit_api, util


class FanScraper:
    def __init__(self, window):
        self.chrome = playwright_driver.Driver(window["id"])
        self.window = window
        pass

    def __wait_for_page(self):
        v1 = {
            "avatar": "div[data-tt='Header_index_HeaderContainer'] div[data-tt=components_Avatar_Absolute]",
            "option": "a[data-tt='Header_UserMenu_TUXMenuItem']"
        }
        v2 = {
            "avatar": "div[data-tt='Header_NewHeader_FlexRow'] div[data-tt=components_Avatar_Absolute]",
            "option": "a[data-tt='Header_NewHeader_TUXMenuItem']"
        }
        if self.chrome.find_element(v1["avatar"]).count() == 0 \
                and self.chrome.find_element(v2["avatar"]).count() == 0:
            time.sleep(2)

        if self.chrome.find_element(v1["avatar"]).count() == 0:
            return v2
        else:
            return v1

    def get_fans(self):
        print(f"[{self.window['name']}]正在打开主页页面")
        self.chrome.open_webpage("https://www.tiktok.com/tiktokstudio")
        pg = self.__wait_for_page()
        self.chrome.find_element(pg["avatar"]).click()

        while self.chrome.find_element(pg["option"]).count() == 0 and \
                self.chrome.find_element(pg["option"]).count() == 0:
            time.sleep(2)
            print("等待弹框出现")

        href = self.chrome.find_element(pg["option"]).get_attribute("href")
        self.chrome.open_webpage(href)
        user = self.chrome.find_element("h1[data-e2e='user-title']").inner_text(timeout=0)
        fan = self.chrome.find_element("strong[data-e2e='followers-count']").inner_text(timeout=0)
        # 关闭窗口
        self.chrome.close_window()
        return {
            "user": user,
            "home": href,
            "fan": fan,
        }

    def quit(self):
        self.chrome.quit_browser()


def exec_scrap_fan(file_path, w, rd, plan):
    scraper = None
    try:
        scraper = FanScraper(w["window"])
        fans = scraper.get_fans()
        data = {
            "group": config["group_name"],
            "window": w["window"]["name"],
            **fans
        }
        vals = list(data.values())
        util.append_file(file_path, f'{','.join(vals)}\n')
        w["is_scraped"] = True
        rd.record(plan)
    except Exception as e:
        traceback.print_exc()
        print("出现错误，本次操作中止")
    finally:
        scraper.quit()


def get_config():
    cfg = None
    config_path = "./fan_config.json"
    if os.path.exists(config_path):
        print(f"使用[{config_path}]中的程序配置文件")
        return util.read_json_file(config_path)
    # 默认配置
    if cfg is None:
        print("使用默认程序配置文件")
        cfg = {
            "group_name": "13043553889-董公子",
            "parallel": 5,
            "scrape_plan": "./scrape_plan.json"
        }
        util.write_json_file(config_path, cfg)
    return cfg


def create_plan(c):
    scrape_plan = c["scrape_plan"]
    if not os.path.exists(scrape_plan):
        group = bit_api.get_group_by_name(config["group_name"])
        if group is None:
            print(f"[{config["group_name"]}]组不存在")
            exit(1)
        group_id = group["id"]
        windows = bit_api.iter_windows(group_id)
        sp = []
        for index, w in enumerate(windows):
            sp.append({
                "index": index + 1,
                "is_scraped": False,
                "window": {
                    "id": w["id"],
                    "seq": w["seq"],
                    "groupId": w["groupId"],
                    "name": w["name"],
                    "lastIp": w["lastIp"],
                    "lastCountry": w["lastCountry"],
                }
            })
        util.write_json_file(c["scrape_plan"], sp)
        print("已生成计划")
        util.write_file(file,
                        "组名,窗口名称,账号,主页,粉丝数\n")
    else:
        print(f"[{c["scrape_plan"]}] 已经生成，跳过")


if __name__ == "__main__":
    config = get_config()

    file = (f"{config["group_name"]}-"
            f"{time.strftime("%Y-%m-%d", time.localtime())}.csv")
    print("=========生成计划===========")
    create_plan(config)
    print("=========准备抓取计划===========")
    recorder = Recorder(config["scrape_plan"])
    s_windows = recorder.read()
    with ThreadPoolExecutor(max_workers=config["parallel"]) as executor:
        for window in s_windows:
            if window["is_scraped"]:
                print(f"[{window["window"]["name"]}]已经抓取粉丝数, 本次跳过")
                continue
            executor.submit(exec_scrap_fan, file, window, recorder, s_windows)
