import jieba
jieba.set_dictionary('./dict.big5.txt')

def get_score(article_string):
    with open('NTUSD_positive_unicode.txt', encoding='utf-8', mode='r') as f:
        positive_words = []
        for l in f:
            positive_words.append(l.strip())

    with open('NTUSD_negative_unicode.txt', encoding='utf-8', mode='r') as f:
        negative_words = []
        for l in f:
            negative_words.append(l.strip())

    score = 0

    if (article_string.strip() != ""):
        jieba_result = jieba.cut(article_string, cut_all=False, HMM=True)

        for word in jieba_result:
            if word.strip() != "":
                if word in positive_words:
                    score += 1
                elif word in negative_words:
                    score -= 1
                else:
                    pass

    return score
