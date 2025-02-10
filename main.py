from browse import browse_amazon as window

gid = '2c9bc061948ca74b0194d9dd9c002a18'
keyword = "Snake Eye Tactical Two ToneFinish Fantasy Desgin NinjaSword Comes with " \
          "Nylon Sheath(Red)"
url = "https://www.amazon.com/Snake-Eye-Tactical-Martial-Throwing/dp/B07DP5PCZ6"


def iter_windows(ws):
    for w in ws:
        browser_window = window.AmazonBrowser(w["id"])
        # 根据keyword浏览
        # browser_window.browse_by_keyword(keyword)
        # 根据网址直接浏览
        browser_window.browse_direct(url)


for i in range(1000):
    windows = window.get_window_by_gid(gid, i, 10)
    if windows:
        print(windows)
        iter_windows(windows["list"])
    if i == windows["totalNum"] - 1:
        break
