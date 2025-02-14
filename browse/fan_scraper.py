import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from lib import playwright_driver, bit_api


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
        user = self.chrome.find_element("h1[data-e2e='user-title']").inner_text()
        fan = self.chrome.find_element("strong[data-e2e='followers-count']").inner_text()
        # 关闭两个端口
        self.chrome.close_window()
        self.chrome.close_window()
        self.quit()
        return {
            "user": user,
            "home": href,
            "fan": fan,
        }

    def quit(self):
        self.chrome.quit_browser()


def exec_scrap_fan(w):
    try:
        fans = FanScraper(w).get_fans()
        data = {
            "group": config["group_name"],
            "window": w["name"],
            **fans
        }
        vals = list(data.values())

        with open(file, "a", encoding="utf-8") as f:
            f.write(f'{','.join(vals)}\n')
    except Exception as e:
        traceback.print_exc()
        print("未知错误，本次操作中止")
        exit(1)


if __name__ == "__main__":
    config = {
        "group_name": "13043553889-董公子",
        "parallel": 5
    }
    file = f"fan-{time.strftime("%Y-%m-%d", time.localtime())}.csv"
    group = bit_api.get_group_by_name(config["group_name"])
    if group is None:
        print(f"[{config["group_name"]}]组不存在")
        exit(1)
    group_id = group["id"]
    windows = bit_api.iter_windows(group_id)
    with open(file, "w", encoding="utf-8") as f:
        f.write("组名,窗口名称,账号,主页,粉丝数\n")
    with ThreadPoolExecutor(max_workers=config["parallel"]) as executor:
        for window in windows:
            executor.submit(exec_scrap_fan, window)
