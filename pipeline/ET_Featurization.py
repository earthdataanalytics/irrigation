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


#!pip install earthengine-api
#!pip install geemap
#!pip install geopandas

import argparse
import sys

import ee
#service_account = 'data-access@second-impact-342800.iam.gserviceaccount.com'
#creds = ee.ServiceAccountCredentials(service_account, '../second-impact-342800-51af159903ca.json')
#ee.Initialize(creds)

import numpy as np
import pandas as pd
import json

from zipfile import ZipFile
import os
import glob
import joblib
from datetime import datetime
from tqdm import tqdm

# custom libraries
import utils

import logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    filename='et_featurization.log',
                    filemode='w')

def generateFeatures(datafile=None,
            nofilterndvi=False,
            nofilterrain=False,
            inpath='',
            outpath=''):

    filter_ndvi = not nofilterndvi
    filter_rain = not nofilterrain

    # ## Load, transform and cleanse data
    df = pd.DataFrame()
    zf = ZipFile(inpath + datafile)
    files = zf.filelist
    for file in tqdm(files):
        try:
            tmp = pd.read_csv(zf.open(file))
            df = pd.concat([df, tmp], ignore_index=True)
        except pd.errors.EmptyDataError:
            pass
        except:
            logging.error(f' in file {file.filename}')

    df = utils.baseETtransforms(df)
    df, num_ET_err = utils.baseETcleanse(df)
    df = utils.generateETlocationLabels(df)

    path = utils.setupOutputPaths(datafile, outpath)

    statsfilename = path + 'summary_stats.json'
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    out_stats = {
        'dataname': datafile,
        'runtime': ts
    }
    if os.path.exists(statsfilename):
        with open(statsfilename, 'r', encoding='utf-8') as f:
            out_stats = json.load(f)
    else:
        out_stats['num_samples'] = int(len(df))
        out_stats['num_blank_ET_samples'] = int(df.ET_24h.isna().sum())
        out_stats['num_locations'] = int(len(df['loc_idx'].unique()))
        out_stats['num_ET_too_low'] = int(num_ET_err)


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
    df_features['sum_precip_priorX'] = df_features.precip.apply(lambda x: sum([float(y) for y in x.strip('][').split(', ')][:3]) if isinstance(x, str) else float(x))


    # ##### Number of days since last precipitation
    rain_threshold = 0.254 # 0.254 mm = 0.01 inches of rainfall in a day, source:  Paolo
    def findFirstPrecip(x):
        if isinstance(x, str):
            # values of 10+ indicate that the date of last rain was outside the number of weather days available in the data
            y1 = [float(y) for y in x.strip('][').split(', ')]
            y2 = np.where(np.array(y1) > rain_threshold)[0][:1]
            y3 = y2.item() if len(y2)>0 else 9
            return y3 + 1
        else:
            return 0 # the precip variable did not contain multiple sample dates

    df_features['last_rain'] = df_features.precip.apply(findFirstPrecip)
    last_rain_present = df_features['last_rain'].sum() > 0


    # ##### Remove low NDVI
    if filter_ndvi:
        out_stats['num_ndvi_filtered_out'] = int((df_features.NDVI < 0.2).sum())
        df_features = df_features[df_features.NDVI >= 0.2] # keep data points where NDVI > threshold
                                            # threshold discussed in team meetings on 22 & 25 Feb 2022


    # ##### Retain data when no precipitation in prior X days
    if filter_rain and last_rain_present:
        out_stats['num_rain_filtered_out'] = int((df_features.last_rain > 3).sum())
        df_features = df_features[df_features.last_rain > 3] # threshold defined in team meeting on 22 Feb 2022


    # ##### Regionalized ET_24h score: ET_24h_R
    if 'ET_R_min' in df_features.columns:
        df_features['ET_24h_R'] = (df_features['ET_24h'].subtract(df_features['ET_R_min'])) \
                           .divide(
                                   df_features['ET_R_max'].subtract(df_features['ET_R_min']).replace(0,np.nan)
                                  )


    # ## Save working dataframe for next step in pipeline
    df_features.to_pickle(path + 'features.pkl')


    # ## Save summary statistics
    for key in terrain_types.keys():
        out_stats['num_'+key+'_post_filters'] = int(len(df_features['type'] == key))

    filename = path + 'summary_stats.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(out_stats, f, ensure_ascii=False, indent=4)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datafile', required=True, help='Filename of ET data to process')
    parser.add_argument('--nofilterndvi', action='store_true', help='Disable NDVI filter')
    parser.add_argument('--nofilterrain', action='store_true', help='Disable Rain filter')
    parser.add_argument('--inpath', required=False, default='../raw_data/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../runs/', help='Path for output files')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    generateFeatures(**vars(opt))
