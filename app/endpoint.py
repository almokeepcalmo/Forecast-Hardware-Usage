from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sys
import traceback
import plotly
import forecast_node

app = FastAPI()
data_storage = {}

class DataModel(BaseModel):
    hosts: str
    period: int

# Без middleware сервер отклоняет POST-запросы от графаны.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI GET endpoint!"}

# По этому пути отправляется POST-запрос из графаны
@app.post("/forecast/")
def post_data(data: DataModel):
    data_storage["latest_data"] = data.dict()  # Сохранение переменных из POST-запроса
    # print (data_storage)
    return forecast_node.main(data_storage["latest_data"]) # Вызов скрипта с переменными

# По этим путям графана делает GET-запросы для получения данных
@app.get("/forecast/disk/")
def get_data():
    return FileResponse("/csv/forecasted_disk_data.csv")

@app.get("/forecast/cpu/")
def get_data():
    return FileResponse("/csv/forecasted_cpu_data.csv")

@app.get("/forecast/ram/")
def get_data():
    return FileResponse("/csv/forecasted_ram_data.csv")