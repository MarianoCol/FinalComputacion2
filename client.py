import tkinter as tk
from tkinter import filedialog
import socket
import os
from arguments import argument_definition

archivos_seleccionados = []

args = argument_definition()


def enviar_archivos_seleccionados():
    global archivos_seleccionados
    archivos_seleccionados = list(filedialog.askopenfilenames())
    print("Archivos seleccionados:", archivos_seleccionados)
    # for filename in archivos_seleccionados:
    #     print("Enviando:", filename)
    #     enviar_archivo(cliente, filename)
    #     print("Archivo {} enviado exitosamente".format(filename))


def enviar_archivo(conn, filename):
    filesize = os.path.getsize(filename)
    conn.sendall(len(filename).to_bytes(4, byteorder='big'))
    conn.sendall(filename.encode())
    conn.sendall(filesize.to_bytes(8, byteorder='big'))
    with open(filename, 'rb') as f:
        for data in f:
            conn.sendall(data)


def main():
    host = args.host
    port = args.port

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((host, port))

    cliente.sendall(args.folder.encode())

    root = tk.Tk()
    root.title("Cliente")
    root.geometry("300x200")

    btn_seleccionar_archivos = tk.Button(root, text="Seleccionar archivos",
                                         command=enviar_archivos_seleccionados())
    btn_seleccionar_archivos.pack(pady=20)

    print(archivos_seleccionados)

    for filename in archivos_seleccionados:
        print("Enviando:", filename)
        enviar_archivo(cliente, filename)
        print("Archivo {} enviado exitosamente".format(filename))

    # root.mainloop()

    # archivos_a_enviar = ['LFP Detalle (01042018).csv',
    #                      'LFP Detalle (31102018).csv',
    #                      'LFP Detalle (07012018).csv']

    # for filename in archivos_a_enviar:
    #     print("Enviando:", filename)
    #     enviar_archivo(cliente, filename)
    #     print("Archivo {} enviado exitosamente".format(filename))

    cliente.close()


if __name__ == "__main__":
    main()


# filename = ['LFP Detalle (01042018).csv', 'LFP Detalle (07012018).csv']
