#!/usr/bin/env python

from __future__ import division
from sklearn.metrics import log_loss
from sklearn.ensemble import RandomForestClassifier as RF

import argparse
import logging
import numpy as np
import os
import time

from const import SEED
from kaggler.data_io import load_data


def train_predict(train_file, test_file, predict_valid_file, predict_test_file,
                  cv_id_file,
                  n_est, depth, n_fold=5, retrain=False):

    feature_name = os.path.basename(train_file)[:-4]
    logging.basicConfig(format='%(asctime)s   %(levelname)s   %(message)s',
                        level=logging.DEBUG,
                        filename='rf_{}_{}_{}.log'.format(n_est,
                                                          depth,
                                                          feature_name))


    logging.info('Loading training and test data...')
    X, y = load_data(train_file, dense=True)
    X_tst, _ = load_data(test_file, dense=True)

    clf = RF(n_estimators=n_est, max_depth=depth, n_jobs=20, random_state=2016)

    logging.info('Loading CV Ids')
    cv_id = np.loadtxt(cv_id_file)

    logging.info('Cross validation...')
    P_val = np.zeros(X.shape[0])
    P_tst = np.zeros(X_tst.shape[0])
    for i in range(1, n_fold + 1):
        logging.info("cv %d" % i)
        i_trn = np.where(cv_id != i)[0]
        i_val = np.where(cv_id == i)[0]
        logging.debug('train: {}'.format(X[i_trn].shape))
        logging.debug('valid: {}'.format(X[i_val].shape))
        logging.debug(len(set(y[i_trn])))

        clf.fit(X[i_trn], y[i_trn])
        P_val[i_val] = clf.predict_proba(X[i_val])[:, 1]
        if not retrain:
            P_tst += clf.predict_proba(X_tst)[:,1] / n_fold

    if retrain:
        logging.info('Retraining with 100% data...')
        clf.fit(X, y)
        P_tst = clf.predict_proba(X_tst)[:, 1]

    logging.info('Saving predictions...')
    np.savetxt(predict_valid_file, P_val, fmt='%.6f', delimiter=',')
    np.savetxt(predict_test_file, P_tst, fmt='%.6f', delimiter=',')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train-file', required=True, dest='train_file')
    parser.add_argument('--test-file', required=True, dest='test_file')
    parser.add_argument('--predict-valid-file', required=True,
                        dest='predict_valid_file')
    parser.add_argument('--predict-test-file', required=True,
                        dest='predict_test_file')
    parser.add_argument('--cv-id', required=True, dest='cv_id_file')
    parser.add_argument('--n-est', default=100, type=int, dest='n_est')
    parser.add_argument('--depth', default=None, type=int, dest='depth')
    parser.add_argument('--retrain', default=False, action='store_true')

    args = parser.parse_args()

    start = time.time()
    train_predict(train_file=args.train_file,
                  test_file=args.test_file,
                  predict_valid_file=args.predict_valid_file,
                  predict_test_file=args.predict_test_file,
                  cv_id_file=args.cv_id_file,
                  n_est=args.n_est,
                  depth=args.depth,
                  retrain=args.retrain)
    logging.info('finished ({:.2f} min elasped)'.format((time.time() - start) /
                                                        60))
