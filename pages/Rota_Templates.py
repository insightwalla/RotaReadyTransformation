# Imports
import streamlit as st
st.set_page_config(page_title="Rota Templates", page_icon=":bar_chart:", layout="wide")
import pandas as pd
from datetime import datetime
import time 

       
class TransformationTemplates: 
    def __init__(self, templates):
        self.templates = templates

    def cleanup(self):
        #remove all the rows with 0 in Hours Column
        for i in range(len(self.templates)):
            self.templates[i] = self.templates[i][self.templates[i]['Hours'] != 0]
            # remove column Unnamed: 0
            self.templates[i] = self.templates[i].drop(columns=['Unnamed: 0'], errors='ignore')
        return self.templates

def handle_single_file(file):
    file_name = file.name
    cafe = file_name.split('-')[1].split('_')[0]
    df_A = pd.read_excel(file, sheet_name='24_A')
    df_B = pd.read_excel(file, sheet_name='24_B')
    df_C = pd.read_excel(file, sheet_name='24_C')
    df_D = pd.read_excel(file, sheet_name='24_D')
    df_E = pd.read_excel(file, sheet_name='24_E')
    df_F = pd.read_excel(file, sheet_name='24_F')
    df_rota_lookup = pd.read_excel(file, sheet_name='2024RotaLookup')
    df_rota_lookup = df_rota_lookup.T
    df_rota_lookup = df_rota_lookup.drop(columns=[1,3], errors='ignore')
    df_rota_lookup = df_rota_lookup.reset_index()
    df_rota_lookup.columns = df_rota_lookup.iloc[0]
    df_rota_lookup = df_rota_lookup.drop(0)
    tt = TransformationTemplates([df_A, df_B, df_C, df_D, df_E, df_F])
    df_A, df_B, df_C, df_D, df_E, df_F = tt.cleanup()
    df_A['Rota'] = 'A'
    df_B['Rota'] = 'B'
    df_C['Rota'] = 'C'
    df_D['Rota'] = 'D'
    df_E['Rota'] = 'E'
    df_F['Rota'] = 'F'
    return cafe, df_A, df_B, df_C, df_D, df_E, df_F, df_rota_lookup

def _init_session_state():
    if 'final_df_whole' not in st.session_state:
        st.session_state.final_df_whole = pd.DataFrame(columns=[
            'Cafe', 'Week', 'Dow', 'Time_Interval', 
            'Time_Interval_15_min', 'Department', 
            'Rota_24', 'RotaQuarterHours'])
        
    if 'df_whole' not in st.session_state:
        st.session_state.df_whole = pd.DataFrame(columns=[
            'Cafe', 'Week', 'Dow', 'Time_Interval', 
            'Time_Interval_15_min', 'Department', 
            'Rota_24', 'RotaQuarterHours'])

    if 'df_filtered' not in st.session_state:
        st.session_state.df_filtered = pd.DataFrame(columns=[
            'Cafe', 'Week', 'Dow', 'Time_Interval', 
            'Time_Interval_15_min', 'Department', 
            'Rota_24', 'RotaQuarterHours'])
    
def show_templates(df_A, df_B, df_C, df_D, df_E, df_F, df_rota_lookup):
    all_df_comb = pd.concat([df_A, df_B, df_C, df_D, df_E, df_F], axis=0)
    list_of_df = [all_df_comb, df_A, df_B, df_C, df_D, df_E, df_F, df_rota_lookup]
    expanders = ['All', 'Rota A', 'Rota B', 'Rota C', 'Rota D', 'Rota E', 'Rota F', '2024RotaLookup']
    for i, df in enumerate(list_of_df):
        if 'Hours' in df.columns:
            with st.expander(f"{expanders[i]} / Total Hours: {df['Hours'].sum()}"):
                st.dataframe(df)
        else: 
            with st.expander(f"{expanders[i]}"):
                st.dataframe(df)

def get_uniques(df_final : pd.DataFrame):
    unique_departments = df_final['Department'].unique()
    unique_departments = [dep.split('&') for dep in unique_departments] 
    unique_departments = [item.strip() for sublist in unique_departments for item in sublist]
    unique_departments = list(set(unique_departments))
    return unique_departments

def get_15_min_intervals():
    fifteen_minutes = ['00', '15', '30', '45']
    hours = list(range(0, 24))
    hours = [h for h in hours if h not in [2,3,4]]
    # houers need to be 00 to 23
    hours = [f'{h:02d}' for h in hours]
    index_5 = hours.index('05')
    hours = hours[index_5:] +hours[:index_5]

    fifteen_minutes_intervals = [f'{h}:{f}:00' for h in hours for f in fifteen_minutes]
    fifteen_minutes_intervals.append('02:00:00')
    fifteen_minutes_intervals = [datetime.strptime(interval, '%H:%M:%S').time() for interval in fifteen_minutes_intervals]
    return fifteen_minutes_intervals

