import streamlit as st
import pandas as pd
from Transformations import TransformationRotaReady

# upload csv
st.title('Transforming RotaReady CSV')
uploaded_file = st.sidebar.file_uploader("Choose a file")
expander_original = st.expander("Original CSV")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    # filter only my first name and last name
    if st.checkbox("Filter only my name"):
        df = df[(df["First name"] == "Roberto") & (df["Last name"] == "Scalas")]
    expander_original.write(df)

    df = TransformationRotaReady(df).df
    expander_final = st.expander("Final CSV", expanded=True)
    expander_final.write(df)

    # download the csv
    csv = df.to_csv(index=False)

    # craete a download button
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="rota_ready.csv",
        mime="text/csv"
    )
