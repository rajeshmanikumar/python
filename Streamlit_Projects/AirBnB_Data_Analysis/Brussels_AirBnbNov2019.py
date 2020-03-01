import streamlit as st
import pandas as pd
import numpy as np

st.title('Brussels AirBnB Nov 2019 Data Analysis')

#http://data.insideairbnb.com/belgium/bru/brussels/2019-11-19/visualisations/listings.csv
#DATA_URL = 'D:\\Learnings\\DataSets\\brussels_listing_Nov2019.csv'
DATA_URL = 'brussels_listing_Nov2019.csv'

# Cache for Data
@st.cache
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    return data

# Load limited data
data_load_state = st.text('Loading data...')
data = load_data(10000)
data_load_state.text('Loading data... done!')

st.subheader('Few Sample Data')
st.write(data[['host_name','name','room_type','price']].head())


# Filter by Price using Slider
# Some number in the range 0-200
price_to_filter = st.slider('Price in €', 0, 200, 30)
filtered_data = data[data['price'] == price_to_filter]

# Display Map on limited data
st.subheader('Map of all Properties at %s € [EUR]' % price_to_filter)
st.map(filtered_data)

# Take distinct locality names
neighbourhood_list = data.neighbourhood.unique()
#st.write(city_list)

# Filter by locality Names using MultiSelect
selected_localities = st.multiselect('Neighbourhood / Locality', neighbourhood_list.tolist(), default='Anderlecht')
loc_filtered_data = data[data['neighbourhood'].isin(selected_localities)]

locality_names = ','.join(selected_localities)
st.subheader('Map of all Properties in Selected Locality %s' % locality_names)
# Display Map on limited data
st.map(loc_filtered_data)
