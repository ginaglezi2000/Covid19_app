# Core Pkgs
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import numpy as np


# The environment:
# conda create -n geo -c conda-forge --strict-channel-priority
# pandas matplotlib notebook scikit-learn geopandas shapely descartes
# xlrd openpyxl streamlit seaborn altair plotly
# conda activate geo

def fetch_data():
    # USA shape file
    usa_git = gpd.read_file('./states_git/usa-states-census-2014.shp')
    # Downloading current Covid-19 information for USA
    _url_current = 'https://api.covidtracking.com/v1/states/current.csv'
    current = pd.read_csv(_url_current)
    # Population data
    population_path = './population_2019_short.xlsx'
    population = pd.read_excel(population_path, header=0, skiprows=1, engine='openpyxl')
    return usa_git,population, current


def create_geodataframe(usa_git,population, current):
    usa_mainland = usa_git.loc[:, ['STUSPS', 'NAME', 'geometry']]
    # Merging population data and Covid-19 data
    cov_pop = population.merge(current.iloc[:, 1:3], left_on='STUSPS', right_on='state')
    cov_pop.drop('state', axis=1, inplace=True)
    # Compute percentage of population already infected by Covid-19 by state
    cov_pop['positive_population_fraction'] = (cov_pop.positive / cov_pop.pop_2019) * 100
    # Adding percentage to shape file
    usa_mainland_info = usa_mainland.merge(cov_pop.iloc[:, [0, 4]], on='STUSPS')
    return usa_mainland_info


def generate_and_save_map(usa_mainland_info):
    fig, ax = plt.subplots(figsize=(10, 10))
    usa_mainland_info.plot(column='positive_population_fraction', ax=ax,
                           cmap='OrRd', legend=True, legend_kwds={'shrink': 0.4})
    plt.savefig('current_map.png', bbox_inches='tight')
    pass


def some_stats(usa_mainland_info):
    state_max = usa_mainland_info.positive_population_fraction.max()
    state_name_max = usa_mainland_info.NAME[np.argmax(usa_mainland_info.positive_population_fraction)]
    max_pair = (state_name_max, state_max)
    state_min = usa_mainland_info.positive_population_fraction.min()
    state_name_min = usa_mainland_info.NAME[np.argmin(usa_mainland_info.positive_population_fraction)]
    min_pair = (state_name_min, state_min)
    return max_pair, min_pair


def frontend(current,max_pair, min_pair):
    st.title("Covid-19 tracker by state")
    st.subheader("By Georgina Gonzalez-Isunza")
    st.header("Percentage of population that has been infected per state")
    st.text('Highest: {} with {:.1f}%      Lowest: {} with {:.1f}% '\
            .format(max_pair[0], max_pair[1], min_pair[0], min_pair[1]))
    last_date = str(current.date[0])
    last_date = last_date[4:6] + '/' + last_date[6:8] + '/' + last_date[0:4]
    st.text('Data from: {}'.format(last_date))
    st.image('current_map.png')
    pass


if __name__ == '__main__':
    usa_git,population, current = fetch_data()
    usa_mainland_info = create_geodataframe(usa_git,population, current)
    max_pair, min_pair = some_stats(usa_mainland_info)
    generate_and_save_map(usa_mainland_info)
    frontend(current, max_pair, min_pair)
