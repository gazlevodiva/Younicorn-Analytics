from methods import get_data
from methods import getUniqActiveUsersPerDay

import streamlit as st
import pandas as pd
import altair as alt
import requests
import datetime



st.title("Аналитика Younicorn 📈")

# Get data from logs
df = get_data()

# Get min & max date from data
min_date = df['Date'].min()
max_date = df['Date'].max()

# Вычисляем дату начала последней недели
start_week_date = max_date - datetime.timedelta(days=10)

# Получение диапазона дат от пользователя
start_date, end_date = st.date_input('**Выберите диапазон дат:**', [start_week_date, max_date])

# Преобразование дат в datetime64
start_date = pd.to_datetime(start_date)
end_date   = pd.to_datetime(end_date)

# Фильтрация данных по диапазону дат
period_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# Проверка диапазона дат
period_df.loc[:, 'Date'] = period_df['Date'].dt.floor('H' if (end_date - start_date).days <= 5 else 'D')

# Метрики для пользователей
# Total users count
all_users    = df['Telegram Id'].nunique()
period_users = period_df['Telegram Id'].nunique()

# Total users with seller id
all_sellers    = df[df['Seller Id'] != 0]['Telegram Id'].nunique()
period_sellers = period_df[period_df['Seller Id'] != 0]['Telegram Id'].nunique()

# Users blocks the bot
all_blocks    = df[df['Action'] == 'stop_bot'].shape[0]
period_blocks = period_df[period_df['Action'] == 'stop_bot'].shape[0]

all_tasks_done    = df[df['Action'] == 'task_stage_5_quiz'].shape[0]
period_tasks_done = period_df[period_df['Action'] == 'task_stage_5_quiz'].shape[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Пользователи",
    value=all_users,
    delta=period_users
)
col2.metric(
    label="Продавцы",
    value=all_sellers,
    delta=period_sellers
)
col3.metric(
    label="Блокировали",
    value=all_blocks,
    delta=period_blocks
)
col4.metric(
    label="Выполненные задания",
    value=all_tasks_done,
    delta=period_tasks_done
)


daily_active_users_count = getUniqActiveUsersPerDay( period_df )
    
# Получение списка уникальных пользователей
unique_users = df['Telegram Id'].unique()

# Создание словаря для сохранения даты первого действия каждого пользователя
first_action_dates = {}

# Итерация по каждому уникальному пользователю
for user in unique_users:
    # Выбор всех строк для данного пользователя
    user_rows = df[df['Telegram Id'] == user]
        
    # Выбор даты первого действия пользователя
    first_action_date = user_rows['Date'].min()
        
    # Добавление даты первого действия пользователя в словарь
    first_action_dates[user] = first_action_date

# Создание списка всех дат или часов в выбранном диапазоне дат
all_dates = pd.date_range(start=start_date, end=end_date, freq='D') if (end_date - start_date).days >= 5 else pd.date_range(start=start_date, end=end_date, freq='H')

# Создание DataFrame для полного набора данных
full_data = pd.DataFrame(all_dates, columns=['Date'])

# Инициализация количества активных и новых пользователей нулями
full_data['Active Users'] = 0
full_data['New Users'] = 0

# Получаем только даты из словаря
first_action_dates_only_date = {k: v.date() for k, v in first_action_dates.items() if pd.notnull(v)}

# Если разница между конечной и начальной датой меньше 5 дней, то преобразовываем дату в формат 'datetime'
# Иначе - в 'date'
if (end_date - start_date).days < 5:
    for i in range(len(full_data)):
        datetime = full_data.loc[i, 'Date']
        if datetime in daily_active_users_count['Date'].values:
            full_data.loc[i, 'Active Users'] = daily_active_users_count[daily_active_users_count['Date'] == datetime]['Count'].values[0]
        full_data.loc[i, 'New Users'] = list(first_action_dates.values()).count(datetime)
else:
    for i in range(len(full_data)):
        date = full_data.loc[i, 'Date'].date()
        if date in daily_active_users_count['Date'].dt.date.values:
            full_data.loc[i, 'Active Users'] = daily_active_users_count[daily_active_users_count['Date'].dt.date == date]['Count'].values[0]
        full_data.loc[i, 'New Users'] = list(first_action_dates_only_date.values()).count(date)


# Переводим данные в "long" формат для корректного отображения легенды
full_data_long = full_data.melt('Date', var_name='Category', value_name='Count')

# Построение линейного графика
chart = alt.Chart(full_data_long).mark_line().encode(
    x       = 'Date:T',
    y       = 'Count:Q',
    color   = 'Category:N',
    tooltip = ['Date', 'Count', 'Category']
).interactive()

# Отображение графика в Streamlit
st.subheader("Активные и новые пользователи")
st.altair_chart(chart, use_container_width=True)

###############################################################
    
# Группировка данных по Action Type и подсчет количества каждого типа
action_counts_bar = (
    period_df['Action']
    .value_counts()
    .reset_index()
)

# Переименование столбцов для лучшего понимания
action_counts_bar.columns = ['Action', 'Count']

# Построение столбчатого графика для визуализации количества каждого типа действия
action_chart = (
    alt.Chart(action_counts_bar)
    .mark_bar()
    .encode(
        x='Count',
        y=alt.Y('Action:N', sort='-x'),
        tooltip=['Action', 'Count']
    )
    .interactive()
)

# Отображение графика в Streamlit
st.subheader("Распределение действий пользователей")
st.altair_chart(action_chart, use_container_width=True)

###############################################################

# Определение функции для обработки данных каждого пользователя
def process_user_data(df):
    user_data_df = df.groupby('Telegram Id').agg({'Date': ['min', 'max'], 'Action': 'count'}).reset_index()
    user_data_df.columns = ['Telegram Id', 'First Action', 'Last Action', 'Actions count']

    user_task_stage_5_quiz = df[df['Action'] == 'task_stage_5_quiz'].groupby('Telegram Id').size().reset_index()
    user_task_stage_5_quiz.columns = ['Telegram Id', 'Complete tasks']

    user_data_df = pd.merge(user_data_df, user_task_stage_5_quiz, on='Telegram Id', how='left')
    user_data_df['Telegram Id'] = user_data_df['Telegram Id'].astype(str).replace(',', '', regex=True)

    
    for chat_id in user_data_df['Telegram Id'].astype(str):
        # получение данных о пользователе от Telegram API
        bot_token = st.secrets["bot_token"] # ваш токен
        url = f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={chat_id}"
        json_data = requests.get(url, allow_redirects=True).json()

        user_data = json_data['result'] if json_data['result']['id'] == int(chat_id) else None

        if user_data is not None:
            
            user_data_df.loc[user_data_df['Telegram Id'] == str(chat_id), 'First Name'] = user_data.get('first_name', '')
            user_data_df.loc[user_data_df['Telegram Id'] == str(chat_id), 'Last Name']  = user_data.get('last_name', '')
            user_data_df.loc[user_data_df['Telegram Id'] == str(chat_id), 'Username']   = user_data.get('username', '')

    return user_data_df

# Подготовка и обработка данных для продавцов
sellers_df = df[df['Seller Id'] != 0]
sellers_data = process_user_data(sellers_df)

# Подготовка и обработка данных для не-продавцов
non_sellers_df = df[df['Seller Id'] == 0]
non_sellers_data = process_user_data(non_sellers_df)

st.write(f"Таблица продацов:")
st.write(sellers_data)

st.write(f"Таблица не-продавцов:")
st.write(non_sellers_data)
