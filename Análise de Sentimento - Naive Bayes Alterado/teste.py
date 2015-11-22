import subprocess
p = subprocess.Popen('python3 criar_classificador.py', stdout=subprocess.PIPE, shell=True)
p.wait()
i = 0
while i < 5:
	p = subprocess.Popen('python3 analise_sentimento_bayes_sequencial.py', stdout=subprocess.PIPE, shell=True)
	p.wait()
	i = i + 1