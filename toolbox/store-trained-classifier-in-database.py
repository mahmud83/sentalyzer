#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

__author__ = 'ma'

import argparse
import argcomplete
import sys

from smm import models
from smm.classifier import classification
from smm import config

import random
import pickle
import logging

from nltk.tokenize import word_tokenize

parser = argparse.ArgumentParser(description='Classify collected reviews', usage='python train-classification.py classifier 10000')
parser.add_argument('name', help='Classifier name - must be unique')
parser.add_argument('size', type=int, help='Corpus size - how much documents to classify')
parser.add_argument('-t', '--type', help='Classifier type', default='votedclassifier')
args = parser.parse_args()

argcomplete.autocomplete(parser)

# Define logger
logger = logging.getLogger('store-pickled-classifier-in-database')

# Load documents from file
logger.info('Start loading of documents  from ' + config.basepath + config.pickles_path + '/documents.pickle.')
documents_f = open(config.basepath + config.pickles_path + "/documents.pickle", "rb")
documents = pickle.load(documents_f)
documents_f.close()
logger.info('Finished loading of documents.')

# Load features from file
logger.info('Start loading of word features from ' + config.basepath + config.pickles_path + '/word_features.pickle.')
word_features_f = open(config.basepath + config.pickles_path + "/word_features.pickle", "rb")
word_features = pickle.load(word_features_f)
word_features_f.close()
logger.info('Finished loading of word features.')

# Search for features in documents
def find_features(document):
    words = word_tokenize(document)
    features = {}
    for w in word_features:
        features[w] = (w in words)

    return features

# Load feature set from file
logger.info('Start loading of featureset from ' + config.basepath + config.pickles_path +'/featuresets.pickle.')
featuresets_f = open(config.basepath + config.pickles_path + "/featuresets.pickle", "rb")
featuresets = pickle.load(featuresets_f)
featuresets_f.close()
logger.info('Finished loading of featureset.')

# Shuffle features
random.shuffle(featuresets)

# Define how many of the features are training data and how many are test data
number_of_training_documents = int(len(documents) * 95 / 100)
number_of_test_documents = int(len(documents) * 5 / 100)

# Define the training set
logger.info('Create training set of ' + str(number_of_training_documents) + ' documents.')
training_set = featuresets[:number_of_training_documents]

# Define the test set
logger.info('Create testing set of ' + str(number_of_test_documents) + ' documents.')
testing_set = featuresets[number_of_test_documents:]

cls = classification.Classifier(training_set, testing_set)

models.connect()

if models.TrainedClassifiers.objects(name = args.name).count():
    print "TrainedClassifier already exists with name %s try to different name" % args.name
    sys.exit()

if args.type == 'naivebayes':
    cls.run_naivebayes(False)

elif args.type == 'multinomialnb':
    cls.run_multinomialnb(False)

elif args.type == 'bernoullinb':
    cls.run_bernoullinb(False)

elif args.type == 'logisticregression':
    cls.run_logisticregression(False)

elif args.type == 'sgd':
    cls.run_sgd(False)

elif args.type == 'linearsvc':
    cls.run_linearsvc(False)

elif args.type == 'nusvc':
    cls.run_nusvc(False)

elif args.type == 'votedclassifier':
    naivebayes_classifier = cls.run_naivebayes(False)
    mnb_classifier = cls.run_multinomialnb(False)
    bernoullinb_classifier = cls.run_bernoullinb(False)
    logisticregression_classifier = cls.run_logisticregression(False)
    sgd_classifier = cls.run_sgd(False)
    linearsvc_classifier = cls.run_linearsvc(False)
    nusvc_classifier = cls.run_nusvc(False)


    cls = classification.VoteClassifier(
        naivebayes_classifier,
        mnb_classifier,
        bernoullinb_classifier,
        logisticregression_classifier,
        sgd_classifier,
        linearsvc_classifier,
        nusvc_classifier
    )

    #votes_classifier_accuracy = (nltk.classify.accuracy(cls, testing_set)) * 100
    #logger.info("Voted Classifier accuracy is '{0}'." .format(votes_classifier_accuracy))

else:
    print '%s is not valid classifier type' % args.type
    sys.exit()

# Save
row = models.TrainedClassifiers()
row.name = args.name
row.set_classifier(cls)
row.stats = dict(
    classifier = cls.__class__.__name__
)

row.save()


print "TrainedClassifier saved with ID: %s  Name: %s" % (row.id, row.name)

