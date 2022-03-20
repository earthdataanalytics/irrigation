#!/usr/bin/env python
# coding: utf-8

# ## Description

# This notebook is used to train a RandomForestClassifier on the ET data
#
# The SEBAL calculations for ET are leveraged from https://github.com/gee-hydro/geeSEBAL
#
# Usage:
#
#     1) Pass in the datafile to use (should be located at path ../raw_data/)


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

import os
import joblib
from datetime import datetime
from tqdm.notebook import tqdm

import matplotlib.pyplot as plt
import seaborn as sns

# custom libraries
import utils

# ## Load, transform and cleanse data

def main(datafile=None,
        filter_ndvi=True,
        filter_rain=True,
        inpath='',
        outpath='',
        calc_ET_region=False,
        save_model=True):
    data_filename = datafile

    if not os.path.exists(inpath + data_filename):
        print('Missing input datafile')

    df = pd.read_pickle(inpath + data_filename)

    out_foldername = data_filename.split('.')[0]
    path = outpath + out_foldername + '/'

    if not os.path.exists(outpath):
        os.mkdir(outpath)
    if not os.path.exists(outpath+out_foldername):
        os.mkdir(outpath+out_foldername)
    if not os.path.exists(path):
        os.mkdir(path)

    # ## Setup stats collecting

    statsfilename = path + 'summary_stats.json'
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    out_stats = {
        'dataname': out_foldername,
        'runtime': ts
    }
    if os.path.exists(statsfilename):
        with open(statsfilename, 'r', encoding='utf-8') as f:
            out_stats = json.load(f)

    # ## Apply filters

    # ##### Remove low NDVI
    if filter_ndvi:
        out_stats['num_ndvi_filtered_out_rf'] = int((df.NDVI >= 0.2).sum())
        df = df[df.NDVI >= 0.2] # keep data points where NDVI > threshold
                                # threshold discussed in team meetings on 22 & 25 Feb 2022

    # ##### Retain data when no precipitation in prior X days
    if filter_rain:
        out_stats['num_rain_filtered_out_rf'] = int((df.last_rain > 3).sum())
        df = df[df.last_rain > 3] # threshold defined in team meeting on 22 Feb 2022


    # ## Train model

    # ##### Setup columns to use
    cols = ['ET_24h', 'NDVI', 'LandT_G', 'last_rain', 'sum_precip_priorX', 'mm', 'yyyy', 'loc_idx', 'date']
    if calc_ET_region:
        cols[0] = = 'ET_24h_R'
    num_cols_rf = 6

    # ##### Setup training/validation dataset
    train_val_data = df.dropna(subset=cols)
    out_stats['num_samples_train_total'] = int(len(train_val_data)))

    X = train_val_data[cols]
    y = train_val_data['type']

    strat = train_val_data[['type']]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=strat)

    out_stats['num_samples_train_irr'] = int(len(y_train[y_train == 'Irrigated'])))
    out_stats['num_samples_train_rain'] = int(len(y_train[y_train=='Rainfed'])))

    out_stats['num_samples_test_irr'] = int((y_test == 'Irrigated').sum())
    out_stats['num_samples_test_rain'] = int((y_test == 'Rainfed').sum())

    classifier = RandomForestClassifier()
    classifier.fit(X_train[cols[:num_cols_rf]], y_train)

    X_test_sub = X_test[cols[:num_cols_rf]]
    out_stats['score_rf'] = float(classifier.score(X_test_sub, y_test))


    # ## Save trained model
    if save_model:
        joblib.dump(classifier, outpath + data_filename + "_rf_model.pkl", compress=3)


    # ## Save summary statistics
    filename = path + 'summary_stats.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(out_stats, f, ensure_ascii=False, indent=4)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datafile', required=True, help='Filename of ET data to process')
    parser.add_argument('--filter_ndvi', required=False, default=True, help='Use NDVI filter')
    parser.add_argument('--filter_rain', required=False, default=True, help='Use Rain filter')
    parser.add_argument('--calc_ET_region', required=False, default=False, help='Use regionalized ET')
    parser.add_argument('--inpath', required=False, default='../../runs/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../../runs/', help='Path for output files')
    parser.add_argument('--save_model', required=False, default=True, help='Save model or not')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    main(**vars(opt))
