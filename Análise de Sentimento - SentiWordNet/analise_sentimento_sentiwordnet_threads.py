from csv import writer
from datetime import datetime
from nltk.corpus import stopwords
from nltk.data import load
from nltk.corpus import sentiwordnet
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from nltk.tokenize import TreebankWordTokenizer
from threading import Lock, Thread
import ujson
wordsTokenizer = TreebankWordTokenizer()
stopWords = set(stopwords.words('english'))
sentencesTokenizer = load('tokenizers/punkt/english.pickle')
arquivoClassificados = open('classificados.json')
classificados = ujson.load(arquivoClassificados)
arquivoClassificados.close()
sentimentos = {}
acertos = 0
lock = Lock()
class ThreadSentimento(Thread):
	def __init__(self, resposta):
		Thread.__init__(self)
		self.__resposta = resposta
	def run(self):
		global acertos
		resposta = self.__resposta
		texto = resposta['corpo']
		frases = sentencesTokenizer.tokenize(texto)
		palavras = []
		for frase in frases:
			palavrasTemp = wordsTokenizer.tokenize(frase)
			palavras.extend([palavra for palavra in palavrasTemp if palavra not in stopWords])
		posTags = pos_tag(palavras)
		positivo = 0
		negativo = 0
		for palavra, tag in posTags:
			synsets = None
			lock.acquire()
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
			lock.release()
			if synsets != None:
				synsets = list(synsets)
				if len(synsets) > 0:
					synset = synsets[0]
					positivo = positivo + synset.pos_score()
					negativo = negativo + synset.neg_score()
		if positivo > negativo:
			sentimentos[texto] = (resposta, 'positivo')
			if resposta['sentimento'] == 'positivo':
				acertos = acertos + 1
		elif negativo > positivo:
			sentimentos[texto] = (resposta, 'negativo')
			if resposta['sentimento'] == 'negativo':
				acertos = acertos + 1
		else:
			sentimentos[texto] = (resposta, 'neutro')
			if resposta['sentimento'] == 'neutro':
				acertos = acertos + 1
threads = []
comeco = datetime.now()
for resposta in classificados:
	thread = ThreadSentimento(resposta)
	threads.append(thread)
	thread.start()
for thread in threads:
	thread.join()
tempo = datetime.now() - comeco
linhas = [['Resposta', 'Pontos', 'Sentimento - SentiWordNet', 'Sentimento - AlchemyAPI']]
for texto in sentimentos.keys():
	tupla = sentimentos[texto]
	resposta = tupla[0]
	linhas.append([texto, resposta['pontos'], tupla[1], resposta['sentimento']])
arquivoMedicoes = open('medicoes_threads.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format((acertos / len(sentimentos)) * 100))
arquivoMedicoes.close()
arquivoResultados = open('resultados_sem_stopwords.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
w.writerows(linhas)
arquivoResultados.close()