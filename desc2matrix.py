import argparse
import json
from ollama import Client

def desc2dict(sys_prompt, prompt, descriptions, client, model = 'desc2matrix'):
    # Pass descriptions to LLM for response
    desc_dicts = []

    for description in descriptions:
        # Generate response while specifying system prompt
        response = client.generate(model = model,
                                   prompt = '{}\nDescription:\n{}'.format(prompt, description),
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
        response = client.generate(model = 'desc2matrix',
                                prompt = prompt.format(desc),
                                system = sys_prompt)['response']
        liststrs.append(response)
    
    return liststrs

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description = 'Extract JSON/dict from description files')

    # Add the arguments
    parser.add_argument('descfile', type = str, help = 'File containing the descriptions separated by newline')
    parser.add_argument('outputfile', type = str, help = 'File to write JSON to')
    parser.add_argument('--model', required = False, type = str, default = 'llama3', help = 'Name of base LLM to use')
    parser.add_argument('--temperature', required = False, type = float, default = 0.1, help = 'Model temperature between 0 and 1')
    parser.add_argument('--seed', required = False, type = int, default = 0, help = 'Model seed value')
    parser.add_argument('--sys_prompt', required = False, type = str, help = 'Text file with the system prompt')
    parser.add_argument('--prompt', required = False, type = str, help = 'Text file with the prompt')

    # Parse the arguments
    args = parser.parse_args()

    # Set default prompt.txt and sys_prompt.txt URL if not given
    if args.sys_prompt == None:
        args.sys_prompt = './prompts/prompt.txt'
    if args.prompt == None:
        args.prompt = './prompts/sys_prompt.txt'

    # Open descfile
    with open(args.descfile, 'r') as descfile, open(args.sys_prompt, 'r') as syspromptfile, open(args.prompt, 'r') as promptfile:
        # Read relevant files
        descs = descfile.read().split('\n')
        sys_prompt = syspromptfile.read()
        prompt = promptfile.read()

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

        # Pass to desc2dict to extract descriptions as dict
        descdict = desc2dict(sys_prompt, prompt, descs, client)
        
        # Write dict as json
        with open(args.outputfile, 'w') as outfile:
            json.dump(descdict, outfile)

if __name__ == '__main__':
    main()