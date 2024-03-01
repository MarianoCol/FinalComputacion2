from flask import Flask, request
from werkzeug.utils import secure_filename
from multiprocessing import Manager
from arguments import argument_definition
import pandas as pd
import os

app = Flask(__name__)
cleaned_dataframes = Manager().list()
args = argument_definition()

# Lista para almacenar los DataFrames limpios
cleaned_dataframes = []


def upload_data(file_path):
    complete_path = os.path.join(args.directory, args.folder, file_path.replace(" ", "_"))
    df = pd.read_csv(complete_path, header=args.header, encoding='latin1', sep=';')
    return df


def clean_data(dataframe):
    cleaned_data = dataframe.drop_duplicates()
    return cleaned_data


def clean_nulls(dataframe):
    cleaned_data = dataframe.dropna()
    return cleaned_data


def drop_columns(dataframe, columns_to_drop):
    # Eliminar las columnas especificadas del DataFrame
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