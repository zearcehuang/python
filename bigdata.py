from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.core.embedding import Embedding
from keras.models import Sequential
from msilib import sequence
import os
import random
import urllib.request
import pandas as pd
import readfiles
import jieba
from keras.preprocessing.text import Tokenizer
from keras.utils.data_utils import pad_sequences


# 下載資料
url = "https://raw.githubusercontent.com/SophonPlus/ChineseNlpCorpus/master/datasets/waimai_10k/waimai_10k.csv"
# 設定儲存的檔案路徑及名稱
filepath = "waimai_10k.csv"
# 判斷檔案是否存在，若不存在才下載
if not os.path.isfile(filepath):
    # 下載檔案
    result = urllib.request.urlretrieve(url, filepath)
    print('downloaded:', result)

# 查看資料
pd_all = pd.read_csv(filepath)

print('評論數目（全部）：%d' % pd_all.shape[0])
print('評論數目（正面）：%d' % pd_all[pd_all.label == 1].shape[0])
print('評論數目（負面）：%d' % pd_all[pd_all.label == 0].shape[0])

# 取得訓練資料train與label標籤
train, label = readfiles.read_files(filepath)
# print(train[3999])
# print(label[3999])
# print(train[4000])
# print(label[4000])

# 步驟二：打亂資料順序
train = train[:8000]
label = label[:8000]

x_shuffle = train
y_shuffle = label
z_shuffle = list(zip(x_shuffle, y_shuffle))

random.shuffle(z_shuffle)

x_train, y_label = zip(*z_shuffle)

# 列印出前10筆資料，查看打亂前及打亂後的排序結果
# print(label[:10])
# print(y_label[:10])

# 將資料分割為訓練資料與測試資料
# 由於原始資料沒有提供測試的資料，因此我們必須自己將資料切分，8成的資料(6400)為訓練資料，2成的資料(1600)為測試資料，如下：
NUM_TRAIN = int(8000 * 0.8)
train, test = x_train[:NUM_TRAIN], x_train[NUM_TRAIN:]
labels_train, labels_test = y_label[:NUM_TRAIN], y_label[NUM_TRAIN:]

# 取得及設定停用詞
# https://github.com/goto456/stopwords/blob/master/cn_stopwords.txt
stopWords = []
with open('stopWord.txt', 'r', encoding='utf8') as f:
    stopWords = f.read().split('\n')
stopWords.append('\n')
# print('stop words')
# print(stopWords)

# 使用結巴(jieba)中文分詞
sentence = []
sentence_test = []

# 透過jieba分詞工具，分別處理train和test資料
for content in train:
    _sentence = list(jieba.cut(content, cut_all=True))
    sentence.append(_sentence)
for content in test:
    _sentence = list(jieba.cut(content, cut_all=True))
    sentence_test.append(_sentence)

remainderWords2 = []
remainderWords_test = []

# 將斷詞分別從train和test資料中移除
for content in sentence:
    remainderWords2.append(list(filter(lambda a: a not in stopWords, content)))
for content in sentence_test:
    remainderWords_test.append(
        list(filter(lambda a: a not in stopWords, content)))

# 查看結果
# print(train[:2])
# print(remainderWords2[:2])

# 建立token字典
# 使用Tokenizer建立大小為3000的字典，接著透過fit_on_texts()方法將訓練的留言資料中，依照文字出現次數排序，而前3000個常出現的單字將會列入token字典中。

token = Tokenizer(num_words=3000)
token.fit_on_texts(remainderWords2)
# print('3000字')
# print(token.word_index)


# 建立數字list
x_train_seq = token.texts_to_sequences(remainderWords2)
x_test_seq = token.texts_to_sequences(remainderWords_test)

# 此外，由於keras只接受長度一樣的list輸入，因此必須使用sequence的pad_sequences()方法，將序列後的訓練及測試資料長度限制在50，表示當list長度超過50時，會自動切斷多出來的內容，反之list長度小於50時便會自動補0，直到長度為50。
# from keras.utils.data_utils import pad_sequences
x_train = pad_sequences(x_train_seq, maxlen=50)
x_test = pad_sequences(x_test_seq, maxlen=50)

# print(x_train[100])

# 建立模型
# 加入Embedding層，並設定output_dim輸出維度為128，而input_dim輸入維度則是與前面設定的字典大小相同為3000，input_length也與前面設定序列長度相同50。
# 轉換為Flatten平坦層，表示會有3000*128個神經元。
# 加入隱藏層，並設定神經元為256個，其中激活函數設定為relu，表示資料會捨去負數，並介於0到無限大區間。
# 加入輸出層，並設定輸出為2個神經元，並定義激活函數為sigmoid表示資料為0或1。

model = Sequential()

model.add(Embedding(output_dim=128, input_dim=3000, input_length=50))
model.add(Dropout(0.2))

model.add(Flatten())

model.add(Dense(units=256, activation='relu'))
model.add(Dropout(0.2))

model.add(Dense(units=2, activation='sigmoid'))
model.summary()

# 開始訓練模型
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

train_history = model.fit(x_train,
                          labels_train,
                          batch_size=100,
                          epochs=10,
                          verbose=2,
                          validation_split=0.2)
# 情緒分析預測結果
# 將test測試的資料加入模型評估結果，並取得模型正確率。
scores = model.evaluate(my_test, test_label, verbose=1)
scores[1]

# 透過predict_classes()方法取得test資料的預測結果，並且轉為一維陣列，接著建立一個方法查看預測結果是否正確。
predict = model.predict_classes(x_test)


def display_test_Sentiment(i):
    print(test[i])
    print('原始結果:', labels_test[i])
    print('預測結果:', predict[i])


# 呼叫display_test_Sentiment()並傳入要查看的資料編號。
display_test_Sentiment(0)

show_train_history('acc','val_acc')

