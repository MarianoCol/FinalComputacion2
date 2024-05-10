import tkinter as tk
from tkinter import filedialog, simpledialog
import socket
import os
import json
from arguments import argument_definition
import pickle

args = argument_definition()


class ClienteController:
    def __init__(self):
        self.cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.archivos_seleccionados = []

    def arguments_send(self, args):
        arguments = {'folder': args.folder, 'header': args.header,
                     'sep': args.sep, 'encoding': args.encoding}
        args_json = json.dumps(arguments)
        print(args_json)
        self.cliente.sendall(args_json.encode())

    def conectar_servidor(self, args):
        self.cliente.connect((args.host, args.port))
        arguments = {'folder': args.folder, 'header': args.header,
                     'sep': args.sep, 'encoding': args.encoding}
        args_json = json.dumps(arguments)
        print(args_json)
        self.cliente.sendall(args_json.encode())
        # self.cliente.sendall(args.folder.encode())

    def seleccionar_archivos(self):
        self.archivos_seleccionados = list(filedialog.askopenfilenames())
        print("Archivos seleccionados:", self.archivos_seleccionados)
        return self.archivos_seleccionados

    def enviar_archivos(self):
        for filename in self.archivos_seleccionados:
            print("Enviando:", filename)
            self.enviar_archivo(filename)
            print("Archivo {} enviado exitosamente".format(filename))

    def enviar_archivo(self, filename):
        filesize = os.path.getsize(filename)
        # big-endian compatible con TCP/IP
        self.cliente.sendall(len(filename).to_bytes(4, byteorder='big'))
        self.cliente.sendall(filename.encode())
        self.cliente.sendall(filesize.to_bytes(8, byteorder='big'))
        with open(filename, 'rb') as f:
            for data in f:
                self.cliente.sendall(data)

    def enviar_resultados(self, eliminar_nulos, eliminar_duplicados,
                          eliminar_columnas, columnas):
        self.cliente.sendall(len(b'').to_bytes(4, byteorder='big'))
        # Envía los resultados al servidor
        resultados = f"{eliminar_nulos},{eliminar_duplicados},{eliminar_columnas},{columnas}"
        self.cliente.sendall(resultados.encode())
        print("Resultados enviados al servidor:", resultados)

    def eliminar_columnas(self):
        columnas_a_eliminar = simpledialog.askstring("Eliminar columnas", "Ingrese las columnas a eliminar separadas por coma:")
        if columnas_a_eliminar:
            lista = columnas_a_eliminar
            return lista
        else:
            return "NO", ""

    def recibir_dataframes(self):
        self.cliente.sendall(b"DESCARGAR_DATAFRAMES")

        # Recibir el tamaño del dataframe serializado del servidor
        dataframe_size = int.from_bytes(self.cliente.recv(4), byteorder='big')

        # Recibir el dataframe serializado del servidor
        combined_dataframe_serializado = b""
        while len(combined_dataframe_serializado) < dataframe_size:
            data = self.cliente.recv(4096)
            combined_dataframe_serializado += data

        # Deserializar el dataframe combinado
        combined_dataframe = pickle.loads(combined_dataframe_serializado)

        # Guardar el dataframe combinado como un archivo CSV localmente
        combined_dataframe.to_csv("combined_dataframe.csv", index=False)
        print("Dataframes descargados y guardados como 'combined_dataframe.csv'")

# def seleccionar_archivos():
#     archivos_seleccionados = list(filedialog.askopenfilenames())
#     print("Archivos seleccionados:", archivos_seleccionados)
#     return archivos_seleccionados


# def enviar_archivo(conn, filename):
#     filesize = os.path.getsize(filename)
#     conn.sendall(len(filename).to_bytes(4, byteorder='big'))
#     conn.sendall(filename.encode())
#     conn.sendall(filesize.to_bytes(8, byteorder='big'))
#     with open(filename, 'rb') as f:
#         for data in f:
#             conn.sendall(data)


