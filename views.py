from flask import Flask, render_template, request, send_file, redirect, url_for
from concurrent.futures import ThreadPoolExecutor
from data_cleaning import directory_creator, upload_data, clean_data, clean_nulls, drop_columns
import os
from shutil import rmtree
from arguments import argument_definition


app = Flask(__name__)

args = argument_definition()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():

    directory_creator(args.directory, args.folder)

    global cleaned_dataframes

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(upload_data, [f for f in os.listdir(args.directory+'/'+args.folder) if os.path.isfile(os.path.join(args.directory+'/'+args.folder, f))])

    cleaned_dataframes = list(p_res)

    # Renderizar la plantilla con los DataFrames limpios
    return render_template('results.html', dataframes=cleaned_dataframes)


@app.route('/drop_duplicates', methods=['POST'])
def drop_duplicates():

    global cleaned_dataframes

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_data, cleaned_dataframes)

    cleaned_dataframes = list(p_res)

    # Renderizar la plantilla con los DataFrames limpios
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

    # Obtener las columnas a eliminar desde el formulario
    columns_to_drop = request.form.get('columns_to_drop').split(',')

    with ThreadPoolExecutor() as thread:
        # Aplicar la función drop_columns a todos los DataFrames
        p_res = thread.map(lambda df: drop_columns(df, columns_to_drop), cleaned_dataframes)

    cleaned_dataframes = list(p_res)

    # Renderizar la plantilla con los DataFrames después de eliminar columnas
    return render_template('results.html', dataframes=cleaned_dataframes)



@app.route('/download_dataframe/<int:idx>')
def download_dataframe(idx):
    # Verificar que idx sea un índice válido en la lista de DataFrames
    if 0 <= idx < len(cleaned_dataframes):
        # Convertir el DataFrame a un archivo CSV en memoria
        csv_data = cleaned_dataframes[idx].to_csv(index=False).encode('utf-8')
        # Crear un objeto BytesIO para almacenar los datos en memoria
        csv_io = BytesIO(csv_data)
        # Enviar el archivo CSV como respuesta
        return send_file(csv_io, mimetype='text/csv', download_name=f'dataframe_{idx + 1}.csv')
    else:
        return "Índice no válido"

@app.route('/download_all_dataframes')
def download_all_dataframes():
    # Concatenar todos los DataFrames en uno solo
    combined_dataframe = pd.concat(cleaned_dataframes, ignore_index=True)
    # Convertir el DataFrame combinado a un archivo CSV en memoria
    csv_data = combined_dataframe.to_csv(index=False).encode('utf-8')
    # Crear un objeto BytesIO para almacenar los datos en memoria
    csv_io = BytesIO(csv_data)
    # Enviar el archivo CSV como respuesta
    return send_file(csv_io, mimetype='text/csv', download_name='all_dataframes.csv')



@app.route('/clear_dataframes', methods=['POST'])
def clear_dataframes():
    global cleaned_dataframes

    # Eliminar los DataFrames de la lista
    cleaned_dataframes = []

    folder_path = args.directory+'/'+args.folder
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