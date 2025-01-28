import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import os
from transformations.Transformations_RR_optimised import TransformationRotaReady as transformation_rr_1
from transformations.Transformations import TransformationRotaReady as transformation_rr_2

def combine_dfs(dfs):
    return pd.concat(dfs, ignore_index=True)

st.title('🚀 Transforming Labour Data CSV')
option_transformation = st.radio('Select Transformation', ['New Version', 'Original Version'], horizontal=True)     
transformation = transformation_rr_1 if option_transformation == 'New Version' else transformation_rr_2

if option_transformation == 'New Version':
    st.info('This is the **New Version** of the RotaReady transformation')
elif option_transformation == 'Original Version':
    st.info('This is the **Original Version** of the RotaReady transformation')

input_folder = st.text_input('Enter input folder path')

if input_folder:
    # Get all CSV files from input folder
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')][:3]
    
    if len(csv_files) > 0:
        # Show files in a table
        files_df = pd.DataFrame(csv_files, columns=['Files to Process'])
        st.write("Files found in input folder:")
        st.dataframe(files_df, use_container_width=True)
        
        c1,c2 = st.columns(2)
        output_folder = c1.text_input('Enter output folder path')
        
        # Add confirmation button
        if output_folder and st.checkbox("✅ Proceed"):
            # Create output folder if it doesn't exist
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                
            # Create progress bar
            progress_bar = st.progress(0)
            total_files = len(csv_files)
            
            for idx, file in enumerate(csv_files):
                # Create expander for each file transformation
                with st.expander(f"Transforming {file}", expanded=True):
                    # Update progress bar
                    progress = (idx + 1) / total_files
                    progress_bar.progress(progress)
                    
                    # Read CSV
                    st.write("Reading CSV file...")
                    df = pd.read_csv(os.path.join(input_folder, file))
                    
                    # Apply RotaReady transformation
                    st.write("Applying RotaReady transformation...")
                    df_transformed = transformation(df).df

                    # Get date range for filename
                    st.write("Processing dates...")
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
                    st.write("Preview of transformed data:")
                    st.write(df_transformed.head())
                    st.write(f"Total rows: {len(df_transformed)}")
    else:
        st.warning("No CSV files found in the input folder")
else:
    st.warning("Please enter input folder path")
