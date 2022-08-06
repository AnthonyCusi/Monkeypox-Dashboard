# Contains functions to create the various charts and graphs.

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from st_aggrid import GridOptionsBuilder, AgGrid

# ------- Cumulative Case Table ------- #
def cumulative_cases(df: pd.DataFrame, countries: list[str], cases: list[int]):
    '''Returns components to build cumulative case table'''

    merged = get_daily_increases(df, countries, cases)

    gb = GridOptionsBuilder.from_dataframe(merged)
    gb.configure_side_bar()
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
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

    # selected = grid_response['selected_rows'] 
    # selected_df = pd.DataFrame(selected) #Pass the selected rows to a new dataframe

    return (gb, grid_response)


# ------- Total Global Cases Graph ------- #
def global_case_graph(df: pd.DataFrame):
    '''Returns tuple with matplotlib (figure, axis1, axis2)'''

    # Removing early dates with almost no cases
    df = df.iloc[60:]
    
    # Axis 1: total cases
    fig, ax = plt.subplots()
    ax.plot(df['Date'], df['Cumulative Cases'], label = 'Total Cases', color = 'purple')
    ax.set_xlabel('Date')
    ax.set_ylabel('Total Cases', color = 'purple')
    ax.tick_params(axis = 'y', labelcolor = 'purple')

    # Axis 2: daily cases
    ax2 = ax.twinx()
    ax2.bar(df['Date'], df['Cases'], label = 'Daily Increase', color = 'teal')
    ax2.set_ylabel('Daily Increase', color = 'teal')
    ax2.set(ylim=(0, 5000))
    ax2.tick_params(axis = 'y', labelcolor = 'teal')

    xticks = ticker.MaxNLocator(5)
    ax.xaxis.set_major_locator(xticks)


    fig.tight_layout()

    return (fig, ax, ax2)

# ------- Global Cases Breakdown Pie Chart ------- #
def global_pie_chart(countries: list[str], cases: list[int]):
    '''Returns tuple with matplotlib (figure, axis)'''

    other_slice = sum([val for val in cases[9:]])
    countries, cases = countries[:9], cases[:9]
    countries.append('Other')
    cases.append(other_slice)

    fig, ax = plt.subplots()
    colors = ['purple', 'mediumorchid', 'lightpink', 'cornflowerblue', 'paleturquoise', 'palegreen', 'olivedrab',
        'mediumturquoise', 'khaki', 'teal']

    ax.pie(cases, labels = countries, autopct='%1.1f%%',
                shadow=False, startangle=90, colors = colors)
    # ax.set_facecolor('#99c2ff')

    return (fig, ax)


# ------- Gender Distribution Pie Chart ------- #
def gender_chart(df: pd.DataFrame):
    '''Returns tuple with matplotlib (figure, axis)'''

    gender_data = df[df['Gender'].isin(('male', 'female'))]['Gender']
    males = len([person for person in gender_data.to_dict().values() if person == 'male'])
    females = len([person for person in gender_data.to_dict().values() if person == 'female'])
    gender_df = pd.DataFrame({'Gender': ['Male', 'Female'], 'Count': [males, females]})

    fig, ax = plt.subplots()
    fig.set_figheight(7)
    gender_list = [gender_df['Count'].iloc[0], gender_df['Count'].iloc[1]]
    colors = ['teal', 'purple']
    ax.pie(list(gender_list), labels = gender_df['Gender'], autopct='%1.1f%%',
                shadow=False, startangle=90, colors = colors)

    return (fig, ax)


# ------- Hospitalization Bar Chart ------- #
def hospitalization_chart(df: pd.DataFrame):
    '''Returns tuple with matplotlib (figure, axis)'''


    hospitalized_dict = df['Hospitalised (Y/N/NA)'].value_counts().to_dict()
    hospitalized_df = pd.DataFrame({'Status': ['Hospitalized', 'Not Hospitalized'], 'Count': [[hospitalized_dict['Y']], [hospitalized_dict['N']]]})

    fig, ax = plt.subplots()
    ax.bar(hospitalized_df['Status'], hospitalized_df['Count'], color = 'teal')
    ax.set_ylabel('Number of People')
    fig.set_figheight(7)

    # Changing graph height based on current numbers
    hospital_graph_max = max([x[0] for x in hospitalized_df['Count'].to_dict().values()])
    ax.set(ylim=(0, hospital_graph_max * 1.5))

    return (fig, ax)


# ----------------- HELPER FUNCTIONS ---------------- #
def get_daily_increases(df: pd.DataFrame, countries: list[str], cases: list[int]):
    '''Returns merged dataframe containing countries and their daily case increase'''
    
    daily_increase = dict()
    for country in df['Country'].unique():
        country_data = df[df['Country'] == country]
        if country == 'Democratic Republic Of The Congo':
            country = 'Dem. Rep. Congo'
        if country == 'United Kingdom':
            country = 'England'
        daily_increase[country] = country_data.tail()['Cases'].loc[country_data.index[-1]]
    
    daily_increase = {'Country': daily_increase.keys(), 'Increase From Yesterday': daily_increase.values()}
    daily_increase = pd.DataFrame.from_dict(daily_increase)

    counts_data = {'Country Name                                  ': countries, 'Cases  ': cases}
    counts_df = pd.DataFrame.from_dict(counts_data)

    merged = counts_df.merge(daily_increase, how = 'left', left_on = 'Country Name                                  ',
        right_on = 'Country')
    merged = merged.drop('Country', axis = 1)
    merged['Increase From Yesterday'] = merged['Increase From Yesterday'].fillna('Not Available')

    merged.index += 1

    return merged