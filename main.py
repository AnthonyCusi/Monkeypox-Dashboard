# Libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import streamlit as st
import numpy as np
import altair as alt
from streamlit_option_menu import option_menu
from st_aggrid import GridOptionsBuilder, AgGrid
from bs4 import BeautifulSoup

# Modules
import data_loader
import charts
import maps


# ---------- Setting Up Webpage ---------- #
st.set_page_config(page_title = 'Monkeypox Dashboard', page_icon = ':bar_chart:', layout = 'wide')
st.set_option('deprecation.showPyplotGlobalUse', False)

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
selected = option_menu(None, ['Home', 'Maps', 'Resources', 'Sources'], 
    icons=['bar-chart-line', 'geo-alt', 'heart', 'info-circle'], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles = {'nav-link': {'--hover-color': '#8E6FF9'}}
)

# ---------- Loading Data ---------- #

# Initializing dataframes 
dataframes = data_loader.load_all()
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

# Getting cumulative cases
#cum_cases = pd.read_csv('https://www.cdc.gov/wcms/vizdata/poxvirus/monkeypox/data/MPX-Cases-by-Country.csv')
#curr_total = str('{:,}'.format(sum(cum_cases['Cases'])))

# markup = '''<html><body><div id="container">Div Content</div></body></html>'''
# soup = BeautifulSoup(markup, 'html.parser')
# div_bs4 = soup.find('div', {'class': 'bite-value'})
curr_total = str('{:,}'.format(total_df['Cumulative Cases'][len(total_df)-1]))

# ---------- Home Page ---------- #
if selected == '"Home"' or selected == 'Home':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases: ' + curr_total)
    st.write(f'Data last updated {last_updated}. (Updates Mon-Fri)')
    st.write('') 
    
    # Gets data for user-selected countries
    selection_df = cum_df[cum_df['Country'].isin(countries)]
   

    # Line chart
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['Date'], empty='none')

    line_chart = alt.Chart(selection_df).mark_line(interpolate = 'basis').encode(
        x = alt.X('Date', axis = alt.Axis(title = 'Date', tickMinStep = 2)),
        y = 'Cumulative Cases',
        color = 'Country'
    )

    selectors = alt.Chart(selection_df).mark_point().encode(
        x = alt.X('Date', axis = alt.Axis(title = 'Date', tickMinStep = 2)),
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
        x = alt.X('Date', axis = alt.Axis(title = 'Date', tickMinStep = 2))
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
    col3, col4 = st.columns(2)
    col5, col6 = st.columns(2)

    # Cumulative cases table
    with col1:
        st.write('## Cumulative Case Table')
        st.write('#### Select countries to directly compare:')
        merged = charts.get_daily_increases(cum_df, names, values)

        gb = GridOptionsBuilder.from_dataframe(merged)
        gb.configure_side_bar()
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
        gridOptions = gb.build()

        grid_response = AgGrid(
            merged, gridOptions=gridOptions,
            data_return_mode='AS_INPUT', update_mode='MODEL_CHANGED', 
            fit_columns_on_grid_load=False,
            theme='dark', enable_enterprise_modules=True, height=350, width='100%', reload_data=True
        )

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
                data_return_mode='AS_INPUT', 
                update_mode='MODEL_CHANGED', theme='dark', height=300
            )

    # Total global cases graph
    with col3: 
        st.write('## Total Cases Globally')
        global_case_graph = charts.global_case_graph(total_df)
        fig, ax, ax2 = global_case_graph[0], global_case_graph[1], global_case_graph[2]
        st.pyplot(fig)

    # Global cases pie chart
    with col4:
        st.write('## Breakdown of Global Cases')
        global_pie_chart = charts.global_pie_chart(names, values)
        fig, ax = global_pie_chart[0], global_pie_chart[1]
        st.pyplot(fig)

    # Gender distribution pie chart
    with col5:
        st.write('## Gender Distribution of Cases')
        gender_chart = charts.gender_chart(full_df)
        fig, ax = gender_chart[0], gender_chart[1]
        st.pyplot(fig)
    
    # Hospitalization bar chart
    with col6:
        st.write('## Hospitalization Rates')
        hosp_chart = charts.hospitalization_chart(full_df)
        fig, ax = hosp_chart[0], hosp_chart[1]
        st.pyplot(fig)
        
    st.write('Note: Gender and hospitalization data were not reported for all cases, \
        so the true distribution may vary slightly.')

