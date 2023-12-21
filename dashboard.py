import pandas as pd
import streamlit as st
import json
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Дашборд")


def load_data():
    
    file_name = "data_file/data.xlsx"
    
    df_load_group = pd.read_excel(file_name, sheet_name="P_RD_group")
    df_load_group["Дата"] = df_load_group["Дата"].apply(pd.to_datetime, format = "%Y-%m-%d")
    
    df_izm_group = pd.read_excel(file_name, sheet_name="IZM_group")
    df_izm_group["Дата"] = df_izm_group["Дата"].apply(pd.to_datetime)
    
    df_productivity_group = pd.read_excel(file_name, sheet_name="Productivity_group")
    df_productivity_group["Дата"] = df_productivity_group["Дата"].apply(pd.to_datetime)

    return df_load_group, df_izm_group, df_productivity_group

df_load_group, df_izm_group, df_productivity_group = load_data()

path_to_json = "Structure/structure.json"

with open (path_to_json, "r", encoding='utf-8') as file:
    structure = json.load(file)

d = []
master_merge_dict = {}
for i in structure.keys():
    d.append(structure[i])

for i in d:
    for key, value in i.items():
        master_merge_dict[key] = value
        
filter_selected_master = st.multiselect("Мастерская", master_merge_dict.keys(), master_merge_dict.keys())

chart_width = 1500
chart_height = 400

tabel_1, tabel_2, tabel_3 = st.tabs(["Готовность", "Качество", "Выработка"])

with tabel_1:
    st.header("Готовность документации")
    
    df_load_group = df_load_group[df_load_group["Мастерская"].isin(filter_selected_master)]

    line_data = df_load_group.groupby(["Мастерская", "Статус по выдаче", df_load_group["Дата"].dt.strftime("%Y-%m-1")]).aggregate({"План":"sum", "Факт":"sum"}).reset_index()

    chart_line = line_data.groupby("Дата").aggregate({"План":"sum", "Факт":"sum"}).reset_index()
    chart_master_status = line_data.groupby(["Дата", "Мастерская"]).aggregate({"План":"sum", "Факт":"sum"}).reset_index()
    chart_status = line_data.groupby(["Дата", "Статус по выдаче"]).aggregate({"План":"sum", "Факт":"sum"}).reset_index()

    figure_line = go.Figure()

    figure_line.add_trace(go.Scatter(x = chart_line["Дата"], 
                                     y = chart_line["Факт"], 
                                     name = "Факт", 
                                     mode = "lines + markers", 
                                     marker_color = "#007FFF"))
    
    
    figure_line.add_trace(go.Scatter(x = chart_line["Дата"], 
                                     y = chart_line["План"], 
                                     name = "План", 
                                     mode = "lines + markers", 
                                     marker_color = "grey"))

    figure_line.update_layout(
                    title = "Статус по выдаче комплектов",
                    width=1500,
                    height=500,
                    xaxis_title='Месяц',
                    yaxis_title='Значение', 
                    legend_orientation="h",
                    legend=dict(x=.5, xanchor="center"),
                    margin=dict(l=0, r=0, t=0, b=0))



    figure_master = px.bar(chart_status, 
                           x = "Дата", 
                           y = "Факт", 
                           color="Статус по выдаче",
                           title="Статус по выдаче комплектов")
    
    figure_status = px.bar(chart_master_status, 
                           x = "Дата", 
                           y = "Факт", 
                           color="Мастерская",
                           title = "Статус по выдаче комплектов по мастерским")

    st.plotly_chart(figure_line)

    chart_3, chart_4  = st.columns(2)

    with chart_3:
        st.plotly_chart(figure_master)
    with chart_4:
        st.plotly_chart(figure_status)
    

with tabel_2:
    st.header("Качество документации")
    
    df_izm_group = df_izm_group[df_izm_group["Мастерская"].isin(filter_selected_master)]

    figure_izm_status = px.bar(df_izm_group,
                               x = "Дата",
                               y = "% ИЗМ",
                               color = "Мастерская",
                               width=1500,
                               height=500)
    
    st.plotly_chart(figure_izm_status)

with tabel_3:
    st.header("Продуктивность мастерских")
    
    df_productivity_group = df_productivity_group[df_productivity_group["Мастерская"].isin(filter_selected_master)]

    productivity_data = df_productivity_group.groupby([df_productivity_group["Дата"].dt.strftime("%Y-%m-1")]).aggregate({"План":"sum","Факт":"sum"}).reset_index().round({"План":2})

    
    figure_productivity_line = go.Figure()
    
    figure_productivity_line.add_trace(go.Scatter(x = productivity_data["Дата"], 
                                     y = productivity_data["Факт"], 
                                     name = "Факт",
                                     marker_color = "#007FFF"))
    
    
    figure_productivity_line.add_trace(go.Scatter(x = productivity_data["Дата"], 
                                     y = productivity_data["План"], 
                                     name = "План",  
                                     marker_color = "grey"))
    
    figure_productivity_line.update_layout(
                    title = "Выработка",
                    width=1500,
                    height=500,
                    xaxis_title='Месяц',
                    yaxis_title='Значение', 
                    legend_orientation="h",
                    legend=dict(x=.5, xanchor="center"),
                    margin=dict(l=0, r=0, t=0, b=0))


    st.plotly_chart(figure_productivity_line)