# NMT

### Rule-constant

1. data-preparation

​	源数据：WMT18 433 万对句子作为源域训练集

​	WMT newsdev2017 和 newstest2017 分别作为源域开发集和测试集。

​	Uncorpus汉英测试集作为目标领域测试集，UNTERM扩展了测试集。

​    预处理：

​	python -u ~/scripts/yunyi_scripts/data_filter/naive_lang_filter_zh_en.py oral.zh oral.en oral.zh.nlf oral.en.nlf
​	python -u ~/scripts/yunyi_scripts/data_filter/filter_formatted_subtitles.py oral.zh.nlf oral.en.nlf oral.zh.nlf.ffs oral.en.nlf.ffs
​	python -u ~/scripts/yunyi_scripts/process/norm_subtitles.py oral.zh.nlf.ffs oral.en.nlf.ffs oral.zh.nlf.ffs.norm oral.en.nlf.ffs.norm

​    python -u corpus_prepare-latinzh.py en zh all

​    (先不做bpe和tokennizer)

​    随机选择 433万训练数据

​    python ~/scripts/yunyi_scripts/process/shuffle.py --corpus all.en.bpe all.zh.bpe --slice 5

​	head -n 800 all.en.bpe.shuf > dev.en
​	head -n 800 all.zh.bpe.shuf > dev.zh
​	tail -n +801 all.en.bpe.shuf > train.en
​	tail -n +801 all.zh.bpe.shuf > train.zh

2. 准备规则数据

   先对原始文本进行分词，

   训练数据使用corpus_prepare-latinzh.py，测试数据使用nltk

   然后对齐，获得一个规则合集

3. WMT 数据集和UN 数据联合 训练BPE 模型

​    把测试集加入进行联合训练一个BPE模型

​      cat un_test.txt >> train.zh

​     cat un_test.txt >> train.en

​     python -u corpus_prepare-latinzh.py en zh all

​     训练完成后在词表vocab中加入三个特殊字符<as><sp><bos>,作为特殊标签输入

4. 模型

CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 
nohup python -u $HOME/THUMT-tensorflow/thumt/bin/trainer.py --model transformer --output zh-en --input train.zh train.en  --vocabulary vocab.zh.txt vocab.en.txt --validation dev.zh --references dev.en.desubword --parameters=device_list=[0,1,2,3,4,5,6,7],update_cycle=1,eval_steps=10000,train_steps=100000,batch_size=6250 >> zh-en.log &

