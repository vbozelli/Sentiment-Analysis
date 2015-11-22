from datetime import datetime
from multiprocessing import Pool
from nltk.classify.naivebayes import NaiveBayesClassifier
from nltk.corpus import sentiwordnet
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from nltk.data import load
from nltk.tokenize import TreebankWordTokenizer
from pickle import HIGHEST_PROTOCOL
from _pickle import dump
from random import shuffle
import ujson
tokenizerFrases = load('tokenizers/punkt/english.pickle')
tokenizerPalavras = TreebankWordTokenizer()
arquivoPositivos = open('positivos.json')
positivos = ujson.load(arquivoPositivos)
arquivoPositivos.close()
arquivoNeutros = open('neutros.json')
neutros = ujson.load(arquivoNeutros)
arquivoNeutros.close()
arquivoNegativos = open('negativos.json')
negativos = ujson.load(arquivoNegativos)
arquivoNegativos.close()
def processoFeatures(resposta):
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	palavras = []
	palavrasTexto = {}
	for frase in frases:
		palavrasTemp = tokenizerPalavras.tokenize(frase)
		for palavra in palavrasTemp:
			palavrasTexto[palavra] = True
	posTags = pos_tag(palavras)
	positivo = 0
	negativo = 0
	for palavra, tag in posTags:
		synsets = None
		if tag.startswith('J'):
			synsets = sentiwordnet.senti_synsets(palavra, wordnet.ADJ)
		elif tag.startswith('V'):
			synsets = sentiwordnet.senti_synsets(palavra, wordnet.VERB)
		elif tag.startswith('N'):
			synsets = sentiwordnet.senti_synsets(palavra, wordnet.NOUN)
		elif tag.startswith('R'):
			synsets = sentiwordnet.senti_synsets(palavra, wordnet.ADV)
		else:
			synsets = sentiwordnet.senti_synsets(palavra, '')
		if synsets != None:
			synsets = list(synsets)
			if len(synsets) > 0:
				synset = synsets[0]
				positivo = positivo + synset.pos_score()
				negativo = negativo + synset.neg_score()
	if positivo > negativo:
		return (palavrasTexto, 'positivo')
	elif negativo > positivo:
		return (palavrasTexto, 'negativo')
	else:
		return (palavrasTexto, 'neutro')
pool = Pool()
features = pool.map(processoFeatures, positivos + negativos + neutros)
pool.terminate()
pool.close()
shuffle(features)
comeco = datetime.now()
classificador = NaiveBayesClassifier.train(features)
tempo = datetime.now() - comeco
arquivoMedicoes = open('medicoes_criar_classificador_sem_stopwords.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\n\nFeatures Importantes:')
featuresImportantes = classificador.most_informative_features(10)
for palavra, booleano in featuresImportantes:
	arquivoMedicoes.write('\n' + palavra)
arquivoMedicoes.close()
arquivoClassificador = open('classificador.pickle', 'wb')
dump(classificador, arquivoClassificador, protocol=HIGHEST_PROTOCOL)
arquivoClassificador.close()