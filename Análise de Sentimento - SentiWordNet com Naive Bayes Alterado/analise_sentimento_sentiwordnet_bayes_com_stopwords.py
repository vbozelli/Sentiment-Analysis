from csv import writer
from datetime import datetime
from multiprocessing import Pool
from nltk.data import load
from nltk.classify.naivebayes import NaiveBayesClassifier
from nltk.classify.util import accuracy
from nltk.tokenize import TreebankWordTokenizer
from os.path import isfile
from pickle import HIGHEST_PROTOCOL
from _pickle import dump
from pymongo import MongoClient
from random import shuffle
from urllib.parse import urlencode
from urllib.request import urlopen
import _pickle
import ujson
tokenizerPalavras = TreebankWordTokenizer()
iteracao = 0
if isfile('iteracao.txt'):
	arquivoIteracao = open('iteracao.txt')
	iteracao = int(arquivoIteracao.read())
	arquivoIteracao.close()
pagina = 0
if isfile('pagina.txt'):
	arquivoPagina = open('pagina.txt')
	pagina = int(arquivoPagina.read())
	arquivoPagina.close()
tokenizerFrases = load('tokenizers/punkt/english.pickle')
arquivoPositivos = open('positivos.json')
positivos = ujson.load(arquivoPositivos)
arquivoPositivos.close()
def processoFeaturesPositivos(resposta):
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	palavrasTexto = {}
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		for palavra in palavras:
			palavrasTexto[palavra] = True
	return (palavrasTexto, 'positivo')
pool1 = Pool()
resultadoPositivos = pool1.map_async(processoFeaturesPositivos, positivos)
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
resultadoNegativos = pool2.map_async(processoFeaturesNegativos, negativos)
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
arquivoClassificador = open('classificador_com_stopwords.pickle', 'rb')
classificador = _pickle.load(arquivoClassificador)
arquivoClassificador.close()
cliente = MongoClient()
stackoverflow = cliente['stackoverflow']
respostas = stackoverflow['respostas']
classificados = respostas.find().sort('_id', 1).skip(15000 + pagina * 1000).limit(1000)
chaves = ['b9f43e4a77a42a5b45b4c47935f309ba18190446', 'b77a682f06c11212cc025114a6984e619bc10f34', 'f287dd26f7b4d799109b7e7714c843d9b516ba27', '70bb1a8de6e93895975b6e5409c9f99a853e682f', '35c7d8531adb3083042a8609a0ff71af60a89cb9', 'd4bba4e6523f424d17b4eeb9541b9abb263f7aee', 'c3de99b0492ad51160c874f8a5deadbed12c4968', 'a3897617bafbac7aa48802a5a35d3bc3dc8d73ac', '3878f6bc9cc18022f964bafb76a523dd03cb3fab', '71d48bfccdf082b1c80166a2c84b47cb2986ae47', '51132791d9f48a7e06dac12bb51678a85cc86260', 'eda6aa5b4584ef633bd00e7118dac9245fe1f4b6', '5e95bec6fc242f439777146d76e334e51b142479', 'dbaba1f399dae6c7dba610390b259c1ecc0a713a', '948014d6c6024a16319d7755d79b0baedd42c679']
indice = 0
sentimentos = {}
erros = 0
parar = False
featuresClassificados = []
def pegarSentimentoAlchemyApi(texto):
	global erros
	global indice
	global parar
	if parar:
		return None
	else:
		conexao = urlopen('http://access.alchemyapi.com/calls/text/TextGetTextSentiment', urlencode({'apikey' : chaves[indice], 'outputMode' : 'json', 'text' : texto}).encode('utf8'))
		alchemyApi = ujson.load(conexao)
		conexao.close()
		if 'docSentiment' in alchemyApi:
			erros = 0
			sentimento = alchemyApi['docSentiment']['type']
			if sentimento == 'positive':
				return 'positivo'
			elif sentimento == 'negative':
				return 'negativo'
			else:
				return 'neutro'
		elif alchemyApi['statusInfo'] == 'unsupported-text-language':
			erros = 0
			return None
		elif indice < 14:
			erros = erros + 1
			if erros > 30:
				indice = indice + 1
				erros = 0
			return pegarSentimentoAlchemyApi(texto)
		else:
			erros = erros + 1
			if erros > 30:
				parar = True
			return pegarSentimentoAlchemyApi(texto)
featuresTemp = []
comeco = datetime.now()
for resposta in classificados:
	texto = resposta['corpo']
	sentimentoAlchemyApi = pegarSentimentoAlchemyApi(texto)
	if sentimentoAlchemyApi != None:
		frases = tokenizerFrases.tokenize(texto)
		feature = {}
		for frase in frases:
			palavras = tokenizerPalavras.tokenize(frase)
			for palavra in palavras:
				feature[palavra] = True
		sentimento = classificador.classify(feature)
		featuresTemp.append((feature, sentimentoAlchemyApi))
		sentimentos[texto] = (resposta, sentimento, sentimentoAlchemyApi)
		if sentimento == sentimentoAlchemyApi:
			featuresClassificados.append((feature, sentimentoAlchemyApi))
			if sentimento == 'positivo':
				positivos.append(resposta)
			elif sentimento == 'negativo':
				negativos.append(resposta)
			else:
				neutros.append(resposta)
tempo = datetime.now() - comeco
precisao = accuracy(classificador, featuresTemp) * 100
iteracao = iteracao + 1
arquivoMedicoes = open('medicoes_analise_com_stopwords_' + str(iteracao) + '.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format(precisao))
arquivoMedicoes.close()
features = resultadoPositivos.get() + resultadoNegativos.get() + resultadosNeutros.get()
pool1.terminate()
pool1.close()
pool2.terminate()
pool2.close()
pool3.terminate()
pool3.close()
if precisao > 50:
	features.extend(featuresClassificados)
	shuffle(features)
	classificador = NaiveBayesClassifier.train(features)
	arquivoClassificador = open('classificador_com_stopwords.pickle', 'wb')
	dump(classificador, arquivoClassificador, protocol=HIGHEST_PROTOCOL)
	arquivoClassificador.close()
	arquivoPositivos = open('positivos.json', 'w')
	ujson.dump(positivos, arquivoPositivos)
	arquivoPositivos.close()
	arquivoNegativos = open('negativos.json', 'w')
	ujson.dump(negativos, arquivoNegativos)
	arquivoNegativos.close()
	arquivoNeutros = open('neutros.json', 'w')
	ujson.dump(neutros, arquivoNeutros)
	arquivoNeutros.close()
arquivoResultados = open('resultados_com_stopwords_' + str(iteracao) + '.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
linhas = [['Resposta', 'Pontos', 'Sentimento - Naive Bayes Alterado', 'Sentimento - AlchemyAPI']]
for texto in sentimentos.keys():
	tupla = sentimentos[texto]
	linhas.append([texto, tupla[0]['pontos'], tupla[1], tupla[2]])
w.writerows(linhas)
arquivoResultados.close()
arquivoIteracao = open('iteracao.txt', 'w')
arquivoIteracao.write(str(iteracao))
arquivoIteracao.close()
arquivoPagina = open('pagina.txt', 'w')
pagina = pagina + 1
arquivoPagina.write(str(pagina))
arquivoPagina.close()