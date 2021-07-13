import requests
import csv
import time
import pandas as pd
import tkinter as tk
import nltk
from nltk.corpus import stopwords
import re, string
from nltk.stem.snowball import SnowballStemmer
from gensim.models import Phrases
from gensim.corpora.dictionary import Dictionary
from numpy import array
import threading
import os
from gensim.models.ldamulticore import LdaMulticore
#import pyLDAvis.gensim_models as gensim
import pyLDAvis.gensim as gensim
import pyLDAvis
import webbrowser

class Worker(threading.Thread):
    def run(self):
        handle_click_start()

def run_in_back():
    w = Worker()
    w.start()

regex = ''
russian_stopwords = ''
stemmer = ''
parse_btn = ''
entry = ''
result_label = ''

def get_clear_domain():
    return entry.get().replace('vk.com/', '').replace('https://', '')

def handle_click_start():
    try:
        parse_btn['state'] = 'disabled'
        parse_btn['text'] = 'Ожидайте...'
        entry['state'] = 'disabled'
        result_label['text'] = ''
        global regex, russian_stopwords, stemmer
        
        all_posts = take_posts()
        file_writer(all_posts)

        df = pd.read_csv(r'%s.csv' % get_clear_domain(), encoding='utf-8', sep=',',usecols=[1])
        nltk.download("stopwords")

        russian_stopwords = stopwords.words("russian")# собираем стоп слова
        regex = re.compile('[%s]' % re.escape(string.punctuation)) # компилим regexp выражение
        stemmer = SnowballStemmer("russian") # инициализируем стэмминг

        
        df['text'] = df['text'].apply(lambda x: preprocessing(x))

        text_clean= []
        for index, row in df.iterrows():
            text_clean.append(row['text'].split())

        
        bigram = Phrases(text_clean) # Создаем биграммы на основе корпуса
        trigram = Phrases(bigram[text_clean])# Создаем триграммы на основе корпуса

        for idx in range(len(text_clean)):
            for token in bigram[text_clean[idx]]:
                if '_' in token:
                    # Токен это би грамма, добавим в документ.
                    text_clean[idx].append(token)
            for token in trigram[text_clean[idx]]:
                if '_' in token:
                    # Токен это три грамма, добавим в документ.
                    text_clean[idx].append(token)

        dictionary = Dictionary(text_clean)

        #Создадим словарь и корпус для lda модели
        corpus = [dictionary.doc2bow(doc) for doc in text_clean]
        print('Количество уникальных токенов: %d' % len(dictionary))
        print('Количество документов: %d' % len(corpus))
        #from gensim.models.ldamulticore import LdaMulticore
        model=LdaMulticore(corpus=corpus,id2word=dictionary, num_topics=2)
        model.show_topics()

        data = gensim.prepare(model, corpus, dictionary)
        pyLDAvis.save_html(data, r'%s.html' % get_clear_domain())
        url = 'file:///' + os.path.realpath(r'%s.html' % get_clear_domain())
        webbrowser.open(url, new=2)  # open in new tab

        print(data)
        result_label['text'] = 'Парсинг %s прошел успешно!' % get_clear_domain()
        parse_btn['state'] = 'active'
        parse_btn['text'] = 'Начать парсинг'
        entry['state'] = 'normal'
        entry.delete(0, 'end')

    except Exception as err:
        print(err)
        result_label['text'] = 'Парсинг %s прошел c ошибкой:%s' % (get_clear_domain(), str(err))
        parse_btn['state'] = 'active'
        parse_btn['text'] = 'Начать парсинг'
        entry['state'] = 'normal'
        entry.delete(0, 'end')

def take_posts():
    token = '254b23ce254b23ce254b23ce08253dd0ec2254b254b23ce45189f38c041c0cb6bfc0dac'
    version = 5.103
    domain = get_clear_domain()
    count = 100
    offset = 0
    all_posts = []

    while offset < 1000:
        print(offset)
        print('https://api.vk.com/method/wall.get?access_token=%s&v=%s&domain=%s&count=%s' % (token, version, domain, count))
        response = requests.get('https://api.vk.com/method/wall.get',
                                params={'access_token': token, 'v': version, 'domain': domain, 'count': count,
                                        'offset': offset})
        print(response.status_code)
        if 'error' in  response.json() and 'error_msg' in response.json()['error']:
            raise Exception(response.json()['error']['error_msg'])
        
        data = response.json()['response']['items']
        offset += 100
        all_posts.extend(data)
        time.sleep(0.5)
    return all_posts


def file_writer(data):
    with open(r'%s.csv' % get_clear_domain(), 'w', encoding="utf-8") as file:
        a_pen = csv.writer(file)
        a_pen.writerow(('likes', 'text'))
        for post in data:
            a_pen.writerow((post['likes']['count'], post['text']))

def preprocessing(text):
    import sys
    if not text:
        return " "
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
    text = str(text).translate(non_bmp_map)

    text = regex.sub('', text) # удаляем пунктуацию
    text = [token for token in text.split() if token not in russian_stopwords] # Удаляем стоп слова
    text = [stemmer.stem(token) for token in text] # Выполняем стэмминг
    text = [token for token in text if token] # Удаляем пустые токены
    return ' '.join(text)


if __name__ == '__main__':
    window = tk.Tk()
    window.geometry("400x200")

    w = 400
    h = 400

    ws = window.winfo_screenwidth()
    hs = window.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    window.geometry('%dx%d+%d+%d' % (w, h, x, y))



    label = tk.Label(text="url группы")

    entry = tk.Entry()

    parse_btn = tk.Button(
            text="Начать парсинг",
            command=run_in_back

    )
    label.pack()
    entry.pack()
    parse_btn.pack()
    result_label = tk.Label(text="")
    result_label.pack()


    window.mainloop()


