"""
Script for defining TraitExtractor classes.
"""

from typing import List
import time

from common_scripts.llmcharjsonprocessor import LLMCharJSONProcessor

class TraitExtractor(LLMCharJSONProcessor):
    """
    Base trait extractor class, used in desc2matrix_wcharlist.py
    """

    # Run mode name in the summary output
    RUN_MODE_NAME = 'desc2json_wcharlist'

    def __init__(self,
                 sys_prompt:str,
                 ext_prompt:str,
                 ext_chars:List[str],
                 base_llm:str,
                 llm_params:dict,
                 llm_name:str = 'desc2matrix',
                 host_url:str = 'http://localhost:11434'):
        """
        Initialise trait extractor.

        Parameters:
            sys_prompt (str): The system prompt to use
            ext_prompt (str): The prompt to use for trait extraction
            ext_chars (List[str]): The list of characteristics to extract
            base_llm (str): Name of the base LLM to use
            llm_params (dict): Dictionary specifying model parameters as specified here: https://github.com/ollama/ollama/blob/main/docs/modelfile.md
            llm_name (str): The name of the model to create. Defaults to 'desc2matrix'
            host_url (str): The Ollama host url to use. Defaults to 'http://localhost:11434'
        """

        # Store ext_prompt and ext_chars
        self.ext_prompt = ext_prompt
        self.ext_chars = ext_chars

        # Run super initialiser
        super().__init__(sys_prompt, base_llm, llm_params, llm_name, host_url)
    
    def ext_step(self, desc:str, show_log:bool = False) -> List[str]:
        """
        Function for a step in the extraction process, where the traits are extracted from an
        additional species and stored.
        This function returns the charjson produced by the given description.
        
        Parameters:
            desc (str): The description to extract the characteristics from
            show_log (bool): If this is set to True, show progress logs. Default is False
        
        Returns:
            char_json (List[str]): The char_json produced from the given description
        """

        # Variable to store the extracted characteristics and values
        char_json = {}

        start = 0
        if show_log:
            print('desc2json: processing... ', end = '', flush = True)
            start = time.time()

        # Prepare prompt
        prompt_wcontent = self.ext_prompt.replace('[DESCRIPTION]', desc) # Insert species description
        prompt_wcontent = prompt_wcontent.replace('[CHARACTER_LIST]', '; '.join(self.ext_chars)) # Insert characteristics
        
        # Generate output
        char_json = self.prompt2charjson(prompt_wcontent, show_log = show_log)
        
        if show_log:
            elapsed_t = time.time() - start
            print(f'done in {elapsed_t:.2f} s!')

        # Update sp_chars
        self.sp_chars.append({
            'status': char_json['status'], # Status: one of 'success', 'bad_structure', 'invalid_json'
            'original_description': desc,
            'char_json': char_json['data'] if char_json['status'] == 'success' else None, # Only use this if parsing succeeded
            'failed_str': char_json['data'] if char_json['status'] != 'success' else None # Only use this if parsing failed
        })

        # Return extracted characteristics
        return char_json
    
    def get_summary(self) -> dict:
        """
        Function for getting the summary of the extraction run.
        The output dictionary is structured as follows:
        {
            'sys_prompt': system prompt,
            'prompt': accumulation prompt,
            'params': model parameters,
            'mode': run mode name ('desc2json_wcharlist'),
            'charlist': list of characteristics used,
            'data': sp_chars data
        }
        
        Parameters:
            None
        
        Returns:
            outdict (dict): Dictionary summary of the run
        """

        # Run super get_summary()
        outdict = super().get_summary()

        # Add some keys
        outdict = dict(outdict,
                       prompt = self.ext_prompt,
                       charlist = self.ext_chars,
                       data = self.sp_chars)
        
        # Re-order keys
        keyorder = ['sys_prompt', 'prompt', 'params', 'mode', 'charlist', 'data']
        outdict = {
            k: outdict[k] for k in keyorder if k in outdict
        }

        # Return summary dictionary
        return outdict