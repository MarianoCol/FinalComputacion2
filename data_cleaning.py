from arguments import argument_definition
import pandas as pd
import os

args = argument_definition()


def upload_data(file_path):
    df = pd.read_csv(file_path, header=args.header, encoding='latin1', sep=';')
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


async def directory_creator(route_name, folder_name):
    directory_path = os.path.join(route_name, folder_name)
    try:
        os.makedirs(directory_path, exist_ok=True)
        print("La carpeta ha sido creada exitosamente.")
    except OSError as error:
        print(f"Error al crear la carpeta: {error}")

    return directory_path
