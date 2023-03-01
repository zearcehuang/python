import os
import jieba
import jieba.analyse
import pandas as pd
import pyodbc
import configparser
from bs4 import BeautifulSoup
import re

config = configparser.ConfigParser()
config.read('config.env')
db_UserName = config.get('DEFAULT', 'DB_USERNAME')
db_Password = config.get('DEFAULT', 'DB_PASSWORD')
db_Name = config.get('DEFAULT', 'DB_NAME')
db_Host = config.get('DEFAULT', 'DB_HOST')

cnxn_str = ("Driver={ODBC Driver 17 for SQL Server};"
            f"Server={db_Host};"
            f"Database={db_Name};"
            f"UID={db_UserName};"
            f"PWD={db_Password};")

cnxn = pyodbc.connect(cnxn_str)
# Create a cursor from the connection
cursor = cnxn.cursor()

# SQL查詢語句
query = ("select id,title ,context from ("
         "select a.id,title,context from pttpost_referendum_1 a "
         "inner join pttpost b on a.source=b.source and a.id=b.Id "
         "union all "
         "select a.id,title,context from pttpost_referendum_1 a "
         "inner join pttpostgossing b on a.source=b.source and a.id=b.Id "
         "union all "
         "select convert(varchar,a.id),title,content from dcard.dbo.pttpost_referendum_1 a "
         "inner join dcard.dbo.post b on a.source=b.forum and a.id=b.Id"
         ") m "
         "where 1=1")

# 讀取資料表
df = pd.read_sql(query, cnxn)

# 設置TF-IDF參數
topK = 50
withWeight = True

# 載入知網詞庫
jieba.set_dictionary('C:\project\python\dict.big5.txt')

# 載入自定義詞庫
jieba.load_userdict('C:\project\python\main.txt')

# 設置停用詞
jieba.analyse.set_stop_words('C:\project\python\stopWord.txt')

# 讀取停用詞表
with open('C:\project\python\stopWord.txt', 'r', encoding='utf-8') as f:
    stop_words = f.read().split()

# 去除 HTML tag
print('remove html tag')
df['context'] = df['context'].apply(
    lambda x: BeautifulSoup(x, "html.parser").get_text())
df['title'] = df['title'].apply(
    lambda x: BeautifulSoup(x, "html.parser").get_text())

# 去除特殊符号
print('remove special word')
df['context'] = df['context'].apply(lambda x: re.sub(r'[^\w\s]', '', x))
df['title'] = df['title'].apply(lambda x: re.sub(r'[^\w\s]', '', x))

# 去除停用词
print('remove stop words')
df['context'] = df['context'].apply(lambda x: ' '.join(
    [word for word in jieba.analyse.extract_tags(x, topK=topK, withWeight=False) if word not in stop_words]))
df['title'] = df['title'].apply(lambda x: ' '.join([word for word in jieba.analyse.extract_tags(
    x, topK=topK, withWeight=False) if word not in stop_words]))

print('start analyze title stop word')
# 使用jieba對每個記錄的title欄位進行中文斷詞
df['title_cut'] = df['title'].apply(lambda x: ' '.join(jieba.cut(x)))

print('start analyze context  stop word')
# 使用jieba對每個記錄的context欄位進行中文斷詞
df['context_cut'] = df['context'].apply(lambda x: ' '.join(jieba.cut(x)))

print('start analyze title tf-idf')
# 使用tf-idf算法計算每個記錄的title欄位的關鍵詞
df['title_keywords'] = df['title_cut'].apply(
    lambda x: jieba.analyse.extract_tags(x, topK=topK, withWeight=withWeight))
print('start analyze context tf-idf')
# 使用tf-idf算法計算每個記錄的context欄位的關鍵詞
df['context_keywords'] = df['context_cut'].apply(
    lambda x: jieba.analyse.extract_tags(x, topK=topK, withWeight=withWeight))

# 取出所有關鍵詞
print('get all key words')
keywords = []
for index, row in df.iterrows():
    for keyword, weight in row['title_keywords']:
        keywords.append((keyword, weight))
    for keyword, weight in row['context_keywords']:
        keywords.append((keyword, weight))

# 轉換為dataframe
print('轉換為dataframe')
keywords_df = pd.DataFrame(keywords, columns=['keyword', 'weight'])

# 合併相同的關鍵詞，計算權重總和
keywords_grouped = keywords_df.groupby(
    ['keyword']).agg({'weight': 'sum'}).reset_index()

# 按權重從大到小排序
print('按權重從大到小排序')
keywords_sorted = keywords_grouped.sort_values('weight', ascending=False)

# 取出前50個關鍵詞
print('取出前50個關鍵詞')
top_keywords = keywords_sorted.head(50)['keyword'].tolist()

# 輸出結果
print(top_keywords)
