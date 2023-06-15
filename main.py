import streamlit as st
import pandas as pd
import altair as alt


st.title(" Аналитика Younicorn 📈 ")

if True:
    # Чтение данных из файла
    df = pd.read_excel("export.xlsx")

    # Преобразование столбца с датой в тип данных datetime
    df['Date'] = pd.to_datetime(df['Created Date UTC'], errors='coerce')
    df = df.dropna(subset=['Date'])

    min_date = df['Date'].min()
    max_date = df['Date'].max()  
    start_date, end_date = st.date_input('**Выберите диапазон дат:**', [min_date, max_date])

    # Преобразование дат в datetime64
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Фильтрация данных по диапазону дат
    period_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    # Проверка диапазона дат
    period_df['Date'] = period_df['Date'].dt.floor('H' if (end_date - start_date).days < 5 else 'D')

    #### Users cards metrics ####
    
    col1, col2, col3 = st.columns(3)

    # Total users count
    all_users    = df['Telegram Id'].nunique()
    period_users = period_df['Telegram Id'].nunique()

    col1.metric(
        label = "Пользователи", 
        value = all_users, 
        delta = period_users
    )

    # Total users with seller id
    all_sellers    = df[df['Seller Id'] != 0]['Telegram Id'].nunique()
    period_sellers = period_df[period_df['Seller Id'] != 0]['Telegram Id'].nunique()

    col2.metric(
        label = "Продавцы", 
        value = all_sellers, 
        delta = period_sellers
    ) 

    # Users blocks the bot
    all_blocks = df[df['Action'] == 'stop_bot'].shape[0]
    period_blocks = period_df[period_df['Action'] == 'stop_bot'].shape[0]

    col3.metric(
        label = "Блокировали", 
        value = all_blocks, 
        delta = period_blocks
    ) 

    ###############################################################

    # Группировка данных по датам и Telegram ID и подсчет уникальных пользователей
    daily_active_users = period_df.groupby(['Date', 'Telegram Id'])['Telegram Id'].nunique().reset_index(name='Count')

    # Группировка данных по датам и подсчет общего количества активных пользователей в день
    daily_active_users_count = daily_active_users.groupby('Date')['Count'].sum().reset_index()
    
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
        x='Date:T',
        y='Count:Q',
        color='Category:N',
        tooltip=['Date', 'Count', 'Category']
    ).interactive()

    # Отображение графика в Streamlit
    st.subheader("Активные и новые пользователи")
    st.altair_chart(chart, use_container_width=True)

    ###############################################################
    
    # Группировка данных по Action Type и подсчет количества каждого типа
    action_counts_bar = period_df['Action'].value_counts().reset_index()

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

