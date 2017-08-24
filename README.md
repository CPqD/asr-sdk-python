CPqD ASR Recognizer
===================

O Recognizer é uma API para criação de aplicações de voz que utilizam o
servidor CPqD ASR para reconhecimento de fala.

Para maiores informações, consulte [a documentação do projeto](http://speech-doc.cpqd.com.br/asr).

### Códigos de Exemplo

Códigos de exemplo estão na raiz do projeto, nos scripts `basic.py` e `mic.py`.

### Dependências

Versão testada com `Python>=3.4`

Depende da biblioteca `pyaudio>=0.2.11`, a qual opera sobre o PortAudio.
Necessário instalar biblioteca PortAudio para correto funcionamento.

* Ubuntu/Debian e derivados: `apt-get install libportaudio2`

Para demais dependências, checar `requirements.txt`.

### Teste

Caso haja interesse em executar os testes do cliente em Python, modifique
o arquivo `tests/config.py` para apontar para um servidor ASR válido. O
servidor deverá conter a gramática de números `builtin:grammar/samples/phone`
disponibilizada por distribuições do CPqD e o modelo de língua estatístico
versão reduzida `builtin:slm/general-small`. Os testes são realizados
utilizando a biblioteca `nose2`.


Licença
-------

Copyright (c) 2017 CPqD. Todos os direitos reservados.

Publicado sob a licença Apache Software 2.0, veja LICENSE.
