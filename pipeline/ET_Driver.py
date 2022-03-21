#!/usr/bin/env python
# coding: utf-8

# ## Description

# This notebook is used to run the end-to-end Irrigation Processing pipeline
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

from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, f1_score

import os
import joblib
from datetime import datetime
from tqdm.notebook import tqdm

import matplotlib.pyplot as plt
import seaborn as sns

# custom libraries
import utils
import ET_EDA as eda
import ET_Featurization as feat
import ET_Train_RF as trainRF


def run(aoi=None,
        datafile=None,
        no_filter_ndvi=False,
        no_filter_rain=False,
        inpath='',
        outpath='',
        calc_ET_region=False,
        extract=False,
        no_eda=False,
        infer=False,
        no_save_model=True,
        verbose=False):

    if extract:
        if (not aoi) or (not os.path.exists(aoi)):
            print('Error: Valid AOI input file required')
            exit()

        pass
        print('Extract Step')
        #datafile = extractET.retrieve(aoi, ...) # to be completed
        #datafile should be zipped and saved in inpath (raw data)

    if (not datafile) or (not os.path.exists(inpath + datafile)):
        print('Error: Valid input data file required')
        exit()

    if (not no_eda):
        print('EDA Step')
        eda.analyze(datafile=datafile, inpath=inpath, outpath=outpath, verbose=verbose)

    print('Featurization Step')
    feat.generateFeatures(datafile=datafile, inpath=inpath, outpath=outpath,
                    no_filter_ndvi=no_filter_ndvi, no_filter_rain=no_filter_rain)

    if not infer:
        print('Train Step')
        # requires setting inpath=outpath
        trainRF.fit(datafile=datafile, inpath=outpath, outpath=outpath,
                    no_filter_ndvi=no_filter_ndvi, no_filter_rain=no_filter_rain,
                    calc_ET_region=calc_ET_region, no_save_model=no_save_model)

    if infer:
        pass
        print('Infer Step')
        #serveET.predict(aoi, ...) # to be completed


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aoi', required=False, help='Area of Interest json filename')
    parser.add_argument('--datafile', required=False, help='Filename of ET data to process')
    parser.add_argument('--no_filter_ndvi', required=False, default=True, help='Disable NDVI filter')
    parser.add_argument('--no_filter_rain', required=False, default=True, help='Disable Rain filter')
    parser.add_argument('--calc_ET_region', action='store_true', help='Use regionalized ET')
    parser.add_argument('--extract', action='store_true', help='Extract samples for training')
    parser.add_argument('--no_eda', action='store_true', help='Disable EDA step')
    parser.add_argument('--infer', action='store_true', help='Serve model for inference')
    parser.add_argument('--inpath', required=False, default='../../raw_data/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../../runs/', help='Path for output files')
    parser.add_argument('--no_save_model', required=False, default=True, help='Disable saving model')
    parser.add_argument('--verbose', action='store_true', help='Print output to console')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    run(**vars(opt))
