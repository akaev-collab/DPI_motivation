import streamlit as st
import json
import datetime as dt
from dateutil import relativedelta
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")


# Загрузка данных 

@st.cache_data
def load_data():
    
    file_name = "data_file/data.xlsx"

    df_load = pd.read_excel(file_name, sheet_name="P_RD")
    df_load["Срок выдачи (факт)"] = df_load["Срок выдачи (факт)"].apply(pd.to_datetime, format = "%Y-%m-%d")


    df_izm = pd.read_excel(file_name, sheet_name="IZM")
    df_izm["Дата изменения (факт)"] = df_izm["Дата изменения (факт)"].apply(pd.to_datetime, format = "%Y-%m-%d")

    df_productivity = pd.read_excel(file_name, sheet_name="Productivity_group")
    df_productivity["Дата"] = df_productivity["Дата"].apply(pd.to_datetime, format = "%Y-%m-%d")
    
    return df_load, df_izm, df_productivity

df_load,  df_izm, df_productivity = load_data()

# Загрузка структуры департамента ДПИ

path_to_json = "Structure"

with open (path_to_json +"\greid_level.json", "r", encoding='utf-8') as file: 
    greid_level = json.load(file) # зависимость процента премии от грейда

with open (path_to_json +"\position.json", "r", encoding='utf-8') as file:
    position = json.load(file) # завимимости должности от управления

with open (path_to_json +"\structure.json", "r", encoding='utf-8') as file:
    structure = json.load(file) # зависимость мастерской и группу от управления

# Статус выдаче комплетов

def load_status(data_frame, master_filter, group_filter, start_period, end_period):
    
    load_df = data_frame[(data_frame["Мастерская"] == master_filter) & (data_frame["Группа"] == group_filter) & \
                   ((data_frame["Срок выдачи (факт)"] >= pd.to_datetime(str(start_period))) & (data_frame["Срок выдачи (факт)"] <= pd.to_datetime(str(end_period))))]
    
    load_df = load_df.groupby("Статус по выдаче", as_index = False).aggregate({"Кол-во комплектов (факт)":"sum"})
    
    time_load      = load_df[load_df["Статус по выдаче"] == "в срок"]["Кол-во комплектов (факт)"].sum()
    time_less_load = load_df[load_df["Статус по выдаче"] == "с задержкой (<14 дней)"]["Кол-во комплектов (факт)"].sum()
    time_more_load = load_df[load_df["Статус по выдаче"] == "с задержкой (>14 дней)"]["Кол-во комплектов (факт)"].sum()
    
    percent_load = (time_load / (load_df["Кол-во комплектов (факт)"].sum()))
    

    if len(load_df) == 0:
        percent_load = 0
    else:
        if time_more_load != 0 or percent_load < 0.8:
            prize_to_load = 0
        elif percent_load >= 0.8 and percent_load < 1:
            prize_to_load = percent_load
        elif percent_load == 1:
            prize_to_load = 0.35

    return prize_to_load

# Качество документации

def izm_status(data_frame, master_filter, group_filter, start_period, end_period):

    df_izm = data_frame[(data_frame["Мастерская"] == master_filter) & (data_frame["Группа\Виновник"] == group_filter) &\
                ((data_frame["Дата изменения (факт)"] >= pd.to_datetime(str(start_period))) & (data_frame["Дата изменения (факт)"] <= pd.to_datetime(str(end_period))))]
    if len(df_izm) != 0:
        df_izm = df_izm.groupby(["Мастерская", "Группа\Виновник"], as_index = False).aggregate({"Общее кол-во листов по разделам ":"sum", "Кол-во листов по разделам":"sum"})

        df_izm["% ИЗМ"] =  (df_izm["Кол-во листов по разделам"] / df_izm["Общее кол-во листов по разделам "])*100


        if len(df_izm) == 0:
            percent_izm = 0
        else:
            percent_izm = df_izm["% ИЗМ"].sum()
            if percent_izm == 0:
                prize_to_izm = 1.2
            elif percent_izm > 0 and percent_izm <= 3:
                prize_to_izm = 1
            else: 
                prize_to_izm = 0
    else:
        prize_to_izm = 0
    
    return prize_to_izm

# Выработка

