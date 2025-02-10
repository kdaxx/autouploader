import json
import os


def get_files(path):
    with os.scandir(path) as files:
        files = [file for file in files if file.name.endswith('.mp4')]
        return files


def write_file(path, obj):
    with open(path, 'w', encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)


def read_file(path):
    with open(path, 'r', encoding="utf-8") as f:
        return json.load(f)
