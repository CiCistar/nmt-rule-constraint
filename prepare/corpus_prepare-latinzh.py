#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
from threading import Thread

MOSES_SCRIPTS = "/home/yunyi/tools/mosesdecoder/scripts/"
YUNYI_SCRIPTS = "/home/yunyi/scripts/yunyi_scripts/"
FASTALIGN = "/home/yunyi/tools/fast_align/build/"
STANFORD_SEGMENTER = "/home/yunyi/tools/stanford-segmenter/"

class Processor(object):
	def __init__(self):
		self.abbr = ""
		self.cmds = []
		self.getOutfiles = lambda infiles: infiles + "." + self.abbr if type(infiles) == str else [infile + "." + self.abbr for infile in infiles]
	def addCmd(self, cmd):
		self.cmds.append(cmd)
	def log(self, msg):
		print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), type(self).__name__ + "[" + self.abbr + "]", msg
	def parallelProcess(self, infilesList, skip = False):
		if skip:
			return self._pseudoParallelProcess(infilesList)
		outputs = {}
		allThreads = {}
		for tid, infiles in enumerate(infilesList):
			def _process(tid, infiles):
				outfiles = self.process(infiles, str(tid))
				outputs[tid] = outfiles
			t = Thread(target = _process, args = (tid, infiles))
			allThreads[tid] = t
		for tid, t in allThreads.items():
			t.start()
		for tid, t in allThreads.items():
			t.join()
		return [outputs[tid] for tid, infiles in enumerate(infilesList)]
	def _pseudoParallelProcess(self, infilesList):
		return [self._pseudoProcess(infiles) for infiles in infilesList]
	def process(self, infiles, partId = "", skip = False):
		if skip:
			return self._pseudoProcess(infiles, partId)
		self.log("process function begin")
		for cmd in self.cmds:
			cmd = cmd.replace("PARTID", partId)
			if type(infiles) == str:
				cmd = cmd.replace("infile", infiles)
			else:
				for idx, infile in enumerate(infiles):
					cmd = cmd.replace("infile_" + str(idx + 1), infile)
			self.log(cmd)
			os.system(cmd)
		self.log("process function end")
		return self.getOutfiles(infiles)
	def _pseudoProcess(self, infiles, partId = ""):
		return self.getOutfiles(infiles)

class LineNomalizer(Processor):
	def __init__(self):
		super(LineNomalizer, self).__init__()
		self.abbr = "line"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "process/normLines.py infile infile.%s" % self.abbr)

class NonTransFilter(Processor):
	def __init__(self):
		super(NonTransFilter, self).__init__()
		self.abbr = "ntf"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/filter_nontranslated.py infile_1 infile_2 infile_1.%s infile_2.%s" % (self.abbr, self.abbr))
		self.addCmd("rm copy.bad")

class Uconverter(Processor):
	def __init__(self, convTo):
		super(Uconverter, self).__init__()
		if convTo.lower() not in ["nfc", "nfd"]:
			raise "unknow conversion target"
		self.abbr = convTo.lower()
		self.addCmd("uconv -x \"any-%s\" -o infile.%s infile" % (convTo.upper(), self.abbr))

class PuncNormalizer(Processor):
	def __init__(self, lang):
		super(PuncNormalizer, self).__init__()
		self.abbr = "np"
		# self.addCmd("perl " + MOSES_SCRIPTS + "tokenizer/normalize-punctuation.perl -b -l %s < infile > infile.%s" % (lang, self.abbr))
		self.addCmd("perl " + YUNYI_SCRIPTS + "process/normalize-punctuation.perl -b -l %s < infile > infile.%s" % (lang, self.abbr))

class Deescaper(Processor):
	def __init__(self):
		super(Deescaper, self).__init__()
		self.abbr = "dees"
		self.addCmd("perl " + MOSES_SCRIPTS + "tokenizer/deescape-special-chars.perl < infile > infile.%s" % self.abbr)

