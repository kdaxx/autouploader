import json
import os


def get_files(path):
    with os.scandir(path) as files:
        files = [file for file in files if file.name.endswith('.mp4')]
        return files


def write_json_file(path, obj):
    with open(path, 'w', encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)


def read_json_file(path):
    with open(path, 'r', encoding="utf-8") as f:
        return json.load(f)


def write_file(path, text):
    with open(path, 'w', encoding="utf-8") as f:
        f.write(text)

def write_bytes(path, b):
    with open(path, 'wb') as f:
        f.write(b)

def read_file(path):
    with open(path, 'r', encoding="utf-8") as f:
        return f.read()


def append_file(path, text):
    with open(path, 'a', encoding="utf-8") as f:
        f.write(text)


def months_diff(start_date, end_date):
    # 确保start_date早于end_date

    if start_date > end_date:
        return None

    year_diff = end_date.year - start_date.year

    month_diff = end_date.month - start_date.month

    return year_diff * 12 + month_diff
