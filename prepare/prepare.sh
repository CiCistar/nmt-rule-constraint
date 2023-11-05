#!/bin/bash

mydir=`dirname $0`
. $mydir/../common/vars
export PYTHONPATH=$zh_segment_home

src=zh
tgt=en
pair=$src-$tgt

tok() {
  path=$1
  name=$2
  # Tokenise the English part
  cat $path.$tgt | \
  $moses_scripts/tokenizer/normalize-punctuation.perl -l $tgt | \
  $moses_scripts/tokenizer/tokenizer.perl -a -l $tgt  \
  >> corpus.tok.$tgt

  #Segment the Chinese part
  python -m jieba -d ' ' < $path.$src >> corpus.tok.$src 

  lines=`wc -l $path.$src | cut -d' ' -f 1`
  yes $name | head -n $lines >> corpus.tok.domain
}

rm -rf segment-*
rm -rf corpus.tok.*

rmutf8=$kpu_preproc_dir/remove_invalid_utf8

for lang in $src $tgt; do
  rm -f booknosplit.$lang booksplit.$lang
  for id in 11 12 13 14 15 16 17 18 19 20; do
    cat $cwmt_dir/datum2017/Book$id.$lang  >> booknosplit.$lang
  done
  for id in 1 2 3 4 5 6 7 8 9 10; do
    cat $cwmt_dir/datum2017/Book$id.$lang  >> booksplit.$lang
  done
done

# Tidy up utf8 and remove 0x1e (it messes up bpe)
recsep=$(echo -e '\x1e')
for corpus in $cwmt_dir/casia2015/casia2015 \
              $cwmt_dir/casict2011/casict-A \
              $cwmt_dir/casict2011/casict-B \
              $cwmt_dir/casict2015/casict2015 \
              $cwmt_dir/datum2011/datum \
              $cwmt_dir/neu2017/NEU \
              booknosplit \
              booksplit \
              $nc_dir/news-commentary-v13.$src-$tgt \
              $un_dir/$tgt-$src/UNv1.0.$tgt-$src; do

  stem=`basename $corpus`
  stem=segment-$stem
  paste $corpus.$src $corpus.$tgt | $rmutf8 | grep -v "$recsep" > $stem.tsv
  cut -f 1 $stem.tsv > $stem.$src
  cut -f 2 $stem.tsv > $stem.$tgt
done

#desegment two files
$mydir/deseg.py < segment-booksplit.zh > tmp
mv tmp segment-booksplit.zh

$mydir/deseg.py < segment-datum.zh  > tmp
mv tmp segment-datum.zh

# Tokenise / segment
tok segment-casia2015 CASIA2015
tok segment-casict-A CASICTA
tok segment-casict-B CASICTB
tok segment-casict2015 CASICT2015
tok segment-datum DATA2011
tok segment-booknosplit BOOKNOSPLIT
tok segment-booksplit BOOKSPLIT
tok segment-NEU NEU
tok segment-news-commentary-v13.$src-$tgt NEWSCOMM
tok segment-UNv1.0.$tgt-$src UN

#
###
#### Clean
`dirname $0`/../common/clean-corpus-n.perl corpus.tok $src $tgt corpus.clean 1 $max_len corpus.retained
###
#
#### Train truecaser and truecase
$moses_scripts/recaser/train-truecaser.perl -model truecase-model.$tgt -corpus corpus.tok.$tgt
$moses_scripts/recaser/truecase.perl < corpus.clean.$tgt > corpus.tc.$tgt -model truecase-model.$tgt

ln -s corpus.clean.$src  corpus.tc.$src
#
#  
# dev sets
for devset in test2017 dev2017 ; do
  for lang  in $src $tgt; do
    if [ $lang == $tgt ]; then
      side="src"
      $moses_scripts/ems/support/input-from-sgm.perl < $dev_dir/news$devset-$tgt$src-$side.$lang.sgm | \
      $moses_scripts/tokenizer/normalize-punctuation.perl -l $lang | \
      $moses_scripts/tokenizer/tokenizer.perl -a -l $lang |  \
      $moses_scripts/recaser/truecase.perl   -model truecase-model.$lang \
      > news$devset.tc.$lang
    else
      side="ref"
      $moses_scripts/ems/support/input-from-sgm.perl < $dev_dir/news$devset-$tgt$src-$side.$lang.sgm | \
      python -m jieba -d ' '  > news$devset.tc.$lang
    fi
    
  done
  cp $dev_dir/news$devset-$src$tgt*sgm .
  cp $dev_dir/news$devset-$tgt$src*sgm .
done
#
#
### Tidy up and compress
paste corpus.tc.$src corpus.tc.$tgt corpus.clean.domain | gzip -c > corpus.gz
#for lang in $src $tgt; do
#  rm -f book*.$lang corpus.tc.$lang corpus.tok.$lang corpus.clean.$lang corpus.retained paracrawl.$lang
#done
#rm corpus.clean.domain corpus.tok.domain
tar zcvf dev.tgz news* &&  rm news*
tar zcvf true.tgz truecase-model.* && rm truecase-model*