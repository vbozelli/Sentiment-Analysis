from csv import writer
from datetime import datetime
from nltk.classify.util import accuracy
from nltk.corpus import stopwords
from nltk.data import load
from nltk.tokenize import TreebankWordTokenizer
from threading import Thread
import _pickle
import ujson
stopWords = set(stopwords.words('english'))
tokenizerFrases = load('tokenizers/punkt/english.pickle')
tokenizerPalavras = TreebankWordTokenizer()
arquivoClassificador = open('classificador.pickle', 'rb')
classificador = _pickle.load(arquivoClassificador)
arquivoClassificador.close()
arquivoClassificados = open('classificados.json')
classificados = ujson.load(arquivoClassificados)
arquivoClassificados.close()
sentimentos = {}
featuresClassificados = []
class ThreadSentimento(Thread):
	def __init__(self, resposta):
		Thread.__init__(self)
		self.__resposta = resposta
	def run(self):
		resposta = self.__resposta
		texto = resposta['corpo']
		frases = tokenizerFrases.tokenize(texto)
		feature = {}
		for frase in frases:
			palavras = tokenizerPalavras.tokenize(frase)
			palavras = [palavra for palavra in palavras if palavra not in stopWords]
			for palavra in palavras:
				feature[palavra] = True
		sentimentos[texto] = (resposta, classificador.classify(feature))
		featuresClassificados.append((feature, resposta['sentimento']))
threads = []
comeco = datetime.now()
for resposta in classificados:
	thread = ThreadSentimento(resposta)
	threads.append(thread)
	thread.start()
for thread in threads:
	thread.join()
tempo = datetime.now() - comeco
arquivoMedicoes = open('medicoes_analise_threads.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format(accuracy(classificador, featuresClassificados) * 100))
arquivoMedicoes.close()
arquivoResultados = open('resultados_sem_stopwords.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
linhas = [['Resposta', 'Pontos', 'Sentimento - Naive Bayes', 'Sentimento - AlchemyAPI']]
for texto in sentimentos.keys():
	tupla = sentimentos[texto]
	resposta = tupla[0]
	linhas.append([texto, resposta['pontos'], tupla[1], resposta['sentimento']])
w.writerows(linhas)
arquivoResultados.close()