import streamlit as st
import pandas as pd
import base64

class Transform:
    '''
    We need to keep
    review_id	created_at_local	venue_name	payment_id	platform	rating	comment	table_number	paid_amount	order_amount	currency_code	staff_name	rating_dimension_food_and_drinks	rating_dimension_ambiance	rating_dimension_service	rating_dimension_value_for_money
    '''
    def __init__(self, df):
        self.df = df.copy()

    def transformation_1(self):
        columns_to_keep = [
            'review_id',
            'created_at_local',
            'venue_name',
            'payment_id',
            'platform',
            'rating',
            'comment',
            'table_number',
            'paid_amount',
            'order_amount',
            'currency_code',
            'staff_name',
            'rating_dimension_food_and_drinks',
            'rating_dimension_ambiance',
            'rating_dimension_service',
            'rating_dimension_value_for_money'
        ]
        # Only keep columns if they are present
        missing_cols = [c for c in columns_to_keep if c not in self.df.columns]
        if missing_cols:
            st.warning(f"Missing columns: {missing_cols} - they will be filled with blanks.")
            for col in missing_cols:
                self.df[col] = ""
        self.df = self.df[columns_to_keep]
        return self

    def transformation_2(self):
        # the created_at_local need to go from this 2025-09-29 23:56:47.383 to this September 29, 2025, 11:56 PM
        self.df['created_at_local'] = pd.to_datetime(self.df['created_at_local'], format='mixed', dayfirst=True)
        self.df['created_at_local'] = self.df['created_at_local'].dt.strftime('%B %d, %Y, %I:%M %p')
        return self


    def get_result(self):
        return self.df

    def get_table_download_link(self):
        # Convert 'created_at_local' back to datetime since it is currently a formatted string
        min_date = pd.to_datetime(self.df['created_at_local'], errors='coerce').min()
        max_date = pd.to_datetime(self.df['created_at_local'], errors='coerce').max()
        # as ddmmyy 
        min_date = min_date.strftime('%d%m%y')
        max_date = max_date.strftime('%d%m%y')
        name = f"sunday_export_{min_date}_{max_date}.csv"
        csv = self.df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
        href = f'<a href="data:file/csv;base64,{b64}" download="{name}">Download final results as CSV</a>'
        return href

st.title("Sunday Preprocess: CSV Upload & Transform")

uploaded_file = st.file_uploader("Choose a CSV file to process 👇", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    with st.expander("View Original Data"):
        st.write(df)

    transformer = Transform(df)
    # Apply transformation(s)
    transformer.transformation_1()
    transformer.transformation_2()
    result_df = transformer.get_result()

    with st.expander("View Transformed Data"):
        st.write(result_df)

    st.markdown(transformer.get_table_download_link(), unsafe_allow_html=True)
