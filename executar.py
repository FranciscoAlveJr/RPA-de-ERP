import subprocess
import os
from time import sleep
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', filename='log.log')

try:
    path = 'task.bat'
    program_path = os.path.abspath(path)
    base_path = os.path.abspath('.')
    xml_path = os.path.abspath('data/ERP.xml')

    def parse_xml(xml):
        namespace = {'': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}

        ET.register_namespace('', 'http://schemas.microsoft.com/windows/2004/02/mit/task')

        tree = ET.parse(xml)
        root = tree.getroot()
        
        start = root.find('.//Triggers/TimeTrigger/StartBoundary', namespace)
        comando = root.find('.//Actions/Exec/Command', namespace)
        work_dir = root.find('.//Actions/Exec/WorkingDirectory', namespace)

        data = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        start.text = data
        comando.text = program_path
        work_dir.text = base_path

        tree.write(xml, encoding='UTF-16')

    parse_xml(xml_path)

    with open(path, encoding='UTF-8') as file:
        linhas = file.readlines()

    for i, l in enumerate(linhas):
        mod_line = f'cd /d "{base_path}"\n'
        if 'cd /d' in l and l != mod_line:
            linhas[i] = mod_line

    with open(path, 'w', encoding='UTF-8') as file:
        file.writelines(linhas)

    task_name = 'ERP'

    cmd_ag = f'schtasks /create /tn "ERP" /xml "{xml_path}" /f'

    subprocess.run(cmd_ag, shell=True)

    sleep(1)

    cmd_run = f'schtasks /run /tn {task_name}'
    subprocess.run(cmd_run, shell=True)

except Exception as e:
    logging.exception(e)

# if __name__=='__main__':
#     parse_xml('ERP.xml')