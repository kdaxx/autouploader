import io
import math
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import pandas

from lib import util, bit_api, playwright_driver
from browse.upload_action import Recorder
from captcha import api
from PIL import Image

element = {
    "login_url": "https://www.tiktok.com/login/phone-or-email/email",
    # 登录表单title
    "login_model_title": "#login-modal-title",

    # 验证码弹窗
    "captcha_container": "#captcha-verify-container-main-page",

    # 错误提示
    "error_tip": 'div[type="error"] span',

    # 点击登录按钮
    "login_btn": "button[data-e2e='login-button']",

    # 旋转验证码滑动按钮
    "spin_captcha_slide_btn": "#captcha_slide_button",

    # 物体识别图片
    "double_click_recognize_img": "img.cap-cursor-pointer",

}


def get_config():
    cfg = None
    config_path = "./auto_login.json"
    if os.path.exists(config_path):
        print(f"使用[{config_path}]中的程序配置文件")
        return util.read_json_file(config_path)
    # 默认配置
    if cfg is None:
        print("使用默认程序配置文件")
        cfg = {
            "group_name": "13235929984-测试",
            "parallel": 3,
            "login_plan": "./login_plan.json",
            "excel_path": "C:\\Users\\Admin\\Desktop\\test.xlsx"
        }
        util.write_json_file(config_path, cfg)
    return cfg


def get_data(excel_path):
    if not os.path.exists(excel_path):
        print(f"没有找到excel:{excel_path}")
        return
    raw_data = pandas.read_excel(excel_path, header=0)
    return raw_data.values


def create_plan(c):
    login_plan = c["login_plan"]
    excel = c["excel_path"]
    login_data = get_data(excel)
    if login_data is None:
        print("没有登录数据，无法生成登录计划")
        return
    mapper = dict({})
    for action in login_data:
        mapper[str(action[0])] = {
            "username": action[1],
            "password": action[2]
        }

    if not os.path.exists(login_plan):
        group = bit_api.get_group_by_name(c["group_name"])
        if group is None:
            print(f"[{c["group_name"]}]组不存在")
            exit(1)
        group_id = group["id"]
        windows = bit_api.iter_windows(group_id)
        sp = []
        for index, w in enumerate(windows):
            if str(w["name"]) not in dict(mapper).keys():
                print(f"窗口[{str(w["name"])}]没有对应账号")
                continue
            sp.append({
                "index": index + 1,
                "is_login": {
                    "success": False,
                    "message": ""
                },
                "window": {
                    "id": w["id"],
                    "seq": w["seq"],
                    "groupId": w["groupId"],
                    "name": w["name"],
                    "lastIp": w["lastIp"],
                    "lastCountry": w["lastCountry"],
                },
                "account": mapper[str(w["name"])],
            })
        util.write_json_file(c["login_plan"], sp)
        print("已生成计划")
    else:
        print(f"[{c["login_plan"]}] 已经生成，跳过")


