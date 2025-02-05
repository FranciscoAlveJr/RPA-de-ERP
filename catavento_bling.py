from catavento import estoque
import pandas as pd
import os
# import dask.dataframe as dd
# import json
from api_bling import atualizar_produto_async, get_produtos_async, get_produtos, atualizar_produto
from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor
import asyncio
import httpx
# from tenacity import RetryError
# from time import sleep
import logging

async def integrar():
    '''
    Função assíncrona para integrar os dados do catálogo, baixado no site do catavento, com os dados da API do bling. Os dados de estoque são comparados e, se forem diferentes, o estoque da API é subistuído pelo estoque do catálogo, que está atualizado.
    '''
    start = datetime.now() # Hora do início da aplicação
    i = 1 # Contagem de páginas

    print()

    arquivo = os.listdir('download') # Catálogo atualizado de produtos
    dir_arq = f'download/{arquivo[0]}'

    print(f'Acessando {arquivo[0]}')
    logging.info(f'Acessando {arquivo[0]}')

    df_catavento = pd.read_csv(dir_arq, delimiter='|', dtype='str') # Dataframe do catálogo
    cata_dict = df_catavento.set_index('Barras').to_dict()
    cata_e = cata_dict['Estoque']
    est_list = list(cata_e.keys())

    estoque_novo = [] # Lista onde entraram novos valores de estoque para serem atualizados

    logging.info('Analisando e filtrando produtos...')
    print('Analisando e filtrando produtos...')

    async with httpx.AsyncClient() as client: # Atribui, de maneira assíncrona, a variável client para requisições httpx
        while True:
            tasks = [get_produtos_async(client, pag) for pag in range(i, i+3)] # Faz 3 requisições por vez
            results = await asyncio.gather(*tasks)
            await asyncio.sleep(0.5) # Espera para a próxima requisição

            # produtos = get_produtos(i) # Função que acessa a API da ERP e retorna os produtos

            if 'continue' in results:
                continue
            elif None in results:
                break
            elif 'invalid_token' in results:
                get_produtos(i)
                continue

            produtos = sum(results, []) # Junta as listas dos produtos em uma lista única
            
            i += 3 # Avança 3 páginas a cada momento do loop

            # Lista de produtos filtrados pelo número de estoque
            novo = [
                {'id': produto['id'],
                'codigo': produto['codigo'],
                'preco': produto['preco'],
                'estoque': cata_e[produto['codigo']]}
                for produto in produtos if produto['codigo'] in est_list and produto['estoque']['saldoVirtualTotal'] != int(cata_e[produto['codigo']])
            ]

            estoque_novo.extend(novo) # Entrada de novos produtos na lista para atualizar

    print()
    print('Atualizando estoque...')
    logging.info('Atualizando estoque...')

    # Usa os valores do estoque novo para fazer as atualizações
    async with httpx.AsyncClient() as client:
        for i in range(0, len(estoque_novo), 3):
            while True:
                batch = estoque_novo[i:i+3] # 3 produtos atribuídos por vez
                tasks = [atualizar_produto_async(client, produto) for produto in batch]
                res = await asyncio.gather(*tasks)
                await asyncio.sleep(0.34)

                if 'invalid_token' in res:
                    atualizar_produto(estoque_novo[i])
                    continue
                break
    
    print()
    print('O estoque está atualizado.')
    logging.info('O estoque está atualizado.')

    arq_dir = os.path.abspath(dir_arq)
    os.remove(arq_dir) # Deleta o arquivo csv baixado no catavento

    end = datetime.now() # Hora do fim da aplicação
    logging.info(end - start)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', filename='log.log')

    arquivos = os.listdir('download')
    downloads = ' '.join(arquivos)

    try:
        if '.csv' not in downloads:
            estoque.acesar_site()
            estoque.login()
            estoque.central_cliente()
        asyncio.run(integrar())
    except Exception as e:
        logging.exception(e)

