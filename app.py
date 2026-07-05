
import streamlit as st
import pandas as pd

st.title("Sales Performance Dashboard")

data = pd.DataFrame({
    "Month":["Jan","Feb","Mar","Apr","May"],
    "Sales":[1200,1500,1800,1700,2200]
})

st.dataframe(data)
st.line_chart(data.set_index("Month"))
st.metric("Total Sales", int(data["Sales"].sum()))
