# encoding: utf-8
# author: cici

import argparse
import json
import time
import jieba
import tqdm
import re
import romdom
from datetime import datetime
import requests
import nltk

def addrule_supNMT_bi(src, tgt, rules):
	addrule = []
	for r in rules:
		r = r[0] +' <as> '+r[1]
		addrule.append(r)
	rules = ' <sp> '.join(rules)
	rules = rules + ' <bos> '
	return rules+src
	
def addrule_supNMT_mono(src, tgt, rules):
	addrule = []
	for r in rules:
		r = r[1]
		addrule.append(r)
	rules = ' <sp> '.join(rules)
	rules = rules + ' <bos> '
	return rules+src
	
def addrule_CSNMT_repalece(src, tgt, rules):
	addrule = []
	for r in rules:
		src.replace(r[0], r[1])
	return src
	
def addrule_CSNMT_append(src, tgt, rules):
	addrule = []
	for r in rules:
		src.replace(r[0], r[0]+' '+ r[1])
	return src
	
def get_rule(allgin):
	rules = []
	for item in allgin.split(' '):
		item = item.split('-')
	       rules.append(item)
	return rules
	
if __name__ == '__main__':
	# 规则创建的时候就要考虑分词情况了，反正是先分词
	src = []
	tgt = []
	align = []
      with open(srcfile,'r',encoding='utf-8') as f1, open(tgtfile,'r',encoding='utf-8') as f2,open(alignfile,'r',encoding='utf-8') as f3:
	       for line in f1:
	            tgt = f2.readline()
	            align = f3.readline()
		     rules = get_rule(align)
		     sample_rule = random.sample(rules,int(10%*len(rules)))
		     src.append(addrule_supNMT_bi(line.replace('\n',''),tgt.replace('\n',''),sample_rule)+'\n')
		     ## src.append(addrule_supNMT_bi(line,tgt,sample_rule))
		     ## src.append(addrule_supNMT_mono(line,tgt,sample_rule))
		     ## src.append(addrule_CSNMT_repalece(line,tgt,sample_rule))
		     ## src.append(addrule_CSNMT_append(line,tgt,sample_rule))
		     
       with open(srcfile+'.rul','w',encoding='utf-8') as fout:
       	   fout.writelines(src)
		     
		     