# def enviar_resultados(cliente, eliminar_nulos, eliminar_duplicados, eliminar_columnas, columnas):
#     cliente.sendall(len(b'').to_bytes(4, byteorder='big'))
#     # Envía los resultados al servidor
#     resultados = f"{eliminar_nulos},{eliminar_duplicados},{eliminar_columnas},{columnas}"
#     cliente.sendall(resultados.encode())
#     print("Resultados enviados al servidor:", resultados)


# def eliminar_columnas():
#     columnas_a_eliminar = simpledialog.askstring("Eliminar columnas", "Ingrese las columnas a eliminar separadas por coma:")
#     if columnas_a_eliminar:
#         lista = columnas_a_eliminar
#         return lista
#     else:
#         return "NO", ""


# def recibir_dataframes(cliente):
#     cliente.sendall(b"DESCARGAR_DATAFRAMES")

#     # Recibir el tamaño del dataframe serializado del servidor
#     dataframe_size = int.from_bytes(cliente.recv(4), byteorder='big')

#     # Recibir el dataframe serializado del servidor
#     combined_dataframe_serializado = b""
#     while len(combined_dataframe_serializado) < dataframe_size:
#         data = cliente.recv(4096)
#         combined_dataframe_serializado += data

#     # Deserializar el dataframe combinado
#     combined_dataframe = pickle.loads(combined_dataframe_serializado)

#     # Guardar el dataframe combinado como un archivo CSV localmente
#     combined_dataframe.to_csv("combined_dataframe.csv", index=False)
#     print("Dataframes descargados y guardados como 'combined_dataframe.csv'")


