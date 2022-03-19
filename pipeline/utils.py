import pandas as pd
import json

def baseETtransforms(df):
    # Convert LandT_G from Kelvin to Celsius
    df.LandT_G = df.LandT_G - 273.15

    # Convert date column from string to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Split .geo into latitude and longitude columns
    df['longitude'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][0])
    df['latitude'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][1])
    df.drop(['.geo', 'system:band_names', 'system:bands', 'version'], axis=1, inplace=True)

    # Convert types
    df.ET_24h = df.ET_24h.astype(float)
    df.loc_type = df.loc_type.astype(int)

    # Add year and month columns
    df['yyyy'] = df['date'].dt.strftime('%Y')
    df['mm'] = df['date'].dt.strftime('%m')

    return df

def baseETcleanse(df):
    num_errs = len(df[df.ET_24h < -2])
    return df[df['ET_24h'] > -2], num_errs

def generateETlocationLabels(df):
    df['loc_idx_tmp'] = df['longitude'].astype(str) + ', ' + df['latitude'].astype(str)

    num_locs = len(df['loc_idx_tmp'].unique())
    for i in range(num_locs):
        vals = df['loc_idx_tmp'].unique()[i]
        df.loc[df['loc_idx_tmp'] == vals, 'loc_idx'] = int(i)

    df.drop(['loc_idx_tmp'], axis=1, inplace=True)
    return df
