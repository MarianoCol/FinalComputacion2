from flask import Flask, render_template, request, redirect, url_for
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from shutil import rmtree
from multiprocessing import Manager
import pandas as pd
import os

app = Flask(__name__)
cleaned_dataframes = Manager().list()
base = 'file_server/'

# Lista para almacenar los DataFrames limpios
cleaned_dataframes = []


def upload_data(file_path):
    complete_path = os.path.join('file_server', 'prueba', file_path.replace(" ", "_"))
    df = pd.read_csv(complete_path, header=0, encoding='latin1', sep=';')
    return df


def clean_data(dataframe):
    cleaned_data = dataframe.drop_duplicates()
    return cleaned_data


def clean_nulls(dataframe):
    cleaned_data = dataframe.dropna()
    return cleaned_data


def drop_columns(dataframe, columns_to_drop):
    cleaned_data = dataframe.drop(columns=columns_to_drop, errors='ignore')
    return cleaned_data


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():

    directory_creator("file_server", 'prueba')

    global cleaned_dataframes

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(upload_data, [f for f in os.listdir('file_server/prueba') if os.path.isfile(os.path.join('file_server/prueba', f))])

    cleaned_dataframes = list(p_res)

    return render_template('results.html', dataframes=cleaned_dataframes)


@app.route('/drop_duplicates', methods=['POST'])
def drop_duplicates():

    global cleaned_dataframes

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_data, cleaned_dataframes)

    cleaned_dataframes = list(p_res)

    return render_template('results.html', dataframes=cleaned_dataframes)


@app.route('/drop_nulls', methods=['POST'])
def drop_nulls():

    global cleaned_dataframes

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_nulls, cleaned_dataframes)

    cleaned_dataframes = list(p_res)

    # Renderizar la plantilla con los DataFrames limpios
    return render_template('results.html', dataframes=cleaned_dataframes)


@app.route('/drop_column', methods=['POST'])
def drop_column():

    global cleaned_dataframes

    columns_to_drop = request.form.get('columns_to_drop').split(',')

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(lambda df: drop_columns(df, columns_to_drop), cleaned_dataframes)

    cleaned_dataframes = list(p_res)

    return render_template('results.html', dataframes=cleaned_dataframes)


@app.route('/clear_dataframes', methods=['POST'])
def clear_dataframes():
    global cleaned_dataframes

    # Eliminar los DataFrames de la lista
    cleaned_dataframes = []

    # Eliminar los archivos en la carpeta 'file_server/prueba'
    folder_path = 'file_server/prueba'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)