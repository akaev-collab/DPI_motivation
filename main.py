import streamlit as st
from st_pages import Page, show_pages, add_page_title


st.set_page_config(page_title="Мотивация ДПИ")

st.title ("Мотивация Департамента проектирования")

add_page_title()
show_pages([Page("dashboard.py", "Дашборд",":book:"),
            Page("test.py", "Калькулятор",":book:")])