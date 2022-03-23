#!/usr/bin/env python
# coding: utf-8


import argparse
import joblib
import sys
import os
import glob
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score


def eval(inpath='',
        outpath=''):

    if not os.path.exists(outpath):
        os.mkdir(outpath)

    paths = glob.glob(inpath+'*')


    # for each file
    #       load the best model for that file
    #       then for each remaining file
    #           load the train/test data for that file
    #           merge train/testdata
    #           Score
    #           save results in dataframe
    #
    # save score dataframe

    evalmodelname = []
    evaldataname = []
    expref = []
    filtndvi = []
    filtrain = []
    etvar = []
    tempor = []
    rf_accuracy = []
    rf_f1 = []

    for path_outer in tqdm(paths):

        bestmodel_path = path_outer + '/best/'
        bestmodel = joblib.load(bestmodel_path + "model_rf.pkl")

        with open(bestmodel_path + 'summary_stats.json', 'r', encoding='utf-8') as f:
            bestmodel_stats = json.load(f)

        exp_ref = bestmodel_stats['exp_ref']
        et_var = bestmodel_stats['et_var']

        for path_inner in tqdm(paths, leave=False):
            testdatapath = path_inner +'/'+ exp_ref + '/testdata.pkl'
            df_test = pd.read_pickle(testdatapath)

            if path_inner != path_outer:
                traindatapath = path_inner +'/'+ exp_ref + '/traindata.pkl'
                df_train = pd.read_pickle(traindatapath)
                df_test = pd.concat([df_test, df_train])

            cols = [et_var, 'NDVI', 'LandT_G', 'last_rain', 'sum_precip_priorX', 'mm', 'yyyy', 'loc_idx', 'date']
            num_cols_rf = 6

            X_test = df_test[cols[:num_cols_rf]]
            y_test = df_test['true_label']

            rf_accuracy.append(bestmodel.score(X_test, y_test))

            y_pred = bestmodel.predict(X_test)
            rf_f1.append(f1_score(y_test, y_pred, pos_label='Irrigated'))

            evalmodelname.append(path_outer.split('/')[-1])
            evaldataname.append(path_inner.split('/')[-1])
            expref.append(bestmodel_stats['exp_ref'])
            filtndvi.append(bestmodel_stats['filter_ndvi'])
            filtrain.append(bestmodel_stats['filter_rain'])
            etvar.append(bestmodel_stats['et_var'])
            tempor.append(bestmodel_stats['temporality'])

    df_results = pd.DataFrame({
            'eval_model': evalmodelname,
            'eval_data': evaldataname,
            'exp_ref': expref,
            'filter_ndvi': filtndvi,
            'filter_rain': filtrain,
            'et_var': etvar,
            'temporality': tempor,
            'rf_accuracy': rf_accuracy,
            'rf_f1': rf_f1,
    })

    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    outfilename = outpath + f'crosseval_{ts}.csv'
    df_results.to_csv(outfilename)
    print('Results save to', outpath)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inpath', required=False, default='../../runs/', help='Path for input files')
    parser.add_argument('--outpath', required=False, default='../../crosseval/', help='Path for output files')
    return parser.parse_args()

if __name__ == "__main__":
    opt = parse_opt()
    eval(**vars(opt))
