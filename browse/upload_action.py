import os
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Semaphore

from lib import playwright_driver
from lib import bit_api
from lib import util


class Recorder:
    def __init__(self, path):
        self.semaphore = Semaphore(1)
        self.path = path

    def record(self, config):
        self.semaphore.acquire()
        util.write_file(self.path, config)
        self.semaphore.release()

    def read(self):
        try:
            self.semaphore.acquire()
            file = util.read_file(self.path)
            return file
        finally:
            self.semaphore.release()


class Uploader:
    def __init__(self, window_id, config, test=False):
        self.chrome = playwright_driver.Driver(window_id)
        self.test = test
        self.schedule = config["schedule"]
        self.config = config

    def __wait_for_page(self):
        # 有两个版本的界面
        v1 = {
            "cargo": "div.Tooltip__root button[role='button']",
            "upload_btn": ".upload-stage-btn",
            "success_info": "span[data-icon=CheckCircleFill]",
            "publish_btn": "button[data-e2e='post_video_button']",
            "toast_btn": ".TUXTopToast",
            "schedule_btn": ".schedule-radio-container input[value='schedule']",
            "schedule_radio": "input.TUXTextInputCore-input",
        }

        v2 = {
            "cargo": "button.css-5qkbk",
            "upload_btn": ".upload-stage-btn",
            "success_info": ".success-info",
            "publish_btn": "button[data-e2e='post_video_button']",
            "toast_btn": ".TUXTopToast",
            "schedule_btn": ".schedule-radio-container input[value='schedule']",
            "schedule_radio": "input.TUXTextInputCore-input",
        }
        while self.chrome.find_element(v1["cargo"]).count() == 0 \
                and self.chrome.find_element(v2["cargo"]).count() == 0:
            time.sleep(1)
        if self.chrome.find_element(v1["cargo"]).count() == 0:
            return v2
        else:
            return v1

    def publish(self, file_path):
        print("打开网页")
        self.chrome.open_webpage("https://www.tiktok.com/tiktokstudio/content")
        info = self.__wait_for_page()
        # 上传
        self.chrome.click_btn(info["cargo"])

        # 等待上传按钮
        while self.chrome.find_element(info["upload_btn"]).count() == 0:
            time.sleep(2)

        self.chrome.page.wait_for_load_state(state="load")

        # 文件上传
        self.chrome.upload_file_with_dom("input[type='file']",
                                         file_path)

        print("等待上传进度")
        # 等待上传进度
        while self.chrome.find_element(info["success_info"]).count() == 0:
            time.sleep(2)

        if self.schedule:
            # 点击定时发布按钮
            print(f"定时发布: 将于[{self.config["date"]} {self.config["time"]}]发布该视频")
            self.chrome.click_btn(info["schedule_btn"])
            while self.chrome.find_element(info["schedule_radio"]).count() == 0:
                time.sleep(2)
            self.chrome.page.evaluate(f"document.querySelectorAll('input.TUXTextInputCore-input')[0].value"
                                      f"='{self.config["time"]}'")
            self.chrome.page.evaluate(f"document.querySelectorAll('input.TUXTextInputCore-input')[1].value"
                                      f"='{self.config["date"]}'")

            # 发布
        if not self.test:
            self.chrome.click_btn(info["publish_btn"])
            # 等待发布
            while self.chrome.find_element(info["toast_btn"]).count() == 0:
                time.sleep(2)

    def quit(self):
        self.chrome.quit_browser()


def generate_upload_plan(gid, every, dir_path):
    files = util.get_files(dir_path)
    windows = bit_api.iter_windows(gid)
    if len(files) < every * len(windows):
        print(f"注意：当前只有{len(files)}个作品, 每个窗口需要{every}作品,只能满足{len(files) // every}个窗口发布作品! "
              f"该组总共包含{len(windows)}个窗口, 至少需要{every * len(windows)}个作品")

    upload_plan = []
    for index, window in enumerate(windows):

        if index * every + every > len(files):
            print(f"作品不够,从[{window["name"]}]窗口起无发布计划")
            return upload_plan
        json = {
            "index": index,
            "is_uploaded": False,
            "window": {
                "id": window["id"],
                "groupId": window["groupId"],
                "name": window["name"],
                "lastIp": window["lastIp"],
                "lastCountry": window["lastCountry"],
            },
            "upload_files": []
        }
        for i in range(every):
            json.get("upload_files").append({
                "file": files[index * every + i].path,
                "uploaded": False
            })
        upload_plan.append(json)
    return upload_plan


def publish(config, test=False):
    recorder = Recorder(config["upload_plan"])
    upload_plan = recorder.read()
    with ThreadPoolExecutor(max_workers=config["parallel"]) as executor:
        for item in upload_plan:
            executor.submit(exec_upload_task, item, config, upload_plan, test)


def exec_upload_task(item, config, upload_plan, test=False):
    recorder = Recorder(config["upload_plan"])
    if item['is_uploaded']:
        print(f"窗口:[{item["window"]["name"]}]作品已经发布，跳过")
        return
    uploader = Uploader(item["window"]["id"], config, test=test)
    print(f"{item["window"]["name"]}正在发布作品")
    print(f"窗口id: {item["window"]["id"]}")
    for file in item["upload_files"]:
        if file["uploaded"]:
            print(f"{file["file"]}已经发布，跳过")
            continue
        print(file["file"])
        uploader.publish(file["file"])
        file["uploaded"] = True
        recorder.record(upload_plan)
    item["is_uploaded"] = True
    recorder.record(upload_plan)
    if not test:
        uploader.quit()


def create_plan(config):
    if not os.path.exists(config["upload_plan"]):
        print("正在获取窗口")
        group = bit_api.get_group_by_name(config["group_name"])
        if group is None:
            print(f"[{config["group_name"]}]组不存在")
            exit(1)
        group_id = group["id"]

        print("正在生成上传计划")
        plan = generate_upload_plan(group_id, config["num"], config["video_path"])
        util.write_file(config["upload_plan"], plan)
        print("生成上传计划成功")
    else:
        print(f"[{config["upload_plan"]}] 已经生成，跳过")


def get_config():
    config = {
        "video_path": "/Users/laixin/Desktop/publish",
        "num": 1,
        "group_name": "13043553889-董公子",
        "upload_plan": "./upload.json",
        "parallel": 2,

        # 定时
        "schedule": True,
        "time": "17:00",
        "date": "2025-02-12",

        # 测试环境
        "test": True
    }
    return config


if __name__ == "__main__":
    c = get_config()
    print("=========校验发布计划===========")
    create_plan(c)
    print("=========开始发布===========")
    publish(c, test=c["test"])
    print("=========完成===========")
