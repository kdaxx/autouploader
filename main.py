from lib import window

gid = '2c9bc061948ca74b0194d9dd9c002a18'
keyword = "Snake Eye Tactical Two ToneFinish Fantasy Desgin NinjaSword Comes with " \
          "Nylon Sheath(Red)"
url = "https://www.amazon.com/Snake-Eye-Tactical-Martial-Throwing/dp/B07DP5PCZ6"


def iter_windows(ws):
    for w in ws:
        browser_window = window.Window(w["id"])
        # browser_window.browse_by_keyword(keyword)
        browser_window.browse_direct(url)


for i in range(100):
    windows = window.get_window_by_gid(gid, i, 10)
    if windows:
        print(windows)
        iter_windows(windows["list"])
    if i == windows["totalNum"] - 1:
        break
