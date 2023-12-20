import pandas as pd
import streamlit as st
import json
import altair as alt
import datetime as dt

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
    df_load_plan = df_load_group.groupby([df_load_group["Дата"].dt.strftime("%Y-%m-1")]).aggregate({"План":"sum"}).reset_index()
    df_load_fact = df_load_group.groupby([df_load_group["Дата"].dt.strftime("%Y-%m-1")]).aggregate({"Факт":"sum"}).reset_index()

    bar_load_plan = alt.Chart(df_load_plan).mark_bar(width=22, xOffset=-10, color="grey").encode(
        alt.X("Дата:T", axis=alt.Axis(format="%m.%Y")),
        y = "План", 
        tooltip=["Дата:T", "План"]
    ).properties(width=chart_width, height=chart_height)

    bar_load_fact = alt.Chart(df_load_fact, title = "Динамика выдачи комплектов").mark_bar(width=22, xOffset=10, color = "#007FFF").encode(
        alt.X("Дата:T"),
        y = "Факт",
        tooltip=["Дата:T", "Факт"]
    ).properties(width=chart_width, height=chart_height)

    df_load_fact_total = df_load_group.groupby(["Мастерская", "Статус по выдаче"], as_index=False).aggregate({"Факт":"sum"})

    bar_load_fact_total = alt.Chart(df_load_fact_total, title = "Статус по выданым комплектам").mark_bar().encode(
        alt.X("Факт", title=""),
        alt.Y("Мастерская", title=""),
        color = "Статус по выдаче"
    ).properties(width=chart_width, height=chart_height)
    st.altair_chart(bar_load_plan + bar_load_fact)
    st.altair_chart(bar_load_fact_total)
    
with tabel_2:
    st.header("Качество документации")
    
    df_izm_group = df_izm_group[df_izm_group["Мастерская"].isin(filter_selected_master)]
    df_izm_group = df_izm_group.round({"% ИЗМ":2})

    chart_izm = alt.Chart(df_izm_group).mark_line(width=18).encode(
        alt.X("Дата"),
        alt.Y("% ИЗМ"),
        color="Мастерская"
    ).properties(width=800, height=400)

    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['Дата'], empty='none')

    selectors = alt.Chart(df_izm_group).mark_point().encode(
        x='Дата',
        opacity=alt.value(0),
    ).add_selection(nearest)

    points = chart_izm.mark_point(size=70).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = chart_izm.mark_text(align='left', dx=25, dy=-25).encode(
    text=alt.condition(nearest, '% ИЗМ:Q', alt.value(' ')))
        
    rules = alt.Chart().mark_rule(color='gray').encode(
    x='Дата:T',
    ).transform_filter(
    nearest
    )

    st.altair_chart((chart_izm + selectors + points + text + rules).interactive())

with tabel_3:
    st.header("Продуктивность мастерских")
    
    df_productivity_group = df_productivity_group[df_productivity_group["Мастерская"].isin(filter_selected_master)]

    df_productivity_plan = df_productivity_group.groupby([df_productivity_group["Дата"].dt.strftime("%Y-%m-1")]).aggregate({"План":"sum"}).reset_index().round({"План":2})

    df_productivity_fact = df_productivity_group.groupby([df_productivity_group["Дата"].dt.strftime("%Y-%m-1")]).aggregate({"Факт":"sum"}).reset_index().round({"Факт":2})

    bar_productivity_plan = alt.Chart(df_productivity_plan).mark_bar(width=22, xOffset=-10, color="grey").encode(
        alt.X("Дата:T", axis=alt.Axis(format="%m.%Y")),
        y = "План", 
        tooltip=["Дата:T", "План"]
    ).properties(width=chart_width, height=chart_height)

    bar_productivity_fact = alt.Chart(df_productivity_fact).mark_bar(width=22, xOffset=10, color = "#007FFF").encode(
        alt.X("Дата:T"),
        y = "Факт",
        tooltip=["Дата:T", "Факт"]
    ).properties(width=chart_width, height=chart_height)

    st.altair_chart(bar_productivity_plan + bar_productivity_fact)
