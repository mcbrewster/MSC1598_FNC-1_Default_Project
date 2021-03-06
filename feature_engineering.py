import os
import re
import nltk
import numpy as np
from sklearn import feature_extraction
from tqdm import tqdm
import ssl
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter


_wnl = nltk.WordNetLemmatizer()

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('averaged_perceptron_tagger')

master_pos_tags = ['NN', 'VBG', 'RB']

def normalize_word(w):
    return _wnl.lemmatize(w).lower()


def get_tokenized_lemmas(s):
    return [normalize_word(t) for t in nltk.word_tokenize(s)]

def get_tokenized_pos(s, pos_tags = master_pos_tags):
    return [word for (word, token) in nltk.pos_tag(get_tokenized_lemmas(s)) if token in pos_tags]

def clean(s):
    # Cleans a string: Lowercasing, trimming, removing non-alphanumeric

    return " ".join(re.findall(r'\w+', s, flags=re.UNICODE)).lower()


def remove_stopwords(l):
    # Removes stopwords from a list of tokens
    return [w for w in l if w not in feature_extraction.text.ENGLISH_STOP_WORDS]

def body_split_sentences(bodies):
    body_part1 = []
    body_part2 = []
    body_part3 = []
    body_part4 = []
    for body in tqdm(bodies):

        sentences = re.split(r'[.?!]\s*', body)
        split_size = int(len(sentences)/4)
        i=0
        body_part1.append(" ".join(sentences[i:i+split_size]))
        i += split_size
        body_part2.append(" ".join(sentences[i:i+split_size]))
        i += split_size
        body_part3.append(" ".join(sentences[i:i+split_size]))
        i += split_size
        body_part4.append(" ".join(sentences[i:i+split_size]))

    return body_part1,body_part2,body_part3,body_part4

def gen_or_load_feats(feat_fn, headlines, bodies, feature_file):
    if not os.path.isfile(feature_file):
        feats = feat_fn(headlines, bodies)
        np.save(feature_file, feats)

    return np.load(feature_file)


##  Returns the TFIDF scoare for each stance from a vectorizer fit on the vocabulary formed by the total corpus 
##  Function implemented following the method outlined in: 
## P. Sujanmulk, "Sentiment Analysis on Amazon Reviews using TF-IDF Approach.", Medium, 2022. [Online]. Available: https://medium.com/analytics-vidhya/sentiment-analysis-on-amazon-reviews-using-tf-idf-approach-c5ab4c36e7a1. [Accessed: 08- Apr- 2022].

def basic_tfidf(headlines, bodies):
    vocab = [get_tokenized_pos(clean(line)) for line in tqdm(headlines+bodies)]
    vocab = [word for subword in total_vocab for word in subword]
    vectorizer= TfidfVectorizer(vocabulary=vocab, tokenizer=get_tokenized_lemmas)
    TFIDF_x_train = vectorizer.fit_transform(np.array(headlines))
    array = TFIDF_x_train.toarray()
    return array

## Returns a feature for cosine similarity for the TFIDF scoare between the healines and the bodies 
## implemented 
## Function is implemented is from Granularity-Based Prediction Framework with Stance Conditioned CNN for Fake News Classification - Stance Detection
## https://github.com/varshanth/FakeNewsChallenge-FNC1/tree/57cc26c62f73953bf49a2be7e35426c28c055991
def tfidf_features(headlines, bodies):

    ## create the vocabulary for the entire corpus 
    vocab = [get_tokenized_pos(clean(line)) for line in tqdm(headlines+bodies)]
    vocab = [word for subword in vocab for word in subword]

    ## find the most common words, we tested 4000 -7000
    wordCount = Counter(vocab)
    mostCommonWords = wordCount.most_common(4500)

    ## fit vectorizer on most common words 
    vocab = [wd for wd,count in mostCommonWords]
    vectorizer = TfidfVectorizer(use_idf=True, vocabulary=vocab, analyzer='word', tokenizer=get_tokenized_lemmas)

    ## Create TFIDF matrices for the headline and bodies 
    headlinesTFIDF = vectorizer.fit_transform(headlines)
    headlinesTFIDF = headlines_tfidf.toarray()
    bodiesTFIDF = tfidf_vectorizer.fit_transform(bodies)
    bodiesTFIDF = bodies_tfidf.toarray()

    ## Compute and return cosine similarty
    cosineSimilarity = cosine_similarity(headlinesTFIDF, bodiesTFIDF)
    X = np.diagonal(cosineSimilarity)
    return X
    

def word_overlap_features(headlines, bodies):
    X = []
    for i, (headline, body) in tqdm(enumerate(zip(headlines, bodies))):
        clean_headline = clean(headline)
        clean_body = clean(body)
        clean_headline = get_tokenized_lemmas(clean_headline)
        clean_body = get_tokenized_lemmas(clean_body)
        features = [
            len(set(clean_headline).intersection(clean_body)) / float(len(set(clean_headline).union(clean_body)))]
        X.append(features)
    print("overlap")
    print(len(X))
    return X


