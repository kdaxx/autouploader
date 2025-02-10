import os
import time

from lib import playwright_driver
from lib import bit_api
from lib import util


class Uploader:
    def __init__(self, window_id, test=False):
        self.chrome = playwright_driver.Driver(window_id)
        self.test = test

    def __wait_for_page(self):
        while self.chrome.find_element("div.Tooltip__root button[role='button']").count() == 0 \
                and self.chrome.find_element("button.css-5qkbk").count() == 0:
            time.sleep(1)

    def publish(self, file_path):
        print("打开网页")
        self.chrome.open_webpage("https://www.tiktok.com/tiktokstudio/content")
        self.__wait_for_page()
        if self.chrome.find_element("div.Tooltip__root button[role='button']").count() == 0:
            self.chrome.click_btn("button.css-5qkbk")

            # 等待上传按钮
            (self.chrome.find_element(".upload-stage-btn")
             .wait_for(state="visible"))
            # 文件上传
            self.chrome.upload_file_with_filechooser("input[type='file']",
                                                     file_path)
            # 等待上传进度
            (self.chrome.find_element(".success-info")
             .wait_for(state="visible"))

            # 发布
            if not self.test:
                self.chrome.click_btn("button[data-e2e='post_video_button']")
        else:
            self.chrome.click_btn("div.Tooltip__root button[role='button']")

            (self.chrome.find_element(".upload-stage-btn")
             .wait_for(state="visible"))
            self.chrome.upload_file_with_filechooser("input[type='file']",
                                                     file_path)

            (self.chrome.find_element("span[data-icon=CheckCircleFill]")
             .wait_for(state="visible"))

            if not self.test:
                self.chrome.click_btn("button[data-e2e='post_video_button']")

        # 等待发布
        (self.chrome.find_element(".TUXTopToast")
         .wait_for(state="attached"))

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


def publish(config_path, test=False):
    config = util.read_file(config_path)
    for item in config:
        if item['is_uploaded']:
            print(f"窗口:[{item["window"]["name"]}]作品已经发布，跳过")
            continue
        uploader = Uploader(item["window"]["id"], test=test)
        print(f"{item["window"]["name"]}正在发布作品")
        print(f"窗口id: {item["window"]["id"]}")
        for file in item["upload_files"]:
            if file["uploaded"]:
                print(f"{file["file"]}已经发布，跳过")
                continue
            print(file["file"])
            uploader.publish(file["file"])
            file["uploaded"] = True
            util.write_file(config_path, config)
        item["is_uploaded"] = True
        util.write_file(config_path, config)
        uploader.quit()


if __name__ == "__main__":
    upload_dir = "/Users/laixin/Desktop/publish"
    num = 1
    group_name = "13043553889-董公子"

    group = bit_api.get_group_by_name(group_name)
    if group is None:
        print(f"[{group_name}]组不存在")
        exit(1)
    group_id = group["id"]
    # 生成上传计划
    config_json = "./config.json"
    if not os.path.exists(config_json):
        print("正在生成上传计划")
        plan = generate_upload_plan(group_id, num, upload_dir)
        util.write_file(config_json, plan)
        print("生成上传计划成功")

    print("=========开始发布===========")
    publish(config_json, test=False)
