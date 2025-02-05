import requests as rq
# from requests.exceptions import ConnectionError
# from requests import Session
# from concurrent.futures import ThreadPoolExecutor
import base64
# from pprint import pprint
import json
# from json.decoder import JSONDecodeError
from time import sleep
# import pandas as pd
from datetime import datetime
import sqlite3
# from time import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from dotenv import dotenv_values

token_path = 'data/token.json' # Caminho para o token de acesso

def criar_db(): 
    '''
    Função para criar o banco de dados que salva o id de estoque dos produtos.
    '''
    conn = sqlite3.connect('data/estoque.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS produtos (id_produto INTEGER, id_estoque INTEGER)')
    conn.commit()
    conn.close()

def credentials():
    '''
    Função para acessar as credenciais da API.
    '''

    clients = dotenv_values('data/.env')
    client_id = clients['client_id']
    client_secret = clients['client_secret']

    c_str = f'{client_id}:{client_secret}'
    c_bytes = c_str.encode('ascii')

    credentials = base64.b64encode(c_bytes)
    credentials = credentials.decode('ascii')

    return credentials

def save_token(code):
    '''
    Função para salvar o token usando o código gerado pela através do link: https://www.bling.com.br/b/Api/v3/oauth/authorize?response_type=code&client_id=294d259dd80d34b37bfa381b3407761626d41736&state=3734cec6520c6fdef043f68f62d45e45
    '''

    credencial = credentials() # Variável com as credenciais da API

    url = 'https://api.bling.com.br/Api/v3/oauth/token'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '1.0',
        'Authorization': f'Basic {credencial}',
    }

    payload = {
        'grant_type': 'authorization_code',
        'code': code
    }

    # Solicitação do token
    res = rq.post(url, headers=headers, data=payload)
    
    json_res = res.json()
    tokens = {}
    tokens['token'] = json_res['access_token']
    tokens['refresh_token'] = json_res['refresh_token']

    # Salva a resposta da solicitação em json, contendo o token e o refresh token
    with open(token_path, 'w') as file:
        json.dump(tokens, file)

def refresh_token(refr_token: str):
    '''
    Função para atualizar o token quando este se encontra vencido, utilizando o refresh token.
    '''
    credencial = credentials()

    url = 'https://api.bling.com.br/Api/v3/oauth/token'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '1.0',
        'Authorization': f'Basic {credencial}',
    }
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refr_token
    }

    # Solicitação de um novo token
    res = rq.post(url, headers=headers, data=payload)

    json_res = res.json()
    tokens = {}
    tokens['token'] = json_res['access_token']
    tokens['refresh_token'] = json_res['refresh_token']

    # Salva o novo token no arquivo json
    with open(token_path, 'w') as file:
        json.dump(tokens, file)


def get_produtos(i: int) -> list[dict]:
    url = 'https://api.bling.com.br/Api/v3/produtos'
    
    # Acessa o arquivo json para extrair o token e refresh token
    with open(token_path) as file:
        json_token = json.load(file)

    token = json_token['token']
    refr_token = json_token['refresh_token']

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Parâmetros necessários para filtrar os tipos de produtos, incluindo a página a ser acessada
    params = {
        'pagina': i,
        'criterio': 5,
        'tipo': 'P',
    }

    # Faz requisição e verifica se está funcionando corretamente, do contrário, ele insite até funcionar
    while True:
        res = rq.get(url, headers=headers, params=params)
        if res.status_code == 504:
            sleep(5)
            continue
        break

    json_res = res.json()

    # Verifica qual o tipo de resposta
    try:
        if json_res['data'] == []: # Se for vazio, retorna None e encerra a pesquisa
            return None
        
        return json_res['data'] # Se houver dados, retorna os valores para continuar a pesquisa
    except KeyError:
        erro = json_res['error']['type']

        if erro == 'invalid_token': # Se ocorrer um erro, verifica se é pelo token e o atualiza
            refresh_token(refr_token)

        sleep(1)
        return 'continue'
