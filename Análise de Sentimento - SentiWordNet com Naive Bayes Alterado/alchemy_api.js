var async = require('async');
var fs = require('fs');
var request = require('request');
var mongoose = require('mongoose');
mongoose.connect('mongodb://localhost/stackoverflow');
var Schema = mongoose.Schema;
var Resposta = mongoose.model('Resposta', new Schema({'_id' : Number, 'corpo' : String, 'criacao' : Date, 'criador' : {'type' : Number, 'ref' : 'Usuario'}, 'pontos' : Number, 'pergunta' : {'type' : Number, 'ref' : 'Pergunta'}}));
var positivos = [];
var negativos = [];
var neutros = [];
var naoReconhecidos = [];
var chaves = ['b9f43e4a77a42a5b45b4c47935f309ba18190446', 'b77a682f06c11212cc025114a6984e619bc10f34', 'f287dd26f7b4d799109b7e7714c843d9b516ba27', '70bb1a8de6e93895975b6e5409c9f99a853e682f', '35c7d8531adb3083042a8609a0ff71af60a89cb9', 'd4bba4e6523f424d17b4eeb9541b9abb263f7aee', 'c3de99b0492ad51160c874f8a5deadbed12c4968', 'a3897617bafbac7aa48802a5a35d3bc3dc8d73ac', '3878f6bc9cc18022f964bafb76a523dd03cb3fab', '71d48bfccdf082b1c80166a2c84b47cb2986ae47', '51132791d9f48a7e06dac12bb51678a85cc86260', 'eda6aa5b4584ef633bd00e7118dac9245fe1f4b6', '5e95bec6fc242f439777146d76e334e51b142479', 'dbaba1f399dae6c7dba610390b259c1ecc0a713a', '948014d6c6024a16319d7755d79b0baedd42c679'];
var ultimoIndice = chaves.length - 1;
var indice = 0;
var erros = 0;
var parar = false;
var regex = new RegExp('\n|\t|\r| ', 'g');
async.parallel([function (callback)
{
	fs.exists('positivos.json', function (existe)
	{
		if(existe)
		{
			fs.readFile('positivos.json', function (erro, dados)
			{
				positivos = JSON.parse(dados);
				callback();
			});
		}
		else
		{
			callback();
		}
	});
}, function (callback)
{
	fs.exists('negativos.json', function (existe)
	{
		if(existe)
		{
			fs.readFile('negativos.json', function (erro, dados)
			{
				negativos = JSON.parse(dados);
				callback();
			});
		}
		else
		{
			callback();
		}
	});
}, function (callback)
{
	fs.exists('neutros.json', function (existe)
	{
		if(existe)
		{
			fs.readFile('neutros.json', function (erro, dados)
			{
				neutros = JSON.parse(dados);
				callback();
			});
		}
		else
		{
			callback();
		}
	});
}, function (callback)
{
	fs.exists('erros.json', function (existe)
	{
		if(existe)
		{
			fs.readFile('erros.json', function (erro, dados)
			{
				naoReconhecidos = JSON.parse(dados);
				callback();
			});
		}
		else
		{
			callback();
		}
	});
}], function (erro, resultados)
{
	var tamanhoPositivos = positivos.length - 1;
	var tamanhoNegativos = negativos.length - 1;
	var tamanhoNeutros = neutros.length - 1;
	Resposta.find().sort({'_id' : 1}).limit(15000).select('corpo pontos').exec(function (erro3, resultado)
	{
		async.eachSeries(resultado, function (resposta, callback)
		{
			var corpo = resposta['corpo'];
			if(corpo.replace(regex, '') != '')
			{
				if(parar)
				{
					console.log('Parou');
					process.exit(0);
				}
				else if(naoReconhecidos.indexOf(corpo) != -1)
				{
					console.log('Erro');
					callback();
				}
				else
				{
					var encontrou = false;
					var i = tamanhoPositivos;
					while(i >= 0)
					{
						if(positivos[i]['corpo'] == corpo)
						{
							encontrou = true;
							break;
						}
						i--;
					}
					if(!encontrou)
					{
						i = tamanhoNegativos;
						while(i >= 0)
						{
							if(negativos[i]['corpo'] == corpo)
							{
								encontrou = true;
								break;
							}
							i--;
						}
						if(!encontrou)
						{
							i = tamanhoNeutros;
							while(i >= 0)
							{
								if(neutros[i]['corpo'] == corpo)
								{
									encontrou = true;
									break;
								}
								i--;
							}
							if(!encontrou)
							{
								pegarSentimento(corpo, callback, resposta['pontos']);
							}
							else
							{
								console.log('Cadastrado');
								callback();
							}
						}
						else
						{
							console.log('Cadastrado');
							callback();
						}
					}
					else
					{
						console.log('Cadastrado');
						callback();
					}
				}
			}
			else
			{
				console.log('Vazio');
				callback();
			}
		}, function (erro4, resultados)
		{
			process.exit(0);
		});
	});
});
function pegarSentimento(corpo, callback, pontos)
{
	request({'url' : 'http://access.alchemyapi.com/calls/text/TextGetTextSentiment', 'headers' : {'content-type' : 'application/x-www-form-urlencoded'}, 'body' : 'apikey=' + chaves[indice] + '&outputMode=json&text=' + corpo, 'method' : 'POST'}, function (erro, resposta)
	{
		if(erro)
		{
			pegarSentimento(corpo, callback, pontos);
		}
		else
		{
			var body = JSON.parse(resposta['body']);
			var docSentiment = body['docSentiment'];
			if(docSentiment)
			{
				console.log('docSentiment ' + indice);
				erros = 0;
				var sentimento = docSentiment['type'];
				if(sentimento == 'positive')
				{
					positivos.push({'corpo' : corpo, 'pontos' : pontos});
					fs.writeFile('positivos.json', JSON.stringify(positivos), function (erro2)
					{
						callback();
					});
				}
				else if(sentimento == 'negative')
				{
					negativos.push({'corpo' : corpo, 'pontos' : pontos});
					fs.writeFile('negativos.json', JSON.stringify(negativos), function (erro2)
					{
						callback();
					});
				}
				else
				{
					neutros.push({'corpo' : corpo, 'pontos' : pontos});
					fs.writeFile('neutros.json', JSON.stringify(neutros), function (erro2)
					{
						callback();
					});
				}
			}
			else if(body['statusInfo'] == 'unsupported-text-language')
			{
				console.log('statusInfo ' +  indice);
				erros = 0;
				naoReconhecidos.push(corpo);
				fs.writeFile('erros.json', JSON.stringify(naoReconhecidos), function (erro2)
				{
					callback();
				});
			}
			else if(indice < ultimoIndice)
			{
				console.log('indice < ultimoIndice ' + indice);
				erros++;
				if(erros > 30)
				{
					indice++;
					erros = 0;
				}
				pegarSentimento(corpo, callback, pontos);
			}
			else
			{
				console.log('else ' + indice);
				erros++;
				if(erros > 30)
				{
					console.log('Parar');
					parar = true;
					callback();
				}
				else
				{
					console.log('else1');
					pegarSentimento(corpo, callback, pontos);
				}
			}
		}
	});
}