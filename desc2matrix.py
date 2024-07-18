import argparse
import json
from ollama import Client
import os
import pandas as pd
import time

def regularise_dict(dict):
    # Return false if the object is not a list; we expect a list of {'characteristic':'', 'value':''}
    if not isinstance(dict, list):
        return False

    new_dict = []

    # Go through elements
    for char in dict:
        # Return false if the keys are different from what we expect
        if set(char.keys()) != {'characteristic', 'value'}:
            return False
        
        # Skip if value is None and similarly 'null-y' values
        if char['value'] == None:
            continue
        if char['value'].lower() in ['unknown', 'null', 'not applicable']:
            continue
        
        # Convert value to string
        char['value'] = str(char['value'])
    
    # Return the new dict
    return new_dict

def desc2dict(sys_prompt, prompt, descriptions, client, model = 'desc2matrix', silent = False):
    # Pass descriptions to LLM for response
    desc_dicts = []

    for i, description in enumerate(descriptions):
        start = 0
        if not silent:
            print('desc2dict: processing {}/{}... '.format(i+1, len(descriptions)), end = '', flush = True)
            start = time.time()

        # Generate response while specifying system prompt
        response = client.generate(model = model,
                                   prompt = prompt + '\n' + description,
                                   system = sys_prompt)['response']

        # Attempt to parse prompt as JSON
        try:
            response_dict = json.loads(response)
            # Check validity / regularise output
            reg_response_dict = regularise_dict(response_dict)
            if reg_response_dict != False:
                desc_dicts.append(reg_response_dict)
            else:
                if not silent:
                    print('Ollama output is JSON but is structured badly:\n{}'.format(str(response_dict)))
                desc_dicts.append(None) # Append None == null if not valid
        except json.decoder.JSONDecodeError as decode_err: # If LLM returns bad string
            if not silent:
                print('Ollama returned bad JSON string:\n{}'.format(response))
            desc_dicts.append(None) # Append None == null
        
        if not silent:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')
    
    # Return characteristics as array of dict
    return desc_dicts

def desc2list(sys_prompt, prompt, descs, client, model = 'desc2matrix', silent = False):
    # List to store list strings
    liststrs = []

    # Pass descriptions to LLM for response
    for i, desc in enumerate(descs):
        start = 0
        if not silent:
            print('desc2list: processing {}/{}... '.format(i+1, len(descs)), end = '', flush = True)
            start = time.time()

        response = client.generate(model = model,
                                prompt = prompt + '\n' + desc,
                                system = sys_prompt)['response']
        liststrs.append(response)

        if not silent:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')
    
    return liststrs

def list2dict(sys_prompt, prompt, liststrs, client, model = 'desc2matrix', silent = False):
    # List to store dicts
    desc_dicts = []

    # Pass liststrs to LLM for response
    for i, liststr in enumerate(liststrs):
        start = 0
        if not silent:
            print('list2dict: processing {}/{}... '.format(i+1, len(liststrs)), end = '', flush = True)
            start = time.time()
        
        # Generate response
        response = client.generate(model = 'desc2matrix',
                            prompt = prompt + '\n' + liststr,
                            system = sys_prompt)['response']
        # Attempt to parse response to dict
        try:
            resp_dict = json.loads(response)
            # Check validity / regularise dict
            reg_resp_dict = regularise_dict(resp_dict)
            if reg_resp_dict != False:
                desc_dicts.append(reg_resp_dict)
            else:
                if not silent:
                    print('Ollama output is JSON but is structured badly:\n{}'.format(str(resp_dict)))
                desc_dicts.append(None) # Append None == null if not valid
        except json.decoder.JSONDecodeError as decode_err: # If LLM returns bad string
            if not silent:
                print('Ollama returned bad JSON string:\n{}'.format(response))
            desc_dicts.append(None) # Append None == null
        
        if not silent:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')

    return desc_dicts

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Extract JSON/dict from description files')

    # Add the arguments
    parser.add_argument('descfile', type = str, help = 'File containing the descriptions produced by dwca2csv.py')
    parser.add_argument('outputfile', type = str, help = 'File to write JSON to')
    parser.add_argument('--mode', required = True, type = str, choices = ['desc2dict', 'desc2list2dict'], help = 'Transcription mode to use')
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
    if(args.mode == 'desc2dict'):

        # Open & read sys_prompt.txt and prompt.txt
        prompt_fnames = ['sys_prompt.txt', 'prompt.txt']
        prompt_ftypes = ['sys_prompt', 'prompt']
        prompts = {}

        for fname, ftype in zip(prompt_fnames, prompt_ftypes):
            with open(os.path.join(args.promptsdir, fname), 'r') as fp:
                prompts[ftype] = fp.read()

        descdicts = desc2dict(prompts['sys_prompt'], prompts['prompt'], descs, client, silent = args.silent == True)

        # Build output JSON
        outdict = [{
            'coreid': descdf.iloc[rowid]['coreid'],
            'original_description': descdf.iloc[rowid]['description'],
            'char_json': dd
        } for rowid, dd in enumerate(descdicts)]

    elif(args.mode == 'desc2list2dict'):

        # Open & read d2l_sys_prompt.txt, d2l_prompt.txt, l2d_sys_prompt.txt, l2d_prompt.txt
        prompt_fnames = ['d2l_sys_prompt.txt', 'd2l_prompt.txt', 'l2d_sys_prompt.txt', 'l2d_prompt.txt']
        prompt_ftypes = ['d2l_sys_prompt', 'd2l_prompt', 'l2d_sys_prompt', 'l2d_prompt']
        prompts = {}

        for fname, ftype in zip(prompt_fnames, prompt_ftypes):
            with open(os.path.join(args.promptsdir, fname), 'r') as fp:
                prompts[ftype] = fp.read()
        
        desclists = desc2list(prompts['d2l_sys_prompt'], prompts['d2l_prompt'], descs, client, silent = args.silent == True)
        descdicts = list2dict(prompts['l2d_sys_prompt'], prompts['l2d_prompt'], desclists, client, silent = args.silent == True)

        # Build output JSON
        outdict = [{
            'coreid': descdf.iloc[rowid]['coreid'],
            'original_description': descdf.iloc[rowid]['description'],
            'char_list': dl,
            'char_json': dd
        } for rowid, dl, dd in zip(list(range(0, len(descdicts))), desclists, descdicts)]

    # Write output as JSON
    with open(args.outputfile, 'w') as outfile:
        json.dump(outdict, outfile)

if __name__ == '__main__':
    main()