def refuting_features(headlines, bodies):
    _refuting_words = [
        'fake',
        'fraud',
        'hoax',
        'false',
        'deny', 'denies',
        # 'refute',
        'not',
        'despite',
        'nope',
        'doubt', 'doubts',
        'bogus',
        'debunk',
        'pranks',
        'retract'
    ]
    X = []
    for i, (headline, body) in tqdm(enumerate(zip(headlines, bodies))):
        clean_headline = clean(headline)
        clean_headline = get_tokenized_lemmas(clean_headline)
        features = [1 if word in clean_headline else 0 for word in _refuting_words]
        X.append(features)
    return X


def polarity_features(headlines, bodies):
    _refuting_words = [
        'fake',
        'fraud',
        'hoax',
        'false',
        'deny', 'denies',
        'not',
        'despite',
        'nope',
        'doubt', 'doubts',
        'bogus',
        'debunk',
        'pranks',
        'retract'
    ]

    def calculate_polarity(text):
        tokens = get_tokenized_lemmas(text)
        return sum([t in _refuting_words for t in tokens]) % 2
    X = []
    for i, (headline, body) in tqdm(enumerate(zip(headlines, bodies))):
        clean_headline = clean(headline)
        clean_body = clean(body)
        features = []
        features.append(calculate_polarity(clean_headline))
        features.append(calculate_polarity(clean_body))
        X.append(features)
    return np.array(X)


def ngrams(input, n):
    input = input.split(' ')
    output = []
    for i in range(len(input) - n + 1):
        output.append(input[i:i + n])
    return output


def chargrams(input, n):
    output = []
    for i in range(len(input) - n + 1):
        output.append(input[i:i + n])
    return output


def append_chargrams(features, text_headline, text_body, size):
    grams = [' '.join(x) for x in chargrams(" ".join(remove_stopwords(text_headline.split())), size)]
    grams_hits = 0
    grams_early_hits = 0
    grams_first_hits = 0
    for gram in grams:
        if gram in text_body:
            grams_hits += 1
        if gram in text_body[:255]:
            grams_early_hits += 1
        if gram in text_body[:100]:
            grams_first_hits += 1
    features.append(grams_hits)
    features.append(grams_early_hits)
    features.append(grams_first_hits)
    return features


def append_ngrams(features, text_headline, text_body, size):
    grams = [' '.join(x) for x in ngrams(text_headline, size)]
    grams_hits = 0
    grams_early_hits = 0
    for gram in grams:
        if gram in text_body:
            grams_hits += 1
        if gram in text_body[:255]:
            grams_early_hits += 1
    features.append(grams_hits)
    features.append(grams_early_hits)
    return features


def hand_features(headlines, bodies):

    def binary_co_occurence(headline, body):
        # Count how many times a token in the title
        # appears in the body text.
        bin_count = 0
        bin_count_early = 0
        for headline_token in clean(headline).split(" "):
            if headline_token in clean(body):
                bin_count += 1
            if headline_token in clean(body)[:255]:
                bin_count_early += 1
        return [bin_count, bin_count_early]

    def binary_co_occurence_stops(headline, body):
        # Count how many times a token in the title
        # appears in the body text. Stopwords in the title
        # are ignored.
        bin_count = 0
        bin_count_early = 0
        for headline_token in remove_stopwords(clean(headline).split(" ")):
            if headline_token in clean(body):
                bin_count += 1
                bin_count_early += 1
        return [bin_count, bin_count_early]

    def count_grams(headline, body):
        # Count how many times an n-gram of the title
        # appears in the entire body, and intro paragraph

        clean_body = clean(body)
        clean_headline = clean(headline)
        features = []
        features = append_chargrams(features, clean_headline, clean_body, 2)
        features = append_chargrams(features, clean_headline, clean_body, 8)
        features = append_chargrams(features, clean_headline, clean_body, 4)
        features = append_chargrams(features, clean_headline, clean_body, 16)
        features = append_ngrams(features, clean_headline, clean_body, 2)
        features = append_ngrams(features, clean_headline, clean_body, 3)
        features = append_ngrams(features, clean_headline, clean_body, 4)
        features = append_ngrams(features, clean_headline, clean_body, 5)
        features = append_ngrams(features, clean_headline, clean_body, 6)
        return features

    X = []
    for i, (headline, body) in tqdm(enumerate(zip(headlines, bodies))):
        X.append(binary_co_occurence(headline, body)
                 + binary_co_occurence_stops(headline, body)
                 + count_grams(headline, body))


    return X