def get_weeks_and_dow():
    weeks = list(range(1, 53))
    dows = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return weeks, dows

_init_session_state()

# App Logic
uploaded_file = st.sidebar.file_uploader("Choose a file", accept_multiple_files=True, type = ['csv', 'xlsx'])
empty_space = st.empty()

# create a dictionary of all the files uploaded
file_dict = {}
if len(uploaded_file) > 0:
    for file in uploaded_file:
        file_dict[file.name] = file

selected_cafe = st.selectbox("Select Cafe", list(file_dict.keys()))
if st.checkbox("Process"):
    file = file_dict[selected_cafe]
    cafe, df_A, df_B, df_C, df_D, df_E, df_F, df_rota_lookup = handle_single_file(file)
    df_final = pd.concat([df_A, df_B, df_C, df_D, df_E, df_F], axis=0)

    show_templates(df_A, df_B, df_C, df_D, df_E, df_F, df_rota_lookup)

    unique_departments = get_uniques(df_final)
    weeks, dows = get_weeks_and_dow()
    fifteen_minutes_intervals = get_15_min_intervals()
    rota_letters = [ df_rota_lookup[df_rota_lookup['Week'] == i]['2024 Final Rota'].values[0] for i in range(1, 53)]
    
    individual_cafe_final_transforamtion = pd.DataFrame(columns=['Cafe', 'Week', 'Dow', 'Time_Interval', 'Time_Interval_15_min', 'Department', 'Rota_24', 'RotaQuarterHours'])
    
    start_time = time.time() 
    empty = st.empty()

    data = []
    start_time = time.time()
    for week in weeks:
        empty_space.info(f"Processing Week {week}/{weeks[-1]}")
        
        
        for division in unique_departments:
            for day in dows:
                rota_template = df_final[(df_final['Rota'] == rota_letters[week-1]) & 
                                        (df_final['Department'] == division) & 
                                        (df_final['Day'] == day)]
                
                for interval in fifteen_minutes_intervals:
                    entry = {
                        'Cafe': cafe,
                        'Week': week,
                        'Dow': day,
                        'Time_Interval': int(str(interval).split(':')[0]),
                        'Time_Interval_15_min': interval,
                        'Department': division,
                        'Rota_24': rota_letters[week-1],
                        'RotaQuarterHours': rota_template[interval].sum()
                    }
                    data.append(entry)

    st.divider()

    st.session_state[f'df_{cafe}'] = pd.DataFrame(data) 
    if week == weeks[-1]:
            empty_space.success(f"Tranformation Completed : Time Taken: {time.time() - start_time}")
    with st.container(border=True):
        with st.expander('Final Data Transformed'):
            st.dataframe(st.session_state[f'df_{cafe}'], use_container_width=True)

            # add download button 
            st.download_button(
                label="Download Data",
                data=st.session_state[f'df_{cafe}'].to_csv(index=False),
                file_name=f"{cafe}_Rota_Transformation.csv",
                mime="text/csv"
            )

        st.divider()
        st.subheader('Checks')
        # No create a dataframe grouped by Week and Sum Quarter Hours but first transform the data into float
        df_grouped = st.session_state[f'df_{cafe}'].copy()
        df_grouped['RotaQuarterHours'] = df_grouped['RotaQuarterHours'].astype(float)
        # Group By Week, Sum Quarter Hours and Keep Rota Letter 
        df_grouped = df_grouped.groupby(['Week', 'Rota_24'])['RotaQuarterHours'].sum().reset_index()
        df_grouped['Hours'] = df_grouped['RotaQuarterHours'] / 4
        st.dataframe(df_grouped, use_container_width=True)
        st.write(f"Total Hours for {cafe} is {df_grouped['Hours'].sum() * 4}")
        st.divider()    

        # add the same but with departemnts as wel

        df_grouped_department_Week_rota_letter = st.session_state[f'df_{cafe}'].copy()
        df_grouped_department_Week_rota_letter['RotaQuarterHours'] = df_grouped_department_Week_rota_letter['RotaQuarterHours'].astype(float)
        df_grouped_department_Week_rota_letter = df_grouped_department_Week_rota_letter.groupby(['Week', 'Rota_24', 'Department'])['RotaQuarterHours'].sum().reset_index()
        df_grouped_department_Week_rota_letter['Hours'] = df_grouped_department_Week_rota_letter['RotaQuarterHours'] / 4
        st.dataframe(df_grouped_department_Week_rota_letter, use_container_width=True)
