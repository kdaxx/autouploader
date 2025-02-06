import time

from lib import tools

chrome = tools.Driver("36974e5a47724407b9453d0904ef0aaf")
print("打开浏览器")

# 打开亚马逊
chrome.open_webpage('https://www.amazon.com/')
print("打开亚马逊")

# 输入
chrome.input_text("#twotabsearchtextbox", "Smith & Wesson Extreme Ops Folding Knife")
print("输入搜索内容")
time.sleep(1)

# 点击
chrome.click_btn("#nav-search-submit-button")
print("点击搜索")

# 点击第一个
chrome.click_btn("[data-index='3']  [data-cy=image-container]")
print("点击第一个")

# 退出
chrome.quit_browser()
