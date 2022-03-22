#!/usr/bin/env python
# coding: utf-8

# ## Description

# This notebook is used to run the end-to-end Irrigation Processing pipeline
#
# The SEBAL calculations for ET are leveraged from https://github.com/gee-hydro/geeSEBAL
#
# Usage:
#
#     python ET_Driver.py --datafile ET_20220308_wesus8_WA.zip
# or
#     python ET_Driver.py --aoi boundary.json



# ## Setup Notebook

# #### Setup Google Earth Engine libraries

# This notebook requires the installation of:
# - earthengine
# - geemap
# - geopandas
# - hdbscan

import argparse
import sys
import os
import glob

# custom libraries
import ET_EDA as eda
import ET_Featurization as feat
import ET_Train_RF as trainRF
import utils

def run(aoi=None,
        datafile=None,
        nofilterndvi=False,
        nofilterrain=False,
        inpath='',
        outpath='',
        calcETregion=False,
        extract=False,
        no_eda=False,
        infer=False,
        no_save_model=True,
        verbose=False):

    if extract:
        if (not aoi) or (not os.path.exists(aoi)):
            print('Error: Valid AOI input file required')
            exit()

        print('Extract Step - not yet implemented')
        print('Use interactive notebook version')
        exit()
        #datafile = extractET.retrieve(aoi, ...) # to be completed
        #datafile should be zipped and saved in inpath (raw data)

    if (not datafile) or (not os.path.exists(inpath + datafile)):
        print('Error: Valid input data file required')
        exit()

    newpath = utils.setupOutputPaths(datafile, outpath)

    if (not no_eda):
        print('EDA Step')
        eda.analyze(datafile=datafile, inpath=inpath, outpath=newpath, verbose=verbose)

    print('Featurization Step')
    feat.generateFeatures(datafile=datafile, inpath=inpath, outpath=newpath,
                    nofilterndvi=nofilterndvi, nofilterrain=nofilterrain)

    if not infer:
        print('Train Step')
        # requires setting inpath=outpath
        trainRF.fit(datafile=datafile, inpath=newpath, outpath=newpath,
                    nofilterndvi=nofilterndvi, nofilterrain=nofilterrain,
                    calcETregion=calcETregion, no_save_model=no_save_model)

    if infer:
        pass
        print('Infer Step')
        #serveET.predict(aoi, ...) # to be completed


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aoi', required=False, help='Area of Interest json filename')
    parser.add_argument('--datafile', required=False, help='Filename of ET data to process')
    parser.add_argument('--nofilterndvi', required=False, default=True, help='Disable NDVI filter')
    parser.add_argument('--nofilterrain', required=False, default=True, help='Disable Rain filter')
    parser.add_argument('--calcETregion', action='store_true', help='Use regionalized ET')
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
