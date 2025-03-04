# 需安装第三方requests
# img_url，图片存放路径
# 读取图片，并获取图片的base64数据

import base64, requests
import json


def get_captcha_position(img_bytes):
    api_post_url = "http://www.bingtop.com/ocr/upload/"
    img64 = base64.b64encode(img_bytes)
    params = {
        "username": "%s" % "liangliangliang",
        "password": "%s" % "Aa13235929984@",
        "captchaData": img64,
        "captchaType": 2301
    }
    response = requests.post(api_post_url, data=params)

    if json.loads(response.text)["code"] != 0:
        print(f"验证码 API 返回错误:{json.loads(response.text)["code"]}")
        print(f"{json.loads(response.text)["message"]}")
        return
    dictdata = json.loads(response.text)
    print(dictdata["data"]["recognition"])

    return dictdata


# get_captcha_position(open('double1.png', 'rb').read())


def get_spin_captcha(outer, inner):
    api_post_url = "http://www.bingtop.com/ocr/upload/"
    o_img64 = base64.b64encode(outer)
    i_img64 = base64.b64encode(inner)

    params = {
        "username": "%s" % "liangliangliang",
        "password": "%s" % "Aa13235929984@",
        "captchaData": o_img64,
        "subCaptchaData ": i_img64,
        "captchaType": 1122
    }
    response = requests.post(api_post_url, data=params)

    if json.loads(response.text)["code"] != 0:
        print(f"验证码 API 返回错误:{json.loads(response.text)["code"]}")
        print(f"{json.loads(response.text)["message"]}")
        return
    dictdata = json.loads(response.text)

    return dictdata

# print(get_spin_captcha(open('spin1.png', 'rb').read(),open('spin1-1.png', 'rb').read()))
# print(get_spin_captcha(open('spin3.png', 'rb').read(),open('spin3-3.png', 'rb').read()))



def get_single_spin_captcha(outer):
    api_post_url = "http://www.bingtop.com/ocr/upload/"
    o_img64 = base64.b64encode(outer)

    params = {
        "username": "%s" % "liangliangliang",
        "password": "%s" % "Aa13235929984@",
        "captchaData": o_img64,
        "captchaType": 1121
    }
    response = requests.post(api_post_url, data=params)

    if json.loads(response.text)["code"] != 0:
        print(f"验证码 API 返回错误:{json.loads(response.text)["code"]}")
        print(f"{json.loads(response.text)["message"]}")
        return
    dictdata = json.loads(response.text)
    print(dictdata["data"]["recognition"])

    return int(dictdata["data"]["recognition"])
# #
# print(get_single_spin_captcha(open('spintest1.png', 'rb').read()))
# print(get_single_spin_captcha(open('spintest2.jpg', 'rb').read()))