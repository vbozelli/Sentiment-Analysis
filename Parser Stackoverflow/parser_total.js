var async = require('async');
var fs = require('fs');
var request = require('request');
var mongoose = require('mongoose');
mongoose.connect('mongodb://localhost/stackoverflow');
var Schema = mongoose.Schema;
var Usuario = mongoose.model('Usuario', new Schema({'_id' : Number, 'criacao' : Date, 'medalha_ouro' : Number, 'medalha_prata' : Number, 'medalha_bronze' : Number, 'nome' : String, 'reputacao' : Number, 'ultimo_acesso' : Date}));
var Tag = mongoose.model('Tag', new Schema({'nome' : {'type' : String, 'unique' : true}}));
var Pergunta = mongoose.model('Pergunta', new Schema({'_id' : Number, 'corpo' : String, 'criacao' : Date, 'criador' : {'type' : Number, 'ref' : 'Usuario'}, 'pontos' : Number, 'respostas' : Number, 'tags' : [{'type' : Schema.ObjectId, 'ref' : 'Tag'}], 'titulo' : String}));
var Resposta = mongoose.model('Resposta', new Schema({'_id' : Number, 'corpo' : String, 'criacao' : Date, 'criador' : {'type' : Number, 'ref' : 'Usuario'}, 'pontos' : Number, 'pergunta' : {'type' : Number, 'ref' : 'Pergunta'}}));
var ids = [];
var proxies = [];
var indiceProxy = null;
var contadorUsuarios = 0;
var pagina = 1;
var paginaApi = 0;
var erros = 0;
var chaves = ['C49pTalrKuKbDTLUvG7zqQ(('];
var indiceChave = 0;
var regex1 = new RegExp('<code>.*?<\/code>|<pre.*?><\/pre>', 'g');
var regex2 = new RegExp('\n|\t|\r|&amp;nbsp;|&.*?;', 'g');
var regex3 = new RegExp('  +', 'g');
/*request('https://theproxisright.com/api/proxy/get?onlyActive=true&apiKey=1e946a57-171f-4f1e-8b5e-043efa51ef02&onlyHttpNotHttps=true&pageResults=false&format=text&onlyHighAvailLowLatency=true', function (erro1, resposta)
{
	var ips = resposta.body.split('\r\n');
	var tamanho = ips.length;
	for(var i = 0; i < tamanho; i++)
	{
		proxies.push('http://' + ips[i]);
	}*/
	fs.exists('paginaBancoRespostas.txt', function (exists1)
	{
		if(exists1)
		{
			fs.readFile('paginaBancoRespostas.txt', function (erro2, dados)
			{
				pagina = parseInt(dados);
				pegarApiRespostas();
			});
		}
		else
		{
			fs.exists('paginaBancoPerguntas.txt', function (exists2)
			{
				if(exists2)
				{
					fs.readFile('paginaBancoPerguntas.txt', function (erro2, dados)
					{
						pagina = parseInt(dados);
						pegarApiPerguntas();
					});
				}
				else
				{
					Usuario.findOne({'$query' : {}, '$orderby' : {'_id' : -1}}, function (erro, usuario)
					{
						if(usuario)
						{
							pegarApiUsuarios(usuario['_id']);
						}
						else
						{
							pegarApiUsuarios(-1);
						}
					});
				}
			});
		}
	});
