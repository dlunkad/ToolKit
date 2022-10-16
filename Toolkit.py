from re import sub
import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide")

menu = ["Singular","Uniform","Linear","Triangular"]
choice = st.sidebar.selectbox("Menu", menu)
st.subheader(choice)
if st.session_state.get('form') is None:
    st.session_state['form'] = 0
rows = []
if choice == menu[0]:
    rows.append("Value")
if choice == menu[1]:
    rows.append("Left")
    rows.append("Right")
if choice == menu[2]:
    rows.append("Left")
    rows.append("Mode")
    rows.append("Right")
if choice == menu[1]:
    rows.append("Left")
    rows.append("Right")
if choice == menu[2]:
    rows.append("Left")
    rows.append("Mode")
    rows.append("Right")
with st.form(key='form1'):
    interest = st.number_input(label = "Enter the interest rate per period: ", key="interest", min_value = 0, max_value = 100)
    n = st.number_input(label = "Enter the number of interest periods: ", key="year", min_value=1)
    submit = st.form_submit_button('Confirm')
if submit:
    st.session_state['form'] = 1

if st.session_state['form'] == 1:
    data = [[np.NaN]*len(rows)]*n
    with st.form(key='form2'):
        years = np.arange(1,n+1)
        df = pd.DataFrame(data, index = years, columns=rows)
        df.reset_index(inplace=True)
        df = df.rename(columns = {'index':'Year'})
        builder = GridOptionsBuilder.from_dataframe(df)
        builder.configure_default_column(resizable=False,filterable=False,sorteable=False,editable=True,suppressMovable=True,filter=False)
        builder.configure_column("Year", editable=False)
        # builder.configure_first_column_as_index()
        go = builder.build()
        grid_return = AgGrid(df, gridOptions=go)
        submit_data = st.form_submit_button('Calculate')
        if submit_data:
            st.session_state['data'] = grid_return['data']
            st.session_state['form'] = 2
if st.session_state['form'] == 2:
    st.session_state['form'] = 1
    data = st.session_state.get('data')
    new_df = data.copy()
    new_df.drop(['Year'], axis=1, inplace=True)
    interest = interest/100.0
    denominator = 1+interest
    PVs = []
    cycle = 1000
    while cycle:
        cycle -= 1
        AV = 0
        for i in range(n):
            if choice==menu[0]:
                rand = float(new_df.iloc[i][0])
            elif choice==menu[1]:
                rand = np.random.uniform(float(new_df.iloc[i][0]), float(new_df.iloc[i][1]))
            elif choice==menu[2]:
                rand = np.random.triangular(float(new_df.iloc[i][0]), float(new_df.iloc[i][1]), float(new_df.iloc[i][2]))
            AV = AV + rand/(denominator**(i+1))
        PVs.append(AV)
    IQR = ['75th', '50th', '25th']
    solution = np.percentile(PVs, [75, 50, 25])
    solution_df = pd.DataFrame(solution, columns = ['Present Value'])
    solution_df.insert(0, "Interquartile", IQR, allow_duplicates=True)
    solution_df.set_index('Interquartile', inplace=True)
    if not solution_df.isnull().values.any():
        st.write(solution_df)

