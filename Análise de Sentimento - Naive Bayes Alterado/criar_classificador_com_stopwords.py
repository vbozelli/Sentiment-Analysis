from datetime import datetime
from multiprocessing import Pool
from nltk.classify.util import accuracy
from nltk.classify.naivebayes import NaiveBayesClassifier
from nltk.data import load
from nltk.tokenize import TreebankWordTokenizer
from pickle import HIGHEST_PROTOCOL
from _pickle import dump
from random import shuffle
import ujson
arquivoPositivos = open('positivos.json')
positivos = ujson.load(arquivoPositivos)
arquivoPositivos.close()
tokenizerFrases = load('tokenizers/punkt/english.pickle')
tokenizerPalavras = TreebankWordTokenizer()
def processoFeaturesPositivos(resposta):
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	palavrasTexto = {}
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		for palavra in palavras:
			palavrasTexto[palavra] = True
	return (palavrasTexto, 'positivo')
pool1 = Pool()
resultadosPositivos = pool1.map_async(processoFeaturesPositivos, positivos)
arquivoNegativos = open('negativos.json')
negativos = ujson.load(arquivoNegativos)
arquivoNegativos.close()
def processoFeaturesNegativos(resposta):
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	palavrasTexto = {}
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		for palavra in palavras:
			palavrasTexto[palavra] = True
	return (palavrasTexto, 'negativo')
pool2 = Pool()
resultadosNegativos = pool2.map_async(processoFeaturesNegativos, negativos)
arquivoNeutros = open('neutros.json')
neutros = ujson.load(arquivoNeutros)
arquivoNeutros.close()
def processoFeaturesNeutros(resposta):
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	palavrasTexto = {}
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		for palavra in palavras:
			palavrasTexto[palavra] = True
	return (palavrasTexto, 'neutro')
pool3 = Pool()
resultadosNeutros = pool3.map_async(processoFeaturesNeutros, neutros)
features = resultadosPositivos.get() + resultadosNegativos.get() + resultadosNeutros.get()
pool1.terminate()
pool1.close()
pool2.terminate()
pool2.close()
shuffle(features)
comeco = datetime.now()
classificador = NaiveBayesClassifier.train(features)
tempo = datetime.now() - comeco
arquivoMedicoes = open('medicoes_criar_classificador_com_stopwords.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\n\nFeatures Importantes:')
featuresImportantes = classificador.most_informative_features(10)
for (palavra, booleano) in featuresImportantes:
	arquivoMedicoes.write('\n' + palavra)
arquivoMedicoes.close()
arquivoClassificador = open('classificador_com_stopwords.pickle', 'wb')
dump(classificador, arquivoClassificador, protocol=HIGHEST_PROTOCOL)
arquivoClassificador.close()