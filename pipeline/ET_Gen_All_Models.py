#!/usr/bin/env python
# coding: utf-8

# ## Description

# This notebook is used to run variations of different input parameters for
# the end-to-end Irrigation Processing pipeline
#
# The SEBAL calculations for ET are leveraged from https://github.com/gee-hydro/geeSEBAL
#
# Usage:
#
# this will run the pipeline for all datafiles found in inpath
#     python ET_Gen_All_Models.py --all
# or
#     python ET_Gen_All_Models.py --datafile ET_20220308_wesus8_WA.zip

import argparse
import sys
import os
import glob
from tqdm import tqdm

# custom libraries
import ET_Driver as driver

def run(all=False,
        datafile=None,
        inpath='',
        outpath='',
        showPlot=False):

    if (not all) and (not datafile):
        print('Requires either specifying a datafile or using the --all flag')
        exit()

    files = []
    if datafile:
        files.append(datafile)
    else:
        files = glob.glob(inpath+'*')

    ndvi_opt = [False, True]
    rain_opt = [False, True]
    calc_ET_region_opt = [False, True]

    for file in tqdm(files):
      for nopt in tqdm(ndvi_opt, leave=False):
        for ropt in tqdm(rain_opt, leave=False):
          for copt in tqdm(calc_ET_region_opt, leave=False):
              filename = file.split('/')[-1]
              driver.run(datafile=filename,
                          inpath=inpath,
                          outpath=outpath,
                          nofilterndvi=nopt,
                          nofilterrain=ropt,
                          calcETregion=copt,
                          showPlot=showPlot)

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='Generate models for all data files in inpath')
    parser.add_argument('--datafile', required=False, help='Filename of ET data to process')
    parser.add_argument('--inpath', required=False, default='../raw_data/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../runs/', help='Path for output files')
    parser.add_argument('--showPlot', action='store_true', help='Display EDA plots (this will freeze processing until popup window is dismissed)')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    run(**vars(opt))
