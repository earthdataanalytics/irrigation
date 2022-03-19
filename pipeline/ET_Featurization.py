#!/usr/bin/env python
# coding: utf-8

# ## Description

# This notebook is used to generate features from the retrieved ET data.  These features are intended for model training and/or inference in other modules.
#
# The SEBAL calculations for ET are leveraged from https://github.com/gee-hydro/geeSEBAL
#
# The map displays labeled sample locations.
# - Irrigated locations are shown in Blue.
# - Rainfed locations are shown in Red.
#
# Usage:
#
#     1) Set toggles for which features to use
#     2) Select the datafile to use (should be located at path ../raw_data/)

# ## Setup Notebook

# #### Setup Google Earth Engine libraries

# This notebook requires the installation of:
# - earthengine
# - geemap
# - geopandas
# - hdbscan
# - ipympl (only for interactive charts with matplotlib)

# In[1]:


#!pip install earthengine-api
#!pip install geemap
#!pip install geopandas
#!pip install hdbscan
#!pip install ipympl

import argparse
import sys

import ee
#ee.Authenticate() # Uncomment this line when first running the notebook in a new environment
ee.Initialize()

import numpy as np
import pandas as pd
import json

from zipfile import ZipFile
import glob
import joblib
from datetime import datetime
from tqdm.notebook import tqdm

import matplotlib.pyplot as plt
import seaborn as sns

# custom libraries
import utils

def main(datafile=None,
            filter_ndvi=True,
            filter_rain=True,
            calc_ET_region=False,
            inpath='',
            outpath=''):

    data_filename = datafile

    # ## Load, transform and cleanse data
    df = pd.DataFrame()
    files = ZipFile(inpath + data_filename).filelist
    for file in tqdm(files):
        df = pd.concat([df, pd.read_csv(zf.open(file))], ignore_index=True)

    df = utils.baseETtransforms(df)
    df = utils.baseETcleanse(df)
    df = utils.generateETlocationLabels(df)

    out_foldername = data_filename.split('.')[0]
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = outpath + out_foldername + '/' + ts + '/'
    os.mkdir(path)

    # ## Feature Engineering
    df_features = df

    # ##### Add terrain-type label
    terrain_types = {
        'Irrigated': [0], # can contain multiple values
        'Rainfed':   [1], # can contain multiple values
    }
    df_features['type'] = np.nan
    for key in terrain_types:
        df_features.loc[df_features.loc_type.isin(terrain_types[key]), 'type'] = key
    df_features = df_features.dropna(subset=['type'])

    # Cumulative precipitation over prior X days
    df_features['sum_precip_priorX'] = df_features.precip.apply(lambda x: sum([float(y) for y in x.strip('][').split(', ')][:3]))


    # ##### Number of days since last precipitation
    rain_threshold = 0.254 # 0.254 mm = 0.01 inches of rainfall in a day, source:  Paolo
    def findFirstPrecip(x):
        # values of 10+ indicate that the date of last rain was outside the number of weather days available in the data
        y1 = [float(y) for y in x.strip('][').split(', ')]
        y2 = np.where(np.array(y1) > rain_threshold)[0][:1]
        y3 = y2.item() if len(y2)>0 else 9
        return y3 + 1

    df_features['last_rain'] = df_features.precip.apply(findFirstPrecip)

    # ##### Remove low NDVI
    if filter_ndvi:
        df_features = df_features[df_features.NDVI >= 0.2] # keep data points where NDVI > threshold
                                            # threshold discussed in team meetings on 22 & 25 Feb 2022

    # ##### Retain data when no precipitation in prior X days
    if filter_rain:
        df_features = df_features[df_features.last_rain > 3] # threshold defined in team meeting on 22 Feb 2022

    # ##### Regionalized ET_24h score: ET_24h_R
    df_features['ET_24h_R'] = (df_features['ET_24h'].subtract(df_features['ET_R_min']))                   .divide(
                               df_features['ET_R_max'].subtract(df_features['ET_R_min']).replace(0,np.nan)
                              )
    # ## Save working dataframe for next step in pipeline
    df_features.to_pickle(path + 'features.pkl')


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datafile', required=True, help='Filename of ET data to process')
    parser.add_argument('--filter_ndvi', required=False, default=True, help='Use NDVI filter')
    parser.add_argument('--filter_rain', required=False, default=True, help='Use Rain filter')
    parser.add_argument('--calc_ET_region', required=False, default=False, help='Use regionalized ET')
    parser.add_argument('--inpath', required=False, default='../raw_data/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../runs/', help='Path for input files')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))
