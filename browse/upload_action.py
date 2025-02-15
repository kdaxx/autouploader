import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from lib import playwright_driver
from lib import bit_api
from lib import util


class Recorder:
    def __init__(self, path):
        self.lock = threading.Lock()
        self.path = path

    def record(self, config):
        self.lock.acquire()
        util.write_json_file(self.path, config)
        self.lock.release()

    def read(self):
        try:
            self.lock.acquire()
            file = util.read_json_file(self.path)
            return file
        finally:
            self.lock.release()


class Uploader:
    def __init__(self, window, config):
        self.chrome = playwright_driver.Driver(window["id"])
        self.window = window
        self.test = dict(config).get("test", True)
        self.schedule = dict(config).get("schedule", False)
        self.config = dict(config)

    def __wait_for_page(self):
        # 有两个版本的界面
        v1 = {
            "cargo": "div.Tooltip__root button[role='button']",
            "upload_btn": ".upload-stage-btn",
            "file_input": "input[type='file']",
            "success_info": "span[data-icon=CheckCircleFill]",
            "publish_btn": "button[data-e2e='post_video_button']",
            "toast_btn": ".TUXTopToast",
            "schedule_btn": ".schedule-radio-container input[value='schedule']",
            "schedule_radio": "input.TUXTextInputCore-input",
        }

        v2 = {
            "cargo": "button[data-tt=Sidebar_index_TUXButton]",
            "upload_btn": ".upload-stage-btn",
            "file_input": "input[type='file']",
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
        print(f"[{self.window['name']}]正在打开作品发布页面")
        self.chrome.open_webpage("https://www.tiktok.com/tiktokstudio/content")
        info = self.__wait_for_page()
        # 上传
        self.chrome.click_btn(info["cargo"])

        self.chrome.page.wait_for_load_state(state="load")

        # 等待上传按钮
        while self.chrome.find_element(info["upload_btn"]).count() == 0:
            time.sleep(2)

        # 等待文件表单
        while self.chrome.find_element(info["file_input"]).count() == 0:
            time.sleep(2)

        self.chrome.page.wait_for_load_state(state="load")

        time.sleep(1)
        # 准备上传文件
        print(f"[{file_path}]提交上传")
        # 文件上传
        self.chrome.upload_file_with_dom(info["file_input"],
                                         file_path)

        print("提交成功, 等待上传进度")
        # 等待上传进度
        index = 1
        while self.chrome.find_element(info["success_info"]).count() == 0:
            time.sleep(2)
            print(f"等待[{self.window['name']}]上传[{file_path}], 已等待{index * 2}s")
            index += 1

        if self.schedule:
            # 点击定时发布按钮
            print(f"定时发布: 将于[{self.config["datetime"]}]发布该视频")
            self.chrome.click_btn(info["schedule_btn"])
            if self.chrome.find_element(".common-modal-confirm-modal button.TUXButton--primary").count() > 0:
                self.chrome.click_btn(".common-modal-confirm-modal button.TUXButton--primary")
            while self.chrome.find_element(info["schedule_radio"]).count() == 0:
                time.sleep(2)

            target_datetime = time.strptime(self.config["datetime"], "%Y-%m-%d %H:%M")

            dt = self.chrome.page.query_selector_all("input.TUXTextInputCore-input")
            time_picker = dt[0]
            date_picker = dt[1]
            hour = target_datetime.tm_hour
            minute = target_datetime.tm_min

            # 时间选择
            print("正在选择时间")
            time_picker.dispatch_event("click")
            while self.chrome.find_element(".tiktok-timepicker-left").count() == 0:
                time.sleep(2)

            for h in self.chrome.page.query_selector_all(".tiktok-timepicker-left"):
                if int(h.inner_text()) == hour:
                    h.dispatch_event("click")
                    break

            for h in self.chrome.page.query_selector_all(".tiktok-timepicker-right"):
                if int(h.inner_text()) == minute:
                    h.dispatch_event("click")
                    break

            time.sleep(1)
            time_picker.dispatch_event("click")

            # 日期
            print("正在选择日期")
            date_picker.dispatch_event("click")

            n = time.strptime(date_picker.get_attribute("value"), "%Y-%m-%d")
            diff = util.months_diff(datetime(n.tm_year, n.tm_mon, n.tm_mday),
                                    datetime(target_datetime.tm_year, target_datetime.tm_mon, target_datetime.tm_mday))
            if diff is None:
                print(f"发布日期{self.config["datetime"]}早于当地时间, 请检查")
                exit(1)
            while self.chrome.find_element("span.arrow").count() == 0:
                time.sleep(2)
            nx_month = self.chrome.page.query_selector_all("span.arrow")[1]
            for i in range(diff):
                nx_month.dispatch_event("click")
                time.sleep(1)
            # 等待
            self.chrome.page.wait_for_load_state(state="load")
            is_selected = False
            for d in self.chrome.page.query_selector_all("div.day-span-container span.day.valid"):
                if int(d.inner_text()) == target_datetime.tm_mday:
                    is_selected = True
                    d.dispatch_event("click")
                    break

            time.sleep(1)

            if not is_selected:
                print("【警告】日期无法被选中，未避免发布错误，当前不会发布任何视频")
                return

            # 等待
            self.chrome.page.wait_for_load_state(state="load")

        # 发布
        if not self.test:
            self.chrome.click_btn(info["publish_btn"])
            # 等待发布
            while self.chrome.find_element(info["toast_btn"]).count() == 0:
                time.sleep(2)
        print(f"[{self.window['name']}]已上传[{file_path}]")

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
            "index": index + 1,
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


def publish(config):
    recorder = Recorder(config["upload_plan"])
    upload_plan = recorder.read()
    with ThreadPoolExecutor(max_workers=config["parallel"]) as executor:
        for item in upload_plan:
            executor.submit(exec_upload_task, item, config, upload_plan, recorder)


def exec_upload_task(item, config, upload_plan, recorder):
    if item['is_uploaded']:
        print(f"窗口:[{item["window"]["name"]}]作品已经发布，跳过")
        return
    uploader = None
    try:
        uploader = Uploader(item["window"], config)
        print(f"{item["window"]["name"]}正在发布作品")
        for file in item["upload_files"]:
            if file["uploaded"]:
                print(f"{file["file"]}已经发布，跳过")
                continue
            print(f"{item["window"]["name"]}正在发布: {file["file"]}")
            uploader.publish(file["file"])
            file["uploaded"] = True
            recorder.record(upload_plan)
        item["is_uploaded"] = True
        recorder.record(upload_plan)
    except Exception as e:
        traceback.print_exc()
        print("未知错误，本次操作中止")
    finally:
        if dict(config).get("quit_enabled", True):
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
        util.write_json_file(config["upload_plan"], plan)
        print("生成上传计划成功")
    else:
        print(f"[{config["upload_plan"]}] 已经生成，跳过")


def get_config():
    config = None
    config_path = "./config.json"
    if os.path.exists(config_path):
        print(f"使用[{config_path}]中的程序配置文件")
        return util.read_json_file(config_path)
    # 默认配置
    if config is None:
        print("使用默认程序配置文件")
        config = {
            # 作品目录路径
            "video_path": r"/Users/laixin/Desktop/publish",

            # 一个窗口发布的作品数
            "num": 1,

            # 组名称
            "group_name": "13043553889-董公子",

            # 上传预览文件
            "upload_plan": "./upload_plan.json",

            # 同时启动的窗口数量
            "parallel": 1,

            # 定时： True为定时，False为立即发布
            "schedule": True,
            # 上传时间
            "datetime": "2025-02-16 12:30",

            # 测试环境
            "test": True,

            # 执行完成后是否关闭窗口
            "quit_enabled": True
        }
        util.write_json_file(config_path, config)
    return config


if __name__ == "__main__":
    print("=========读取配置===========")
    c = get_config()
    td = time.strptime(c["datetime"], "%Y-%m-%d %H:%M")
    if td.tm_min % 5 != 0:
        print("发布时间[datetime]的分钟数必须是5的倍数")
        exit(1)
    print("=========校验发布计划===========")
    create_plan(c)
    print("=========开始发布===========")
    publish(c)
    print("=========完成===========")
