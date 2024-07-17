import argparse
import re
import json
import nltk

nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords

def get_word_set(descstr):
    # Gather stop words
    stop_words = set(stopwords.words('english'))

    # Insert whitespace after period, comma, colon and semicolon
    descstr = re.sub(r'[^0-9] *\. *[^0-9]', '. ', descstr) # Do not substitute periods in floating-point numbers
    descstr = re.sub(r' *, *', ', ', descstr)
    descstr = re.sub(r' *: *', ': ', descstr)
    descstr = re.sub(r' *; *', '; ', descstr)

    # Collapse numeric ranges to single 'word' to check for presence
    descstr = re.sub(r'([0-9]) *- * ([0-9])', r'\1-\2', descstr)

    # Tokenise words
    descset = set([w for w in nltk.word_tokenize(descstr) if not w.lower() in stop_words])

    # Remove punctuations post-tokenisation
    descset = descset.difference({'.', ',', ':', ';', '“', '”', '"', "'"})

    # Return word set
    return descset

# Read output from desc2matrix.py
desc_output = {}

with open('test_scripts/test_output.json', 'r') as fp:
    desc_output = json.loads(fp.read())

# Extract original descriptions and their JSON counterparts
descs = [desc['original_description'] for desc in desc_output]
descdicts = [desc['char_json'] for desc in desc_output]

# Merge characteristics in descdicts into single strings
descs_formatted = ['\n'.join(['{}: {}'.format(char['characteristic'], char['value']) for char in descdict])
                   for descdict in descdicts]

# Get word sets
descset = [get_word_set(desc) for desc in descs][0]
descset_formatted = [get_word_set(desc_f) for desc_f in descs_formatted][0]

# Calculate exact word match proportion
common_words = descset.intersection(descset_formatted)
original_only = descset.difference(descset_formatted)
formatted_only = descset_formatted.difference(descset)
word_match_proportion = len(common_words) / len(descset)

print(f'Proportion of Words Matched: {word_match_proportion:.2f}')
print('Common words:\n{}'.format(', '.join(common_words)))
print('Words in the original description only:\n{}'.format(', '.join(original_only)))
print('Words in the formatted descrtiption only:\n{}'.format(', '.join(formatted_only)))