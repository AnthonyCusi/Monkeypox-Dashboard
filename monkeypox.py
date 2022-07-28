from itertools import count
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
import altair as alt
from streamlit_option_menu import option_menu
import pydeck as pdk
import geopandas


# Acknowledgements:
# cases data: https://www.cdc.gov/poxvirus/monkeypox/response/2022/world-map.html

# -- CHANGES TO MAKE -- #
# check box to 'include suspected cases' which uses the 'Status' column in data



# ---------- Setting Up Webpage ---------- #
st.set_page_config(page_title = 'Monkeypox Visualization', page_icon = ':bar_chart:', layout = 'wide')

# Hide hamburger menu
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Reduce padding above nav bar
st.write('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# Navigation bar
selected = option_menu(None, ['Home', 'Maps', 'Resources', 'Sources'], 
    icons=['bar-chart-line', 'geo-alt', 'clipboard-check', 'info-circle'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles = {'nav-link': {'--hover-color': '#8E6FF9'}}
)


# ---------- Loading Data --------- #
# Saves cleaned data in cache to prevent reloading it every page refresh
@st.cache
def load_full_data():
    df = pd.read_csv('https://raw.githubusercontent.com/globaldothealth/monkeypox/main/latest.csv')

    df.drop(['Source', 'Source_II', 'Source_III', 'Source_IV', 'Source_V', 'Source_VI', 'Source_VII',
        'ID', 'Contact_ID', 'Contact_comment', 'Date_last_modified'], axis = 1, inplace = True)
    df = df[(df['Status'] == 'confirmed') | (df['Status'] == 'suspected')]

    return df

@st.cache
def load_cumulative_cases():
    df = pd.read_csv('https://raw.githubusercontent.com/globaldothealth/monkeypox/main/timeseries-country-confirmed.csv')
    
    # Formatting information for readability
    df.rename(columns = {'Cumulative_cases': 'Cumulative Cases'}, inplace = True)
    return df

# Initializing dataframes 
full_df = load_full_data() # Detailed data for each case
cum_df = load_cumulative_cases() # Cumulative case data for each country

# Gets date data was last updated
date_df = pd.to_datetime(cum_df['Date'])
date_df = date_df.sort_values(ascending = False)
last_updated = list(date_df.dt.strftime('%b %d, %Y').head())[0]

# Dataframe with countries and their current cases
country_counts = full_df['Country'].value_counts().to_frame()


# ---------- Sidebar ---------- #
# Logo
st.sidebar.image('content/Monkeypox_Dashboard.png')
st.sidebar.write('')
st.sidebar.write('')

# Filters
st.sidebar.header('Data Filters')
countries = st.sidebar.multiselect('Country Selection', 
    options = list(cum_df['Country'].unique()),
    default = ['United States', 'Germany', 'Spain', 'United Kingdom']
)

st.sidebar.write('test  \nhi')





# ---------- Home Page ---------- #
if selected == '"Home"' or selected == 'Home':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases')
    st.write(f'Data last updated {last_updated}.')
    st.write('') 

    # Gets data for user-selected countries
    selection_df = cum_df[cum_df['Country'].isin(countries)]

    # Line chart
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['Date'], empty='none')

    line_chart = alt.Chart(selection_df).mark_line(interpolate = 'basis').encode(
        x = alt.X('Date', axis = alt.Axis(tickCount = 5)),
        y = 'Cumulative Cases',
        color = 'Country'
    )

    selectors = alt.Chart(selection_df).mark_point().encode(
        x='Date',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    points = line_chart.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    text = line_chart.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'Cumulative Cases', alt.value(' '))
    )

    rules = alt.Chart(selection_df).mark_rule(color='gray').encode(
        x='Date',
    ).transform_filter(
        nearest
    )

    line_chart = alt.layer(
        line_chart, selectors, points, rules, text
    ).properties(
        width=600, height=300
    ).configure_axisX(labelAngle = 90).interactive()

    st.write('## Cumulative Confirmed Cases')
    st.altair_chart(line_chart, use_container_width=True)

    country_counts_dict = country_counts['Country'].to_dict()
    if 'Democratic Republic Of The Congo' in country_counts_dict:
        country_counts_dict['Dem. Rep. Congo'] = country_counts_dict['Democratic Republic Of The Congo']
        country_counts_dict.pop('Democratic Republic Of The Congo')
    country_counts_dict = sorted(country_counts_dict.items(), key = lambda x: x[1], reverse = True)
    

    names, values = [], []
    for country, cases in country_counts_dict:
        names.append(country)
        values.append(cases)
        

    col1, col2 = st.columns(2)
    # Cumulative cases table
    with col1:
        st.write('## Cumulative Cases by Country')
        st.write('#### Scroll the list to see more')
        counts_data = {'Country Name                    ': names, 'Cases  ': values}
        counts_df = pd.DataFrame.from_dict(counts_data)
        counts_df.index += 1
        st.write(counts_df)

    # Pie chart
    with col2:
        other_slice = sum([val for val in values[9:]])
        names = names[:9]
        values = values[:9]
        names.append('Other')
        values.append(other_slice)

        fig1, ax1 = plt.subplots()
        ax1.pie(values, labels = names, autopct='%1.1f%%',
                 shadow=True, startangle=90)

        # Setting background color
        ax1.set_facecolor('#99c2ff')
        
        st.write('## Breakdown of Global Cases')
        st.pyplot(fig1)


