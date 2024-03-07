from typing import List
import uuid
import os
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from concurrent.futures import ThreadPoolExecutor
from data_cleaning import directory_creator, upload_data, clean_data, clean_nulls, drop_columns
from os import rmdir
from arguments import argument_definition
import pandas as pd
from io import BytesIO

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="prueba_secret_key")

args = argument_definition()

cleaned_dataframes = {}

templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/upload')
async def upload(request: Request, folder_name: str = Form(...), files: List[UploadFile] = File(...)):

    directory_path = await directory_creator(args.directory, folder_name)
    global cleaned_dataframes

    file_id = str(uuid.uuid4())

    file_paths = []
    for file in files:
        # Asegurarnos de que el nombre del archivo sea correcto
        safe_filename = "".join(c for c in file.filename if c.isalnum() or
                                c in (' ', '.', '_')).rstrip()
        filename = os.path.join(directory_path, safe_filename)

        with open(filename, 'wb') as out_file:
            content = await file.read()  # async read
            out_file.write(content)
        file_paths.append(filename)

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(upload_data, file_paths)

    cleaned_dataframes[file_id] = list(p_res)

    request.session['file_identifier'] = file_id
    request.session['folder_name'] = folder_name

    return RedirectResponse(url='/results', status_code=303)


@app.get('/results')
async def show_results(request: Request):

    global cleaned_dataframes

    results = cleaned_dataframes[request.session.get('file_identifier')]

    return templates.TemplateResponse("results.html", {
        "request": request, "dataframes": results})


@app.route('/drop_duplicates', methods=['POST'])
def drop_duplicates(request: Request):

    global cleaned_dataframes

    file_id = request.session.get('file_identifier')

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_data, cleaned_dataframes[file_id])

    cleaned_dataframes[file_id] = list(p_res)

    return templates.TemplateResponse("results.html", {
        "request": request, "dataframes": cleaned_dataframes[file_id]})


@app.route('/drop_nulls', methods=['POST'])
def drop_nulls(request: Request):

    global cleaned_dataframes

    file_id = request.session.get('file_identifier')

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(clean_nulls, cleaned_dataframes[file_id])

    cleaned_dataframes[file_id] = list(p_res)

    return templates.TemplateResponse("results.html", {
        "request": request, "dataframes": cleaned_dataframes[file_id]})


@app.post('/drop_column')
async def drop_column(request: Request, columns_to_drop: str = Form(...)):
    global cleaned_dataframes

    file_id = request.session.get('file_identifier')

    columns_to_drop_list = [column.strip() for column in columns_to_drop.split(',')]

    with ThreadPoolExecutor() as thread:
        p_res = thread.map(lambda df: drop_columns(df, columns_to_drop_list),
                           cleaned_dataframes[file_id])

    cleaned_dataframes[file_id] = list(p_res)

    return templates.TemplateResponse("results.html", {
        "request": request,
        "dataframes": cleaned_dataframes[file_id]
    })


@app.get('/download_dataframe/{idx}')
async def download_dataframe(request: Request, idx: int):
    file_id = request.session.get('file_identifier')
    if 0 <= idx < len(cleaned_dataframes[file_id]):
        csv_data = cleaned_dataframes[file_id][idx].to_csv(index=False).encode('utf-8')
        csv_io = BytesIO(csv_data)
        csv_io.seek(0)
        return StreamingResponse(csv_io, media_type="text/csv",
                                 headers={"Content-Disposition":
                                          f"attachment;filename=dataframe_{idx+1}.csv"})
    else:
        return ("Índice no válido")


@app.get('/download_all_dataframes')
async def download_all_dataframes(request: Request):
    file_id = request.session.get('file_identifier')
    combined_dataframe = pd.concat(cleaned_dataframes[file_id], ignore_index=True)
    csv_data = combined_dataframe.to_csv(index=False).encode('utf-8')
    # Guarda el csv en memoria
    csv_io = BytesIO(csv_data)
    # Pone el puntero al inicio del archivo
    csv_io.seek(0)
    return StreamingResponse(csv_io, media_type="text/csv",
                             headers={"Content-Disposition":
                                      "attachment;filename=full_dataframe.csv"})


@app.route('/clear_dataframes', methods=['POST'])
def clear_dataframes(request: Request):
    global cleaned_dataframes

    file_id = request.session.get('file_identifier')
    folder_name = request.session.get('folder_name')

    cleaned_dataframes[file_id] = []

    directory_path = os.path.join(args.directory, folder_name)
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

    rmdir(directory_path)

    request.session.pop(file_id, None)
    request.session.pop(folder_name, None)

    return templates.TemplateResponse('index.html', {'request': request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