# ---------- Maps Page ---------- #
if selected == '"Maps"' or selected == 'Maps':

    # Page Header
    st.write('# Current Monkeypox (MPXV) Cases: ' + curr_total)
    st.write(f'Data last updated {last_updated}.')
    st.write("") 

    # World map
    st.write('## Global Data')
    merged, fig, ax, sm = maps.plot_world(country_counts)
    merged.plot(column='Cases', cmap='cool', linewidth=0.8, ax=ax, edgecolor='0.7')
    st.pyplot()
    st.write('')
    st.write('')

    # US map
    st.write('## U.S. Data')
    us_merged, fig, ax, sm = maps.plot_us()
    us_merged.plot(column='cases', cmap='cool', linewidth=0.8, ax=ax, edgecolor='0.7')
    st.pyplot()

# ---------- Resources Page ---------- #
if selected == '"Resources"' or selected == 'Resources':
    st.write('# Important Information about Monkeypox')
    st.write('Information gathered from the CDC: https://www.cdc.gov/poxvirus/monkeypox/')

    st.write('### How does Monkeypox spread?')
    st.markdown("- Direct contact with rash, scabs, or body fluids from a person with monkeypox")
    st.markdown("- Touching objects, fabrics (clothing, bedding, or towels), and surfaces that have been used by someone with monkeypox")
    st.markdown("- Sex, hugging, massages, kissing")
    st.markdown("- Being scratched or bitten by infected animals or eating meat using products from infected animals")
    st.markdown("- Contact with respiratory secretions")
    
    st.write('### What are the main symptoms?')
    st.markdown("- Rash near genitals")
    st.markdown("- Fever, chills, swollen lymph nodes, exhaustion")
    st.markdown("- Muscle aches, backache, headache")
    st.markdown("- Respiratory symptoms (sore throat, nasal congestion, cough)")

    st.write('### How can I stay safe?')
    st.markdown("- Limit your number of sexual partners")
    st.markdown("- Minimize skin-to-skin contact in crowded places like raves and festivals")
    st.markdown("- Avoid sharing clothing, towels, and other personal items with others")
    st.markdown("- Contain contaminated linens and clothing after laundering; keep separate from other household members")

    st.write('### Where can I find more information?')
    st.markdown("- Centers for Disease Control and Prevention (CDC): https://www.cdc.gov/poxvirus/monkeypox/")
    st.markdown("- Center for Infectious Disease Research and Policy (CIDRAP): https://www.cidrap.umn.edu/monkeypox")
    st.markdown("- National Coalition for LGBTQ Health: https://healthlgbtq.org/monkeypox/")
    st.markdown('''
    <style>
    [data-testid="stMarkdownContainer"] ul{
        list-style-position: inside;
    }
    </style>
    ''', unsafe_allow_html=True)

# ---------- Sources Page ---------- #
if selected in ('"Sources"', 'Sources'):
    st.write('## Sources and Acknowledgments')
    st.write('The visualizations in this dashboard are made possible by public data provided by various sources.')
    st.write('')
    st.write('')
    st.write('Data on Monkeypox cases are provided by Global.health, and can be found at the following repository:')
    st.write(f'https://github.com/globaldothealth/monkeypox (Last accessed: {last_updated})')
    st.write('')
    st.write('Case counts by U.S. state is provided by the CDC:')
    st.write('https://www.cdc.gov/poxvirus/monkeypox/response/2022/us-map.html')
    st.write('')
    st.write('Geographic (GIS) data for map building is provided by Natural Earth at the following link:')
    st.write('http://www.naturalearthdata.com/downloads/50m-cultural-vectors/')
    st.write('')
    st.write('Geographic data for the US map is provided by the United States Census:')  
    st.write('https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html')  
    st.write('')
    st.write('Information about Monkeypox was gathered from the CDC:')
    st.write('https://www.cdc.gov/poxvirus/monkeypox/')
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('All data is used with permission under a CC-BY-4.0 license.')
    st.write('')
    st.write('')
    st.write('---------------------------------------------------------')
    st.write('Monkeypox Dashboard was created by Anthony Cusimano.')
    st.write('Contribute to the repository! https://github.com/AnthonyCusi/Monkeypox-Dashboard')
    st.write('')
    st.write('Thank you for visiting this page, and please stay safe!')


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
