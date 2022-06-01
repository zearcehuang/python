import csv
import numpy as np

# 讀取csv檔案
def read_files(filepath):
    path = filepath
    label = []
    all_texts = []
    all_label = []
    # 取得review資料
    with open(path, newline='', encoding='UTF-8') as csvfile_train:
        reader = csv.DictReader(csvfile_train)
        content = [row['review'] for row in reader]
        all_texts += content
    # 取得label資料
    with open(path, newline='', encoding='UTF-8') as csvfile_label:
        reader = csv.DictReader(csvfile_label)
        tag = [row['label'] for row in reader]
        label += tag
    # 將label list的值轉為int格式
    all_label = list(map(int, label))
    return all_texts, all_label
