# Como Rodar o Projeto Localmente

Siga estes passos para configurar e executar a aplicação no seu ambiente.

 1. Crie e Ative o Ambiente Virtual (venv)
Abra o terminal na pasta do projeto.

Execute o comando para criar um ambiente virtual chamado venv:

```
python -m venv venv
```
Ative o ambiente virtual. Se estiver no Windows, use:

```
.\venv\Scripts\activate
```

2. Instale as Dependências
Com o ambiente virtual ativado, instale todas as bibliotecas necessárias a partir do arquivo requirements.txt:
```
pip install -r requirements.txt
```
3. Inicie o Servidor do Grafo
Execute o servidor Python que irá fornecer os dados do grafo para a página web.

No terminal, rode o arquivo servidor_grafo.py:
```
python servidor_grafo.py
```
Aguarde a mensagem que indica que o servidor está em execução, geralmente algo como: Running on http://127.0.0.1:5000.

4. Acesse a Aplicação Web
Abra o arquivo ```teste_grafo.html``` diretamente no seu navegador de internet.

O navegador irá carregar a página e se conectar automaticamente ao servidor Python que você iniciou no passo anterior para exibir o grafo.
