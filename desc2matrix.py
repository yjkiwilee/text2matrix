import argparse
import json
from ollama import Client

def desc2dict(parent_model, params, sys_prompt, prompt, descriptions, host = 'http://localhost:11434', new_model = 'desc2matrix'):
    # Build modelfile
    modelfile = '{}\n{}'.format(
        'FROM {}'.format(parent_model),
        '\n'.join(['PARAMETER {} {}'.format(param, value) for param, value in params.items()])
    )

    # Make connection to client
    client = Client(host = host)

    # Create model with the specified params
    client.create(model = new_model, modelfile = modelfile)

    # Pass descriptions to LLM for response
    desc_dicts = []

    for description in descriptions:
        # Generate response while specifying system prompt
        response = client.generate(model = new_model,
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

def desc2list(desc, ollama):
    sys_prompt = """
You are a diligent robot assistant made by a botanist. You have expert knowledge of botanical terminology.
Your goal is to extract a list of characteristics that are mentioned in the botanical description of a species.
Output only the list of characteristics, with no other text.
    """

    prompt = """
You are given a botanical description of a plant species.
List EVERY SINGLE characteristics mentioned in this description and their corresponding values in bullet points.
Try to include every word present in the description except stop words. Stop words are commonly used words like articles (e.g. 'the', 'a', 'an') which do not carry botanical information.
Follow the instructions below.

Instructions:

1. List all the characteristics relating to the whole plant, such as growth form, plant height, and branching.

2. Iterate through every mentioned organs (e.g. leaf, flower, fruit, tuber) and parts of organs (e.g. stipule, anther, ovary) and list their corresponding characteristics.
The length, width, shape, color, surface texture, surface features, and arrangement of each organ or part of an organ must be separate characteristics.
You may nest the list as needed.

3. In your response, you must include every word in the description except stop words. Stop words are commonly used words like articles (e.g. 'the', 'a', 'an') which do not carry botanical information.

You must follow all the rules below:

A. The value of each characteristic must be shorter than 5 words. If a value is 5 words or longer, break the characteristic down to smaller characteristics.
B. The names of organs must be written in singular form. For example, write 'stem' not 'stems', 'fruit' not 'fruits'.
C. Only list characteristics that were explicitly mentioned in the description.
D. Do not list characteristics that were not mentioned in the description.
E. Use botanical terms from the description where possible and do not paraphrase.
F. Each numeric characteristic should be given as a single value, multiple values, or a range, together with the unit.
G. Include only the number and the unit in the value of a numeric characteristic.

Description:

{}
    """

    # Fetch response
    response = ollama.generate(model = 'desc2matrix',
                            prompt = prompt.format(desc),
                            system = sys_prompt)['response']
    
    return response

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

        # Pass to desc2dict to extract descriptions as dict
        descdict = desc2dict(parent_model = args.model,
                             params = {'temperature': args.temperature, 'seed': args.seed},
                             sys_prompt = sys_prompt,
                             prompt = prompt,
                             descriptions = descs)
        
        # Write dict as json
        with open(args.outputfile, 'w') as outfile:
            json.dump(descdict, outfile)

if __name__ == '__main__':
    main()