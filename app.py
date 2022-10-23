from re import sub
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
    interest = st.number_input(label = "Enter the interest rate per period: ", key="interest", min_value = 0, max_value = 100)
    n = st.number_input(label = "Enter the number of interest periods: ", key="year", min_value=1)
    submit = st.form_submit_button('Confirm')
    if submit:
        st.session_state['data'] = None
        st.session_state['history'] = None

data = [[np.NaN]*len(rows)]*n
with st.form(key='form2'):
    years = np.arange(1,n+1)
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
            st.session_state['history'] = None
        if not new_df.isnull().values.any():
            interest = interest/100.0
            denominator = 1+interest
            PVs = []
            cycle = 1000
            while cycle:
                cycle -= 1
                AV = 0
                for i in range(n):
                    if choice == "Singular":
                        rand = float(new_df.iloc[i][0])
                    elif choice == "Uniform":
                        rand = np.random.uniform(float(new_df.iloc[i][0]), float(new_df.iloc[i][1]))
                    elif choice == "Linear":
                        break
                    elif choice == "Triangular":
                        rand = np.random.triangular(float(new_df.iloc[i][0]), float(new_df.iloc[i][1]), float(new_df.iloc[i][2]))
                    AV = AV + rand/(denominator**(i+1))
                PVs.append(AV)
            IQR = ['75th', '50th', '25th']
            solution = np.percentile(PVs, [75, 50, 25])
            solution_df = pd.DataFrame(solution, columns = ['Present Value'])
            solution_df.insert(0, "Interquartile", IQR, allow_duplicates=True)
            solution_df.set_index('Interquartile', inplace=True)
            st.session_state['solution'] = solution_df

            history = st.session_state.get('history')
            if history is None:
                history = pd.DataFrame(columns = ["75th", "50th","25th"])
            history.loc[len(history), history.columns] = solution[0], solution[1], solution[2]
            st.session_state['history'] = history

    if solution_df is not None and not solution_df.isnull().values.any():
        st.write(solution_df)

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=True, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data
history = st.session_state.get('history')
if history is not None:
    st.write("History")
    st.write(history)
    df_xlsx = to_excel(history)
    st.download_button(label='📥 Export', data=df_xlsx, file_name='History.xlsx')        