import requests
from bs4 import BeautifulSoup
from pretty_print import pretty_print
import urllib.parse

# 動態
# index = str(
#     input('想抓取哪個ptt看板？(ex: 八卦版請輸入 https://www.ptt.cc/bbs/Gossiping/index.html)：\n'))
# pages = eval(input('想抓取幾頁呢？ex: 5：'))
# 固定
index = 'https://www.ptt.cc/bbs/Gossiping/index.html'
pages = 20

not_exist = BeautifulSoup('<a>(本文已被刪除)</a>', 'lxml').a  # '本文已被刪除'的結構不同，自行生成<a>

# 18歲認證


def get_resp(page_url):
    cookies = {
        'over18': '1'
    }
    resp = requests.get(page_url, cookies=cookies)
    if resp.status_code != 200:
        return 'error'
    else:
        return resp

# 爬取一頁的文章


def get_articles_on_ptt(resp):  # 爬取一頁的文章
    soup = BeautifulSoup(resp.text, 'lxml')  # 得到網頁原始碼
    articles = []
    #要比對的關鍵字
    extensionsToCheck = ['倉促', '中鋼', '孔明', '自立自強']

    for i in soup.find_all('div', 'r-ent'):
        meta = i.find('div', 'title').find('a') or not_exist
        # if (not meta.getText().strip().startswith('(本文已被刪除)') and not meta.getText().strip().find('公告') >= 0):
        if (not meta.getText().strip().startswith('(本文已被刪除)') and not meta.getText().strip().startswith('[公告]') and (any(stringkey in meta.getText().strip() for stringkey in extensionsToCheck))):
            # if (not meta.getText().strip().startswith('(本文已被刪除)') and not meta.getText().strip().startswith('[公告]') and (meta.getText().strip().find('確診破萬') >= 0 or meta.getText().strip().find('慶祝') >= 0)):
            articles.append({
                'title': meta.getText().strip(),  # strip 去除頭尾字符，預設是空白
                'push': i.find('div', 'nrec').getText(),
                'date': i.find('div', 'date').getText(),
                'author': i.find('div', 'author').getText(),
            })

    next_link = soup.find(
        'div', 'btn-group-paging').find_all('a', 'btn')[1].get('href')  # 控制頁面選項(上一頁)

    return articles, next_link

# 要爬幾頁


def get_pages(num):  # 要爬幾頁
    page_url = index
    all_articles = []

    for j in range(num):
        print('第'+str(j)+'頁')
        resp = get_resp(page_url)
        articles, next_link = get_articles_on_ptt(resp)
        all_articles += articles
        page_url = urllib.parse.urljoin(
            index, next_link)  # 將上一頁按鈕的網址和 index 網址比對後取代

    return all_articles


# 輸出至螢幕
data = get_pages(pages)

for k in data:  # 輸出至螢幕
    pretty_print(k['push'], k['title'], k['date'], k['author'])


# 匯出csv
csv_or_not = input('輸入 y 以匯出成csv檔，輸入其他結束程式：')

if csv_or_not == 'y':
    board = index.split('/')[-2]  # 取出看板名
    csv = open('./ptt_%s版_前%d頁.csv' % (board, pages),
               'a+', encoding='utf-8')  # 檔名格式，'a+'代表可覆寫
    csv.write('推文數,標題,發文日期,作者ID,\n')
    for l in data:
        l['title'] = l['title'].replace(',', '，')  # 與用來分隔的逗點作區別
        csv.write(l['push'] + ',' + l['title'] + ',' +
                  l['date'] + ',' + l['author'] + ',\n')
    csv.close()
    print('csv檔案已儲存在您的資料夾中。')
else:
    quit()