def productivity_status(data_frame, master_filter, group_filter, start_period, end_period):
    
    df_productivity = data_frame[(data_frame["Мастерская"] == master_filter) & (data_frame["Группа"] == group_filter) & \
                                  ((data_frame["Дата"] >= pd.to_datetime(str(start_period))) & (data_frame["Дата"] <= pd.to_datetime(str(end_period))))]

    productivity_plan = df_productivity["План"].sum()
    productivity_fact = df_productivity["Факт"].sum()
    percent_productivity = (productivity_fact / productivity_plan)

    if len(df_productivity) == 0:
        prize_to_productivity = 0
    else:
        if percent_productivity < 0.7:
            prize_to_productivity = 0
        elif percent_productivity >= 0.7 and percent_productivity <= 1.2:
            prize_to_productivity = percent_productivity
        elif percent_productivity > 1.2:
            prize_to_productivity = 1.2

    return prize_to_productivity


# Настройка виджетов

def setting_set(number_of_periods):
        
        
        total_salary = []
        total_prize_for_period = []
        total_bonus = []

        for i in range(number_of_periods):
            st.markdown(f"## {i + 1}-й период")

            columns_1, columns_2 = st.columns(2)

            with columns_1:
                departament_select = st.selectbox(f"Укажите департамент на {i + 1}-м периоде", position.keys()) # фильтр по управлению
            with columns_2:
                master_select = st.selectbox(f"Укажите мастерскую на {i+1}-м периоде", structure[departament_select])

            columns_3, columns_4, columns_5 = st.columns(3)

            with columns_3:
                group_select = st.selectbox(f"Укажите группу на {i + 1}-м периоде", structure[departament_select][master_select])
            with columns_4:
                position_select = st.selectbox(f"Выберите должность на {i + 1}-м периоде", position[departament_select])
            with columns_5:
                greid = st.selectbox(f"Выберите ваш грейд на {i + 1}-м периоде", greid_level.keys())

            columns_6, columns_7, columns_8 = st.columns(3)

            with columns_6:
                start_period = st.date_input(f"Укажите дату начала работы на должности для {i + 1}-го периода", dt.datetime(2023,1,1), format="DD.MM.YYYY")
            with columns_7:
                end_period = st.date_input(f"Укажите дату окончания работы на должности для {i + 1}-го периода", dt.datetime.today(), format="DD.MM.YYYY")
            with columns_8:
                salary = st.number_input(f"Укажите размер заработной платы для {i + 1}-го периода:", value=0, placeholder="Зарплата в рублях")
            
            total_salary.append(salary)

            delta = relativedelta.relativedelta(end_period, start_period)
            delta_s = str(delta.months) + " / " + str(delta.days)

            salary_for_period = salary * delta.months + (salary/30) * delta.days
            prize_for_period = (salary_for_period * greid_level[greid])
            
            total_prize_for_period.append(prize_for_period)
            
            
            prize_to_load = load_status(df_load, master_select, group_select, start_period, end_period)
            prize_to_izm = izm_status(df_izm, master_select, group_select, start_period, end_period)
            prize_to_productivity = productivity_status(df_productivity, master_select, group_select, start_period, end_period)

            bonus = prize_for_period*prize_to_load*0.35 + prize_for_period*prize_to_izm*0.35 + prize_for_period*prize_to_productivity*0.2
            total_bonus.append(bonus)

            
            metric_1, metric_2, metric_3, metric_4 = st.columns(4)

            with metric_1:
                st.metric(label="Отработано месяцев / дней", value=delta_s)
            with metric_2:
                st.metric(label="Заработная плата за период", value = round(salary_for_period))
            with metric_3:
                st.metric(label="Размер целевой премии", value = round(prize_for_period))
            with metric_4:
                st.metric(label="Премия с учетом выполнения показателей", value = round(bonus))


            st.markdown("---")
        
        
            st.text(master_select)
            st.text(group_select)

            col1, col2, col3 = st.columns(3)
            

            with col1:
                st.text(load_status(df_load, master_select, group_select, start_period, end_period))
            with col2:
                st.text(izm_status(df_izm, master_select, group_select, start_period, end_period))
            with col3:
                st.text(productivity_status(df_productivity, master_select, group_select, start_period, end_period))
            
            


        st.markdown("## Общие показатели")
        st.markdown("---")

        metric_5, metric_6, metric_7 = st.columns(3)

        with metric_5:
            st.metric(label = "Итого заработная плата", value = np.sum(total_salary))
        with metric_6:
            st.metric(label = "Итого целевая премия", value = round(np.sum(total_prize_for_period)))
        with metric_7:
            st.metric(label = "Итого премия с учетом выполнения показателей", value = round(np.sum(total_bonus)))

transfer_on = st.selectbox("Укажите был ли перевод за отчетный период", ("Переводов не было","Был перевод"))

if transfer_on == "Переводов не было":

    setting_set(1)

else:
    number_of_periods = st.number_input('Укажите колличество переводов', min_value=0, max_value=5, value=0)

    setting_set(number_of_periods)