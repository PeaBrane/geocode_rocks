import os
import pandas as pd
import numpy as np

from urllib import request
from bs4 import BeautifulSoup

import re
from tqdm import tqdm


def get_votes(df: pd.DataFrame):
    
    votes = []
    for index in tqdm(range(len(df))):
        url = df['URL'].iloc[index]
        response = request.urlopen(url)
        soup = BeautifulSoup(response.read(), 'html.parser')

        results = soup.body.find_all(string=re.compile('.*{0}.*'.format('Avg')), recursive=True)[0]
        start_index = results.find('from') + 5
        end_index = results.find('votes') - 5

        vote = int(results[start_index:end_index])
        votes.append(vote)

    return np.array(votes)


def build_df(df: pd.DataFrame, 
             votes: np.array,
             boulder=True, 
             tol=1e-7):
    
    latitudes, longitudes = df['Area Latitude'].to_numpy(), df['Area Longitude'].to_numpy()
    coords = np.stack([latitudes, longitudes], axis=-1)
    distances = coords[np.newaxis, ...] - coords[:, np.newaxis]
    sames = (np.absolute(distances) <= tol).all(-1)

    indices = []
    for index, same in enumerate(sames):
        if (index == 0) or (not same[:index].any()):
            indices.append(np.where(same[index:])[0] + index)

    routes = []
    for index in indices:
        route = []
        for i in index:
            if boulder:
                route.append(f"{df['Route'].iloc[i]} ({df['Rating'].iloc[i]} {df['Avg Stars'].iloc[i]} {votes[i]})")
            else:
                route.append(f"{df['Route'].iloc[i]} ({df['Rating'].iloc[i]} {df['Avg Stars'].iloc[i]} {votes[i]}) ({df['Route Type'].iloc[i]} {df['Pitches'].iloc[i]} {df['Length'].iloc[i]})")
        routes.append(' \n '.join(route))

    first_index = [index[0] for index in indices]

    locations = df['Location'].iloc[first_index]
    locations = [location.split('>')[0][:-1] for location in locations]

    latitudes = df['Area Latitude'].iloc[first_index]
    longitudes = df['Area Longitude'].iloc[first_index]
    urls = df['URL'].iloc[first_index]
    
    votes_most = votes[first_index]

    return pd.DataFrame(data={'Route': routes, 'Location': locations, 'Latitude': latitudes, 'Longitude': longitudes, 'URL': urls}), votes_most


def process_problems(filename: pd.DataFrame, 
                     vote_threshold=2, 
                     vote_popular_threshold=20, 
                     boulder=True):
    """processes the problems and group them into boulders/crags based on spatial similarity

    Args:
        filename (str): the file name of the csv file to be processed (exported from mountain project)
        vote_threshold (int, optional): problems whose vote count below this threshold will be ignored. Defaults to 2.
        vote_split (int, optional): problems whose vote count above this threshold will be treated as popular problems. Defaults to 20.
        boulder (bool, optional): whether the problem is a boulder of roped problem. Defaults to True.
    """
    
    df = pd.read_csv(filename)
    votes = get_votes(df)

    df_processed, votes_most = build_df(df, votes, boulder)

    unpopular_mask = (votes_most >= vote_threshold) & (votes_most < vote_popular_threshold)
    popular_mask = (votes_most >= vote_popular_threshold)
    
    df_processed.loc[unpopular_mask].to_csv(filename[:-4] + '_processed.csv', index=False)
    df_processed.loc[popular_mask].to_csv(filename[:-4] + '_processed_popular.csv', index=False)


filenames = ['jtree_boulders.csv']
filenames = [os.path.join('data', filename) for filename in filenames]
for filename in filenames:
    process_problems(filename)