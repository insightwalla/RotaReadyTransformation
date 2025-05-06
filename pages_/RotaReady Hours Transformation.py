import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from transformations.Transformations import TransformationRotaReady
from transformations.Transformations_Fourth import TransformationFourth, TransformationFourtDOUBLE

def combine_dfs(dfs):
    return pd.concat(dfs, ignore_index=True)

st.title('🚀 Transforming Labour Data CSV')

choice = st.sidebar.radio('Choose an option', ('RotaReady', 'Fourth Single Shifts', 'Fourth Double Shifts'))

uploaded_file = st.sidebar.file_uploader("Choose a file", accept_multiple_files=True)
expander_original = st.expander("📄 Original CSV")

if uploaded_file is not None and uploaded_file != []:
    if len(uploaded_file) > 1:
        df = combine_dfs([pd.read_csv(file) for file in uploaded_file])
    elif len(uploaded_file) == 1:
        df = pd.read_csv(uploaded_file[0])

    if choice == 'Fourth Single Shifts':
        df = TransformationFourth(df).transform()
    elif choice == 'RotaReady':
        df = df
    elif choice == 'Fourth Double Shifts':
        df = TransformationFourtDOUBLE(df).df
        df = TransformationFourth(df).transform()

    # filter only my first name and last name
    names = df["First name"].unique()
    
    choosen_name = st.sidebar.selectbox("Filter by name", names, index = None)
    if choosen_name is not None:
        # filter to keep only my name
        df = df[(df["First name"] == choosen_name)]
        surnames = df["Last name"].unique()
    
    site_to_keep = [
        'Covent Garden',
        'Shoreditch',
        'Kings Cross', 
        'Carnaby',
        'Edinburgh',
        'Kensington',
        'Manchester',
        'Birmingham',
        'Canary Wharf',
        'Battersea',

        'Brighton Permit Room',
        'Cambridge Permit Room',
        'Oxford Permit Room',
        'Portobello Permit Room'
    ]
    
    # Filter df to only include rows with site attribution in site_to_keep
    df = df[df['Site (attribution)'].isin(site_to_keep)]
    
    with expander_original:
        st.write(f"Total rows: **{len(df)}**")
        # Create summary table of event types
        event_type_summary = pd.DataFrame({
            'Event Type': df["Event type"].unique(),
            'Count': [len(df[df["Event type"] == event_type]) for event_type in df["Event type"].unique()]
        })
        # Add total row
        event_type_summary.loc['Total'] = ['Total', event_type_summary['Count'].sum()]
        
        # Create summary table of sites (filtered for shifts only)
        shift_df = df[df["Event type"] == "Shift"]
        site_summary = pd.DataFrame({
            'Site': shift_df["Site (attribution)"].unique(),
            'Count': [len(shift_df[shift_df["Site (attribution)"] == site]) for site in shift_df["Site (attribution)"].unique()]
        })
        # Add total row
        site_summary.loc['Total'] = ['Total', site_summary['Count'].sum()]
        
        c1,c2 = st.columns(2)
        with c1:
            st.dataframe(event_type_summary, use_container_width=True)
        with c2:
            st.dataframe(site_summary, use_container_width=True)
        st.write(df)

    toggle_start = st.toggle("🚀 Start Transformation", value=False)  
    if not toggle_start:
        st.stop()
    if choice == 'Fourth Single Shifts':
        df_transformed = TransformationRotaReady(df).df
    elif choice == 'RotaReady':
        df_transformed = TransformationRotaReady(df).df
    elif choice == 'Fourth Double Shifts':
        # transform start and finish in datetime
        # craete a unique index
        df = df.reset_index()
        df["Start"] = pd.to_datetime(df["Start"], format='mixed', dayfirst=True)
        df["Finish"] = pd.to_datetime(df["Finish"], format='mixed', dayfirst=True)
        # recalculate the duration

        # keep the first 20 columsn
        df = df.iloc[:, :20]

        df_transformed = TransformationRotaReady(df, False).df
        # paid hours is the difference between finish and start
        df_transformed["Paid hours"] = df_transformed["HourEnd"] - df_transformed["HourStart"]
        df_transformed['TotalHours'] = df_transformed['Paid hours']
        st.write(df_transformed)

    expander_final = st.expander("📊 Final CSV", expanded=True)
    with expander_final:
        st.write(f"Total rows: **{len(df_transformed)}**")
        c1,c2 = st.columns(2)
        with c1:
            # add the same check for event types and sites
            event_type_summary = pd.DataFrame({
                'Event Type': df_transformed["Event type"].unique(),
                'Count': [len(df_transformed[df_transformed["Event type"] == event_type]) for event_type in df_transformed["Event type"].unique()]
            })
            st.dataframe(event_type_summary, use_container_width=True) 
        with c2:
            site_summary = pd.DataFrame({
                'Site': df_transformed["Site (attribution)"].unique(),
                'Count': [len(df_transformed[df_transformed["Site (attribution)"] == site]) for site in df_transformed["Site (attribution)"].unique()]
            })
            st.dataframe(site_summary, use_container_width=True)
        st.write(df_transformed)

    # transform start to a datetime object
    df["Start"] = pd.to_datetime(df["Start"], format='mixed', dayfirst=True)
    # sort by start
    df = df.sort_values(by=["Start"])


    # get minimum date
    min_date = df["Start"].min()
    # get maximum date
    max_date = df["Start"].max()

    # make only date
    min_date = min_date.date()
    max_date = max_date.date()

    # download the csv
    csv = df_transformed.to_csv(index=False)

    # craete a download button

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="rota_ready_{}_{}.csv".format(min_date, max_date),
        mime="text/csv"
    )

else:
    st.warning("Please upload a CSV file")
