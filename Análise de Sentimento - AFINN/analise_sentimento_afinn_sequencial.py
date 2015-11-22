from csv import writer
from datetime import datetime
from nltk.corpus import stopwords
from nltk.data import load
from nltk.tokenize import TreebankWordTokenizer
import ujson
tokenizerPalavras = TreebankWordTokenizer()
stopWords = set(stopwords.words('english'))
tokenizerFrases = load('tokenizers/punkt/english.pickle')
arquivoClassificados = open('classificados.json')
classificados = ujson.load(arquivoClassificados)
arquivoClassificados.close()
file = open('AFINN-111.txt')
linhas = file.readlines()
file.close()
afinn = {}
for linha in linhas:
	palavra = linha.split()
	afinn[palavra[0]] = int(palavra[1])
sentimentos = {}
comeco = datetime.now()
for resposta in classificados:
	texto = resposta['corpo']
	frases = tokenizerFrases.tokenize(texto)
	sentimento = 0
	for frase in frases:
		palavras = tokenizerPalavras.tokenize(frase)
		palavras = [palavra for palavra in palavras if palavra not in stopWords]
		for palavra in palavras:
			if palavra in afinn:
				sentimento += afinn[palavra]
	if sentimento > 0:
		sentimentos[texto] = (resposta, 'positivo')
	elif sentimento < 0:
		sentimentos[texto] = (resposta, 'negativo')
	elif sentimento == 0:
		sentimentos[texto] = (resposta, 'neutro')
tempo = datetime.now() - comeco
acertos = 0
linhas = [['Resposta', 'Pontos', 'Sentimento - AFINN', 'Sentimento - AlchemyAPI']]
for texto in sentimentos.keys():
	tupla = sentimentos[texto]
	resposta = tupla[0]
	sentimento = tupla[1]
	if resposta['sentimento'] == sentimento:
		acertos = acertos + 1
	linhas.append([resposta['corpo'], resposta['pontos'], sentimento, resposta['sentimento']])
arquivoMedicoes = open('medicoes_sequencial.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format((acertos / len(sentimentos)) * 100))
arquivoMedicoes.close()
arquivoResultados = open('resultados_sem_stopwords.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
w.writerows(linhas)
arquivoResultados.close()