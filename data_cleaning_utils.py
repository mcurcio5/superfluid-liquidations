import pandas as pd


def clean_imported_df(df):
    df = df.drop(columns=['Unnamed: 0'])
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    return df