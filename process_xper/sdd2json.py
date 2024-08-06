"""
This script converts an SDD-formatted XML file from Xper into a JSON file containing the species and their corresponding characteristics & characteristic values.
"""

import argparse
import xmltodict
import json
from typing import Optional

def sddxml2dict(sddxml:str):
    """
    Convert a SDD XML string into a structured dict of species descriptions.
    The output dict is structured as follows:
    {
        "species 1": [
            {"characteristic": (name of characteristic), "value": (corresponding value)},
            (...)
        ], (...)
    }

    Parameters:
        sddxml (str): Raw XML string

    Returns:
        desc_dict (dict): Output dictionary
    """

    # Parse the raw XML
    sdd_dict:dict = xmltodict.parse(sddxml)
    
    sdd_dataset:dict = sdd_dict['Datasets']['Dataset'] # Extract the dataset only
    characters:dict = sdd_dataset['Characters'] # Get labelled characteristics
    coded_descs:list = sdd_dataset['CodedDescriptions']['CodedDescription'] # Get coded descriptions of each species

    # ===== Retrieve characteristics, values, and corresponding codes =====
    
    # Dict for storing characteristic codes
    cat_char_codes:dict = {}
    quant_char_codes:dict = {}

    # Retrieve categorical characteristics
    for cat_char in characters['CategoricalCharacter']: # For each categorical characteristic
        # Skip over characteristics with certain keywords
        # TODO: Make this work with non-Solanaceae?
        rm_keywords = ['clade', 'distribution']
        # Characteristic name
        char_name = cat_char['Representation']['Label'].lower()
        # If at least one of the keywords is in the characteristic name
        if True in [rm_keyword in char_name for rm_keyword in rm_keywords]:
            continue # Skip over

        # Add an entry in the dictionary
        cat_char_codes[cat_char['@id']] = {
            'type': 'categorical', # Type of characteristic
            'characteristic': char_name, # Name of characteristic in lowercase
            'values': { # Possible values in key-value pairs
                statedef['@id']: statedef['Representation']['Label'].lower() # Convert to lowercase
                for statedef in cat_char['States']['StateDefinition']
            }
        }

    # Retrieve quantitative characteristics
    for quant_char in characters['QuantitativeCharacter']: # For each quantitative characteristic
        # Add an entry in the dictionary
        quant_char_codes[quant_char['@id']] = {
            'type': 'quantitative', # Type of characteristic
            'characteristic': quant_char['Representation']['Label'].lower(), # Name of characteristic in lowercase
            'units': quant_char['MeasurementUnit']['Label'].lower() # Unit for characteristic value in lowercase
        }
    
    # ===== Retrieve coded descriptions of species =====
    
    # Dict for storing species descriptions
    spp_chars:dict = {}

    # Iterate through each species
    for sp in coded_descs:
        # Species binomial
        sp_name:str = ' '.join(sp['Representation']['Label'].split(' ')[0:2]) # Remove author
        # Species characteristics
        sp_chars:list = []
        # Raw species characteristics
        sp_raw_chars:dict = sp['SummaryData']
        
        # Gather categorical characteristics
        for cat_char_code in cat_char_codes:
            # Find characteristic with cat_char_code for the species
            cat_chars = [cat_char for cat_char in sp_raw_chars['Categorical'] if cat_char['@ref'] == cat_char_code]

            # String representing the characteristic value
            val_str:Optional[str] = ''

            # Put None if character value is not found
            if len(cat_chars) == 0:
                val_str = None

            # Retrieve characteristic
            cat_char = cat_chars[0]
            
            if 'State' not in cat_char: # Put None if character value is not given
                val_str = None
            else:
                # Check if there are multiple categorical values
                if isinstance(cat_char['State'], list): # If there are more than one categorical value
                    val_str = '; '.join([
                        cat_char_codes[cat_char['@ref']]['values'][char_state['@ref']] for char_state in cat_char['State']
                    ]) # Join multiple values together with semicolon
                else: # If there is only one categorical value
                    val_str = cat_char_codes[cat_char['@ref']]['values'][cat_char['State']['@ref']]
            
            # Append item to sp_chars
            sp_chars.append({
                'characteristic': cat_char_codes[cat_char['@ref']]['characteristic'],
                'value': val_str
            })
        
        # Gether quantitative characteristics
        for quant_char_code in quant_char_codes:
            # Find characteristic with quant_char_code for the species
            quant_chars = [quant_char for quant_char in sp_raw_chars['Quantitative'] if quant_char['@ref'] == quant_char_code]

            # String representing the characteristic value
            val_str:Optional[str] = ''

            # Put None if character value is not found
            if len(quant_chars) == 0:
                val_str = None

            # Retrieve characteristic
            quant_char = quant_chars[0]

            if 'Measure' not in quant_char: # Put None if character value is not given
                val_str = None
            else:
                # Value range (sort so that the minimum value comes first)
                val_range = sorted([float(val['@value']) for val in quant_char['Measure']])

                # Set value string
                val_str = str(
                    val_range[0] if val_range[0] == val_range[1] # Single value if range minimum and maximum are identical
                    else '{}-{}'.format(*val_range) # Range if range minimum and maximum are different
                ) + ' ' + quant_char_codes[quant_char['@ref']]['units'] # Append units to end
                
            # Append characteristic
            sp_chars.append({
                'characteristic': quant_char_codes[quant_char['@ref']]['characteristic'],
                'value': val_str
            })

        # Sort characteristics
        sp_chars = sorted(sp_chars, key = lambda char: char['characteristic'])
        
        # Append species characteristics to spp_chars
        spp_chars[sp_name] = sp_chars

    # Return species characteristics dict
    return spp_chars


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Convert an SDD XML file from Xper into a JSON format')

    # Basic I/O arguments
    parser.add_argument('sddfile', type = str, help = 'SDD XML file from Xper to process')
    parser.add_argument('outfile', type = str, help = 'File to write the processed JSON into')
    parser.add_argument('--charout', type = str, required = False, help = 'File to write information about characters and their possible values/units to')
    
    # Parse the arguments
    args = parser.parse_args()

    # Variable for storing the final JSON output as dict
    final_dict:dict = {}

    # Read XML file
    with open(args.sddfile, 'r') as fp:
        final_dict = sddxml2dict(fp.read())

    with open(args.outfile, 'w') as fp:
        json.dump(final_dict, fp)

if __name__ == '__main__':
    main()