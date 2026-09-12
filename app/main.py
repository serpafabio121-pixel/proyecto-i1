import streamlit as st
import home


st.set_page_config(
    page_title="Detector de grietas",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

home.show()
