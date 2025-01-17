import sys
import json
import requests
import csv
import pandas as pd
import time
from prophet import Prophet
import plotly

PROMETHEUS_URL = "http://ENTER_PROMETHEUS_ADDRESS_HERE/api/v1/query_range"

# Сбор данных с прометея
def fetch_prometheus_data(query, start_time, end_time, step):
    params = {
        'query': query,
        'start': start_time,
        'end': end_time,
        'step': step
    }
    response = requests.get(PROMETHEUS_URL, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from Prometheus: {response.status_code}")
        return None

# Прогноз с помощью Prophet (https://facebook.github.io/prophet/)
def forecast_with_prophet(df, period):
    m = Prophet(growth='logistic')
    m.fit(df)

    future = m.make_future_dataframe(periods=period*24, freq='H')
    future['cap'] = 100 # максимальное значение прогноза
    future['floor'] = 0 # минимальное значение прогноза
    future.tail()

    forecast = m.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    

def main(post_variables):
    
    period = 30
    hosts = post_variables['hosts'] # значение подставляется из POST-запроса, принятого сервером
    period = int(post_variables['period']) # значение подставляется из POST-запроса, принятого сервером

    
    end_time = int(time.time())  # Текущее время, используется как конечная точка сбора данных из прометея
    start_time = end_time - (period * 24 * 60 * 60)  # Начальная точка, с которой нужно начать сбор данных из прометея
    step = '1h'  # Частота сбора данных, задана почасовая (условно - для сбора данных за последние сутки будет собрано 24 значения метрики)

    # Запросы к прометею по диску, ЦПУ и РАМ
    query_disk = f'100 - ((avg_over_time(node_filesystem_avail_bytes{{instance="{hosts}",mountpoint="/",fstype!="rootfs"}}[1h]) * 100) / avg_over_time(node_filesystem_size_bytes{{instance="{hosts}",mountpoint="/",fstype!="rootfs"}}[1h]))'
    query_cpu = f'(sum by(instance) (irate(node_cpu_seconds_total{{instance="{hosts}", mode!="idle"}}[1h])) / on(instance) group_left sum by (instance)((irate(node_cpu_seconds_total{{instance="{hosts}",}}[1h])))) * 100'
    query_ram = f'100 - ((avg_over_time(node_memory_MemAvailable_bytes{{instance="{hosts}"}}[1h]) * 100) / avg_over_time(node_memory_MemTotal_bytes{{instance="{hosts}"}}[1h]))'
    # Вызов функции для диска
    prometheus_data_disk = fetch_prometheus_data(query_disk, start_time, end_time, step)
    # Форматирование данных для дальнейшего использования в Prophet
    if 'data' in prometheus_data_disk and 'result' in prometheus_data_disk['data'] and len(prometheus_data_disk['data']['result']) > 0:
        time_series_disk = [
            (point[0], point[1]) for point in prometheus_data_disk['data']['result'][0]['values']
        ]
    df_disk = pd.DataFrame(time_series_disk, columns=['ds', 'y'])
    df_disk['ds'] = pd.to_datetime(df_disk['ds'], unit='s')
    df_disk['y'] = df_disk['y'].astype(float)
    df_disk['cap'] = 100 # максимальное значение прогноза
    df_disk['floor'] = 0 # минимальное значение прогноза
    df_disk.head()
    # Вызов функции прогноза на основе созданного датафрейма и запись в CSV
    forecast_disk = forecast_with_prophet(df_disk, period)
    forecast_disk.to_csv('/csv/forecasted_disk_data.csv')
    
    # Аналогичные шаги для ЦПУ
    prometheus_data_cpu = fetch_prometheus_data(query_cpu, start_time, end_time, step)
    if 'data' in prometheus_data_cpu and 'result' in prometheus_data_cpu['data'] and len(prometheus_data_cpu['data']['result']) > 0:
        time_series_cpu = [
            (point[0], point[1]) for point in prometheus_data_cpu['data']['result'][0]['values']
        ]
    df_cpu = pd.DataFrame(time_series_cpu, columns=['ds', 'y'])
    df_cpu['ds'] = pd.to_datetime(df_cpu['ds'], unit='s')
    df_cpu['y'] = df_cpu['y'].astype(float)
    df_cpu['cap'] = 100 # максимальное значение прогноза
    df_cpu['floor'] = 0 # минимальное значение прогноза
    df_cpu.head()
    # Вызов функции прогноза на основе созданного датафрейма и запись в CSV
    forecast_cpu = forecast_with_prophet(df_cpu, period)
    forecast_cpu.to_csv('/csv/forecasted_cpu_data.csv')
    
    #Аналогичные шаги для РАМ
    prometheus_data_ram = fetch_prometheus_data(query_ram, start_time, end_time, step)
    if 'data' in prometheus_data_ram and 'result' in prometheus_data_ram['data'] and len(prometheus_data_ram['data']['result']) > 0:
        time_series_ram = [
            (point[0], point[1]) for point in prometheus_data_ram['data']['result'][0]['values']
        ]
    df_ram = pd.DataFrame(time_series_ram, columns=['ds', 'y'])
    df_ram['ds'] = pd.to_datetime(df_ram['ds'], unit='s')
    df_ram['y'] = df_ram['y'].astype(float)
    df_ram['cap'] = 100 # максимальное значение прогноза
    df_ram['floor'] = 0 # минимальное значение прогноза
    df_ram.head()
    # Вызов функции прогноза на основе созданного датафрейма и запись в CSV
    forecast_ram = forecast_with_prophet(df_ram, period)
    forecast_ram.to_csv('/csv/forecasted_ram_data.csv')
if __name__ == "__main__":
    main()