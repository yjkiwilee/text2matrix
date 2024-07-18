import argparse
import json
from ollama import Client
import os
import pandas as pd
import time

def regularise_charjson(chars):
    # Return false if the object is not a list; we expect a list of {'characteristic':'', 'value':''}
    if not isinstance(chars, list):
        return False

    new_dict = []

    # Go through elements
    for char in chars:
        # Return false if the keys are different from what we expect
        if set(char.keys()) != {'characteristic', 'value'}:
            return False
        
        # Skip if value is None
        if char['value'] == None:
            continue
        
        # Convert value to string
        char['value'] = str(char['value'])

        # Append characteristic to new dict
        new_dict.append(char)
    
    # Return the new dict
    return new_dict

def desc2charjson(sys_prompt, prompt, descs, client, model = 'desc2matrix', silent = False):
    # Pass descriptions to LLM for response
    char_jsons = []

    for i, desc in enumerate(descs):
        start = 0
        if not silent:
            print('desc2json: processing {}/{}... '.format(i+1, len(descs)), end = '', flush = True)
            start = time.time()

        # Generate response while specifying system prompt
        resp = client.generate(model = model,
                                   prompt = prompt + '\n' + desc,
                                   system = sys_prompt)['response']

        # Attempt to parse prompt as JSON
        try:
            resp_json = json.loads(resp)
            # Check validity / regularise output
            reg_resp_json = regularise_charjson(resp_json)
            if reg_resp_json != False:
                char_jsons.append(reg_resp_json)
            else:
                if not silent:
                    print('Ollama output is JSON but is structured badly:\n{}'.format(str(resp_json)))
                char_jsons.append(None) # Append None == null if not valid
        except json.decoder.JSONDecodeError as decode_err: # If LLM returns bad string
            if not silent:
                print('Ollama returned bad JSON string:\n{}'.format(resp))
            char_jsons.append(None) # Append None == null
        
        if not silent:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')
    
    # Return characteristics as array of dict
    return char_jsons