'''
def get_produto(codigo: str) -> list:
    url = 'https://developer.bling.com.br/api/bling/produtos'
    produtos_list = []
    i = 1

    while True:
        with open(token_path) as file:
            json_token = json.load(file)

        token = json_token['access_token']
        refr_token = json_token['refresh_token']

        headers = {
            'Authorization': f'Bearer {token}'
        }

        params = {
            'criterio': 5,
            'tipo': 'P',
            'codigos[]': [codigo]
        }

        res = rq.get(url, headers=headers, params=params)
        json_res = res.json()

        try:
            produto = json_res['data']
        except KeyError:
            erro = json_res['error']['type']
            if erro == 'invalid_token':
                refresh_token(refr_token)
                sleep(1)
                continue

        return produto

def acessar_estoque():
    ini = datetime.now()
    produtos = get_produtos()

    f = datetime.now()
    print(f-ini)

    df = pd.DataFrame(produtos)
    df.to_csv('ERP.csv', sep='|', encoding='UTF-8')
'''
def atualizar_produto(produto: dict):
    url_post = f'https://api.bling.com.br/Api/v3/estoques'
    
    conn = sqlite3.connect('data/estoque.db')
    cursor = conn.cursor()

    dados = cursor.execute('SELECT * FROM produtos').fetchall()
    dados = list(zip(*dados))

    try:
        id_prod_list = dados[0]
    except IndexError:
        id_prod_list = []

    # estoque = json.dumps(estoque)

    codigo = produto['codigo']
    preco = produto['preco']
    estoque = produto['estoque']
    id = produto['id']

    while True:
        with open(token_path) as file:
            json_token = json.load(file)

        token = json_token['token']
        refr_token = json_token['refresh_token']

        headers = {
            'Authorization': f'Bearer {token}',
            "Content-Type": "application/json",
        }

        try:
            if estoque.isnumeric():
                data = datetime.now()
                data = data.strftime("%Y-%m-%d %H:%M:%S")

                if int(id) in id_prod_list:
                    id_estoque = cursor.execute(f'SELECT id_estoque FROM produtos WHERE id_produto={id}').fetchone()
                    id_estoque = id_estoque[0]

                    url_put = f'https://api.bling.com.br/Api/v3/estoques/{id_estoque}'

                    body = {
                        "operacao": "B",
                        "preco": preco,
                        "custo": 0,
                        "quantidade": int(estoque),
                        "observacoes": "Balanço gerado pela liberação de espaço",
                        "data": data
                    }

                    params = {
                        'idEstoque': id_estoque,
                        }
                
                    res = rq.put(url_put, headers=headers, json=body, params=params)
                    if res.text == '':
                        pass
                    else:
                        json_res = res.json()
                        erro = json_res['error']['type']

                        if erro == 'invalid_token': # Se ocorrer um erro, verifica se é pelo token e o atualiza
                            refresh_token(refr_token)
                        
                else:
                    # state = str(uuid.uuid4())
                    body = {
                        "produto": {
                            "id": id,
                            "codigo": codigo
                        },
                        "deposito": {
                            "id": 14886610297
                        },
                        "operacao": "B",
                        "preco": preco,
                        "custo": 0,
                        "quantidade": int(estoque),
                        "observacoes": "Balanço gerado pela liberação de espaço",
                        }

                    res = rq.post(url_post, headers=headers, json=body)
                    json_res = res.json()

                    if res.status_code == 201:
                        id_estoque = json_res['data']['id']

                        conn.execute('INSERT INTO produtos (id_produto, id_estoque) VALUES (?, ?)', [id, id_estoque])
                        conn.commit()
                    else:
                        json_res = res.json()
                        erro = json_res['error']['type']

                        if erro == 'invalid_token': # Se ocorrer um erro, verifica se é pelo token e o atualiza
                            refresh_token(refr_token)                       
            break
        except KeyError:
            erro = json_res['error']
            if erro == 'Too many requests':
                sleep(1)
                continue
        except AttributeError:
            break
    
    conn.close()


