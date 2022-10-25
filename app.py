from textwrap import indent
import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO

st.set_page_config(layout="wide")

menu = [
            "Singular",
            "Uniform",
            # "Linear",
            "Triangular"
        ]
choice = st.sidebar.selectbox("Menu", menu)
if choice != st.session_state.get('prev_choice'):
    for key in st.session_state.keys():
        if key=='history':
            continue
        del st.session_state[key]

st.subheader(choice)
if st.session_state.get('form') is None:
    st.session_state['form'] = 0
rows = []
if choice == "Singular":
    rows.append("Value")
elif choice == "Uniform":
    rows.append("Left")
    rows.append("Right")
if choice == "Linear":
    rows.append("Left")
    rows.append("Mode")
    rows.append("Right")
elif choice == "Triangular":
    rows.append("Left")
    rows.append("Mode")
    rows.append("Right")
st.session_state['prev_choice'] = choice

with st.form(key='form1'):
    rates = [np.NaN]*len(rows)
    for i in range(len(rows)):
        rates[i] = st.number_input(label = "Enter the interest rate per period: {} (%)".format(rows[i]), key="interest-{}".format(rows[i]), min_value = 0, max_value = 100)
    n = st.number_input(label = "Enter the number of interest periods: ", key="year", min_value=1)
    submit = st.form_submit_button('Confirm')
    rates_df = pd.DataFrame(columns = rows)
    rates_df.loc[len(rates_df), rates_df.columns] = rates
    if not np.isnan(rates).any() and submit :
        st.session_state['data'] = None
        st.session_state['solution'] = None

data = [[np.NaN]*len(rows)]*n
with st.form(key='form2'):
    years = np.arange(n)
    df = pd.DataFrame(data, index = years, columns=rows)
    df.reset_index(inplace=True)
    df = df.rename(columns = {'index':'Year'})
    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_default_column(resizable=False,filterable=False,sorteable=False,editable=True,suppressMovable=True,filter=False)
    builder.configure_column("Year", editable=False)
    builder.configure_grid_options(stopEditingWhenCellsLoseFocus=True)
    gridOptions = builder.build()
    grid_return = AgGrid(df, gridOptions=gridOptions)
    submit_data = st.form_submit_button('Calculate')
    
    solution_df = st.session_state.get('solution')
    if submit_data:
        data = grid_return['data']
        new_df = data.copy()
        new_df.drop(['Year'], axis=1, inplace=True)
        old_df = st.session_state.get('old_data')
        if old_df is None or not old_df.equals(new_df):
            st.session_state['old_data'] = new_df
        if not new_df.isnull().values.any():
            interest = 0
            denominator = 1
            PVs = []
            cycle = 1000
            while cycle:
                cycle -= 1
                AV = 0
                for i in range(n):
                    if choice == "Singular":
                        interest = float(rates[0])
                        rand = float(new_df.iloc[i][0])
                    elif choice == "Uniform":
                        interest = np.random.uniform(float(rates[0]), float(rates[1]))
                        rand = np.random.uniform(float(new_df.iloc[i][0]), float(new_df.iloc[i][1]))
                    elif choice == "Linear":
                        break
                    elif choice == "Triangular":
                        interest = np.random.triangular(float(rates[0]), float(rates[1]), float(rates[2]))
                        rand = np.random.triangular(float(new_df.iloc[i][0]), float(new_df.iloc[i][1]), float(new_df.iloc[i][2]))
                    interest = interest/100.0
                    denominator = 1+interest
                    AV = AV + rand/(denominator**(i+1))
                PVs.append(AV)
            IQR = ['75th', '50th', '25th']
            solution = np.percentile(PVs, [75, 50, 25])
            solution_df = pd.DataFrame(solution, columns = ['Present Value'])
            solution_df.insert(0, "Interquartile", IQR, allow_duplicates=True)
            solution_df.set_index('Interquartile', inplace=True)
            st.session_state['solution'] = solution_df
            st.session_state['new_df'] = new_df

    if solution_df is not None and not solution_df.isnull().values.any():
        st.write(solution_df)
        save = st.form_submit_button('Save')
        if save:
            history = st.session_state.get('history')
            if history is None:
                history = pd.DataFrame(columns = ["Rate", "Input", "75th", "50th","25th"])
            history.loc[len(history), history.columns] = rates_df, st.session_state.get('new_df'), solution_df.iloc[0,0], solution_df.iloc[1,0], solution_df.iloc[2,0]
            st.session_state['history'] = history

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=True, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data
history = st.session_state.get('history')
i = 0
if history is not None:
    st.write("History")
    rate, ip, op, delete = st.columns(4)
    with rate:
        st.write("Rate of interest")
    with ip:
        st.write("Input")
    with op:
        st.write("Output")
    with delete:
        delete_all = st.button('Clear All')
        if delete_all:
            history = None
            st.session_state['history'] = history
            st.experimental_rerun()
    for idx in history.index:
        roi, ip, op, delete = st.columns(4)
        rate = history.loc[idx][0]
        input = history.loc[idx][1]
        output = history.loc[idx][2:]
        with roi:
            st.write(rate)
        with ip:
            st.write(input)
        with op:
            st.write(output)
        with delete:
            clear = st.button('Clear',key='Clear-{}'.format(i))
            i+=1
            if clear:
                history.drop(idx,axis=0,inplace=True)
                if(len(history)==0):
                    history = None
                st.session_state['history'] = history
                st.experimental_rerun()
    df_xlsx = to_excel(history)
    st.download_button(label='📥 Export', data=df_xlsx, file_name='History.xlsx')