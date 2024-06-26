import pandas as pd
import os
import pickle


def upload_data(file_path, arguments):
    df = pd.read_csv(file_path, header=arguments['header'],
                     encoding=arguments['encoding'],
                     sep=arguments['sep'])
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


def send_all_dataframes(conn, dataframes):
    # Combinar los dataframes en uno solo
    print('entro')
    lista_dataframes = []
    for i in list(dataframes):
        lista_dataframes.append(i)
    combined_dataframe = pd.concat(lista_dataframes, ignore_index=True,
                                   verify_integrity=True)
    df_clean = combined_dataframe.drop_duplicates(keep=False)
    print(df_clean)

    # Serializar el dataframe combinado
    combined_dataframe_serializado = pickle.dumps(df_clean)
    print('dumpeados')

    # Enviar el tamaño del dataframe serializado al cliente
    conn.sendall(len(combined_dataframe_serializado).to_bytes(4,
                                                              byteorder='big'))
    print('tamaño enviado')

    # Enviar el dataframe serializado al cliente
    conn.sendall(combined_dataframe_serializado)
    print('enviado')


def directory_creator(route_name, folder_name):
    directory_path = os.path.join(route_name, folder_name)
    try:
        os.makedirs(directory_path, exist_ok=True)
        print(f"La carpeta {directory_path} ha sido creada exitosamente.")
    except OSError as error:
        print(f"Error al crear la carpeta: {error}")

    return directory_path