class CharWidthConverter(Processor):
	def __init__(self, direction, lang):
		super(CharWidthConverter, self).__init__()
		if direction == "h2f":
			self.abbr = "h2f"
			if lang == "ja":
				self.addCmd("python -u " + YUNYI_SCRIPTS + "process/half2full_ja.py infile infile.%s" % self.abbr)
			else:
				raise Exception("CharWidthConverter(direction=%s, lang=%s) is not supported yet" % (direction, lang))
		elif direction == "f2h":
			self.abbr = "f2h"
			if lang == "zh" or lang == "ja":
				self.addCmd("perl " + YUNYI_SCRIPTS + "process/full2half_zh.pl < infile > infile.%s" % self.abbr)
			else:
				self.addCmd("perl " + YUNYI_SCRIPTS + "process/full2half.pl < infile > infile.%s" % self.abbr)
		else:
			raise Exception("CharWidthConverter(direction=%s, lang=%s) is not supported yet" % (direction, lang))

class BadCodeFilter(Processor):
	def __init__(self, langSrc, langTgt):
		super(BadCodeFilter, self).__init__()
		self.abbr = "rb"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/removebadcode-latin.py %s %s infile_1 infile_2 infile_1.%s infile_2.%s PARTID.%s.out" % (langSrc, langTgt, self.abbr, self.abbr, self.abbr))

class LanguageFilter(Processor):
	def __init__(self, langSrc, langTgt):
		super(LanguageFilter, self).__init__()
		self.abbr = "lf"
		if langSrc == "zh" and langTgt == "ja":
			self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/lang_filter_zh_ja.py infile_1 infile_2 infile_1.%s infile_2.%s PARTID.%s.out" % (self.abbr, self.abbr, self.abbr))
		elif langSrc == "ja" and langTgt == "zh":
			self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/lang_filter_zh_ja.py infile_2 infile_1 infile_2.%s infile_1.%s PARTID.%s.out" % (self.abbr, self.abbr, self.abbr))
		elif langSrc == "zh" or langTgt == "zh":
			if langSrc == "zh":
				self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/lang_filter_zh_latin.py infile_1 infile_2 infile_1.%s infile_2.%s PARTID.%s.out" % (self.abbr, self.abbr, self.abbr))
			else:
				self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/lang_filter_zh_latin.py infile_2 infile_1 infile_2.%s infile_1.%s PARTID.%s.out" % (self.abbr, self.abbr, self.abbr))
		else:
			raise Exception("LanguageFilter(langSrc=%s, langTgt=%s) is not supported yet" % (langSrc, langTgt))

class Detokenizer(Processor):
	def __init__(self, langSrc, langTgt):
		super(Detokenizer, self).__init__()
		self.abbr = "detok"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "process/detokenize.py %s %s infile_1 infile_2 infile_1.%s infile_2.%s" % (langSrc, langTgt, self.abbr, self.abbr))

class Deduplicator(Processor):
	def __init__(self):
		super(Deduplicator, self).__init__()
		self.abbr = "dedup"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/dedup-v2.py infile_1 infile_2 infile_1.%s infile_2.%s" % (self.abbr, self.abbr))
		self.addCmd("rm dup.out")

class Tokenizer(Processor):
	def __init__(self, lang, aggressive = False, escape = False, threads = 12, protected = None):
		super(Tokenizer, self).__init__()
		self.abbr = "tok"
		self.addCmd("perl " + MOSES_SCRIPTS + "tokenizer/tokenizer.perl -b -l %s -threads %s" % (lang, threads) + (" -a" if aggressive else "") + ((" -protected %s" % protected) if protected else "" ) + (" -no-escape" if not escape else "") + " < infile > infile.%s" % self.abbr)

class ControlCharFilter(Processor):
	def __init__(self):
		super(ControlCharFilter, self).__init__()
		self.abbr = "fcc"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/filter_control_char.py infile_1 infile_2 infile_1.%s infile_2.%s" % (self.abbr, self.abbr))

class LengthFilter(Processor):
	def __init__(self, langSrc, langTgt, minLen = 1, maxLen = 80, retained = ""):
		super(LengthFilter, self).__init__()
		self.abbr = "clean"
		self.addCmd("ln -s infile_1 PARTID.forclean.%s" % langSrc)
		self.addCmd("ln -s infile_2 PARTID.forclean.%s" % langTgt)
		self.addCmd("perl " + MOSES_SCRIPTS + "training/clean-corpus-n.perl PARTID.forclean %s %s PARTID.cleaned %s %s" % (langSrc, langTgt, minLen, maxLen) + ((" PARTID." + retained) if retained and retained.strip() != "" else ""))
		self.addCmd("mv PARTID.cleaned.%s infile_1.%s" % (langSrc, self.abbr))
		self.addCmd("mv PARTID.cleaned.%s infile_2.%s" % (langTgt, self.abbr))
		self.addCmd("rm PARTID.forclean.%s" % langSrc)
		self.addCmd("rm PARTID.forclean.%s" % langTgt)