# @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=3, max=30))
async def get_produtos_async(client:httpx.AsyncClient, pagina: int) -> list[dict]:
    '''
    Função assíncrona que retorna uma lista de dicionários com os produtos, acessando por página. Cada página retorna 100 produtos.
    '''

    url = 'https://api.bling.com.br/Api/v3/produtos'
    
    # Acessa o arquivo json com o token e o refresh token
    with open(token_path) as file:
        json_token = json.load(file)

    token = json_token['token']
    refr_token = json_token['refresh_token']

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Parâmetros de entrada para a API, variando por página
    params = {
        'pagina': pagina,
        'criterio': 5,
        'tipo': 'P',
    }

    # Faz requisição e verifica se está funcionando corretamente, do contrário, ele insite até funcionar
    while True:
        res = await client.get(url, headers=headers, params=params)
        if res.status_code == 504:
            sleep(5)
            continue
        break

    json_res = res.json()

    # Verifica qual o tipo de resposta
    try:
        if json_res['data'] == []: # Se for vazio, retorna None e encerra a pesquisa
            return None
        
        return json_res['data'] # Se houver dados, retorna os valores para continuar a pesquisa
    except KeyError:
        erro = json_res['error']['type']

        if erro == 'invalid_token': # Se ocorrer um erro, verifica se é pelo token e o atualiza
            return erro

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=3, max=30))
async def atualizar_produto_async(client: httpx.AsyncClient, produto: dict):
    '''
    Função assíncrona atualizar o estoque de um produto contido em um dicionário
    '''
    url_post = f'https://api.bling.com.br/Api/v3/estoques'
    
    # Acessa o banco de dados
    conn = sqlite3.connect('data/estoque.db')
    cursor = conn.cursor()

    # Dados da id do produto e do estoque
    dados = cursor.execute('SELECT * FROM produtos').fetchall()
    dados = list(zip(*dados))

    # Verifica se "dados" esta vazio
    try:
        id_prod_list = dados[0]
    except IndexError:
        id_prod_list = []

    # Dados do produto atualizado
    codigo = produto['codigo']
    preco = produto['preco']
    estoque = produto['estoque']
    id = produto['id']

    # Acesso ao arquivo json com token e refresh token
    with open(token_path) as file:
        json_token = json.load(file)

    token = json_token['token']
    refr_token = json_token['refresh_token']

    headers = {
        'Authorization': f'Bearer {token}',
        "Content-Type": "application/json",
    }

    # try:
    if estoque.isnumeric(): # Verifica se o estoque é numérico antes de começar. Não sendo, encerra.
        data = datetime.now()
        data = data.strftime("%Y-%m-%d %H:%M:%S") # Data e hora do momento da atualização

        # Verifica se o id do produto está no banco de dados. Se sim, faz a requisição pelo método  PUT
        if int(id) in id_prod_list:
            id_estoque = cursor.execute(f'SELECT id_estoque FROM produtos WHERE id_produto={id}').fetchone()
            id_estoque = id_estoque[0] # Id do estoque salvo no banco de dados

            url_put = f'https://api.bling.com.br/Api/v3/estoques/{id_estoque}'

            # O body solicitado pela a API para o método PUT
            body = {
                "operacao": "B",
                "preco": preco,
                "custo": 0,
                "quantidade": int(estoque),
                "observacoes": "Balanço gerado pela liberação de espaço",
                "data": data
            }

            params = {
                'idEstoque': id_estoque,
                }
        
            # Faz a requisição e insiste, caso ocorra um erro
            while True:
                res = await client.put(url_put, headers=headers, json=body, params=params, timeout=60)
                if res.status_code == 204:
                    logging.info(f'Produto {id} atualizado com sucesso.')
                    break
                else:
                    logging.info(f'Ocorreu um erro no produto {id}')
                    print(f'Ocorreu um erro no produto {id}')
                    json_res = res.json()
                    logging.info(json_res)
                    
                    erro = json_res['error']['type']
                    if erro == 'invalid_token': # Se o erro for de token, o mesmo é atualizado
                        # refresh_token(refr_token)
                        return erro
                    else:
                        break
                        
        else: # Se o id do produto não estiver no banco de dados, a requisição deve ser pelo método POST
            # O body solicitado pela API pelo método POST
            body = {
                "produto": {
                    "id": id,
                    "codigo": codigo
                },
                "deposito": {
                    "id": 14886610297
                },
                "operacao": "B",
                "preco": preco,
                "custo": 0,
                "quantidade": int(estoque),
                "observacoes": "Balanço gerado pela liberação de espaço",
                }

            # Insiste na requisição, se houver erro, continua.
            while True:
                res = await client.post(url_post, headers=headers, json=body)

                # Se o resultado for positivo, retorna um id de estoque
                if res.status_code == 200:  
                    id_estoque = json_res['data']['id']

                    # O id de estoque então é salvo no banco de dados, junto do respectivo id do produto
                    conn.execute('INSERT INTO produtos (id_produto, id_estoque) VALUES (?, ?)', [id, id_estoque])
                    conn.commit()
                    break
                else:
                    print(f'Ocorreu um erro no produto {id}')
                    logging.info(f'Ocorreu um erro no produto {id}')
                    json_res = res.json()
                    print(json_res)
                    logging.info(json_res)

                    erro = json_res['error']['type']
                    if erro == 'invalid_token': # Se o erro for por token, o mesmo é atualizado
                        # refresh_token(refr_token)
                        return erro
    
    # No final, fecha o banco de dados
    conn.close()

if __name__=='__main__':
    save_token('f0554b0fcb1c3d393668dcb7432d23fe4c29b5bd')
    # criar_db()
    # acessar_estoque()
    # get_produtos(1)
