import socket
import os
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from arguments import argument_definition
from data_cleaning import upload_data, clean_data, clean_nulls, drop_columns, directory_creator, send_all_dataframes


def recibir_archivo(conn, filename, filesize):
    with open(filename, 'wb') as f:
        recibido = 0
        while recibido < filesize:
            data = conn.recv(min(1024, filesize - recibido))
            if not data:
                break
            f.write(data)
            recibido += len(data)


def handle_client(conn, addr):
    try:
        arguments = conn.recv(1024).decode()
        print(f'parametros recibidos: {arguments}')
        arguments_parsed = json.loads(arguments)
        directory_path = directory_creator('file_server',
                                           arguments_parsed['folder'])
        file_paths = []

        while True:
            filename_len = int.from_bytes(conn.recv(4), byteorder='big')
            if not filename_len:
                break
            filename = conn.recv(filename_len).decode()
            filename = filename.split('/')
            filename = filename[-1]
            filesize = int.from_bytes(conn.recv(8), byteorder='big')
            print("Recibiendo:", filename)
            filepath = os.path.join(directory_path, filename)
            file_paths.append(filepath)
            recibir_archivo(conn, filepath, filesize)
            print("Archivo {} recibido exitosamente".format(filename))

        dataframes = handle_parameters(conn, file_paths, arguments_parsed)
        df_list = list(dataframes)
        print('DATAFRAMES')
        print(df_list)
        # Serializar el dataframe combinado
        descarga = conn.recv(1024).decode()
        if descarga != '':
            print(descarga)

            send_all_dataframes(conn, df_list)

    except Exception as e:
        print(f"Error al manejar la conexión con el cliente: {e}")

    finally:
        try:
            directory_path = os.path.join('file_server',
                                          arguments_parsed['folder'])
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error al eliminar {file_path}: {e}")

            os.rmdir(directory_path)

        except Exception as e:
            print(f"Error al eliminar el directorio temporal: {e}")

    conn.close()


def handle_parameters(conn, file_paths, arguments):
    try:
        parameters = conn.recv(1024).decode()
        list_parameters = parameters.split(',')
        with ThreadPoolExecutor() as thread:
            p_res = thread.map(lambda df: upload_data(df, arguments), file_paths)

        if list_parameters[0] == 'SI':
            with ThreadPoolExecutor() as thread:
                p_res = thread.map(clean_data, p_res)

        if list_parameters[1] == 'SI':
            with ThreadPoolExecutor() as thread:
                p_res = thread.map(clean_nulls, p_res)

        columns_to_drop_list = list_parameters[3:]

        if list_parameters[2] == 'SI':
            with ThreadPoolExecutor() as thread:
                p_res = thread.map(lambda df: drop_columns(df,
                                                           columns_to_drop_list), list(p_res))

        return p_res

    except Exception as e:
        print(f"Error al manejar los parámetros: {e}")


def main():
    args = argument_definition()

    host = '::'  # Recibe IPv4 como en IPv6
    port = args.port

    servidor = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, port))
    servidor.listen(5)
    print("Servidor escuchando en {}:{}".format(host, port))

    with ProcessPoolExecutor(max_workers=5) as executor:  # Ejecutar hasta 5 procesos simultáneos
        while True:
            try:
                conn, addr = servidor.accept()
                print("Conexión establecida desde:", addr)

                # Enviar la tarea a un proceso del pool
                executor.submit(handle_client, conn, addr)

            except Exception as e:
                print(f"Error al aceptar una conexión: {e}")


if __name__ == "__main__":
    main()
