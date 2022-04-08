import sys
from this import s
import numpy as np

from sklearn.ensemble import GradientBoostingClassifier
from feature_engineering import refuting_features, polarity_features, hand_features, gen_or_load_feats, tfidf_features, basic_tfidf
from feature_engineering import word_overlap_features
from utils.dataset import DataSet
from utils.generate_test_splits import kfold_split, get_stances_for_folds
from utils.score import report_score, LABELS, score_submission

from utils.system import parse_params, check_version
import pandas

##Baseline code is take from Thorne, B. Nadion, D. Rao and Y. Pan,
#  "FakeNewsChallenge/fnc-1-baseline: A baseline implementation for FNC-1", GitHub, 2017.
#  [Online]. Available: https://github.com/FakeNewsChallenge/fnc-1-baseline. [Accessed: 08- Apr- 2022].

##This file includes the additoan of the basic TFIF feature and the cosign TFIDF features 
def generate_features(stances,dataset,name):
    h, b, y = [],[],[]

    for stance in stances:
        y.append(LABELS.index(stance['Stance']))
        h.append(stance['Headline'])
        b.append(dataset.articles[stance['Body ID']])

    X_overlap = gen_or_load_feats(word_overlap_features, h, b, "features/overlap."+name+".npy")
    X_refuting = gen_or_load_feats(refuting_features, h, b, "features/refuting."+name+".npy")
    X_polarity = gen_or_load_feats(polarity_features, h, b, "features/polarity."+name+".npy")
    X_hand = gen_or_load_feats(hand_features, h, b, "features/hand."+name+".npy")

    ## include the basic TFIDF feature tested 
    # X_basic_tfidf = gen_or_load_feats(basic_tfidf, h, b, "features/basic_tfidf."+name+".npy")
    # X = np.c_[X_hand, X_polarity, X_refuting, X_overlap, X_basic_tfidf]

     ## include the basic TFIDF feature based on cosine similarity 
    X_tfidf = gen_or_load_feats(tfidf_features, h, b, "features/tfidf."+name+".npy")
    X = np.c_[X_hand, X_polarity, X_refuting, X_overlap, X_tfidf]
    return X,y

## baseline code below remains unchanged, see fnc_kfold.iynb for sequential model impliementation
if __name__ == "__main__":
    print("here")
    check_version()
    parse_params()

    #Load the training dataset and generate folds
    d = DataSet()
    folds,hold_out = kfold_split(d,n_folds=10)
    fold_stances, hold_out_stances = get_stances_for_folds(d,folds,hold_out)

    # Load the competition dataset
    competition_dataset = DataSet("competition_test")
    X_competition, y_competition = generate_features(competition_dataset.stances, competition_dataset, "competition")

    h, b = [], []
    for stance in competition_dataset.stances:
        h.append(stance['Headline'])
        b.append(stance['Body ID'])

    answers = {'Headline': h, 'Body ID': b, 'Stance': []}

    Xs = dict()
    ys = dict()

    # Load/Precompute all features now
    X_holdout,y_holdout = generate_features(hold_out_stances,d,"holdout")
    for fold in fold_stances:
        Xs[fold],ys[fold] = generate_features(fold_stances[fold],d,str(fold))


    best_score = 0
    best_fold = None


    # Classifier for each fold
    for fold in fold_stances:
        ids = list(range(len(folds)))
        del ids[fold]

        X_train = np.vstack(tuple([Xs[i] for i in ids]))
        y_train = np.hstack(tuple([ys[i] for i in ids]))

        X_test = Xs[fold]
        y_test = ys[fold]

        clf = GradientBoostingClassifier(n_estimators=200, random_state=14128, verbose=True)
        clf.fit(X_train, y_train)

        predicted = [LABELS[int(a)] for a in clf.predict(X_test)]
        actual = [LABELS[int(a)] for a in y_test]

        fold_score, _ = score_submission(actual, predicted)
        max_fold_score, _ = score_submission(actual, actual)

        score = fold_score/max_fold_score

        print("Score for fold "+ str(fold) + " was - " + str(score))
        if score > best_score:
            best_score = score
            best_fold = clf



    #Run on Holdout set and report the final score on the holdout set
    predicted = [LABELS[int(a)] for a in best_fold.predict(X_holdout)]
    actual = [LABELS[int(a)] for a in y_holdout]

    print("Scores on the dev set")
    report_score(actual,predicted)

    #Run on competition dataset
    predicted = [LABELS[int(a)] for a in best_fold.predict(X_competition)]
    answers["Stance"] = predicted
    answers = pandas.DataFrame(answers)
    answers.to_csv('answer.csv', index=False, encoding='utf-8')
    actual = [LABELS[int(a)] for a in y_competition]
    print("Scores on the test set")
    report_score(actual,predicted)