# ---------- Maps Page ---------- #
if selected == '"Maps"' or selected == 'Maps':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases')
    st.write(f'Data last updated {last_updated}.')
    st.write("") 

    map_df = geopandas.read_file('land_data/ne_50m_admin_0_countries.shp')
    map_df = map_df[['NAME', 'geometry']]
    st.set_option('deprecation.showPyplotGlobalUse', False)

    # Removing Antarctica from map
    map_df.drop([map_df.index[239]], inplace = True)
    
    # Fixing spelling differences between data sources

    map_df['NAME'] = np.where(map_df['NAME'] == 'United States of America', 'United States', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Bosnia and Herz.', 'Bosnia And Herzegovina', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Congo', 'Republic of Congo', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Dem. Rep. Congo', 'Democratic Republic Of The Congo', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Dominican Rep.', 'Dominican Republic', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Central African Rep.', 'Central African Republic', map_df['NAME'])
    map_df['NAME'] = np.where(map_df['NAME'] == 'Czechia', 'Czech Republic', map_df['NAME'])

    
    base = map_df['NAME'].unique()

    other = country_counts['Country'].to_dict()
    
    uk_current = other['England']
    uk_new = sum([other[country] for country in other if country in ('England', 'Scotland', 'Wales', 'Northern Ireland', 'Cayman Islands')])
    
    other = pd.DataFrame(list(other.items()), columns = ['Country', 'Cases'])
    other.loc[len(other.index)] = ['United Kingdom', uk_new]



    fix_names = [country for country in other if country not in base]
    

    
    merged = map_df.merge(other, how = 'left', left_on = 'NAME',
        right_on = 'Country')
    merged['Cases'] = merged['Cases'].fillna(0)



    # Set range for choropleth values
    # change max to the current max cases
    min, max = 0, round(max(merged['Cases']), -3) 

    # create figure and axes for Matplotlib
    fig, ax = plt.subplots(1, figsize=(30, 10))
 
    # remove the axis
    ax.axis('off')

    ax.set_title('Total Monkeypox Cases per Country', fontdict={'fontsize': '25', 'fontweight' : '4'})



    # colorbar legend
    sm = plt.cm.ScalarMappable(cmap='Reds', norm=plt.Normalize(vmin=min, vmax=max))

    # empty array for data
    sm.set_array([])

    # Displaying colorball legend and map 
    fig.colorbar(sm, orientation="horizontal", fraction=0.036, pad=0.1, aspect = 40)

    merged.plot(column='Cases', cmap='Reds', linewidth=0.8, ax=ax, edgecolor='0.7')


    st.write('## Global Data')
    st.pyplot()

    st.write('## U.S. Data')
    # ALSO DO SAME THING BUT FOR US STATES DATA


# ---------- Sources Page ---------- #
if selected in ('"Sources"', 'Sources'):
    st.write('## Sources and Acknowledgments')
    st.write('The visualizations in this dashboard are made possible by public data provided by various sources.')
    st.write('')
    st.write('')
    st.write('Data on Monkeypox cases are provided by Global.health, and can be found at the following repository:')
    st.write(f'https://github.com/globaldothealth/monkeypox (Last accessed: {last_updated})')
    st.write('')
    st.write('')
    st.write('Geographic (GIS) data for map building is provided by Natural Earth at the following link:')
    st.write('http://www.naturalearthdata.com/downloads/50m-cultural-vectors/')
    st.write('')
    st.write('')    
    st.write('')
    st.write('All data is used with permission under a CC-BY-4.0 license.')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('---------------------------------------------------------')
    st.write('Monkeypox Dashboard was created by Anthony Cusimano.')
    st.write('Thank you for visiting this page, and please stay safe!')


#st.sidebar.write("https://www.linkedin.com/in/anthonycusi/", color = 'gray')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')
st.sidebar.write('')


#st.sidebar.write('Created by Anthony Cusimano')


# [theme]
# base="dark"
# primaryColor="#6C3EFF"
# backgroundColor="#0e0b16"
# textColor="#e7dfdd"
