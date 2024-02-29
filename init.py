from flask import Flask, request, render_template
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Manager
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
cleaned_dataframes = Manager().list()
base = 'file_server/'

# Lista para almacenar los DataFrames limpios
cleaned_dataframes = []


def upload_data(file_path):
    complete_path = os.path.join('file_server', 'prueba', file_path.replace(" ", "_"))
    df = pd.read_csv(complete_path, header=0, encoding='latin1', sep=';')
    return df

def directory_creator(route_name, folder_name):
    path = os.path.join(route_name, folder_name)
    try:
        os.makedirs(path, exist_ok=True)
        print(f"La carpeta '{folder_name}' ha sido creada exitosamente.")
    except OSError as error:
        print(f"Error al crear la carpeta: {error}")

    for uploaded_file in request.files.getlist('files[]'):
        filename = secure_filename(uploaded_file.filename)
        target_path = os.path.join(path, filename)
        uploaded_file.save(target_path)

@app.route('/upload', methods=['POST'])
def upload():

    directory_creator("file_server", 'prueba')

    global cleaned_dataframes

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(upload_data, [f for f in os.listdir('file_server/prueba') if os.path.isfile(os.path.join('file_server/prueba', f))])

    cleaned_dataframes = list(p_res)

    # Renderizar la plantilla con los DataFrames limpios
    return render_template('results.html', dataframes=cleaned_dataframes)