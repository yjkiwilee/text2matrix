"""
This script converts an SDD-formatted XML file from Xper into a JSON file containing the species and their corresponding characteristics & characteristic values.
"""

import argparse
import xml

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Convert an SDD XML file from Xper into a JSON format')

    # Basic I/O arguments
    parser.add_argument('sddfile', type = str, help = 'SDD XML file from Xper to process')
    parser.add_argument('outputfile', type = str, help = 'File to write the processed JSON into')
    
    # Parse the arguments
    args = parser.parse_args()