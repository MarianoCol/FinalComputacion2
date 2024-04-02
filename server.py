import socket
import os
from concurrent.futures import ThreadPoolExecutor
from data_cleaning import upload_data, clean_data, clean_nulls, drop_columns


def recibir_archivo(conn, filename, filesize):
    with open(filename, 'wb') as f:
        recibido = 0
        while recibido < filesize:
            data = conn.recv(min(1024, filesize - recibido))
            if not data:
                break
            f.write(data)
            recibido += len(data)


def main():
    host = '::'  # Escuchará tanto en IPv4 como en IPv6
    port = 12345

    servidor = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, port))
    servidor.listen(1)
    print("Servidor escuchando en {}:{}".format(host, port))

    conn, addr = servidor.accept()
    print("Conexión establecida desde:", addr)

    file_paths = []

    while True:
        filename_len = int.from_bytes(conn.recv(4), byteorder='big')
        if not filename_len:
            break
        filename = conn.recv(filename_len).decode()
        filesize = int.from_bytes(conn.recv(8), byteorder='big')
        print("Recibiendo:", filename)
        filepath = os.path.join('file_server', filename)
        file_paths.append(filepath)
        recibir_archivo(conn, filepath, filesize)
        print("Archivo {} recibido exitosamente".format(filename))

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(upload_data, file_paths)

    dataframes = list(p_res)

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_data, dataframes)

    cleaned_dataframes = list(p_res)

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_nulls, cleaned_dataframes)

    no_null_dataframes = list(p_res)

    columns_to_drop_list = ['cadena', 'jornada']

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(lambda df: drop_columns(df, columns_to_drop_list),
                           no_null_dataframes)

    print(list(p_res))

    conn.close()


if __name__ == "__main__":
    main()