class DataConcatenator(Processor):
	def __init__(self, outfile):
		super(DataConcatenator, self).__init__()
		self.abbr = "concat"
		self.getOutfiles = lambda x: outfile
		def _process(infiles, skip = False):
			if not skip:
				self.log("process function begin")
				cmd = "cat %s > %s" % (" ".join(infiles), outfile)
				self.log(cmd)
				os.system(cmd)
				self.log("process function end")
			return self.getOutfiles(infiles)
		self.process = _process

class TruecaserTrainer(Processor):
	def __init__(self, lang):
		super(TruecaserTrainer, self).__init__()
		self.abbr = "truecaser"
		model = "truecaser." + lang
		self.getOutfiles = lambda x: model
		model = "truecaser." + lang
		self.addCmd("perl " + MOSES_SCRIPTS + "recaser/train-truecaser.perl -model %s -corpus infile" % model)

class Truecaser(Processor):
	def __init__(self, model):
		super(Truecaser, self).__init__()
		self.abbr = "tc"
		self.addCmd("perl " + MOSES_SCRIPTS + "recaser/truecase.perl -b -model %s < infile > infile.%s" % (model, self.abbr))

class WordSegmenter(Processor):
	def __init__(self, lang):
		super(WordSegmenter, self).__init__()
		self.abbr = "seg"
		if lang == "zh":
			self.addCmd("sh " + STANFORD_SEGMENTER + "segment.sh ctb infile UTF-8 0 > infile.%s0" % self.abbr)
			self.addCmd("python -u " + YUNYI_SCRIPTS + "process/postSeg.py infile.%s0 infile.%s" % (self.abbr, self.abbr))
			self.addCmd("rm infile.%s0" % self.abbr)
		elif lang == "ja":
			self.addCmd("mecab -O wakati < infile > infile.%s0" % self.abbr)
			self.addCmd("sh " + YUNYI_SCRIPTS + "process/postSeg-ja.sh infile.%s0 > infile.%s" % (self.abbr, self.abbr))
			self.addCmd("rm infile.%s0" % self.abbr)
		else:
			raise Exception("WordSegmenter(lang=%s) is not supported yet" % lang)

class AlignmentFilter(Processor):
	def __init__(self, threshold = 0.3):
		super(AlignmentFilter, self).__init__()
		self.abbr = "af"
		af_dir = "af_PARTID"
		self.addCmd("mkdir %s" % af_dir)
		self.addCmd("python -u " + YUNYI_SCRIPTS + "format_conv/combine_biling_files.py infile_1 infile_2 %s/bin" % af_dir)
		self.addCmd(FASTALIGN + "fast_align -i %s/bin -d -o -v > %s/forward.align" % (af_dir, af_dir))
		self.addCmd(FASTALIGN + "fast_align -i %s/bin -d -o -v -r > %s/reverse.align" % (af_dir, af_dir))
		self.addCmd(FASTALIGN + "atools -i %s/forward.align -j %s/reverse.align -c grow-diag-final > %s/gdf.align" % (af_dir, af_dir, af_dir))
		self.addCmd("python -u " + YUNYI_SCRIPTS + "data_filter/al_filter.py infile_1 infile_2 %s/forward.align %s/reverse.align %s/gdf.align %s/ %s" % (af_dir, af_dir, af_dir, af_dir, threshold))
		self.addCmd("mv %s/out.ch infile_1.%s" % (af_dir, self.abbr))
		self.addCmd("mv %s/out.en infile_2.%s" % (af_dir, self.abbr))

