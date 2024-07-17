import argparse
import json
from ollama import Client
import os

def desc2dict(sys_prompt, prompt, descriptions, client, model = 'desc2matrix'):
    # Pass descriptions to LLM for response
    desc_dicts = []

    for description in descriptions:
        # Generate response while specifying system prompt
        response = client.generate(model = model,
                                   prompt = prompt + '\n' + description,
                                   system = sys_prompt)['response']

        # Attempt to parse prompt as JSON
        try:
            response_dict = json.loads(response)
            desc_dicts.append(response_dict)
        except json.decoder.JSONDecodeError as decode_err: # Throw error if LLM returns bad string
            print('Ollama returned bad JSON string:\n{}'.format(response))
            raise decode_err
    
    # Return characteristics as array of dict
    return desc_dicts

def desc2list(sys_prompt, prompt, descs, client, model = 'desc2matrix'):
    # List to store list strings
    liststrs = []

    # Pass descriptions to LLM for response
    for desc in descs:
        response = client.generate(model = model,
                                prompt = prompt + '\n' + desc,
                                system = sys_prompt)['response']
        liststrs.append(response)
    
    return liststrs

def list2dict(sys_prompt, prompt, liststrs, client, model = 'desc2matrix'):
    # List to store dicts
    desc_dicts = []

    # Pass liststrs to LLM for response
    for liststr in liststrs:
        # Generate response
        response = client.generate(model = 'desc2matrix',
                            prompt = prompt + '\n' + liststr,
                            system = sys_prompt)['response']
        # Parse response to dict
        resp_dict = json.loads(response)
        # Add to list
        desc_dicts.append(resp_dict)

    return desc_dicts

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Extract JSON/dict from description files')

    # Add the arguments
    parser.add_argument('descfile', type = str, help = 'File containing the descriptions separated by newline')
    parser.add_argument('outputfile', type = str, help = 'File to write JSON to')
    parser.add_argument('--mode', required = True, type = str, choices = ['desc2dict', 'desc2list2dict'], help = 'Transcription mode to use')
    parser.add_argument('--model', required = False, type = str, default = 'llama3', help = 'Name of base LLM to use')
    parser.add_argument('--temperature', required = False, type = float, default = 0.1, help = 'Model temperature between 0 and 1')
    parser.add_argument('--seed', required = False, type = int, default = 0, help = 'Model seed value')
    parser.add_argument('--promptsdir', required = False, type = str, default = './prompts', help = 'Folder storing the prompt files')

    # Parse the arguments
    args = parser.parse_args()

    # Open descfile
    with open(args.descfile, 'r') as descfile:
        # Read relevant files
        descs = descfile.read().split('\n')

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

        # Check given transcription mode
        if(args.mode == 'desc2dict'):

            # Open & read sys_prompt.txt and prompt.txt
            prompt_fnames = ['sys_prompt.txt', 'prompt.txt']
            prompt_ftypes = ['sys_prompt', 'prompt']
            prompts = {}

            for fname, ftype in zip(prompt_fnames, prompt_ftypes):
                with open(os.path.join(args.promptsdir, fname), 'r') as fp:
                    prompts[ftype] = fp.read()

            descdict = desc2dict(prompts['sys_prompt'], prompts['prompt'], descs, client)

        elif(args.mode == 'desc2list2dict'):

            # Open & read d2l_sys_prompt.txt, d2l_prompt.txt, l2d_sys_prompt.txt, l2d_prompt.txt
            prompt_fnames = ['d2l_sys_prompt.txt', 'd2l_prompt.txt', 'l2d_sys_prompt.txt', 'l2d_prompt.txt']
            prompt_ftypes = ['d2l_sys_prompt', 'd2l_prompt', 'l2d_sys_prompt', 'l2d_prompt']
            prompts = {}

            for fname, ftype in zip(prompt_fnames, prompt_ftypes):
                with open(os.path.join(args.promptsdir, fname), 'r') as fp:
                    prompts[ftype] = fp.read()
            
            desclists = desc2list(prompts['d2l_sys_prompt'], prompts['d2l_prompt'], descs, client)
            # descdict = list2dict(prompts['l2d_sys_prompt'], prompts['l2d_prompt'], descs, client)
            descdict = desclists
        
        # Write dict as json
        with open(args.outputfile, 'w') as outfile:
            # json.dump(descdict, outfile)
            outfile.write(descdict[0])

if __name__ == '__main__':
    main()