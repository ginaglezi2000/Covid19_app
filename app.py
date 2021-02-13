# Core Pkgs
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import numpy as np
import seaborn as sns


# The environment:
# conda create -n geo -c conda-forge --strict-channel-priority
# pandas matplotlib notebook scikit-learn geopandas shapely descartes
# xlrd openpyxl streamlit seaborn altair plotly
# conda activate geo

st.set_page_config(page_title='Gonzalez-Isunza.Covid19App',
                   page_icon='🦠',
                   layout='wide',
                   initial_sidebar_state='expanded')

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


def merge_covid_and_population(current, population):
    cov_pop = population.merge(current.loc[:, ['state', 'positive', 'death']], left_on='STUSPS', right_on='state')
    cov_pop.drop('state', axis=1, inplace=True)
    return cov_pop


def create_geodataframe(usa_git,cov_pop):
    usa_mainland = usa_git.loc[:, ['STUSPS', 'NAME', 'geometry']]
    # Compute percentage of population already infected by Covid-19 by state
    cov_pop['positive_population_fraction'] = (cov_pop.positive / cov_pop.pop_2019) * 100
    # Adding percentage to shape file
    for_map = ['STUSPS', 'pop_2019', 'positive_population_fraction']
    usa_mainland_info = usa_mainland.merge(cov_pop.loc[:,for_map], on='STUSPS')
    return usa_mainland_info


def generate_and_save_map(usa_mainland_info):
    fig, ax = plt.subplots(figsize=(10, 10))
    usa_mainland_info.plot(column='positive_population_fraction', ax=ax,
                           cmap='OrRd', legend=True, legend_kwds={'shrink': 0.4})
    plt.savefig('current_map.png', bbox_inches='tight')
    pass


def death_rate_plot(cov_pop):
    cov_pop['death_per100k'] = (cov_pop.death * 100000) / cov_pop.pop_2019
    fig, ax = plt.subplots(figsize=(6, 15))
    temp = cov_pop.sort_values('death_per100k', ascending=False)
    sns.set_color_codes('pastel')
    sns.barplot(x='death_per100k', y='NAME', data=temp, color='orange')
    ax.set(title='Deaths per 100,000 population', xlabel='', ylabel='',
           xticklabels=[])
    for p in ax.patches:
        height = p.get_height()  # height of each horizontal bar is the same
        width = p.get_width()  # width (average number of passengers)
        # adding text to each bar
        ax.text(x=width + 3,  # x-coordinate position of data label, padded 3 to right of bar
                y=p.get_y() + (height / 2),
                # y-coordinate position of data label, padded to be in the middle of the bar
                s='{:.0f}'.format(width),  # data label, formatted to ignore decimals
                va='center')  # sets vertical alignment (va) to center
    sns.despine(bottom=True)  # removes box lines
    ax.tick_params(bottom=False)
    plt.savefig('death_rate_plot.png', bbox_inches='tight')
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
    def frontend_death100k():
        st.header("Number of deaths for every 100,000 people")
        st.image('death_rate_plot.png')
        pass

    def frontend_infection():
        st.header("Percentage of population that has been infected")
        st.text('Highest: {} with {:.1f}%      Lowest: {} with {:.1f}% '
                .format(max_pair[0], max_pair[1], min_pair[0], min_pair[1]))
        st.image('current_map.png')
        pass

    def menu():
        selection = st.sidebar.radio("Select the desired information:", (
            "Population percentage of infection",
            "Death per 100,000 population"))
        if selection == 'Death per 100,000 population':
            frontend_death100k()
        else:
            frontend_infection()
        pass

    st.title("Covid-19 tracker")
    st.subheader("By Georgina Gonzalez-Isunza")
    # st.sidebar.text('Select the desired information:')
    last_date = str(current.date[0])
    last_date = last_date[4:6] + '/' + last_date[6:8] + '/' + last_date[0:4]
    st.text('Data from: {}'.format(last_date))
    menu()
    JHU = 'Johns Hopkins University CSSE'
    census = 'U.S. Census Bureau'
    st.text('Source: {} & {} (2019 population)'.format(JHU, census))
    # st.image('death_rate_plot.png')
    pass


if __name__ == '__main__':
    usa_git,population, current = fetch_data()
    cov_pop = merge_covid_and_population(current, population)
    usa_mainland_info = create_geodataframe(usa_git,cov_pop)
    max_pair, min_pair = some_stats(usa_mainland_info)
    generate_and_save_map(usa_mainland_info)
    death_rate_plot(cov_pop)
    frontend(current, max_pair, min_pair)
