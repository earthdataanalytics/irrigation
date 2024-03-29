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
#service_account = 'data-access@second-impact-342800.iam.gserviceaccount.com'
#creds = ee.ServiceAccountCredentials(service_account, '../second-impact-342800-51af159903ca.json')
#ee.Initialize(creds)
#import geemap.foliumap as geemap

import numpy as np
import pandas as pd
import json

from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, f1_score

import os
import joblib
from datetime import datetime
from tqdm import tqdm

import matplotlib.pyplot as plt
import seaborn as sns

# custom libraries
import utils

# ## Load, transform and cleanse data

def fit(datafile=None,
        nofilterndvi=False,
        nofilterrain=False,
        inpath='',
        outpath='',
        calcETregion=False,
        nosavemodel=False):

    filter_ndvi = not nofilterndvi
    filter_rain = not nofilterrain
    save_model = not nosavemodel

    infilename = inpath + '/features.pkl'
    if not os.path.exists(infilename):
        print('Missing input datafile')

    df = pd.read_pickle(infilename)

    path = utils.setupOutputPaths(datafile, outpath)

    # ## Setup stats collecting

    statsfilename = path + 'summary_stats.json'
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    out_stats = {
        'dataname': datafile,
        'runtime': ts
    }
    if os.path.exists(statsfilename):
        with open(statsfilename, 'r', encoding='utf-8') as f:
            out_stats = json.load(f)

    # ## Apply filters

    # ##### Remove low NDVI
    out_stats['filter_ndvi'] = False
    if filter_ndvi:
        out_stats['filter_ndvi'] = True
        out_stats['num_ndvi_filtered_out_rf'] = int((df.NDVI >= 0.2).sum())
        df = df[df.NDVI >= 0.2] # keep data points where NDVI > threshold
                                # threshold discussed in team meetings on 22 & 25 Feb 2022

    # ##### Retain data when no precipitation in prior X days
    out_stats['filter_rain'] = False
    if filter_rain:
        out_stats['filter_rain'] = True
        out_stats['num_rain_filtered_out_rf'] = int((df.last_rain > 3).sum())
        df = df[df.last_rain > 3] # threshold defined in team meeting on 22 Feb 2022


    # ## Train model

    # ##### Setup columns to use
    et_var = 'ET_24h'
    if calcETregion:
        et_var = 'ET_24h_R'
    out_stats['et_var'] = et_var
    out_stats['temporality'] = 'all_months'

    cols = [et_var, 'NDVI', 'LandT_G', 'last_rain', 'sum_precip_priorX', 'mm', 'yyyy', 'loc_idx', 'date']
    num_cols_rf = 5 # changed from 6 on 2022.08.02 to remove yyyy from predictors

    use_gridsearchcv = False # flag added to code in July 2022.
                              # Disabled on 2022.08.02 because accuracy and f1 score not correctly output.

    # ##### Setup training/validation dataset
    train_val_data = df.dropna(subset=cols)
    out_stats['num_samples_train_total'] = int(len(train_val_data))

    train_val_data.loc[train_val_data['type']=='Irrigated', 'type'] = 1
    train_val_data.loc[train_val_data['type']=='Rainfed', 'type'] = 0

    X = train_val_data[cols]
    y = train_val_data['type']
    y = y.astype('int')

    if use_gridsearchcv:
        X_train = X_test = X
        y_train = y_test = y
    else:
        strat = train_val_data[['type']]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=strat)

        out_stats['num_samples_train_irr'] = int(len(y_train[y_train == 0]))
        out_stats['num_samples_train_rain'] = int(len(y_train[y_train==1]))

        out_stats['num_samples_test_irr'] = int((y_test == 0).sum())
        out_stats['num_samples_test_rain'] = int((y_test == 1).sum())

    # ##### Create and train model
    clf = RandomForestClassifier()

    if use_gridsearchcv:
        # ##### Cross-Validation and GridSearch
        param_grid = {
                     'n_estimators': [10, 50, 100],
                     'max_depth': [4, 8, None],
                     'min_samples_split': [2, 4, 8],
                     'min_samples_leaf': [1, 2, 4]
                 }
        classifier = GridSearchCV(clf, param_grid, scoring='f1', n_jobs=-1, cv=10) # uses Stratified k-fold

    else:
        classifier = clf

    classifier.fit(X_train[cols[:num_cols_rf]], y_train)

    # ##### Score model
    X_test_sub = X_test[cols[:num_cols_rf]]
    y_pred = classifier.predict(X_test_sub)

    if use_gridsearchcv:
        out_stats['rf_f1'] = classifier.best_score_
    else:
        out_stats['rf_accuracy'] = float(classifier.score(X_test_sub, y_test))
        f1_rf = f1_score(y_test, y_pred, pos_label=1)
        out_stats['rf_f1'] = float(f1_rf)

    # ## Create plots

    # ##### Confusion Matrix
    cm_plot = ConfusionMatrixDisplay.from_estimator(classifier, X_test_sub, y_test, normalize='true', values_format='.2f')
    cm_plot.plot()
    plt.savefig(path + 'rf_cm.png')

    # ##### Decision Tree
    if False: # not use_gridsearchcv: # causes crash
        fig = plt.figure(figsize=(25,20))
        dt_plot = tree.plot_tree(classifier.estimators_[0], feature_names=cols, class_names=y_test.unique(),
                      max_depth=3, proportion=False, rounded=True, filled = True)
        plt.savefig(path + 'rf_tree.png')
    plt.clf()

    # ##### Histogram of False Negatives
    fig = plt.figure(figsize=(10,5))
    mask1 = y_test != y_pred
    mask2 = y_test == 0 # Irrigated
    false_neg_idx = X_test[mask1 & mask2].index
    tmp_data = train_val_data.loc[false_neg_idx].sort_values('loc_idx').groupby('loc_idx').count()[et_var]
    if len(tmp_data.index) > 0:
        fn_plot = tmp_data.plot.bar()
        plt.title('Histogram of False Negatives')
        plt.savefig(path + 'rf_hist_fn_by_loc.png')

    # by month
    tmp_data = train_val_data.loc[false_neg_idx].sort_values('loc_idx').groupby('mm').count()[et_var]
    if len(tmp_data.index) > 0:
        fn_plot = tmp_data.plot.bar()
        plt.title('Histogram of False Negatives')
        plt.savefig(path + 'rf_hist_fn_by_month.png')

    # ##### Histogram of False Positives
    mask2 = y_test != 0 # Irrigated
    false_pos_idx = X_test[mask1 & mask2].index
    tmp_data = train_val_data.loc[false_pos_idx].sort_values('loc_idx').groupby('loc_idx').count()[et_var]
    if len(tmp_data.index) > 0:
        fp_plot1 = tmp_data.plot.bar()
        plt.title('Histogram of False Positives')
        plt.savefig(path + 'rf_hist_fp_by_loc.png')

    # by month
    tmp_data = train_val_data.loc[false_pos_idx].sort_values('loc_idx').groupby('mm').count()[et_var]
    if len(tmp_data.index) > 0:
        fp_plot2 = tmp_data.plot.bar()
        plt.title('Histogram of False Positives')
        plt.savefig(path + 'rf_hist_fp_by_month.png')


    # ## Save training and test data

    # test data
    if save_model:
        out = X_test
        out.loc[:, 'true_label'] = y_test
        out.loc[:, 'pred_label'] = y_pred
        out.to_pickle(path + 'testdata.pkl')

    # training data
    if save_model:
        out = X_train
        out.loc[:, 'true_label'] = y_train
        out.loc[:, 'pred_label'] = classifier.predict(X_train[cols[:num_cols_rf]])
        out.to_pickle(path + 'traindata.pkl')


    # ## Save trained model
    if save_model:
        joblib.dump(classifier, path + "model_rf.pkl", compress=3)


    # ## Save summary statistics
    out_stats['exp_ref'] = path.split('/')[-2]

    filename = path + 'summary_stats.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(out_stats, f, ensure_ascii=False, indent=4)


    # ## Save best model

    save_as_best = False
    if save_model:
        bestpath = '/'.join(path.split('/')[:-2]) + '/best/'
        statsfilename = bestpath + 'summary_stats.json'
        if not os.path.exists(bestpath):
            os.mkdir(bestpath)
            save_as_best = True

        elif os.path.exists(statsfilename):
            with open(statsfilename, 'r', encoding='utf-8') as f:
                priorbest = json.load(f)

            if out_stats['rf_f1'] > priorbest['rf_f1']:
                save_as_best = True

        if save_as_best:
            # save summary stats
            with open(statsfilename, 'w', encoding='utf-8') as f:
                json.dump(out_stats, f, ensure_ascii=False, indent=4)

            joblib.dump(classifier, bestpath + "model_rf.pkl", compress=3)

    plt.close('all')


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--datafile', required=True, help='Filename of ET data to process')
    parser.add_argument('--nofilterndvi', action='store_true', help='Disable NDVI filter')
    parser.add_argument('--nofilterrain', action='store_true', help='Disable Rain filter')
    parser.add_argument('--calcETregion', action='store_true', help='Use regionalized ET')
    parser.add_argument('--inpath', required=False, default='../runs/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../runs/', help='Path for output files')
    parser.add_argument('--nosavemodel', action='store_true', help='Disable saving model')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    try:
        fit(**vars(opt))
    except:
        print('fit error')
