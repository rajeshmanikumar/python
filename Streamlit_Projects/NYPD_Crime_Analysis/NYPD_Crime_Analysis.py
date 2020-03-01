import streamlit as st
import pandas as pd
import numpy as np

st.title('NYPD Complaint Data History 2018')

DATA_URL = 'NYPD_Complaint_Data_Historic.csv'

# Cache for Data
@st.cache
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    data['CMPLNT_FR_TM'] = pd.to_datetime(data['CMPLNT_FR_TM'])
    # Rename Columns
    data = data.rename(columns={"CMPLNT_NUM": "ComplaintNumber", "BORO_NM": "City_Name"})
    return data

# Load limited data
data_load_state = st.text('Loading data...')
data = load_data(10000)
data_load_state.text('Loading data... done!')

st.subheader('Few Sample Data')
st.write(data[['ComplaintNumber','City_Name']].head())

# Filter by Hours using Slider
# Some number in the range 0-23
hour_to_filter = st.slider('Hour', 0, 23, 17)
filtered_data = data[data['CMPLNT_FR_TM'].dt.hour == hour_to_filter]

# Display Map on limited data
st.subheader('Map of all Crimes at %s:00' % hour_to_filter)
st.map(filtered_data)

# Take distinct City names
city_list = data.City_Name.unique()
#st.write(city_list)

# Filter by City Names using MultiSelect
st_ms = st.multiselect('City', city_list.tolist(), default='BROOKLYN')
city_filtered_data = data[data['City_Name'].isin(st_ms)]

city_names = ','.join(st_ms)
st.subheader('Map of all Crimes in Cities %s' % city_names)
# Display Map on limited data
st.map(city_filtered_data)