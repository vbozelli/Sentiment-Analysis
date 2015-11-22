from csv import writer
from datetime import datetime
from nltk.classify.util import accuracy
from multiprocessing import Pool
from nltk.data import load
from nltk.tokenize import TreebankWordTokenizer
import _pickle
import ujson
tokenizerFrases = load('tokenizers/punkt/english.pickle')
tokenizerPalavras = TreebankWordTokenizer()
arquivoClassificador = open('classificador.pickle', 'rb')
classificador = _pickle.load(arquivoClassificador)
arquivoClassificador.close()
arquivoClassificados = open('classificados.json')
classificados = ujson.load(arquivoClassificados)
arquivoClassificados.close()
def analiseDeSentimento(resposta):
	frases = tokenizerFrases.tokenize(resposta['corpo'])
	feature = {}
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		for palavra in palavras:
			feature[palavra] = True
	return (feature, resposta, classificador.classify(feature))
pool = Pool()
comeco = datetime.now()
sentimentos = pool.map(analiseDeSentimento, classificados)
tempo = datetime.now() - comeco
featuresClassificados = []
linhas = [['Resposta', 'Pontos', 'Sentimento - Naive Bayes com Sentiwordnet', 'Sentimento - AlchemyAPI']]
for feature, resposta, sentimento in sentimentos:
	texto = resposta['corpo']
	frases = tokenizerFrases.tokenize(texto)
	sentimentoTemp = resposta['sentimento']
	featuresClassificados.append((feature, sentimentoTemp))
	linhas.append([texto, resposta['pontos'], sentimento, sentimentoTemp])
arquivoMedicoes = open('medicoes_analise_com_stopwords.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format(accuracy(classificador, featuresClassificados) * 100))
arquivoMedicoes.close()
arquivoResultados = open('resultados_com_stopwords.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
w.writerows(linhas)
arquivoResultados.close()