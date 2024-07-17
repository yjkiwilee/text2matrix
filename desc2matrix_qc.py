import argparse
import json
import nltk

nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords

# Tokenize words using NLTK
stop_words = set(stopwords.words('english'))

# Read output from desc2matrix.py

desc_words_set = set([w for w in nltk.word_tokenize(desc) if not w.lower() in stop_words]) 
desc_formatted_words_set = set([w for w in nltk.word_tokenize(desc_formatted) if not w.lower() in stop_words]  )

# Calculate exact word match proportion
common_words = desc_words_set.intersection(desc_formatted_words_set)
word_match_proportion = len(common_words) / len(desc_words_set)
print(f'Proportion of Words Matched: {word_match_proportion:.2f}')