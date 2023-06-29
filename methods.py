import requests
import pandas as pd
from io import BytesIO


def get_data():

    url = "https://zom.info/LogsAll/ExportLogs"
    response = requests.get(url)

    # Убедимся, что запрос прошел успешно
    response.raise_for_status()

    # Загружаем данные из файла Excel в DataFrame
    df = pd.read_excel(BytesIO(response.content))

    # Преобразование столбца с датой в тип данных datetime
    df['Date'] = pd.to_datetime(df['Created Date UTC'], errors='coerce')
    df = df.dropna(subset=['Date'])

    # Удаляем тестовых продацов
    sellers_to_remove = [72689, 72688, 306075, 55555]
    df = df[~df['Seller Id'].isin(sellers_to_remove)]

    return df

def getSellers():
    pass

def getNotSellers():
    pass

def getUniqActiveUsersPerDay( df ):
    # Группировка данных по датам и Telegram ID и подсчет уникальных пользователей
    daily_active_users = (
        df.groupby(['Date', 'Telegram Id'])['Telegram Id']
        .nunique()
        .reset_index(name='Count')
    )

    # Группировка данных по датам и подсчет общего количества активных пользователей в день
    return (
        daily_active_users.groupby('Date')['Count']
        .sum()
        .reset_index()
    )