class DntExtractor(Processor):
	def __init__(self):
		super(DntExtractor, self).__init__()
		self.abbr = "de"
		af_dir = "de_PARTID"
		self.addCmd("mkdir %s" % af_dir)
		self.addCmd("python -u " + YUNYI_SCRIPTS + "format_conv/combine_biling_files.py infile_1 infile_2 %s/bin" % af_dir)
		self.addCmd(FASTALIGN + "fast_align -i %s/bin -d -o -v > %s/forward.align" % (af_dir, af_dir))
		self.addCmd(FASTALIGN + "fast_align -i %s/bin -d -o -v -r > %s/reverse.align" % (af_dir, af_dir))
		self.addCmd(FASTALIGN + "atools -i %s/forward.align -j %s/reverse.align -c grow-diag-final > %s/gdf.align" % (af_dir, af_dir, af_dir))
		self.addCmd("python -u " + YUNYI_SCRIPTS + "process/extractDntFromAlignment.py %s/bin %s/gdf.align %s/dnt.src %s/dnt.tgt" % (af_dir, af_dir, af_dir, af_dir))
		self.addCmd("cat %s/dnt.src infile_1 > infile_1.%s" % (af_dir, self.abbr))
		self.addCmd("cat %s/dnt.tgt infile_2 > infile_2.%s" % (af_dir, self.abbr))

class BpeTrainer(Processor):
	def __init__(self, langSrc, langTgt, separator = "@@", step = 30000, outputVocab = True):
		super(BpeTrainer, self).__init__()
		self.abbr = "codes"
		codesFile = "bpe-%sk.codes" % str(step / 1000)
		if outputVocab:
			self.getOutfiles = lambda x: (codesFile, "fullvocab.%s" % srcLang, "fullvocab.%s" % tgtLang)
		else:
			self.getOutfiles = lambda x: codesFile
		self.addCmd("cat infile_1 infile_2 | python -u " + YUNYI_SCRIPTS + "process/subword-nmt-2/learn_bpe.py -v -s %s -o %s" % (step, codesFile))
		if outputVocab:
			srcBpeScript = "apply_bpe.py"
			tgtBpeScript = "apply_bpe.py"
			self.addCmd(("python -u " + YUNYI_SCRIPTS + "process/subword-nmt-2/%s -c %s -s \"%s\" < infile_1 | python -u " + YUNYI_SCRIPTS + "process/subword-nmt-2/get_vocab.py > fullvocab.%s") % (srcBpeScript, codesFile, separator, langSrc))
			self.addCmd(("python -u " + YUNYI_SCRIPTS + "process/subword-nmt-2/%s -c %s -s \"%s\" < infile_2 | python -u " + YUNYI_SCRIPTS + "process/subword-nmt-2/get_vocab.py > fullvocab.%s") % (tgtBpeScript, codesFile, separator, langTgt))

class BpeApplier(Processor):
	def __init__(self, lang, codes, vocabulary, separator = "@@", step = 30000, vocabThreshold = 50):
		super(BpeApplier, self).__init__()
		self.abbr = "bpe-%sk" % str(step / 1000)
		if lang == "ja":
			srcBpeScript = "apply_bpe-ja.py"
		elif lang == "zh":
			srcBpeScript = "apply_bpe-zh.py"
		else:
			srcBpeScript = "apply_bpe.py"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "process/subword-nmt-2/%s -c %s -s \"%s\" --vocabulary %s --vocabulary-threshold %s < infile > infile.%s" % (srcBpeScript, codes, separator, vocabulary, vocabThreshold, self.abbr))

class DomainTagger(Processor):
	def __init__(self, domain, prob = 1.01):
		super(DomainTagger, self).__init__()
		self.abbr = "tag"
		self.addCmd("python -u " + YUNYI_SCRIPTS + "process/appendDomainTag.py infile_1 infile_2 %s %s" % (domain, prob))

if len(sys.argv) < 4:
	print "params: srcLang tgtLang domain1 [domain2 ...]"
	sys.exit()

srcLang = sys.argv[1]
tgtLang = sys.argv[2]
domains = sys.argv[3:]

srcFiles = [domain + "." + srcLang for domain in domains]
tgtFiles = [domain + "." + tgtLang for domain in domains]

p = LineNomalizer()
srcFiles = p.parallelProcess(srcFiles)
tgtFiles = p.parallelProcess(tgtFiles)

p = Deescaper()
srcFiles = p.parallelProcess(srcFiles)
tgtFiles = p.parallelProcess(tgtFiles)

