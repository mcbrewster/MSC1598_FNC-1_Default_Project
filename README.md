# TFIDF Approach

Our first approach was to add a TFIDF feature to the baseline model provided found at https://github.com/FakeNewsChallenge/fnc-1-baseline

Using just the TFIDF score for the healdines the max score generated was 79.15% on the dev set and 
75.51% on the competition set we did not exceed the baseline score. 

Using the cosine similary of the TFIDF scores between the headline and the article the max score generated was 
81.86% on the dev set and 78.3% on the competion set which just barely exceeds the baseline score. 


To run this version of the model Run: 


```
python3 main.y fnc_kfold.py
```


# Sequential model with TFIDF 

In an attempt to improve the baseline model we implemented a bi-directional LSTM 
Using this model we  were ble to improve on this score by 0.13%, the max score was 79.40 on the dev set and 
75.43% on the competion set 


To run this version of the model Run: 
download gloVe from https://nlp.stanford.edu/projects/glove/ and run

```
python3 main.y fnc_kfold.ipynb
```

