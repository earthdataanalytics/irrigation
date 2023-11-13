import pandas as pd
import json
import glob
import os
import ee
import geemap

def setupOutputPaths(datafile, outpath):
    if not os.path.exists(outpath):
        os.mkdir(outpath)

    if '/exp' in outpath.split('.')[-1]:
        return outpath

    data_filename = datafile.split('.')[0]
    exppath = 'exp01/'
    rootpaths = glob.glob(outpath + data_filename)

    if rootpaths:
        exppaths = glob.glob(outpath + data_filename + '/exp*')
        if exppaths:
            lastnum = int(max(exppaths)[-2:]) + 1
            exppath = f'exp{lastnum:02d}/'
    else:
        os.mkdir(outpath + data_filename)

    newpath = outpath + data_filename + '/' + exppath
    os.mkdir(newpath)

    return newpath


def baseETtransforms(df):
    # Convert LandT_G from Kelvin to Celsius
    # Commented out by BCJ on 2023.11.12 to avoid re-converting when loading training back data to GEE for GEE classifier training
    # df.LandT_G = df.LandT_G - 273.15

    # Convert date column from string to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Split .geo into latitude and longitude columns
    df['longitude'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][0])
    df['latitude'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][1])
    df.drop(['.geo', 'system:index', 'system:band_names', 'system:bands', 'version', 'status'], errors='ignore', axis=1, inplace=True)

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

def train_test_split(data_fc):
    split = 0.8
    with_random = data_fc.randomColumn('random', 112358)
    train_partition = with_random.filter(ee.Filter.lt('random', split))
    test_partition = with_random.filter(ee.Filter.gte('random', split))
    return dict(train_partition=train_partition, test_partition=test_partition)
