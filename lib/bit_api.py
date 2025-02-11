import requests
import json
import time

# 官方文档地址
# https://doc2.bitbrowser.cn/jiekou/ben-di-fu-wu-zhi-nan.html

# 此demo仅作为参考使用，以下使用的指纹参数仅是部分参数，完整参数请参考文档

url = "http://127.0.0.1:54345"
headers = {'Content-Type': 'application/json'}


def createBrowser():  # 创建或者更新窗口，指纹参数 browserFingerPrint 如没有特定需求，只需要指定下内核即可，如果需要更详细的参数，请参考文档
    json_data = {
        'name': 'google',  # 窗口名称
        'remark': '',  # 备注
        'proxyMethod': 2,  # 代理方式 2自定义 3 提取IP
        # 代理类型  ['noproxy', 'http', 'https', 'socks5', 'ssh']
        'proxyType': 'noproxy',
        'host': '',  # 代理主机
        'port': '',  # 代理端口
        'proxyUserName': '',  # 代理账号
        "browserFingerPrint": {  # 指纹对象
            'coreVersion': '124'  # 内核版本，注意，win7/win8/winserver 2012 已经不支持112及以上内核了，无法打开
        }
    }

    res = requests.post(f"{url}/browser/update",
                        data=json.dumps(json_data), headers=headers).json()
    browserId = res['data']['id']
    print(browserId)
    return browserId


def updateBrowser():  # 更新窗口，支持批量更新和按需更新，ids 传入数组，单独更新只传一个id即可，只传入需要修改的字段即可，比如修改备注，具体字段请参考文档，browserFingerPrint指纹对象不修改，则无需传入
    json_data = {'ids': ['93672cf112a044f08b653cab691216f0'],
                 'remark': '我是一个备注', 'browserFingerPrint': {}}
    res = requests.post(f"{url}/browser/update/partial",
                        data=json.dumps(json_data), headers=headers).json()
    print(res)


def openBrowser(id):  # 直接指定ID打开窗口，也可以使用 createBrowser 方法返回的ID
    json_data = {"id": f'{id}'}
    res = requests.post(f"{url}/browser/open",
                        data=json.dumps(json_data), headers=headers).json()
    return res


def closeBrowser(id):  # 关闭窗口
    json_data = {'id': f'{id}'}
    requests.post(f"{url}/browser/close",
                  data=json.dumps(json_data), headers=headers).json()


def deleteBrowser(id):  # 删除窗口
    json_data = {'id': f'{id}'}
    print(requests.post(f"{url}/browser/delete",
                        data=json.dumps(json_data), headers=headers).json())


# 根据组ID分页获取窗口
def get_windows_by_gid(group_id, page, page_size):
    json_data = {
        "page": page,
        "pageSize": page_size,
        "groupId": group_id
    }
    res = requests.post(f"{url}/browser/list",
                        data=json.dumps(json_data), headers=headers).json()
    return res['data']


def iter_windows(gid):
    window_list = []
    page = 0
    page_size = 10
    index = 0
    while True:
        data = get_windows_by_gid(gid, page, page_size)
        for window in data["list"]:
            window_list.append(window)
            index += 1
        if data['totalNum'] - 1 <= page * page_size + page_size:
            break
        page += 1
    return window_list


def get_groups(page, page_size):
    json_data = {
        "page": page,
        "pageSize": page_size,
        "all": True,
        "sortDirection": "asc",
        "sortProperties": "sortNum"
    }
    res = requests.post(f"{url}/group/list",
                        data=json.dumps(json_data), headers=headers).json()
    return res['data']


def get_group_by_name(group_name):
    page = 0
    page_size = 10
    while True:
        data = get_groups(page, page_size)
        for g in data['list']:
            if g['groupName'] == group_name:
                return g

        if data['totalNum'] - 1 <= page:
            break
        page += 1
    return None