p = Uconverter("NFC")
srcFiles = p.parallelProcess(srcFiles)
tgtFiles = p.parallelProcess(tgtFiles)

p = CharWidthConverter(direction = "f2h", lang = srcLang)
srcFiles = p.parallelProcess(srcFiles)
p = CharWidthConverter(direction = "f2h", lang = tgtLang)
tgtFiles = p.parallelProcess(tgtFiles)

p = Deduplicator()
files = zip(srcFiles, tgtFiles)
files = p.parallelProcess(files)
srcFiles, tgtFiles = zip(*files)

p = LanguageFilter(srcLang, tgtLang)
files = zip(srcFiles, tgtFiles)
files = p.parallelProcess(files)
srcFiles, tgtFiles = zip(*files)

p = ControlCharFilter()
files = zip(srcFiles, tgtFiles)
files = p.parallelProcess(files)
srcFiles, tgtFiles = zip(*files)

if srcLang != "zh":
	p = Tokenizer(srcLang, aggressive = True)
	srcFiles = p.parallelProcess(srcFiles)
if tgtLang != "zh":
	p = Tokenizer(tgtLang, aggressive = True)
	tgtFiles = p.parallelProcess(tgtFiles)

if srcLang == "zh":
	p = WordSegmenter(srcLang)
	srcFiles = p.parallelProcess(srcFiles)
if tgtLang == "zh":
	p = WordSegmenter(tgtLang)
	tgtFiles = p.parallelProcess(tgtFiles)

p = LengthFilter(srcLang, tgtLang, maxLen = 256)
files = zip(srcFiles, tgtFiles)
files = p.parallelProcess(files)
srcFiles, tgtFiles = zip(*files)

if srcLang != "zh":
	p = DataConcatenator("fortc." + srcLang)
	srcFile = p.process(srcFiles)
	p = TruecaserTrainer(srcLang)
	srcModel = p.process(srcFile)
	os.system("rm " + srcFile)
	p = Truecaser(srcModel)
	srcFiles = p.parallelProcess(srcFiles)
if tgtLang != "zh":
	p = DataConcatenator("fortc." + tgtLang)
	tgtFile = p.process(tgtFiles)
	p = TruecaserTrainer(tgtLang)
	tgtModel = p.process(tgtFile)
	os.system("rm " + tgtFile)
	p = Truecaser(tgtModel)
	tgtFiles = p.parallelProcess(tgtFiles)

p = AlignmentFilter()
files = zip(srcFiles, tgtFiles)
files = p.parallelProcess(files)
srcFiles, tgtFiles = zip(*files)

p = DntExtractor()
files = zip(srcFiles, tgtFiles)
files = p.parallelProcess(files)
srcFiles, tgtFiles = zip(*files)

p = DataConcatenator("forbpe." + srcLang)
srcFile = p.process(srcFiles)
p = DataConcatenator("forbpe." + tgtLang)
tgtFile = p.process(tgtFiles)
p = BpeTrainer(srcLang, tgtLang)
codes, srcVocab, tgtVocab = p.process([srcFile, tgtFile])
os.system("rm " + srcFile)
os.system("rm " + tgtFile)
p = BpeApplier(srcLang, codes, srcVocab)
srcFiles = p.parallelProcess(srcFiles)
p = BpeApplier(tgtLang, codes, tgtVocab)
tgtFiles = p.parallelProcess(tgtFiles)

outSrcFiles = []
outTgtFiles = []
for domain, srcFile, tgtFile in zip(domains, srcFiles, tgtFiles):
	p = DomainTagger(domain)
	if domain == "general":
		inputSrc = srcFile
		inputTgt = tgtFile
		srcFile, tgtFile = p.process([srcFile, tgtFile], skip = True)
		os.system("ln -s " + inputSrc + " " + srcFile)
		os.system("ln -s " + inputTgt + " " + tgtFile)
	else:
		srcFile, tgtFile = p.process([srcFile, tgtFile])
	outSrcFiles.append(srcFile)
	outTgtFiles.append(tgtFile)
srcFiles = outSrcFiles
tgtFiles = outTgtFiles

p = DataConcatenator("all.tag." + srcLang)
srcFile = p.process(srcFiles)
p = DataConcatenator("all.tag." + tgtLang)
tgtFile = p.process(tgtFiles)
