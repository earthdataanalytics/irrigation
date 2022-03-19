#!/usr/bin/env python
# coding: utf-8

# ## Description

# This notebook is used to produce summary EDA statistics and charts.
#
# The SEBAL calculations for ET are leveraged from https://github.com/gee-hydro/geeSEBAL
#
# The map displays labeled sample locations.
# - Irrigated locations are shown in Blue.
# - Rainfed locations are shown in Red.
#
# Usage:
#
#     1) Select the datafile to use (should be located at path ../raw_data/)

#data_filename = 'ET_20220308_wesus8_WA.zip'
#data_filename = 'ET_20220309_wesus9_CO.zip'
#data_filename = 'ET_20220314_easus11_IL.zip'
#data_filename = 'ET_20220315_wesus12_CA.zip'
#data_filename = 'ET_20220317_wesus13_OR.zip'
#data_filename = 'ET_20220318_wesus14_WA.zip'


# ## Setup Notebook

# #### Setup Google Earth Engine libraries

# This notebook requires the installation of:
# - earthengine
# - geemap
# - geopandas
# - hdbscan
# - ipympl (only for interactive charts with matplotlib)


#!pip install earthengine-api
#!pip install geemap
#!pip install geopandas


import argparse
import sys

import ee
#ee.Authenticate() # Uncomment this line when first running the notebook in a new environment
ee.Initialize()
#import geemap.foliumap as geemap

import numpy as np
import pandas as pd
import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
i
from zipfile import ZipFile
import os
import glob
import joblib
from tqdm.notebook import tqdm

import matplotlib.pyplot as plt
import seaborn as sns

# custom libraries
import utils


# ## Load, transform and cleanse data

def main(datafile=None):
    data_filename = datafile

    df = pd.DataFrame()
    files = ZipFile(data_filename).filelist
    for file in tqdm(files):
        df = pd.concat([df, pd.read_csv(zf.open(file))], ignore_index=True)

    df = utils.baseETtransforms(df)
    df = utils.generateETlocationLabels(df)

    out_foldername = data_filename.split('.')[0]
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    path = out_foldername + '/' + ts + '/'
    os.mkdir(path)

    # ## EDA

    out_stats = {
    }

    # ##### Basic counts
    out_stats['num_samples'] = len(df)
    out_stats['num_blank_ET_samples'] = df.ET_24h.isna().sum()
    out_stats['num_locations'] = len(df['loc_idx'].unique())

    out_stats['num_ok_irr_samples'] = len(df[(df.loc_type == 0) & (~df.ET_24h.isna())])
    out_stats['num_ok_rain_samples'] = len(df[(df.loc_type == 1) & (~df.ET_24h.isna())])

    # check for any dates where the location type changes between rainfed and irrigated
    #     - this was tested by manually changing a datapoint
    #     - it will show any rows where the type changed for a specific location
    df_tmp = df.sort_values(['loc_idx', 'date']).groupby(['loc_idx'])
    out_stats['num_type_changes'] = len(df[df_tmp.loc_type.diff() > 0])

    # inspect number of datapoints
    print(f'Total number of samples        {out_stats['num_samples']:>5}')
    print(f'Number of blank ET_24 samples  {out_stats['num_blank_ET_samples']:>5}')
    print(f'Number of locations            {out_stats['num_locations']:>5}')

    print(f'Number of OK irrigated samples {out_stats['num_ok_irr_samples']:>5}')
    print(f'Number of OK rainfed samples   {out_stats['num_ok_rain_samples']:>5}')

    print('Number of locations changing')
    print(f'    between Irr/Rain labels    {out_stats['num_type_changes']:>5}')

    # ##### Plots

    # histogram
    fig, ax = plt.subplots(1,3, figsize=(20,5))
    ax[0].hist(df.loc_idx)
    ax[1].hist(df.sort_values('yyyy').yyyy)
    ax[2].hist(df.sort_values('mm').mm)
    plt.show()
    plt.savefig(path + 'histogram.png')

    # NDVI
    df.sample(frac=1).boxplot(column='NDVI', by='loc_idx')
    plt.suptitle('')
    plt.savefig(path + 'ndvi.png')

    # ET daily
    df.sample(frac=1).boxplot(column='ET_24h', by='loc_idx')
    plt.suptitle('')
    plt.savefig(path + 'etdaily.png')

    # land temperature
    df.sample(frac=0.2).boxplot(column='LandT_G', by='loc_idx')
    plt.suptitle('')
    plt.savefig(path + 'landtemp.png')

    if False:
        # wind speed
        df.sample(frac=0.2).boxplot(column='ux_G', by='loc_idx')
        plt.suptitle('')
        plt.savefig(path + 'windspeed.png')

        # relative humidity
        df.sample(frac=0.2).boxplot(column='UR_G', by='loc_idx')
        plt.suptitle('')
        plt.savefig(path + 'humidity.png')

        # slope
        if 'slope' in df.columns:
            df.sample(frac=.2).boxplot(column='slope', by='loc_idx')
            plt.suptitle('')
            plt.savefig(path + 'slope.png')


        # air temperature
        df.sample(frac=0.2).boxplot(column='AirT_G', by='loc_idx')
        plt.suptitle('')
        plt.savefig(path + 'airtemp.png')


    # ## Save summary statistics
    filename = path + 'summary_stats.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(out_stats, f, ensure_ascii=False, indent=4)

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datafile', required=True, help='filename of ET data to process')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))
