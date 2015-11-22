from csv import writer
from datetime import datetime
from multiprocessing import Pool
from nltk.corpus import stopwords
from nltk.data import load
from nltk.corpus import sentiwordnet
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from nltk.tokenize import TreebankWordTokenizer
import ujson
wordsTokenizer = TreebankWordTokenizer()
stopWords = set(stopwords.words('english'))
sentencesTokenizer = load('tokenizers/punkt/english.pickle')
arquivoClassificados = open('classificados.json')
classificados = ujson.load(arquivoClassificados)
arquivoClassificados.close()
def analiseSentimento(resposta):
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
		return (resposta, 'positivo')
	elif negativo > positivo:
		return (resposta, 'negativo')
	else:
		return (resposta, 'neutro')
pool = Pool(4)
comeco = datetime.now()
sentimentos = pool.map(analiseSentimento, classificados)
tempo = datetime.now() - comeco
pool.terminate()
pool.close()
acertos = 0
linhas = [['Resposta', 'Pontos', 'Sentimento - SentiWordNet', 'Sentimento - AlchemyAPI']]
for resposta, sentimento in sentimentos:
	sentimentoTemp = resposta['sentimento']
	if sentimento == sentimentoTemp:
		acertos = acertos + 1
	linhas.append([resposta['corpo'], resposta['pontos'], sentimento, sentimentoTemp])
arquivoMedicoes = open('medicoes_processos.txt', 'w')
arquivoMedicoes.write('Tempo de Execução = ' + str(tempo) + '\nPrecisão = {0:.2f}%'.format((acertos / len(sentimentos)) * 100))
arquivoMedicoes.close()
arquivoResultados = open('resultados_sem_stopwords.csv', 'w', newline='')
w = writer(arquivoResultados, delimiter=',')
w.writerows(linhas)
arquivoResultados.close()