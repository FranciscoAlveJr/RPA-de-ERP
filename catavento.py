from selenium.webdriver import Chrome
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from selenium.common.exceptions import JavascriptException, TimeoutException, UnexpectedAlertPresentException

from dotenv import dotenv_values
from time import sleep
import os
# import pandas as pd
import logging

class Estoque:
    '''
    Classe para acessar, logar e baixar o estoque do site catavento.
    '''
    def __init__(self) -> None:
        self.url = 'https://www.cataventobr.com.br/index.php?opcao=login'

        # Acesso dos dados de login no site do catavento
        login = dotenv_values('data/.env')
        self.email = login['email']
        self.senha = login['senha']

    def acesar_site(self):
        '''
        Função que acessa o site catavento
        '''

        dir = os.path.abspath('download') # caminho do download

        options = Options()
        options.add_experimental_option('prefs',{
        "download.default_directory": dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
        })
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")      
        options.add_argument("--password-store=basic")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.driver = Chrome(options=options)
        self.driver.maximize_window()
        self.driver.get(self.url)

        self.wa = WebDriverWait(self.driver, 10)

    def login(self): 
        '''
        Função para fazer login no site do catavento.
        '''

        self.wa.until(EC.presence_of_element_located((By.ID, 'usuario')))

        # Inserir usuário
        input_usuario = self.driver.find_element(By.ID, 'usuario')
        input_usuario.send_keys(self.email)

        sleep(1)

        # Inserir senha
        input_senha = self.driver.find_element(By.ID, 'senha')
        input_senha.send_keys(self.senha)

        sleep(1)

        # Clicar no botão entrar
        btn_entrar = self.driver.find_element(By.ID, 'envia_login')
        btn_entrar.click()

    def central_cliente(self):
        '''
        Função para acessar a aba de download na página da central do cliente e baixar o arquivo csv do catálogo.
        '''
        self.wa.until(EC.presence_of_element_located((By.CLASS_NAME, 'dl-trigger')))

        # Link direto para a aba de download na página da central do cliente
        url = 'https://www.cataventobr.com.br/index.php?opcao=central_cliente#tab-csv'

        self.driver.get(url)

        self.wa.until(EC.presence_of_element_located((By.CLASS_NAME, 'ajax-csv')))
        # Clica no botão de Download
        btn_download = self.driver.find_element(By.CLASS_NAME, 'ajax-csv')
        btn_download.click()

        print('Baixando catálogo...')
        logging.info('Baixando catálogo...')

        # Aguardar o término do download
        while True:
            arquivos = os.listdir('download')
            if any(a.endswith('.crdownload') for a in arquivos):
                break
            sleep(1)

        while True:
            arquivos = os.listdir('download')
            if not any(a.endswith('.crdownload') for a in arquivos):
                print()
                print('Download completo!')
                logging.info('Download completo!')
                self.driver.quit()
                break
            sleep(1)
    
    # def ler_csv(self):
    #     arquivo = os.listdir('download')
    #     dir_arq = f'download/{arquivo[0]}'
    #     df = pd.read_csv(dir_arq, delimiter='|')
    #     codigos = df['Barras'].to_list()

    #     return df
        # sleep(1)

        # arq_dir = os.path.abspath(dir_arq)
        # os.remove(arq_dir)

estoque = Estoque()
if __name__=='__main__':
    estoque = Estoque()
    # estoque.acesar_site()
    # estoque.login()
    # estoque.central_cliente()

    # estoque.driver.quit()