//});
function downloadUsuarios(id)
{
	var corpo = '';
	console.log('http://api.stackexchange.com/2.2/users/' + ids.join(';') + '?pagesize=100&site=stackoverflow&key=' + chaves[indiceChave]);
	var opcoes = {'timeout' : 20000, 'url': 'http://api.stackexchange.com/2.2/users/' + ids.join(';') + '?pagesize=100&site=stackoverflow&key=' + chaves[indiceChave], 'gzip': true};
	if(indiceProxy)
	{
		console.log(proxies[indiceProxy]);
	}
	if(indiceProxy && indiceProxy < proxies.length)
	{
		opcoes['proxy'] = proxies[indiceProxy];
	}
	request(opcoes, function(erro, resposta)
	{
		if(typeof resposta === 'undefined')
		{
			erros++;
			if(erros > 10)
			{
				if(indiceProxy == null)
				{
					indiceProxy = 0;
				}
				else
				{
					indiceProxy++;
					if(indiceProxy >= proxies.length)
					{
						indiceProxy = null;
					}
				}
				erros = 0;
			}
			downloadUsuarios(id);
		}
		else
		{
			console.log(corpo);
			if(erros > 0)
			{
				erros = 0;
			}
			if(corpo.indexOf('<') == 0)
			{
				if(indiceProxy == null)
				{
					indiceProxy = 0;
				}
				else
				{
					indiceProxy++;
					if(indiceProxy >= proxies.length)
					{
						indiceProxy = null;
					}
				}
				downloadUsuarios(id);
			}
			else
			{
				try
				{
					var usuarioApi = JSON.parse(corpo);
					if('items' in usuarioApi)
					{
						var items = usuarioApi['items'];
						if(items.length > 0)
						{
							if(contadorUsuarios > 0)
							{
								contadorUsuarios = 0;
							}
							async.each(items, function (atributos, callback2)
							{
								if(atributos['user_type'] != 'does_not_exist' && atributos['user_type'] != 'unregistered')
								{
									var medalhas = atributos['badge_counts'];
									new Usuario({'_id': atributos['user_id'], 'criacao': new Date(1000 * atributos['creation_date']), 'medalha_ouro': medalhas['gold'], 'medalha_prata': medalhas['silver'], 'medalha_bronze': medalhas['bronze'], 'nome': atributos['display_name'], 'reputacao': parseInt(atributos['reputation']), 'ultimo_acesso': new Date(1000 * atributos['last_access_date'])}).save();
								}
								callback2();
							}, function (erro2)
							{
								ids.splice(0, ids.length);
								pegarApiUsuarios(id);
							});
						}
						else
						{
							contadorUsuarios++;
							ids.splice(0, ids.length);
							pegarApiUsuarios(id);
						}
					}
					else
					{
						if(indiceProxy == null)
						{
							var palavras = usuarioApi['error_message'].split(' ');
							setTimeout(function ()
							{
								indiceProxy = null;
							}, parseInt(palavras[palavras.length - 2]) * 1000);
							indiceProxy = 0;
						}
						else
						{
							indiceProxy++;
							if(indiceProxy >= proxies.length)
							{
								indiceProxy = null;
							}
						}
						downloadUsuarios(id);
					}
				}
				catch(e)
				{
					downloadUsuarios(id);
				}
			}
		}
	}).on('data', function (data)
	{
		corpo += data;
	});
}
function downloadPerguntas()
{
	fs.writeFile('paginaApiPerguntas.txt', paginaApi.toString());
	console.log('http://api.stackexchange.com/2.2/users/' + ids.join(';') + '/questions?pagesize=100&site=stackoverflow&filter=withbody&page=' + paginaApi + '&key=' + chaves[indiceChave]);
	var corpo = '';
	var opcoes = {'timeout' : 20000, 'url': 'http://api.stackexchange.com/2.2/users/' + ids.join(';') + '/questions?pagesize=100&site=stackoverflow&filter=withbody&page=' + paginaApi + '&key=' + chaves[indiceChave], 'gzip': true};
	if(indiceProxy && indiceProxy < proxies.length)
	{
		opcoes['proxy'] = proxies[indiceProxy];
	}
	request(opcoes, function(erro, resposta)
	{
		if(typeof resposta === 'undefined')
		{
			erros++;
			if(erros > 10)
			{
				if(indiceProxy == null)
				{
					indiceProxy = 0;
				}
				else
				{
					indiceProxy++;
					if(indiceProxy >= proxies.length)
					{
						indiceProxy = null;
					}
				}
				erros = 0;
			}
			downloadPerguntas();
		}
		else
		{
			if(erros > 0)
			{
				erros = 0;
			}
			console.log(corpo);
			if(corpo.indexOf('<') == 0)
			{
				if(indiceProxy == null)
				{
					indiceProxy = 0;
				}
				else
				{
					indiceProxy++;
					if(indiceProxy >= proxies.length)
					{
						indiceProxy = null;
					}
				}
				downloadPerguntas();
			}
			else
			{
				try
				{
					var perguntaApi = JSON.parse(corpo);
					if('items' in perguntaApi)
					{
						var items = perguntaApi['items'];
						if(items.length > 0)
						{
							async.eachSeries(items, function (item, callback1)
							{
								var tags = item['tags'];
								var tags1 = [];
								async.each(tags, function (tag, callback2)
								{
									Tag.findOne({'nome' : tag}, function (erro1, tag1)
									{
										if(tag1)
										{
											tags1.push(tag1['_id']);
											callback2();
										}
										else
										{
											Tag.create({'nome' : tag}, function (erro2, tag2)
											{
												if(erro2)
												{
													Tag.findOne({'nome' : tag}, function (erro3, tag3)
													{
														tags1.push(tag3['_id']);
														callback2();
													});
												}
												else
												{
													tags1.push(tag2['_id']);
													callback2();
												}
											});
										}
									});
								}, function (erro)
								{
									new Pergunta({'_id' : item['question_id'], 'corpo' : item['body'].replace(regex1, '').replace(regex2, ' ').replace(regex3, ' '), 'criacao' : new Date(1000 * item['creation_date']), 'criador' : item['owner']['user_id'], 'pontos' : item['score'], 'respostas' : item['answer_count'], 'tags' : tags1, 'titulo' : item['title']}).save();
									callback1();
								});
							}, function (erro)
							{
								if(perguntaApi['has_more'])
								{
									paginaApi++;
									downloadPerguntas();
								}
								else
								{
									ids.splice(0, ids.length);
									pagina++;
									pegarApiPerguntas();
								}
							});
						}
						else
						{
							if(perguntaApi['has_more'])
							{
								paginaApi++;
								downloadPerguntas();
							}
							else
							{
								ids.splice(0, ids.length);
								pagina++;
								pegarApiPerguntas();
							}
						}
					}
					else
					{
						if(indiceProxy == null)
						{
							var palavras = usuarioApi['error_message'].split(' ');
							setTimeout(function ()
							{
								indiceProxy = null;
							}, parseInt(palavras[palavras.length - 2]) * 1000);
							indiceProxy = 0;
						}
						else
						{
							console.log(indiceProxy);
							indiceProxy++;
							if(indiceProxy >= proxies.length)
							{
								indiceProxy = null;
							}
						}
						downloadPerguntas();
					}
				}
				catch(e)
				{
					downloadPerguntas();
				}
			}
		}
	}).on('data', function (data)
	{
		corpo += data;
	});
}
function downloadRespostas()
{
	fs.writeFile('paginaApiRespostas.txt', paginaApi.toString());
	console.log('http://api.stackexchange.com/2.2/questions/' + ids.join(';') + '/answers?pagesize=100&site=stackoverflow&filter=withbody&page=' + paginaApi + '&key=' + chaves[indiceChave]);
	var corpo = '';
	var opcoes = {'timeout' : 20000, 'url': 'http://api.stackexchange.com/2.2/questions/' + ids.join(';') + '/answers?pagesize=100&site=stackoverflow&filter=withbody&page=' + paginaApi + '&key=' + chaves[indiceChave], 'gzip': true};
	if(indiceProxy && indiceProxy < proxies.length)
	{
		opcoes['proxy'] = proxies[indiceProxy];
	}
	request(opcoes, function (erro1, resposta)
	{
		if(typeof resposta === 'undefined')
		{
			erros++;
			if(erros > 10)
			{
				if(indiceProxy == null)
				{
					indiceProxy = 0;
				}
				else
				{
					indiceProxy++;
					if(indiceProxy >= proxies.length)
					{
						indiceProxy = null;
					}
				}
				erros = 0;
			}
			downloadRespostas();
		}
		else
		{
			console.log(corpo);
			if(erros > 0)
			{
				erros = 0;
			}
			if(corpo.indexOf('<') == 0)
			{
				if(indiceProxy == null)
				{
					indiceProxy = 0;
				}
				else
				{
					indiceProxy++;
					if(indiceProxy >= proxies.length)
					{
						indiceProxy = null;
					}
				}
				downloadRespostas();
			}
			else
			{
				try
				{
					var respostaApi = JSON.parse(corpo);
					if('items' in respostaApi)
					{
						var items = respostaApi['items'];
						if(items.length > 0)
						{
							async.each(items, function (item, callback)
							{
								var criador = item['owner'];
								Usuario.findOne({'_id' : criador['user_id']}, function (erro2, usuario)
								{
									if(usuario)
									{
										new Resposta({'_id' : item['answer_id'], 'corpo' : item['body'].replace(regex1, '').replace(regex2, ' ').replace(regex3, ' '), 'criacao' : new Date(1000 * item['creation_date']), 'criador' : criador['user_id'], 'pontos' : item['score'], 'pergunta' : item['question_id']}).save();
									}
									callback();
								});
							}, function (erro2)
							{
								if(respostaApi['has_more'])
								{
									paginaApi++;
									downloadRespostas();
								}
								else
								{
									ids.splice(0, ids.length);
									pagina++;
									pegarApiRespostas();
								}
							});
						}
						else
						{
							if(respostaApi['has_more'])
							{
								paginaApi++;
								downloadRespostas();
							}
							else
							{
								ids.splice(0, ids.length);
								pagina++;
								pegarApiRespostas();
							}
						}
					}
					else
					{
						if(indiceProxy == null)
						{
							var palavras = usuarioApi['error_message'].split(' ');
							setTimeout(function ()
							{
								indiceProxy = null;
							}, parseInt(palavras[palavras.length - 2]) * 1000);
							indiceProxy = 0;
						}
						else
						{
							indiceProxy++;
							if(indiceProxy >= proxies.length)
							{
								indiceProxy = null;
							}
						}
						downloadRespostas();
					}
				}
				catch(e)
				{
					downloadRespostas();
				}
			}
		}
	}).on('data', function (data)
	{
		corpo += data;
	});
}
function pegarApiUsuarios(id)
{
	if(contadorUsuarios < 10)
	{
		var i;
		var j = id;
		for(i = 0; i < 100; i++)
		{
			ids.push(j);
			j++;
		}
		downloadUsuarios(j);
	}
	else
	{
		ids.splice(0, ids.length);
		fs.readFile('paginaBancoPerguntas.txt', function (erro, dados)
		{
			if(erro)
			{
				pagina = 1;
			}
			else
			{
				pagina = parseInt(dados);
			}
			pegarApiPerguntas();
		});
	}
}
function pegarApiPerguntas()
{
	fs.writeFile('paginaBancoPerguntas.txt', pagina.toString());
	Usuario.find().sort({'_id' : 1}).skip((pagina - 1) * 100).limit(100).exec(function (erro1, resultado)
	{
		if(resultado.length > 0)
		{
			var tamanho = resultado.length;
			for(var i = 0; i < tamanho; i++)
			{
				ids.push(resultado[i]['_id']);
			}
			if(paginaApi == 0)
			{
				fs.readFile('paginaApiPerguntas.txt', function (erro2, dados)
				{
					if(erro2)
					{
						paginaApi = 1;
					}
					else
					{
						paginaApi = parseInt(dados);
					}
					downloadPerguntas();
				});
			}
			else
			{
				paginaApi = 1;
				downloadPerguntas();
			}
		}
		else
		{
			pagina = 1;
			paginaApi = 0;
			fs.unlink('paginaBancoPerguntas.txt');
			fs.unlink('paginaApiPerguntas.txt');
			pegarApiRespostas();
		}
	});
}
function pegarApiRespostas()
{
	console.log(1)
	fs.writeFile('paginaBancoRespostas.txt', pagina.toString());
	console.log(2)
	Pergunta.find().sort({'_id' : 1}).skip((pagina - 1) * 100).limit(100).exec(function (erro1, resultado)
	{
		console.log(3)
		if(resultado.length > 0)
		{
			var tamanho = resultado.length;
			for(var i = 0; i < tamanho; i++)
			{
				ids.push(resultado[i]['_id']);
			}
			if(paginaApi == 0)
			{
				fs.readFile('paginaApiRespostas.txt', function (erro2, dados)
				{
					if(erro2)
					{
						paginaApi = 1;
					}
					else
					{
						paginaApi = parseInt(dados);
					}
					downloadRespostas();
				});
			}
			else
			{
				paginaApi = 1;
				downloadRespostas();
			}
		}
		else
		{
			pagina = 1;
			paginaApi = 0;
			fs.unlink('paginaBancoRespostas.txt');
			fs.unlink('paginaApiRespostas.txt');
		}
	});
}