class ClienteView(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.title("Cliente")
        self.geometry("300x400")

        self.controller = controller

        btn_seleccionar_archivos = tk.Button(self,
                                             text="Seleccionar archivos",
                                             command=self.controller.seleccionar_archivos)
        btn_seleccionar_archivos.pack(pady=20)

        archivos_seleccionados = self.controller.seleccionar_archivos()

        print(archivos_seleccionados)

        for filename in archivos_seleccionados:
            print("Enviando:", filename)
            self.controller.enviar_archivo(filename)
            print("Archivo {} enviado exitosamente".format(filename))

        self.eliminar_nulos_var = tk.StringVar(value="NO")
        self.eliminar_duplicados_var = tk.StringVar(value="NO")
        self.eliminar_columnas_var = tk.StringVar(value="NO")

        lbl_eliminar_nulos = tk.Label(self, text="Desea eliminar los duplicados:")
        lbl_eliminar_nulos.pack()
        radio_eliminar_nulos_si = tk.Radiobutton(self, text="SI", variable=self.eliminar_duplicados_var, value="SI")
        radio_eliminar_nulos_si.pack()
        radio_eliminar_nulos_no = tk.Radiobutton(self, text="NO", variable=self.eliminar_duplicados_var, value="NO")
        radio_eliminar_nulos_no.pack()

        lbl_eliminar_duplicados = tk.Label(self, text="Desea eliminar los nulos:")
        lbl_eliminar_duplicados.pack()
        radio_eliminar_duplicados_si = tk.Radiobutton(self, text="SI", variable=self.eliminar_nulos_var, value="SI")
        radio_eliminar_duplicados_si.pack()
        radio_eliminar_duplicados_no = tk.Radiobutton(self, text="NO", variable=self.eliminar_nulos_var, value="NO")
        radio_eliminar_duplicados_no.pack()

        lbl_eliminar_columnas = tk.Label(self, text="Desea eliminar columnas:")
        lbl_eliminar_columnas.pack()
        radio_eliminar_columnas_si = tk.Radiobutton(self, text="SI", variable=self.eliminar_columnas_var, value="SI")
        radio_eliminar_columnas_si.pack()
        radio_eliminar_columnas_no = tk.Radiobutton(self, text="NO", variable=self.eliminar_columnas_var, value="NO")
        radio_eliminar_columnas_no.pack()

        self.btn_enviar_resultados = tk.Button(self, text="Enviar resultados", command=self.enviar_resultados_seleccionados)
        self.btn_enviar_resultados.pack(pady=20)

        self.btn_descargar_dataframes = tk.Button(self, text="Descargar dataframes", command=self.controller.recibir_dataframes)
        self.btn_descargar_dataframes.pack(pady=20)

    def enviar_resultados_seleccionados(self):
        eliminar_nulos = self.eliminar_nulos_var.get()
        eliminar_duplicados = self.eliminar_duplicados_var.get()
        eliminar_columna = self.eliminar_columnas_var.get()
        if eliminar_columna == 'SI':
            columnas = self.controller.eliminar_columnas()
        else:
            columnas = []
        self.controller.enviar_resultados(eliminar_duplicados, eliminar_nulos,
                                          eliminar_columna, columnas)


def main():
    host = args.host
    port = args.port

    # cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # cliente.connect((host, port))

    # cliente.sendall(args.folder.encode())

    controller = ClienteController()
    controller.conectar_servidor(args)
    # controller.arguments_send(args)

    view = ClienteView(controller)
    view.mainloop()

    # root = tk.Tk()
    # root.title("Cliente")
    # root.geometry("300x400")

    # btn_seleccionar_archivos = tk.Button(root, text="Seleccionar archivos", command=seleccionar_archivos)
    # btn_seleccionar_archivos.pack(pady=20)

    # archivos_seleccionados = seleccionar_archivos()

    # print(archivos_seleccionados)

    # for filename in archivos_seleccionados:
    #     print("Enviando:", filename)
    #     enviar_archivo(cliente, filename)
    #     print("Archivo {} enviado exitosamente".format(filename))

    # eliminar_nulos_var = tk.StringVar(value="NO")
    # eliminar_duplicados_var = tk.StringVar(value="NO")
    # eliminar_columnas_var = tk.StringVar(value="NO")

    # lbl_eliminar_nulos = tk.Label(root, text="Desea eliminar los nulos:")
    # lbl_eliminar_nulos.pack()
    # radio_eliminar_nulos_si = tk.Radiobutton(root, text="SI", variable=eliminar_nulos_var, value="SI")
    # radio_eliminar_nulos_si.pack()
    # radio_eliminar_nulos_no = tk.Radiobutton(root, text="NO", variable=eliminar_nulos_var, value="NO")
    # radio_eliminar_nulos_no.pack()

    # lbl_eliminar_duplicados = tk.Label(root, text="Desea eliminar los duplicados:")
    # lbl_eliminar_duplicados.pack()
    # radio_eliminar_duplicados_si = tk.Radiobutton(root, text="SI", variable=eliminar_duplicados_var, value="SI")
    # radio_eliminar_duplicados_si.pack()
    # radio_eliminar_duplicados_no = tk.Radiobutton(root, text="NO", variable=eliminar_duplicados_var, value="NO")
    # radio_eliminar_duplicados_no.pack()

    # lbl_eliminar_columnas = tk.Label(root, text="Desea eliminar columnas:")
    # lbl_eliminar_columnas.pack()
    # radio_eliminar_columnas_si = tk.Radiobutton(root, text="SI", variable=eliminar_columnas_var, value="SI")
    # radio_eliminar_columnas_si.pack()
    # radio_eliminar_columnas_no = tk.Radiobutton(root, text="NO", variable=eliminar_columnas_var, value="NO")
    # radio_eliminar_columnas_no.pack()

    # def enviar_resultados_seleccionados():
    #     eliminar_nulos = eliminar_nulos_var.get()
    #     eliminar_duplicados = eliminar_duplicados_var.get()
    #     eliminar_columna = eliminar_columnas_var.get()
    #     if eliminar_columna == 'SI':
    #         columnas = eliminar_columnas()
    #     else:
    #         columnas = []
    #     enviar_resultados(cliente, eliminar_nulos, eliminar_duplicados, eliminar_columna, columnas)

    # btn_enviar_resultados = tk.Button(root, text="Enviar resultados", command=enviar_resultados_seleccionados)
    # btn_enviar_resultados.pack(pady=20)

    # btn_descargar_dataframes = tk.Button(root, text="Descargar dataframes", command=lambda: recibir_dataframes(cliente))
    # btn_descargar_dataframes.pack(pady=20)

    # root.mainloop()

    # cliente.close()

if __name__ == "__main__":
    main()
