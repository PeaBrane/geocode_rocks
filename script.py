import os
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from rusty_scrapper import fetch_votes_py


def build_df(df: pd.DataFrame, votes: np.array, boulder=True, tol=1e-7):
    latitudes, longitudes = (
        df["Area Latitude"].to_numpy(),
        df["Area Longitude"].to_numpy(),
    )
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
                route.append(
                    f"{df['Route'].iloc[i]} ({df['Rating'].iloc[i]} {df['Avg Stars'].iloc[i]} {votes[i]})"
                )
            else:
                route.append(
                    f"{df['Route'].iloc[i]} ({df['Rating'].iloc[i]} {df['Avg Stars'].iloc[i]} {votes[i]}) ({df['Route Type'].iloc[i]} {df['Pitches'].iloc[i]} {df['Length'].iloc[i]})"
                )
        routes.append(" \n ".join(route))

    first_index = [index[0] for index in indices]

    locations = df["Location"].iloc[first_index]
    locations = [location.split(">")[0][:-1] for location in locations]

    latitudes = df["Area Latitude"].iloc[first_index]
    longitudes = df["Area Longitude"].iloc[first_index]
    urls = df["URL"].iloc[first_index]

    votes_most = votes[first_index]

    return (
        pd.DataFrame(
            data={
                "Route": routes,
                "Location": locations,
                "Latitude": latitudes,
                "Longitude": longitudes,
                "URL": urls,
            }
        ),
        votes_most,
    )


def process_problems(filename: pd.DataFrame, vote_threshold=2, boulder=True):
    """processes the problems and group them into boulders/crags based on spatial similarity

    Args:
        filename (str): the file name of the csv file to be processed (exported from mountain project)
        vote_threshold (int, optional): problems whose vote count below this threshold will be ignored. Defaults to 2.
        vote_split (int, optional): problems whose vote count above this threshold will be treated as popular problems. Defaults to 20.
        boulder (bool, optional): whether the problem is a boulder of roped problem. Defaults to True.
    """
    df = pd.read_csv(filename)
    votes = fetch_votes_py(df["URL"].tolist())

    df_processed, votes_most = build_df(df, votes, boulder)
    mask = votes_most >= vote_threshold
    df_processed, votes_most = df_processed.loc[mask], votes_most[mask]

    votes_most_log = np.log10(votes_most)
    df_processed["votes_most_log"] = votes_most_log
    df_processed.iloc[::-1].to_csv(filename[:-4] + "_processed.csv", index=False)

    # unpopular_mask = (votes_most >= vote_threshold) & (votes_most < vote_popular_threshold)
    # popular_mask = (votes_most >= vote_popular_threshold)

    # df_processed.loc[unpopular_mask].to_csv(filename[:-4] + '_processed.csv', index=False)
    # df_processed.loc[popular_mask].to_csv(filename[:-4] + '_processed_popular.csv', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Mountain Project data to group problems by location.')
    parser.add_argument('filename', type=str, help='CSV file to process (exported from Mountain Project)')
    
    args = parser.parse_args()
    # Get the directory where the script is located
    script_dir = Path(__file__).parent.absolute()
    # Construct absolute path for the input file
    filename = script_dir / "data" / args.filename
    process_problems(str(filename))
