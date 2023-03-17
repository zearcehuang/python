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

def PrintKeyWord(col1, col2, resultString):
 # 取出所有關鍵詞
    print('get all key words')
    keywords = []
    for index, row in df.iterrows():
        for keyword, weight in row[col1]:
            keywords.append((keyword, weight))
        for keyword, weight in row[col2]:
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
    print(f'{resultString} result:')
    print(top_keywords)

def pagerank(graph, weight=None, alpha=0.85, max_iter=100, tol=1e-6, weight_args=None):
    # 初始化權重
    if weight is None:
        weight = uniform_weight
    # 初始化分數
    scores = {node: 1.0 / len(graph) for node in graph}
    # 開始迭代
    for _ in range(max_iter):
        # 計算每個節點的分數
        new_scores = {}
        for node in graph:
            new_score = 0.0
            for neighbor in graph[node]:
                weight_value = weight(node, neighbor, graph, weight_args)
                new_score += weight_value * scores[neighbor]
            new_scores[node] = new_score
        # 計算調整因子
        sum_diff = sum(abs(new_scores[node] - scores[node]) for node in graph)
        if sum_diff < tol:
            break
        # 更新分數
        for node in graph:
            scores[node] = alpha * new_scores[node] + (1 - alpha) / len(graph)
    return scores

# 定義權重函數
def uniform_weight(x, y, graph, weight_args):
    return 1.0 / len(graph[x])

# 定義 text-rank 分析函數
def get_keywords_textrank(content):
    # 使用 jieba 進行斷詞
    words = jieba.lcut(content)
    # 去除停用詞和非中文詞
    words = [word for word in words if word not in stop_words and re.match(
        '^[\u4e00-\u9fa5]+$', word)]

    # 建立關鍵詞圖
    graph = {}
    for i in range(len(words)):
        if words[i] not in graph:
            graph[words[i]] = set()
        for j in range(i+1, len(words)):
            if words[j] not in graph:
                graph[words[j]] = set()
            if j - i > 5:
                break
            graph[words[i]].add(words[j])
            graph[words[j]].add(words[i])
    # 計算關鍵詞權重
    scores = pagerank(graph, weight=None, alpha=0.85,
                      max_iter=100, tol=1e-6, weight_args=None)
    # 取得前 topK 個權重最大的關鍵詞
    tr_keywords = []
    for word, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:topK]:
        tr_keywords.append((word, score))
    return tr_keywords

# 定義處理字串的函式
def process_text(text):
    # 使用 jieba 分詞
    words = jieba.cut(text)
    # 去除停用詞
    words = [word for word in words if word not in stop_words]
    # 回傳字詞列表
    return words

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

# 去除HTML tag
print('去除HTML tag')
df['context'] = df['context'].apply(lambda x: re.sub(r'<[^<]+?>', '', x))
df['title'] = df['title'].apply(lambda x: re.sub(r'<[^<]+?>', '', x))

# 去除標點符號及數字
print('去除標點符號及數字')
df['context'] = df['context'].apply(
    lambda x: re.sub(r'[^\u4e00-\u9fa5]+', '', x))
df['title'] = df['title'].apply(lambda x: re.sub(r'[^\u4e00-\u9fa5]+', '', x))

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

PrintKeyWord('title_keywords', 'context_keywords','tf-idf')

# 將 text-rank 分析結果加入 DataFrame 中
# print('start analyze context textrank')
# df['tr_content_keywords'] = df['context_cut'].apply(get_keywords_textrank)
df['tr_content_keywords'] = df['context_cut'].apply(
    lambda x: jieba.analyse.textrank(x, topK=topK, withWeight=withWeight), allowPOS=('ns', 'n', 'vn', 'v')
# print('start analyze title textrank')
# df['tr_title_keywords'] = df['title_cut'].apply(get_keywords_textrank)
df['tr_title_keywords'] = df['title_cut'].apply(
    lambda x: jieba.analyse.textrank(x, topK=topK, withWeight=withWeight), allowPOS=('ns', 'n', 'vn', 'v')

PrintKeyWord('tr_content_keywords', 'tr_title_keywords','text-rank')

print('start analyze title tf')
# 處理 context 欄位
corpus_context = [process_text(text) for text in df['context']]
# 處理 title 欄位
corpus_title = [process_text(text) for text in df['title']]
# 合併兩個 corpus
corpus = corpus_context + corpus_title

# 使用 nltk.FreqDist 計算詞頻
word_freq = nltk.FreqDist(word for words in corpus for word in words)
# 取出前 50 筆
top_words = word_freq.most_common(50)

# 顯示結果
for word, freq in top_words:
    print(f"{word}: {freq}")
