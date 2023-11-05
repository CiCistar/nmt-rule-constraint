# encoding: utf-8
# author: cici
# write for crawling info from unterm

import argparse
import json
import time
import jieba
import tqdm
import re
import urllib
from datetime import datetime
import requests
import nltk

# 中文
# from nltk.parse.stanford import StanfordSegmenter
# 英文

def align_find(src,tgt):
    if src in tgt:
        return [src,tgt]
    
# 正常应该加载一个stopwords
# with open('stopwords.txt','r',encoding='utf-8') as f:
#     stopwords = f.readlines()
stopwords = ['\n',',','.','"','*','?',':','!',';','/','-','(',')',
             'For','To','With','Upon','I',"We","At","The","In","An","Each","Once","One","Only","It","As","On","This",'There',"All",
             'January','February','March','April','August','May','June','July','January','September','December','October','November']

if __name__ == '__main__':

    with open('D:\\AppData\\code_VS\\python\\nmt-data-prepare\\data\\UNv1.0.testset.en','r',encoding='utf-8') as f:
        data = f.readlines()
    cout =0
    final_res = []
    for raw_text in data:
        cout = cout+1
        if cout<=2306:
            continue
        input_text = raw_text.replace('^[\d\.]+','')
        # encoded_str= urllib.parse.quote(chinese_query.encode('utf-8'))
        # playload = "\{\"searchTerm\":"+chinese_query+",\"searchType\":0,\"searchLanguages\":[\"en\",\"zh\"],\"languagesDisplay\":[\"en\",\"zh\"],\"datasets\":[\"ECA\",\"ITU\",\"ICAO\",\"IMO\",\"UNESCO\",\"UNDP\",\"UNHQ\",\"ECLAC\"],\"bodies\":[],\"subjects\":[],\"recordTypes\":[],\"acronymSearch\":True,\"localDBSearch\":True,\"termTitleSearch\":True,\"phraseologySearch\":False,\"footnoteSearch\":False,\"fullTextSearch\":False,\"facetedSearch\":True,\"buildSubjectList\":False}"
        headers = {
            'Content-type':'application/json',
        }
        # input_text_piece = jieba.lcut(input_text)
        eng_text_piece = nltk.word_tokenize(input_text)
        eng_text_piece = list(set(eng_text_piece))

        suggest_items = []
        for piece_word in eng_text_piece:
            # 数字和单个字就放弃查询，选择所有大写的、开头大写的
            if re.search('\d',piece_word) or piece_word in stopwords or len(piece_word)<3:
                continue
            if piece_word.islower():
                # 对一些长尾单词也进行处理
                if len(piece_word) < 11:
                    continue
                
            url = "https://conferences.unite.un.org/untermapi/api/term/search?page=0&query="+piece_word
            payload = json.dumps({
            "searchTerm": piece_word,
            "searchType": 0,
            "searchLanguages": [
                "en",
                "zh"
            ],
            "languagesDisplay": [
                "en",
                "zh"
            ],
            "datasets": [],
            "bodies": [],
            "subjects": [],
            "recordTypes": [],
            "acronymSearch": True,
            "localDBSearch": True,
            "termTitleSearch": True,
            "phraseologySearch": False,
            "footnoteSearch": False,
            "fullTextSearch": False,
            "facetedSearch": False,
            "buildSubjectList": True
            })
            try:
                res = requests.request("POST", url, headers=headers, data=payload)
            except Exception as e:
                print('Error {} occur in {}'.format(e, url))
                with open('res_match.txt','a',encoding='utf-8') as fout:
                    for item in final_res:
                        fout.write(item + '\n')
                final_res = []
                break

            #这里只考虑第一条，可以增加更多数据库来扩展术语
            try:
                res = json.loads(res.text)
                if res['results'] == []:
                    suggest_items = []
                    break
                for i in res['results']:
                    if i['chinese'] is not None and i['english'] is not None:
                        item_results = i
                        break
                # 中文在词典
                chinese = []
                english = []
                if item_results['chinese'] == None or item_results['english'] == None:
                    suggest_items = []
                    break
                for item in item_results['chinese']['terms']:
                    chinese.append(item['term'])
                for item in item_results['english']['terms']:
                    english.append(item['term'])
                for index, word in enumerate(english):
                    if piece_word == word:
                        if index < len(chinese):
                            suggest_items.append(piece_word+' '+ chinese[index])
                        else:
                            suggest_items.append(piece_word+' '+ chinese[0])
                        break
                    if index == len(english) - 1:
                        suggest_items.append(word+' '+ chinese[0])
            except Exception as e:
                print('Error {} occur in {}'.format(e, url))
                with open('res_match.txt','a',encoding='utf-8') as fout:
                    for item in final_res:
                        fout.write(item + '\n')
                final_res = []
                break
            time.sleep(3)

        if suggest_items!= None:
            final_text = ''
            for i in suggest_items:
                final_text = final_text+'##'+i
            final_res.append(raw_text.replace('\n','') + '\t' + final_text)
        else:
            final_res.append(raw_text.replace('\n','')+'\t'+'0')
            
        print('Deal with {}'.format(cout))
    
    with open('res_match_2306.txt','a',encoding='utf-8') as fout:
        for item in final_res:
            fout.write(item + '\n')

