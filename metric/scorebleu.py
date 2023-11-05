# -*- coding: utf-8 -*-
import requests
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction, modified_precision
import sys
import numpy as np
import re
import random
import pandas as pd

headers = {
    'content-type': "application/x-www-form-urlencoded",
}

"""
python score-bozh.py test_tb_zh_new.txt bo-zh
"""

TEST_DIR = '/home/sjx/score_bleu/'


def bleu_count(trans_text, target_text):
    # 读取参考与模型翻译的句子
    # bleu
    smooth = SmoothingFunction()
    bleu = nltk.translate.bleu_score.corpus_bleu(target_text, trans_text, smoothing_function=smooth.method1)
    return bleu
    

if __name__ == '__main__':
    # load data
    input_file = sys.argv[1] 
    ref_file = sys.argv[2]
    df = pd.read_excel(input_file)

    # f1, f2=open(input_file, 'r', encoding='utf-8'), open(ref_file, 'r', encoding='utf-8')
    # if len(input_file.split('/')) > 1:
    #     filename = input_file.split('/')[1]
    # else:
    #     filename = input_file.split('/')[0]

    # \u180e is space separator which can not be encoder by some python compiler
    pairs=[(l1.replace('\n','').replace('\ufeff',''),l2.replace('\n','').replace('\ufeff','')) for l1,l2 in zip(df["内容"],df["内容(中文)"])]

    # calculate the accuracy
    acc =[]
    hypo, ref = [],[]
    for p in pairs:
        hypo.append(list(p[0]))
        ref.append([list(p[1])])
            
    bleu = bleu_count(hypo,ref)

    print('The {} times bleu is {}'.format(1,bleu))
    # python bo-zh_percision.py TRANSLATION.TXT REFERENCE.TXT

