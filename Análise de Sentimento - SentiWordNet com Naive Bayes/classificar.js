var async = require('async');
var fs = require('fs');
var request = require('request');
var mongoose = require('mongoose');
mongoose.connect('mongodb://localhost/stackoverflow');
var Schema = mongoose.Schema;
var Resposta = mongoose.model('Resposta', new Schema({'_id' : Number, 'corpo' : String, 'criacao' : Date, 'criador' : {'type' : Number, 'ref' : 'Usuario'}, 'pontos' : Number, 'pergunta' : {'type' : Number, 'ref' : 'Pergunta'}}));
var classificados = [];
var chaves = ['b9f43e4a77a42a5b45b4c47935f309ba18190446', 'b77a682f06c11212cc025114a6984e619bc10f34', 'f287dd26f7b4d799109b7e7714c843d9b516ba27', '70bb1a8de6e93895975b6e5409c9f99a853e682f', '35c7d8531adb3083042a8609a0ff71af60a89cb9', 'd4bba4e6523f424d17b4eeb9541b9abb263f7aee', 'c3de99b0492ad51160c874f8a5deadbed12c4968', 'a3897617bafbac7aa48802a5a35d3bc3dc8d73ac', '3878f6bc9cc18022f964bafb76a523dd03cb3fab', '71d48bfccdf082b1c80166a2c84b47cb2986ae47', '51132791d9f48a7e06dac12bb51678a85cc86260', 'eda6aa5b4584ef633bd00e7118dac9245fe1f4b6', '5e95bec6fc242f439777146d76e334e51b142479', 'dbaba1f399dae6c7dba610390b259c1ecc0a713a', '948014d6c6024a16319d7755d79b0baedd42c679'];
var ultimoIndice = chaves.length - 1;
var indice = 0;
var erros = 0;
var parar = false;
var regex = new RegExp('\n|\t|\r| ', 'g');
fs.exists('classificados.json', function (existe)
{
	if(existe)
	{
		fs.readFile('classificados.json', function (erro1, dados)
		{
			classificados = JSON.parse(dados);
			pegarBanco();
		});
	}
	else
	{
		pegarBanco();
	}
});
function pegarBanco()
{
	Resposta.find().sort({'_id' : 1}).select('corpo pontos').skip(15000).limit(1000).exec(function (erro3, resultado)
	{
		async.eachSeries(resultado, function (resposta, callback)
		{
			var corpo = resposta['corpo'];
			if(corpo.replace(regex, '') != '')
			{
				if(parar)
				{
					process.exit(0);
				}
				else if(classificados.indexOf(corpo) != -1)
				{
					callback();
				}
				else
				{
					pegarSentimento(corpo, callback, resposta['pontos']);
				}
			}
			else
			{
				callback();
			}
		}, function (erro4, resultados)
		{
			process.exit(0);
		});
	});
}
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
				erros = 0;
				var sentimento = docSentiment['type'];
				if(sentimento == 'positive')
				{
					classificados.push({'corpo' : corpo, 'pontos' : pontos, 'sentimento' : 'positivo'});
					fs.writeFile('classificados.json', JSON.stringify(classificados), function (erro2)
					{
						callback();
					});
				}
				else if(sentimento == 'negative')
				{
					classificados.push({'corpo' : corpo, 'pontos' : pontos, 'sentimento' : 'negativo'});
					fs.writeFile('classificados.json', JSON.stringify(classificados), function (erro2)
					{
						callback();
					});
				}
				else if(sentimento = 'neutral')
				{
					classificados.push({'corpo' : corpo, 'pontos' : pontos, 'sentimento' : 'neutro'});
					fs.writeFile('classificados.json', JSON.stringify(classificados), function (erro2)
					{
						callback();
					});
				}
			}
			else if(body['statusInfo'] == 'unsupported-text-language')
			{
				erros = 0;
				callback();
			}
			else if(indice < ultimoIndice)
			{
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
				erros++;
				if(erros > 30)
				{
					parar = true;
					callback();
				}
				else
				{
					pegarSentimento(corpo, callback, pontos);
				}
			}
		}
	});
}