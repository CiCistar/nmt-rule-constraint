import time
import pandas as pd
from tqdm import tqdm
import re
import os
import sys
CUR_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.append(CUR_PATH + '/..')

df = pd.read_csv(CUR_PATH+'res_match.csv',sep='\t',encoding="utf-8",names=['en','zh','label'],quoting=3)
label = df['label']
en = df['en']
ruledict = {}

labelout = []
for index, l in enumerate(label):
    if pd.isna(l):
        continue
    ls = l.split('##')
    for j in ls:
        if j!="":
            en_j, zh_j = j.rsplit(' ',1)
            if len(en_j.split(' '))<=3:
                ruledict[en_j] = zh_j


for i, item in enumerate(en):
    rules = []
    if pd.isna(label[i]):
        for word in item.split(' '):
            if word in ruledict.keys():
                rules.append(word+' '+ruledict[word])
        label[i] = '##'.join(rules)+'\n'
    else:
        ls = label[i].split('##')
        for j in ls:
            if j!="":
                en_j, zh_j = j.rsplit(' ',1)
                if len(en_j.split(' '))<=3:
                    rules.append(j)
        label[i] =  '##'.join(rules)+'\n'
           

with open(CUR_PATH+'label.csv','w',encoding='utf-8') as f:
    f.writelines(label)