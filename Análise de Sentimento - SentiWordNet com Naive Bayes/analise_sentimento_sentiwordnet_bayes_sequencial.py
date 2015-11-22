from csv import writer
from datetime import datetime
from nltk.classify.util import accuracy
from nltk.corpus import stopwords
from nltk.data import load
from nltk.tokenize import TreebankWordTokenizer
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
sentimentos = []
comeco = datetime.now()
for resposta in classificados:
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	feature = {}
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		palavras = [palavra for palavra in palavras if palavra not in stopWords]
		for palavra in palavras:
			feature[palavra] = True
	sentimentos.append((feature, resposta, classificador.classify(feature)))
tempo = datetime.now() - comeco
featuresClassificados = []
linhas = [['Resposta', 'Pontos', 'Sentimento - Naive Bayes com Sentiwordnet', 'Sentimento - AlchemyAPI']]
for feature, resposta, sentimento in sentimentos:
	texto = resposta['corpo']
	frases = tokenizerFrases.tokenize(texto)
	sentimentoTemp = resposta['sentimento']
	featuresClassificados.append((feature, sentimentoTemp))
	linhas.append([texto, resposta['pontos'], sentimento, sentimentoTemp])
arquivoMedicoes = open('medicoes_analise_sequencial.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format(accuracy(classificador, featuresClassificados) * 100))
arquivoMedicoes.close()
arquivoResultados = open('resultados_sem_stopwords.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
w.writerows(linhas)
arquivoResultados.close()