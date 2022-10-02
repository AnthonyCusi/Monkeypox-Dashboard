# This module loads the necessary data from csv files.

import pandas as pd

def load_full_data():
    df = pd.read_csv('https://raw.githubusercontent.com/globaldothealth/monkeypox/main/latest_deprecated.csv')

    df.drop(['Source', 'Source_II', 'Source_III', 'Source_IV', 'Source_V', 'Source_VI', 'Source_VII',
        'ID', 'Contact_ID', 'Contact_comment', 'Date_last_modified'], axis = 1, inplace = True)
    df = df[(df['Status'] == 'confirmed') | (df['Status'] == 'suspected')]

    return df

def load_cumulative_cases():
    df = pd.read_csv('https://raw.githubusercontent.com/globaldothealth/monkeypox/main/timeseries-country-confirmed-deprecated.csv')
    
    # Formatting information for readability
    df.rename(columns = {'Cumulative_cases': 'Cumulative Cases'}, inplace = True)
    return df

def load_total_cases():
    df = pd.read_csv('https://raw.githubusercontent.com/globaldothealth/monkeypox/main/timeseries-confirmed-deprecated.csv')

    # Formatting information for readability
    df.rename(columns = {'Cumulative_cases': 'Cumulative Cases'}, inplace = True)
    return df

# Returns all of the dataframes concisely
def load_all():
    cum_df = load_cumulative_cases()
    date_df = pd.to_datetime(cum_df['Date']).sort_values(ascending = False)

    return [load_full_data(), cum_df, load_total_cases(), date_df]