# Libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import streamlit as st
import numpy as np
import altair as alt
from streamlit_option_menu import option_menu
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
import geopandas
from bs4 import BeautifulSoup
import requests
import urllib

# Modules
from data_loader import *



# -- CHANGES TO MAKE -- #
# check box to 'include suspected cases' which uses the 'Status' column in data


# ---------- Setting Up Webpage ---------- #
st.set_page_config(page_title = 'Monkeypox Visualization', page_icon = ':bar_chart:', layout = 'wide')

# Hide hamburger menu
hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
            #MainMenu {visibility: hidden;}
            #header {visibility: hidden;}

st.markdown(hide_st_style, unsafe_allow_html=True)

# Reduce padding above nav bar
st.write('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# Navigation bar
selected = option_menu(None, ['Home', 'Maps', 'Sources'], 
    icons=['bar-chart-line', 'geo-alt', 'info-circle'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles = {'nav-link': {'--hover-color': '#8E6FF9'}}
)

#### Add Resources to first list and 'clipboard-check' to second list

# ---------- Loading Data ---------- #

# Initializing dataframes 
dataframes = load_all()
full_df = dataframes[0]
cum_df = dataframes[1]
total_df = dataframes[2]

# Gets date data was last updated
date_df = dataframes[3]
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


# ---------- Home Page ---------- #
if selected == '"Home"' or selected == 'Home':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases')
    st.write(f'Data last updated {last_updated}. (Updates Mon-Fri)')
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

    st.write('## Cumulative Cases by Country')
    st.write('Select countries to visualize on the left sidebar.')
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
        daily_increase = dict()

        for country in cum_df['Country'].unique():
            country_data = cum_df[cum_df['Country'] == country]
            if country == 'Democratic Republic Of The Congo':
                country = 'Dem. Rep. Congo'
            if country == 'United Kingdom':
                country = 'England'
            daily_increase[country] = country_data.tail()['Cases'].loc[country_data.index[-1]]
        
        increase_data = {'Country': daily_increase.keys(), 'Increase From Yesterday': daily_increase.values()}
        daily_increase = pd.DataFrame.from_dict(increase_data)

        st.write('## Cumulative Case Table')
        st.write('#### Select countries to directly compare:')
        counts_data = {'Country Name                                  ': names, 'Cases  ': values}
        counts_df = pd.DataFrame.from_dict(counts_data)

        merged = counts_df.merge(daily_increase, how = 'left', left_on = 'Country Name                                  ',
            right_on = 'Country')
        merged = merged.drop('Country', axis = 1)
        merged.index += 1


        gb = GridOptionsBuilder.from_dataframe(merged)
        #gb.configure_pagination(paginationAutoPageSize=True) #Add pages
        gb.configure_side_bar() #Add a sidebar
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
        gridOptions = gb.build()

        grid_response = AgGrid(
            merged,
            gridOptions=gridOptions,
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED', 
            fit_columns_on_grid_load=False,
            theme='dark',
            enable_enterprise_modules=True,
            height=350, 
            width='100%',
            reload_data=True
        )

        data = grid_response['data']
        selected = grid_response['selected_rows'] 
        selected_df = pd.DataFrame(selected) #Pass the selected rows to a new dataframe
        
    # Direct Comparison Table
    with col2: 
        if selected_df.shape[0] > 0:
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('#### Direct Comparison Table')
            gb2 = GridOptionsBuilder.from_dataframe(selected_df)
            gb2.configure_side_bar()
            grid2Options = gb2.build()

            grid2_response = AgGrid(
                selected_df,
                #gridOptions=grid2Options,
                data_return_mode='AS_INPUT', 
                update_mode='MODEL_CHANGED', 
                #fit_columns_on_grid_load=False,
                theme='dark',
                #enable_enterprise_modules=True,
                height=300
            )

    col3, col4 = st.columns(2)

    # Total global cases graph
    with col3:
        # Removing early dates with almost no cases
        total_df = total_df.iloc[60:]
        
        st.write('## Total Cases Globally')
        fig, ax = plt.subplots()
        ax.plot(total_df['Date'], total_df['Cumulative Cases'], label = 'Total Cases', color = 'purple')
    
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Cases', color = 'purple')
        ax.tick_params(axis = 'y', labelcolor = 'purple')

        
        ax2 = ax.twinx()
        ax2.bar(total_df['Date'], total_df['Cases'], label = 'Daily Increase', color = 'teal')
        # ax.yaxis.set_label_position('left')
        # ax.yaxis.tick_left()
        ax2.set_ylabel('Daily Increase', color = 'teal')
        ax2.set(ylim=(0, 5000))

        ax2.tick_params(axis = 'y', labelcolor = 'teal')


        fig.tight_layout()
        st.pyplot(fig)

    # Global cases pie chart
    with col4:
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
    
    col5, col6 = st.columns(2)

    # Gender distribution pie chart
    with col5:
        gender_data = full_df[full_df['Gender'].isin(('male', 'female'))]['Gender']
        males = len([person for person in gender_data.to_dict().values() if person == 'male'])
        females = len([person for person in gender_data.to_dict().values() if person == 'female'])
        gender_df = pd.DataFrame({'Gender': ['Male', 'Female'], 'Count': [males, females]})
        
        fig2, ax2 = plt.subplots()
        gender_list = [gender_df['Count'].iloc[0], gender_df['Count'].iloc[1]]
        ax2.pie(list(gender_list), labels = gender_df['Gender'], autopct='%1.1f%%',
                    shadow=True, startangle=90)
        st.write('## Gender Distribution of Cases')
        fig2.set_figheight(7)
        st.pyplot(fig2)
    
    # Hospitalization bar chart
    with col6:
        hospitalized_dict = full_df['Hospitalised (Y/N/NA)'].value_counts().to_dict()
        hospitalized_df = pd.DataFrame({'Status': ['Hospitalized', 'Not Hospitalized'], 'Count': [[hospitalized_dict['Y']], [hospitalized_dict['N']]]})
        
        st.write('## Hospitalization Rates')
        fig3, ax3 = plt.subplots()
        ax3.bar(hospitalized_df['Status'], hospitalized_df['Count'], color = 'teal')
        ax3.set_ylabel('Number of People')

        # Changing graph height based on current numbers
        hospital_graph_max = max([x[0] for x in hospitalized_df['Count'].to_dict().values()])
        ax3.set(ylim=(0, hospital_graph_max * 1.5))

        fig3.set_figheight(7)
        st.pyplot(fig3)
        
    st.write('Note: Gender and hospitalization data are not available for some cases, so the true distribution may vary slightly.')

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
    st.write('Coming soon')
    # ALSO DO SAME THING BUT FOR US STATES DATA
    # HTTP request
    url = 'https://www.cdc.gov/poxvirus/monkeypox/response/2022/us-map.html'
    html = urllib.request.urlopen(url)

    
    result = requests.get(url)
    #doc = BeautifulSoup(result.content, 'html.parser')
    doc = BeautifulSoup(html)
    
    num = doc.findAll('td', {'role': 'gridcell'})



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



# [theme]
# base="dark"
# primaryColor="#6C3EFF"
# backgroundColor="#0e0b16"
# textColor="#e7dfdd"
