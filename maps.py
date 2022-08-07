# Contains functions to create the global and US maps.
import geopandas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_world(country_counts):
    '''Displays a world map colored by case counts for each country'''

    map_df = geopandas.read_file('land_data/country_map/ne_50m_admin_0_countries.shp')
    map_df = map_df[['NAME', 'geometry']]

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
    
    # Combining counts for the United Kingdom
    uk_current = other['England']
    uk_new = sum([other[country] for country in other if country in ('England', 'Scotland', 'Wales', 'Northern Ireland', 'Cayman Islands')])
    
    other = pd.DataFrame(list(other.items()), columns = ['Country', 'Cases'])
    other.loc[len(other.index)] = ['United Kingdom', uk_new]

    # Merging the map and data by country name
    merged = map_df.merge(other, how = 'left', left_on = 'NAME',
        right_on = 'Country')
    merged['Cases'] = merged['Cases'].fillna(0)
    
    # Change max for colorbar to the current max cases
    min, max = 0, round(merged['Cases'].max(), -3) 

    # Create figure and axes for Matplotlib
    fig, ax = plt.subplots(1, figsize=(30, 10))
 
    # Customizing the axis
    ax.axis('off')
    ax.set_title('Total Monkeypox Cases per Country', fontdict={'fontsize': '25', 'fontweight' : '4'})

    # Colorbar legend
    sm = plt.cm.ScalarMappable(cmap='cool', norm=plt.Normalize(vmin=min, vmax=max))
    sm.set_array([])

    # Displaying colorball legend and map 
    fig.colorbar(sm, orientation="horizontal", fraction=0.036, pad=0.1, aspect = 40)

    return merged, fig, ax, sm


def plot_us():
    '''Displays the US map colored by case counts for each state'''

    # Set up data
    us_map_df = geopandas.read_file('land_data/us_map/cb_2018_us_state_5m.shp')
    us_map_df = us_map_df[['NAME', 'geometry']]
    
    state_cases = pd.read_csv('https://raw.githubusercontent.com/gridviz/monkeypox/main/data/processed/monkeypox_cases_states_cdc_latest.csv')
    state_cases = state_cases[['state', 'cases']]

    # Merge map and case data on state names
    us_merged = us_map_df.merge(state_cases, how = 'left', left_on = 'NAME',
        right_on = 'state')
    us_merged.dropna(inplace = True)

    # Change max to the current max cases
    min, max = 0, round(us_merged['cases'].max(), -3)

    # Create figure and axes for Matplotlib
    fig, ax = plt.subplots(1, figsize=(30, 15))
 
    # Customize the axis and boundaries
    ax.axis('off')
    ax.set_title('Total Monkeypox Cases per State (Contiguous U.S.)', fontdict={'fontsize': '25', 'fontweight' : '4'})

    bounds = [-129, 25, -61, 50]
    xlim = ([bounds[0], bounds[2]])
    ylim = ([bounds[1],  bounds[3]])
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # Labeling states
    manual_list = ['Louisiana', 'Mississippi', 'West Virginia', 'Virginia', 'District of Columbia', 'Delaware', 'New York',
        'New Hampshire', 'Massachusetts', 'Rhode Island', 'Vermont', 'Connecticut']
    
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = x['geometry'].centroid.coords[0], 
                ha = 'center', fontsize = 14) if x.NAME not in manual_list else '', axis = 1)

    # Manual label adjustents
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.5), 
        ha = 'center', fontsize = 14) if x.NAME == 'Louisiana' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.75), 
        ha = 'center', fontsize = 14) if x.NAME == 'Mississippi' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.75), 
        ha = 'center', fontsize = 14) if x.NAME == 'West Virginia' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0], x['geometry'].centroid.coords[0][1] - 0.75), 
        ha = 'center', fontsize = 14) if x.NAME == 'Virginia' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 0.3, x['geometry'].centroid.coords[0][1] - 0.5), 
        ha = 'center', fontsize = 14) if x.NAME == 'New York' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 0.3, x['geometry'].centroid.coords[0][1] - 0.5), 
        ha = 'center', fontsize = 14) if x.NAME == 'Vermont' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + '\n' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 0.5, x['geometry'].centroid.coords[0][1] - 0.4), 
        ha = 'center', fontsize = 14) if x.NAME == 'Connecticut' else '', axis = 1)
    
    # Side key
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 10, x['geometry'].centroid.coords[0][1] - 2), 
        ha = 'center', fontsize = 14) if x.NAME == 'District of Columbia' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 8.2, x['geometry'].centroid.coords[0][1] - 3), 
        ha = 'center', fontsize = 14) if x.NAME == 'Delaware' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 4.5, x['geometry'].centroid.coords[0][1] - 4.25), 
        ha = 'center', fontsize = 14) if x.NAME == 'New Hampshire' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 4.5, x['geometry'].centroid.coords[0][1] - 3.7), 
        ha = 'center', fontsize = 14) if x.NAME == 'Massachusetts' else '', axis = 1)
    us_merged.apply(lambda x: ax.annotate(text = x.NAME + ': ' + str(int(x.cases)), xy = (x['geometry'].centroid.coords[0][0] + 4.4, x['geometry'].centroid.coords[0][1] - 3.95), 
        ha = 'center', fontsize = 14) if x.NAME == 'Rhode Island' else '', axis = 1)   

    # Colorbar legend
    sm = plt.cm.ScalarMappable(cmap='cool', norm=plt.Normalize(vmin=min, vmax=max))
    sm.set_array([])

    # Displaying colorbar legend and map 
    fig.colorbar(sm, orientation="horizontal", fraction=0.036, pad=0.1, aspect = 40)

    return us_merged, fig, ax, sm