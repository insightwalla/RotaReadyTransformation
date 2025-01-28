import streamlit as st

pg = st.navigation([
    st.Page("pages_/RotaReady Hours Transformation.py", title="Rota Ready Hours Transformation", icon="⏰"),
    st.Page("pages_/Rota_Templates_2024.py", title="Rota Ready Template 2024", icon="📅"), 
    st.Page("pages_/Rota_Templates_2025.py", title="Rota Ready Template 2025", icon="🗓️"),
])
pg.run()
