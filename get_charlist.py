import argparse
import json
from ollama import Client
import os
import pandas as pd
import time

sys_prompt = """
You are a diligent robot assistant made by a botanist. You have expert knowledge of botanical terminology.
Your goal is to obtain a list of traits that are mentioned in the botanical description of a plant species.
Your answer must be as complete and accurate as possible.
Your answer must only be a comma-separated list of traits, with no other introductory text.
"""

prompt = """
You are given a botanical description of a plant species taken from published floras.
You compile the list of characteristics mentioned in the description and transcribe them into a comma-separated list.
Your answer should be formatted as follows: (name of characteristic 1),(name of characteristic 2),(name of characteristic 3),...
(name of characteristic 1/2/3/...) should be substituted with the name of the characteristic.
The name of every characteristic must be written in lowercase.
Do not include any text (e.g. introductory text) other than the comma-separated list.

Follow the instructions below.

1. Compile all the mentioned characteristics relating to the whole plant, such as growth form, reproduction, plant height, and branching.

2. Iterate through every mentioned organs (e.g. leaf and other leaf-like organs, stem, flower, inflorescence, fruit, seed and root) and parts of organs (e.g. stipule, anther, ovary) and list all related characteristics that are mentioned in the description.
Examples of characteristics that may be mentioned include length, width, shape, color, surface texture, surface features, and arrangement of each organ or part of an organ.
Each of these characteristics must be separate. The name of every characteristic relating to an organ or a part of an organ must be formatted as follows: "(name of organ or part of organ) (type of characteristic)", where (name of organ or part of organ) should be substituted with the name of the organ or part of the organ, and (type of characteristic) should be substituted with the specific type of characteristic.

In the final output, try to use verbatim the words that appear in the given description.
Do not make up characteristics that are not mentioned in the description.

Here are some examples of descriptions and their corresponding list of characteristics:

Sentence: "Fruit: ovoid berry, 10-12 mm wide, 13-15 mm long, yellow to yellow-green throughout."
Output: fruit shape,fruit type,fruit width,fruit length,fruit color

Sentence: "Perennial dioecious herbs 60-100cm tall. Leaves alternate, green and glabrous adaxially and hirsute with white to greyish hair abaxially."
Output: life history,reproduction,growth form,plant height,leaf arrangement,leaf color,leaf texture,leaf hair color

Here is the description that you should transcribe:
"""

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Extract a list of trait names from descriptions')

    # Basic I/O arguments
    parser.add_argument('descfile', type = str, help = 'File containing the descriptions produced by dwca2csv.py')
    parser.add_argument('outputfile', type = str, help = 'File to write JSON to')
    parser.add_argument('--desctype', required = True, type = str, help = 'The "type" value used for morphological descriptions in the description file')
    parser.add_argument('--sysprompt', required = False, type = str, help = 'Text file specifying the system prompt')
    parser.add_argument('--prompt', required = False, type = str, help = 'Text file specifying the initial part of the prompt')
    parser.add_argument('--silent', required = False, action = 'store_true', help = 'Suppress output showing job progress')

    # Run configs
    parser.add_argument('--start', required = False, type = int, default = 0, help = 'Order ID of the species to start transcribing from')
    parser.add_argument('--spnum', required = False, type = int, help = 'Number of species to process descriptions of. Default behaviour is to process all species present in the file')
    parser.add_argument('--saveeachsp', required = False, action = 'store_true', help = 'If specified, the script writes outputs to the file after running each species description')

    # Model properties
    parser.add_argument('--model', required = False, type = str, default = 'llama3', help = 'Name of base LLM to use')
    parser.add_argument('--temperature', required = False, type = float, default = 0.1, help = 'Model temperature between 0 and 1')
    parser.add_argument('--seed', required = False, type = int, default = 1, help = 'Model seed value')
    parser.add_argument('--repeatlastn', required = False, type = int, default = 0, help = 'Number of prompts for the model to look back to prevent repetition')
    parser.add_argument('--numpredict', required = False, type = int, default = 2048, help = 'Maximum number of tokens the model can generate')
    parser.add_argument('--numctx', required = False, type = int, default = 4096, help = 'Size of context window used to generate the token')
    parser.add_argument('--topk', required = False, type = int, help = 'A higher value (e.g. 100) will give more diverse answers, while a lower value (e.g. 10) will be more conservative.')
    parser.add_argument('--topp', required = False, type = float, help = 'A higher value (e.g., 0.95) will lead to more diverse text, while a lower value (e.g., 0.5) will generate more focused and conservative text.')

    # Parse the arguments
    args = parser.parse_args()

    # ===== Prompt setup =====

    # Read prompt files to override default prompts if specified
    if(args.sysprompt != None):
        with open(args.sysprompt, 'r') as fp:
            sysprompt = fp.read()
    if(args.prompt != None):
        with open(args.prompt, 'r') as fp:
            prompt = fp.read()
    
    # ===== Read descfile =====

    # Read descfile
    descdf = pd.read_csv(args.descfile, sep = '\t')

    # Filter morphological descriptions only
    descdf = descdf.loc[descdf['type'] == args.desctype]

    # Slice according to --start and --spnum options
    if(args.spnum != None):
        descdf = descdf[args.start : args.start + args.spnum]

    # Extract descriptions
    descs = descdf['description'].tolist()

    # ===== Setup Ollama ======

    # Build params
    params = {
        'temperature': args.temperature,
        'seed': args.seed,
        'repeat_last_n': args.repeatlastn,
        'num_predict': args.numpredict,
        'num_ctx': args.numctx,
        'top_k': args.topk,
        'top_p': args.topp
    }

    # Build modelfile
    modelfile = '{}\n{}'.format(
        'FROM {}'.format(args.model),
        '\n'.join(['PARAMETER {} {}'.format(param, value) for param, value in params.items() if value != None])
    )

    # Make connection to client
    client = Client(host = 'http://localhost:11434')

    # Create model with the specified params
    client.create(model = 'desc2matrix', modelfile = modelfile)

    # ===== Generate output =====

    # Dictionary to store the final output
    outdict = {}

    # Store metadata about the prompts provided, mode, and the parameters
    outdict['sys_prompt'] = sys_prompt
    outdict['prompt'] = prompt
    outdict['params'] = params
    outdict['data'] = []

    # If running in 'saveeachsp' mode
    if(args.saveeachsp == True):
        # Variable to store extracted characteristic data
        sp_list = []

        # Loop through each species description
        for rowid, desc in enumerate(descs):
            # Log number of species if not silent
            if(args.silent != True):
                print('Processing {}/{}'.format(rowid + 1, len(descs)))

            # Generate output for one species
            if(args.mode == 'desc2json'): # If in desc2json mode
                # Generate output
                char_json = desc2charjson_single(prompts['sys_prompt'], prompts['prompt'], desc, client, silent = args.silent == True)

                # Add entry to sp_list
                sp_list.append({
                    'coreid': descdf.iloc[rowid]['coreid'],
                    'status': char_json['status'], # Status: one of 'success', 'bad_structure', 'invalid_json'
                    'original_description': descdf.iloc[rowid]['description'],
                    'char_json': char_json['data'] if char_json['status'] == 'success' else None, # Only use this if parsing succeeded
                    'failed_str': char_json['data'] if char_json['status'] != 'success' else None # Only use this if parsing failed
                })
            elif(args.mode == 'desc2list2json'): # If in desc2list2json mode
                # Generate output
                desc_out = desc2list2charjson_single(prompts['d2l_sys_prompt'], prompts['d2l_prompt'],
                                        prompts['l2j_sys_prompt'], prompts['l2j_prompt'],
                                        desc, client, silent = args.silent == True)
                char_list = desc_out['list']
                char_json = desc_out['json']

                # Add entry to sp_list
                sp_list.append({
                    'coreid': descdf.iloc[rowid]['coreid'],
                    'status': char_json['status'], # Status: one of 'success', 'bad_structure', 'invalid_json'
                    'original_description': descdf.iloc[rowid]['description'],
                    'char_list': char_list,
                    'char_json': char_json['data'] if char_json['status'] == 'success' else None, # Only use this if parsing succeeded
                    'failed_str': char_json['data'] if char_json['status'] != 'success' else None # Only use this if parsing failed
                })
            
            # Store generated outputs
            outdict['data'] = sp_list

            # Write output as JSON
            with open(args.outputfile, 'w') as outfile:
                json.dump(outdict, outfile)

    # If running in bulk mode (default, save to file after all species have been processed)
    else:
        # Retrieve outputs and build output JSON
        if(args.mode == 'desc2json'): # If in desc2json mode
            # Generate output
            char_jsons = desc2charjson(prompts['sys_prompt'], prompts['prompt'], descs, client, silent = args.silent == True)

            # Compile data
            sp_list = [{
                'coreid': descdf.iloc[rowid]['coreid'],
                'status': cj['status'], # Status: one of 'success', 'bad_structure', 'invalid_json'
                'original_description': descdf.iloc[rowid]['description'],
                'char_json': cj['data'] if cj['status'] == 'success' else None, # Only use this if parsing succeeded
                'failed_str': cj['data'] if cj['status'] != 'success' else None # Only use this if parsing failed
            } for rowid, cj in enumerate(char_jsons)]

        elif(args.mode == 'desc2list2json'): # If in desc2list2json mode
            # Generate output
            desc_outs = desc2list2charjson(prompts['d2l_sys_prompt'], prompts['d2l_prompt'],
                                    prompts['l2j_sys_prompt'], prompts['l2j_prompt'],
                                    descs, client, silent = args.silent == True)

            # Compile data
            sp_list = [{
                'coreid': descdf.iloc[rowid]['coreid'],
                'status': cj['status'], # Status: one of 'success', 'bad_structure', 'invalid_json'
                'original_description': descdf.iloc[rowid]['description'],
                'char_list': cl,
                'char_json': cj['data'] if cj['status'] == 'success' else None, # Only use this if parsing succeeded
                'failed_str': cj['data'] if cj['status'] != 'success' else None # Only use this if parsing failed
            } for rowid, cl, cj in zip(list(range(0, len(desc_outs['jsons']))), desc_outs['lists'], desc_outs['jsons'])]

        # Store extracted information
        outdict['data'] = sp_list

        # Write output as JSON
        with open(args.outputfile, 'w') as outfile:
            json.dump(outdict, outfile)

if __name__ == '__main__':
    main()