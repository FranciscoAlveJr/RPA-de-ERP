# RPA de ERP do Bling
Essa RPA, feita em Python, cria uma tarefa, via o script `executar.py` que, a cada 2 horas, abre o site Catavento, que contém um catálogo de produtos com o suas devidas características e números de estoque
, faz login, com as credenciais previamente salvas, e acessa diretamente a página de download do catálogo, que está no formato CSV. Então, o robô clica em fazer o download e baixa o arquivo 
no diretório `download/`.<p>
O robô espera a realização do download e, após o término, lê o arquivo baixado e cria um dataframe com os dados do mesmo.<p>
Após isso, é feita a conexão com a API do bling, com as credenciais previamente criadas no site do [bling](https://www.bling.com.br/). Com os dados obtidos via requisição da API, é feita uma
comparação entre os estoques presentes no dataframe e na ERP, havendo diferença, o valor de estoque do produto da ERP é atualizada para o valor contido no catálogo.<p>
Após a atualização, o robô apaga o arquivo CSV contido na pasta `download/`.<p>

## Principais Bibliotecas Usadas
- Pandas (Tratamento de dados)
- Requests (Conexão com a API)
- Httpx (Conexão alternativa com a API)
- Selenium (Automação de navegador)
- Sqlite3 (Armazenamento de dados)
