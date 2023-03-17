import os
import jieba
import jieba.analyse
import pandas as pd
import pyodbc
import configparser
from bs4 import BeautifulSoup
import re
import nltk

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
         " inner join pttpost b on a.source=b.source and a.id=b.Id "
         " where not exists (select * from keyword where source=99 and (b.title like '%'+keyname+'%' or b.context like '%'+keyname+'%')) "
         " union all "
         " select a.id,title,context from pttpost_referendum_1 a "
         " inner join pttpostgossing b on a.source=b.source and a.id=b.Id "
         " where not exists (select * from keyword where source=99 and (b.title like '%'+keyname+'%' or b.context like '%'+keyname+'%')) "
         " union all "
         " select convert(varchar,a.id),title,content from dcard.dbo.pttpost_referendum_1 a "
         " inner join dcard.dbo.post b on a.source=b.forum and a.id=b.Id "
         " where not exists (select * from keyword where source=99 and (b.title like '%'+keyname+'%' or b.content like '%'+keyname+'%')) "
         " ) m "
         "where 1=1")

# 讀取資料表
df = pd.read_sql(query, cnxn)

with open('NTUSD_positive_unicode.txt', encoding='utf-8', mode='r') as f:
        positive_words = []
        for l in f:
            positive_words.append(l.strip())

with open('NTUSD_negative_unicode.txt', encoding='utf-8', mode='r') as f:
    negative_words = []
    for l in f:
        negative_words.append(l.strip())


# 定義處理負面字串的函式
def process_text_negative(text):
    # 使用 jieba 分詞
    words = jieba.cut(text)
    
    words = [word for word in words if word in negative_words]   

    # 回傳字詞列表
    return words

# 定義處理正面字串的函式
def process_text_postive(text):
    # 使用 jieba 分詞
    words = jieba.cut(text)
    
    words = [word for word in words if word in positive_words]   

    # 回傳字詞列表
    return words

# 載入知網詞庫
jieba.set_dictionary('C:\project\python\dict.big5.txt')

# 載入自定義詞庫
jieba.load_userdict('C:\project\python\main.txt')

print('start analyze emotion word in context')
# 處理 context 欄位
corpus_context_negative = [process_text_negative(text) for text in df['context']]
corpus_context_postive = [process_text_postive(text) for text in df['context']]
print('start analyze emotion word in title')
# 處理 title 欄位
corpus_title_negative = [process_text_negative(text) for text in df['title']]
corpus_title_postive = [process_text_postive(text) for text in df['title']]

# 合併兩個 corpus
corpus_postive = corpus_context_postive + corpus_title_postive
corpus_negative = corpus_context_negative + corpus_title_negative

# 使用 nltk.FreqDist 計算詞頻
# word_freq = nltk.FreqDist(word for words in corpus for word in words)
word_freq = nltk.FreqDist(word for words in corpus_postive for word in words)
# 取出前 10 筆
top_words = word_freq.most_common(10)

# 顯示結果
for word, freq in top_words:
    print("正面詞彙")
    print(f"{word}: {freq}")

word_freq = nltk.FreqDist(word for words in corpus_negative for word in words)
# 取出前 10 筆
top_words = word_freq.most_common(10)

# 顯示結果
for word, freq in top_words:
    print("負面詞彙")
    print(f"{word}: {freq}")
