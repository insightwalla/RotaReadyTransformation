import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import os
from Transformations import TransformationRotaReady

def combine_dfs(dfs):
    return pd.concat(dfs, ignore_index=True)

st.title('🚀 Transforming Labour Data CSV')

input_folder = st.text_input('Enter input folder path')
output_folder = st.text_input('Enter output folder path') 

if input_folder and output_folder:
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    # Get all CSV files from input folder
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    
    if len(csv_files) > 0:
        for file in csv_files:
            # Read CSV
            df = pd.read_csv(os.path.join(input_folder, file))
            
            # Apply RotaReady transformation
            df_transformed = TransformationRotaReady(df).df

            # Get date range for filename
            df["Start"] = pd.to_datetime(df["Start"], format='mixed', dayfirst=True)
            df = df.sort_values(by=["Start"])
            min_date = df["Start"].min().date()
            max_date = df["Start"].max().date()

            # Save transformed file
            output_filename = f"rota_ready_{min_date}_{max_date}.csv"
            output_path = os.path.join(output_folder, output_filename)
            df_transformed.to_csv(output_path, index=False)
            
            st.success(f"Transformed {file} and saved to {output_filename}")

            # Display sample of transformed data
            expander = st.expander(f"Preview of {file}", expanded=False)
            with expander:
                st.write(df_transformed.head())
                st.write(f"Total rows: {len(df_transformed)}")
    else:
        st.warning("No CSV files found in the input folder")
else:
    st.warning("Please enter both input and output folder paths")