def desc2list2charjson(d2l_sys_prompt, d2l_prompt, l2j_sys_prompt, l2j_prompt, descs, client, model = 'desc2matrix', silent = False):
    # List to store intermediate lists and final JSONs
    desc_lists = []
    char_jsons = []

    # Pass descriptions to LLM for response
    for i, desc in enumerate(descs):
        # Progress log
        start = 0
        if not silent:
            print('desc2list: processing {}/{}... '.format(i+1, len(descs)), end = '', flush = True)
            start = time.time()
        
        # Generate list string
        liststr = client.generate(model = model,
                                prompt = d2l_prompt + '\n' + desc,
                                system = d2l_sys_prompt)['response']
        
        # Append list string
        desc_lists.append(liststr)

        # Progress log
        if not silent:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')
            print('list2json: processing {}/{}... '.format(i+1, len(descs)), end = '', flush = True)
            start = time.time()
        
        # Generate JSON response
        resp = client.generate(model = 'desc2matrix',
                            prompt = l2j_prompt + '\n' + liststr,
                            system = l2j_sys_prompt)['response']
        
        # Attempt to parse response to JSON
        try:
            resp_json = json.loads(resp)
            # Check validity / regularise JSON
            reg_resp_json = regularise_charjson(resp_json)
            if reg_resp_json != False: # If JSON valid
                char_jsons.append(reg_resp_json)
            else:
                if not silent:
                    print('Ollama output is JSON but is structured badly:\n{}'.format(str(resp_json)))
                char_jsons.append(None) # Append None == null if not valid
        except json.decoder.JSONDecodeError as decode_err: # If LLM returns bad string
            if not silent:
                print('Ollama returned bad JSON string:\n{}'.format(resp_json))
            char_jsons.append(None) # Append None == null
        
        if not silent:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')
    
    # Return desc_lists and char_jsons as dictionary
    return {'lists': desc_lists, 'jsons': char_jsons}

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Extract JSON/dict from description files')

    # Add the arguments
    parser.add_argument('descfile', type = str, help = 'File containing the descriptions produced by dwca2csv.py')
    parser.add_argument('outputfile', type = str, help = 'File to write JSON to')
    parser.add_argument('--mode', required = True, type = str, choices = ['desc2json', 'desc2list2json'], help = 'Transcription mode to use')
    parser.add_argument('--desctype', required = True, type = str, help = 'The "type" value used for morphological descriptions in the description file')
    parser.add_argument('--start', required = False, type = int, default = 0, help = 'Order ID of the species to start transcribing from')
    parser.add_argument('--spnum', required = False, type = int, help = 'Number of species to process descriptions of. Default behaviour is to process all species present in the file')
    parser.add_argument('--model', required = False, type = str, default = 'llama3', help = 'Name of base LLM to use')
    parser.add_argument('--temperature', required = False, type = float, default = 0.1, help = 'Model temperature between 0 and 1')
    parser.add_argument('--seed', required = False, type = int, default = 0, help = 'Model seed value')
    parser.add_argument('--promptsdir', required = False, type = str, default = './prompts', help = 'Folder storing the prompt files')
    parser.add_argument('--silent', required = False, action = 'store_true', help = 'Suppress output showing job progress')

    # Parse the arguments
    args = parser.parse_args()

    # Read descfile
    descdf = pd.read_csv(args.descfile, sep = '\t')

    # Filter morphological descriptions only
    descdf = descdf.loc[descdf['type'] == args.desctype]

    # Slice according to --start and --spnum options
    if(args.spnum != None):
        descdf = descdf[args.start : args.start + args.spnum]

    # Extract descriptions
    descs = descdf['description'].tolist()

    # Build params
    params = {'temperature': args.temperature, 'seed': args.seed}

    # Build modelfile
    modelfile = '{}\n{}'.format(
        'FROM {}'.format(args.model),
        '\n'.join(['PARAMETER {} {}'.format(param, value) for param, value in params.items()])
    )

    # Make connection to client
    client = Client(host = 'http://localhost:11434')

    # Create model with the specified params
    client.create(model = 'desc2matrix', modelfile = modelfile)

    outdict = None

    # Check given transcription mode
    if(args.mode == 'desc2json'):

        # Open & read sys_prompt.txt and prompt.txt
        prompt_fnames = ['sys_prompt.txt', 'prompt.txt']
        prompt_ftypes = ['sys_prompt', 'prompt']
        prompts = {}

        for fname, ftype in zip(prompt_fnames, prompt_ftypes):
            with open(os.path.join(args.promptsdir, fname), 'r') as fp:
                prompts[ftype] = fp.read()

        char_jsons = desc2charjson(prompts['sys_prompt'], prompts['prompt'], descs, client, silent = args.silent == True)

        # Build output JSON
        outdict = [{
            'coreid': descdf.iloc[rowid]['coreid'],
            'original_description': descdf.iloc[rowid]['description'],
            'char_json': cj
        } for rowid, cj in enumerate(char_jsons)]

    elif(args.mode == 'desc2list2json'):

        # Open & read d2l_sys_prompt.txt, d2l_prompt.txt, l2d_sys_prompt.txt, l2d_prompt.txt
        prompt_fnames = ['d2l_sys_prompt.txt', 'd2l_prompt.txt', 'l2j_sys_prompt.txt', 'l2j_prompt.txt']
        prompt_ftypes = ['d2l_sys_prompt', 'd2l_prompt', 'l2j_sys_prompt', 'l2j_prompt']
        prompts = {}

        for fname, ftype in zip(prompt_fnames, prompt_ftypes):
            with open(os.path.join(args.promptsdir, fname), 'r') as fp:
                prompts[ftype] = fp.read()
        
        desc_outs = desc2list2charjson(prompts['d2l_sys_prompt'], prompts['d2l_prompt'],
                                   prompts['l2j_sys_prompt'], prompts['l2j_prompt'],
                                   descs, client, silent = args.silent == True)

        # Build output JSON
        outdict = [{
            'coreid': descdf.iloc[rowid]['coreid'],
            'original_description': descdf.iloc[rowid]['description'],
            'char_list': cl,
            'char_json': cj
        } for rowid, cl, cj in zip(list(range(0, len(desc_outs['jsons']))), desc_outs['lists'], desc_outs['jsons'])]

    # Write output as JSON
    with open(args.outputfile, 'w') as outfile:
        json.dump(outdict, outfile)

if __name__ == '__main__':
    main()