class LoginRobot:

    def __init__(self, window):
        self.chrome = playwright_driver.Driver(window["id"])
        self.window = window
        pass

    def __wait_for_page(self):
        pass

    def has_login(self):
        # 弹出登录成功提示
        return self.chrome.page.locator("div[role='alert']").count() > 0 or \
            not self.chrome.page.url.startswith(element["login_url"])  # 已经跳转

    def is_trigger_verification(self):
        return self.chrome.page.locator(element["captcha_container"]).count() > 0

    def is_error(self):
        return self.chrome.page.locator(element['error_tip']).count() > 0

    def wait_for_captcha(self):
        while self.chrome.page.locator(element['spin_captcha_slide_btn']).count() == 0 and \
                self.chrome.page.locator(element['double_click_recognize_img']).count() == 0:
            time.sleep(1)

    def click_img(self, x, y):
        self.chrome.page.mouse.move(float(x), float(y))
        self.chrome.page.mouse.down()
        self.chrome.page.mouse.up()

    def pass_verification(self):
        self.wait_for_captcha()
        if self.chrome.page.locator(element['spin_captcha_slide_btn']).count() == 0:
            # 确认
            print("图片识别验证码")
            while not self.has_login() and \
                    self.chrome.page.locator(element['double_click_recognize_img']).count() > 0:
                captcha_img = self.chrome.page.locator(element['double_click_recognize_img']).screenshot()
                width, height = Image.open(io.BytesIO(captcha_img)).size

                json_loads = api.get_captcha_position(captcha_img)
                first = str(str(json_loads["data"]['recognition']).split('|')[0]).split(',')
                second = str(str(json_loads["data"]['recognition']).split('|')[1]).split(',')

                imgs = self.chrome.page.locator(element['double_click_recognize_img']).bounding_box(timeout=0)

                time.sleep(1)
                print("第一次点击")
                self.click_img(imgs["x"] + float(first[0]) / width * imgs['width'],
                               imgs["y"] + float(first[1]) / height * imgs['height'])
                time.sleep(1)
                print("第二次点击")
                self.click_img(imgs["x"] + float(second[0]) / width * imgs['width'],
                               imgs["y"] + float(second[1]) / height * imgs['height'])

                self.chrome.page.locator("button.TUXButton--default").dispatch_event('click')

                # 等待网页跳转或触发验证码
                wait_secs = 0
                while not self.has_login() and \
                        self.chrome.page.locator(element['double_click_recognize_img']).count() == 0 and \
                        self.chrome.page.locator(element['error_tip']).count() == 0:
                    time.sleep(2)
                    wait_secs += 2
                    print(f"等待网页跳转或验证码已等待{wait_secs}秒")
                    self.chrome.page.wait_for_load_state(timeout=0, state="load")
        else:
            # 旋转验证码
            print("旋转验证码")
            times = 0
            while not self.has_login() and \
                    self.chrome.page.locator(element['spin_captcha_slide_btn']).count() > 0:
                times = times + 1
                print(f"第{times}次识别")
                # 获取图片
                img = "div.cap-justify-center img"
                while self.chrome.page.locator(img).count() == 0:
                    time.sleep(1)
                img = self.chrome.page.query_selector_all(img)[0].screenshot()
                captcha_rotation = api.get_single_spin_captcha(img)

                move_distance = (captcha_rotation / 180 * 284)
                drag_box = self.chrome.page.locator(element['spin_captcha_slide_btn']).bounding_box(timeout=0)
                self.chrome.page.mouse.move(drag_box["x"] + drag_box["width"] / 2,
                                            drag_box["y"] + drag_box["height"] / 2)
                self.chrome.page.mouse.down()
                location_x = drag_box["x"]
                base = 34
                to_spin = move_distance + base
                for i in range(base, math.ceil(to_spin)):
                    if i > to_spin - 3:
                        time.sleep(1)
                    self.chrome.page.mouse.move(location_x + i, drag_box["y"])
                self.chrome.page.mouse.up()

                # 等待网页跳转或触发验证码
                wait_secs = 0
                while not self.has_login() and \
                        self.chrome.page.locator(element['spin_captcha_slide_btn']).count() == 0 and \
                        self.chrome.page.locator(element['error_tip']).count() == 0:
                    time.sleep(2)
                    wait_secs += 2
                    print(f"等待网页跳转或验证码已等待{wait_secs}秒")
                    self.chrome.page.wait_for_load_state(timeout=0, state="load")

    def do_login(self, account):
        print(f"[{self.window['name']}]正在打开主页页面")
        self.chrome.open_webpage("https://www.tiktok.com/login/phone-or-email/email")
        self.chrome.page.wait_for_load_state(timeout=0, state="load")
        if self.has_login():
            print("该账户已经登录")
            return {
                "success": True,
                "message": "该账户已登录"
            }

        self.chrome.page.locator("input[name='username']").fill(account["username"])
        self.chrome.page.locator("input[type='password']").fill(account["password"])
        self.chrome.page.locator(element['login_btn']).dispatch_event("click")
        self.chrome.page.wait_for_load_state(timeout=0, state="load")
        # 等待网页跳转或触发验证码
        wait_secs = 0
        while not self.has_login() and \
                self.chrome.page.locator(element['captcha_container']).count() == 0 and \
                self.chrome.page.locator(element['error_tip']).count() == 0:
            time.sleep(2)
            wait_secs += 2
            print(f"等待网页跳转或验证码已等待{wait_secs}秒")
            self.chrome.page.wait_for_load_state(timeout=0, state="load")

        # 是否触发验证码
        if self.is_trigger_verification():
            self.chrome.page.wait_for_load_state(timeout=0, state="load")
            self.pass_verification()

        if self.is_error():
            print(f"登录遇到限制:{self.chrome.page.locator(element['error_tip']).inner_text()}")
            return {
                "success": False,
                "message": f"登录遇到限制:{self.chrome.page.locator(element['error_tip']).inner_text()}"
            }

        print("登录成功")
        return {
            "success": True,
            "message": "登录成功"
        }

    def quit(self):
        self.chrome.quit_browser()


def auto_login(w, rd, plan):
    robot = None
    try:
        robot = LoginRobot(w["window"])
        w["is_login"] = robot.do_login(w["account"])
        rd.record(plan)
    except Exception as e:
        traceback.print_exc()
        print("出现错误，本次操作中止")
    finally:
        pass
        robot.quit()


if __name__ == "__main__":
    config = get_config()
    print("=========生成计划===========")
    create_plan(config)
    print("=========登录===========")
    recorder = Recorder(config["login_plan"])
    s_windows = recorder.read()
    with ThreadPoolExecutor(max_workers=config["parallel"]) as executor:
        for window in s_windows:
            if window["is_login"]["success"]:
                print(f"[{window["window"]["name"]}]已经登录, 本次跳过")
                continue
            executor.submit(auto_login, window, recorder, s_windows)
