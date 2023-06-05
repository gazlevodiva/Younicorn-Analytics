import streamlit as st
import pandas as pd
import altair as alt

st.title(" Аналитики Younicorn 📈 ")

if True:
    # Чтение данных из файла
    df = pd.read_excel("export.xlsx")

    # Преобразование столбца с датой в тип данных datetime
    df['Date'] = pd.to_datetime(df['Created Date UTC'], errors='coerce')
    df = df.dropna(subset=['Date'])

    min_date = df['Date'].min()
    max_date = df['Date'].max()  
    start_date, end_date = st.date_input('Выберите диапазон дат:', [min_date, max_date])

    # Преобразование дат в datetime64
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Фильтрация данных по диапазону дат
    filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    ###############################################################

    # Кол-во пользователей
    Total_Users = df['Telegram Id'].unique().tolist()
    st.write(f"Кол-во пользователей бота: {len(Total_Users)}")

    Total_Users_Sellers = df[df['Seller Id'] != 0]['Telegram Id'].nunique()
    st.write(f"Кол-во продацов: {Total_Users_Sellers}")    

    # Проверка диапазона дат
    if (end_date - start_date).days < 5:
        filtered_df['Date'] = filtered_df['Date'].dt.floor('H')  # Группировка по часам
    else:
        filtered_df['Date'] = filtered_df['Date'].dt.floor('D')  # Группировка по дням

    # Группировка данных по датам и Telegram ID и подсчет уникальных пользователей
    daily_active_users = filtered_df.groupby(['Date', 'Telegram Id'])['Telegram Id'].nunique().reset_index(name='Count')

    # Группировка данных по датам и подсчет общего количества активных пользователей в день
    daily_active_users_count = daily_active_users.groupby('Date')['Count'].sum().reset_index()

    # Построение линейного графика
    # Создание линейного графика с Altair
    active_chart = (
        alt.Chart(daily_active_users_count)
        .mark_line(color='red')
        .encode(
            x='Date:T',
            y='Count:Q'
        )
        .interactive()
    )

    # Вычисляем дату первого действия каждого пользователя
    df['First Action Date'] = df.groupby('Telegram Id')['Date'].transform('min')

    # Определяем, является ли действие первым действием пользователя
    df['Is New User'] = df['Date'] == df['First Action Date']

    # Группируем данные по датам и подсчет общего количества новых пользователей в день
    daily_new_users = df[df['Is New User']].groupby('Date')['Telegram Id'].nunique().reset_index(name='New Users Count')

    # Проверка диапазона дат
    if (end_date - start_date).days < 5:
        daily_new_users['Date'] = daily_new_users['Date'].dt.floor('H')  # Группировка по часам
    else:
        daily_new_users['Date'] = daily_new_users['Date'].dt.floor('D')  # Группировка по дням

    # Построение линейного графика для новых пользователей
    new_users_chart = (
        alt.Chart(daily_new_users)
        .mark_line(color='blue')
        .encode(
            x='Date:T',
            y='New Users Count:Q'
        )
        .interactive()
    )

    # Объединение двух графиков
    combined_chart = alt.layer(active_chart, new_users_chart)

    # Отображение графика в Streamlit
    st.write("График активных и новых пользователей")
    st.altair_chart(combined_chart, use_container_width=True)

    # Группировка данных по Telegram ID и Seller ID и подсчет количества действий каждого пользователя
    user_activity = filtered_df.groupby(['Telegram Id', 'Seller Id']).size().reset_index(name='Activity Count')

    # Сортировка данных по количеству действий
    user_activity = user_activity.sort_values(by='Activity Count', ascending=False)[:10]

    # Отображение таблицы в Streamlit
    st.write("Таблица самых активных пользователей за указанный период")
    st.table(user_activity)

