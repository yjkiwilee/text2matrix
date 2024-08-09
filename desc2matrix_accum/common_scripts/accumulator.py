"""
Script for defining TraitAccumulator classes.
"""

from typing import List, Optional
import time
import json
import copy

from common_scripts import regularise, process_words
from common_scripts.llmcharjsonprocessor import LLMCharJSONProcessor

class TraitAccumulator(LLMCharJSONProcessor):
    """
    Base trait accumulator class, used in desc2matrix_accum.py
    """

    # Run mode name in the summary output
    RUN_MODE_NAME = 'desc2json_accum'

    def __init__(self,
                 sys_prompt:str,
                 init_prompt:str,
                 accum_prompt:str,
                 base_llm:str,
                 llm_params:dict,
                 llm_name:str = 'desc2matrix',
                 host_url:str = 'http://localhost:11434'):
        """
        Initialise trait accumulator.

        Parameters:
            sys_prompt (str): The system prompt to use
            init_prompt (str): The prompt to use to get the initial list of traits, either by tabulation or from a single species
            accum_prompt (str): The prompt to use for trait accumulation
            base_llm (str): Name of the base LLM to use
            llm_params (dict): Dictionary specifying model parameters as specified here: https://github.com/ollama/ollama/blob/main/docs/modelfile.md
            llm_name (str): The name of the model to create. Defaults to 'desc2matrix'
            host_url (str): The Ollama host url to use. Defaults to 'http://localhost:11434'
        """
        
        # Run super initialiser
        super().__init__(sys_prompt, base_llm, llm_params, llm_name, host_url)

        # Store parameters
        self.init_prompt = init_prompt
        self.accum_prompt = accum_prompt

        # Variable to store characteristic list history
        self.charlist_history:List[List[str]] = []

    def extract_init_chars(self, desc:str, show_log:bool = False) -> List[str]:
        """
        Function for extracting the initial list of characteristics from a single species description.
        The initial list of characteristics is stored in the object and returned.
        
        Parameters:
            desc (str): The description to extract the initial characteristics from
            show_log (bool): If this is set to True, show progress logs. Default is False
        
        Returns:
            init_charlist (List[str]): The initial list of characteristic names
        """

        # Prepare prompt
        prompt_wcontent = self.accum_prompt.replace('[DESCRIPTION]', desc) # Insert species description

        # Generate LLM output for the description
        char_json = self.prompt2charjson(prompt_wcontent, show_log = show_log)
        
        # Extract list of characteristics (empty list if the run didn't succeed)
        init_charlist = ([char['characteristic'] for char in char_json['data']]
                         if char_json['status'] == 'success' else [])

        # Store list of characteristics
        self.charlist_history = [init_charlist]
        
        # Return extracted initial list of characteristics
        return init_charlist
    
    def accum_step(self, desc:str, show_log:bool = False) -> List[str]:
        """
        Function for a step in the accumulation process, where the traits are extracted from an
        additional species and the list of characteristics is updated if
        the new list of characteristics is longer than the most recent list.
        This function returns the latest list of traits that results.
        
        Parameters:
            desc (str): The description to extract the characteristics from
            show_log (bool): If this is set to True, show progress logs. Default is False
        
        Returns:
            new_charlist (List[str]): The new list of characteristic names
        """

        # Check if charlist has been initialised
        if self.charlist_history == []:
            raise Exception("Charlist has not been initialised. You must run extract_init_chars() first before running accum_step().")

        # Get the latest list of characteristics
        last_charlist = self.charlist_history[len(self.charlist_history) - 1]

        # Prepare prompt
        prompt_wcontent = self.accum_prompt.replace('[DESCRIPTION]', desc) # Insert species description
        prompt_wcontent = prompt_wcontent.replace('[CHARACTER_LIST]', '; '.join(last_charlist)) # Insert characteristics

        # Generate output with predetermined character list
        char_json = self.prompt2charjson(prompt_wcontent, show_log = show_log)

        # Extract list of characteristics (copy of latest list if run didn't succeed)
        new_charlist = ([char['characteristic'] for char in char_json['data']]
                         if char_json['status'] == 'success' else copy.deepcopy(last_charlist))
        
        # If the new list of characteristics is shorter than the previous one, override with the previous one
        new_charlist = new_charlist if len(new_charlist) > len(last_charlist) else copy.deepcopy(last_charlist)

        # Store list of characteristics
        self.charlist_history.append(new_charlist)

        # Update sp_chars
        self.sp_chars.append({
            'status': char_json['status'], # Status: one of 'success', 'bad_structure', 'invalid_json'
            'original_description': desc,
            'char_json': char_json['data'] if char_json['status'] == 'success' else None, # Only use this if parsing succeeded
            'failed_str': char_json['data'] if char_json['status'] != 'success' else None # Only use this if parsing failed
        })

        # Return new list of characteristics
        return new_charlist
    
    def get_summary(self) -> dict:
        """
        Function for getting the summary of the accumulation run.
        The output dictionary is structured as follows:
        {
            'metadata': {
                'params': model parameters,
                'mode': run mode name,
                'sys_prompt': system prompt used,
                'init_prompt': initial trait extraction / tabulation prompt,
                'prompt': accumulation prompt
            },
            'data': sp_chars data,
            'charlist_len_history': list of the charlist lengths,
            'charlist_history': list of the charlists used
        }
        
        Parameters:
            None
        
        Returns:
            outdict (dict): Dictionary summary of the run
        """

        # Run super get_summary()
        outdict = super().get_summary()

        # Add some keys to metadata
        outdict['metadata'] = dict(
            outdict['metadata'],
            init_prompt = self.init_prompt,
            prompt = self.accum_prompt
        )

        # Add charlist lengths and history as data
        outdict = dict(
            outdict,
            charlist_len_history = [len(charlist) for charlist in self.charlist_history],
            charlist_history = self.charlist_history
        )

        # Return summary dictionary
        return outdict

class TabTraitAccumulator(TraitAccumulator):
    """
    Trait accumulator with initial tabulation, used in desc2matrix_accum_tab.py
    NB: For TabTraitAccumulator, init_prompt is the tabulation prompt.
    """

    # Run mode name in the summary output
    RUN_MODE_NAME = 'desc2json_accum_tab'

    def extract_init_chars(self, sp_ids:List[str], descs:List[str], show_log:bool = False) -> dict:
        """
        Function for extracting the initial list of characteristics by tabulating multiple species descriptions.
        The initial list of characteristics is stored in the object and returned.
        
        Parameters:
            prompt (str): The prompt to use for character extraction. '[DESCRIPTION]' in the string is replaced by the species description and '[CHARACTER_LIST]' is replaced by the provided list of characteristics.
            sp_ids (List[str]): The species IDs to use when building the list of descriptions to pass to the LLM.
            descs (List[str]): The botanical descriptions of the plant species.
            show_log (bool): If this is set to True, it will show the status of each run. Default is False.
        
        Returns:
            init_charlist (List[str]): The initial list of characteristic names
        """

        # Build description string
        # NB: the species ID is a 'made-up' wfo id.
        desc_str = '\n\n'.join(['Species ID: {}\n\nSpecies description:\n{}'.format(spid, desc) for spid, desc in zip(sp_ids, descs)])

        # Build prompt string
        prompt_wcontent = self.init_prompt.replace('[DESCRIPTIONS]', desc_str)
        
        # Generate LLM output for the description
        # NB: The regulariser for table output must be used here.
        char_json = self.prompt2charjson(prompt_wcontent, regulariser = regularise.regularise_table, show_log = show_log)

        # Extract list of characteristics (empty list if the run didn't succeed)
        init_charlist = ([char['characteristic'] for char in char_json['data']]
                         if char_json['status'] == 'success' else [])

        # Store list of characteristics
        self.charlist_history = [init_charlist]
        
        # Return extracted initial list of characteristics
        return init_charlist
    
class FollowupTraitAccumulator(TraitAccumulator):
    """
    Trait accumulator with follow-up questions and without tabulation, currently only used internally
    """

    # Run mode name in the summary output
    RUN_MODE_NAME = 'desc2json_accum_followup'

    def __init__(self,
                 sys_prompt:str,
                 init_prompt:str,
                 accum_prompt:str,
                 f_prompt:str,
                 base_llm:str,
                 llm_params:dict,
                 llm_name:str = 'desc2matrix',
                 host_url:str = 'http://localhost:11434'):
        """
        Initialise trait accumulator.

        Parameters:
            sys_prompt (str): The system prompt to use
            init_prompt (str): The prompt to use to get the initial list of traits, either by tabulation or from a single species
            accum_prompt (str): The prompt to use for trait accumulation
            f_prompt (str): The follow-up prompt
            base_llm (str): Name of the base LLM to use
            llm_params (dict): Dictionary specifying model parameters as specified here: https://github.com/ollama/ollama/blob/main/docs/modelfile.md
            llm_name (str): The name of the model to create. Defaults to 'desc2matrix'
            host_url (str): The Ollama host url to use. Defaults to 'http://localhost:11434'
        """

        # Store follow-up prompt
        self.f_prompt = f_prompt

        # Run superclass initiator to store parameters and initialist Ollama model
        super().__init__(sys_prompt, init_prompt, accum_prompt, base_llm, llm_params, llm_name, host_url)

    def accum_step(self, desc:str, chars:List[str] = None, show_log:bool = False):
        """
        Function for a step in the accumulation process, where the traits are extracted from an
        additional species and the list of characteristics is updated if
        the new list of characteristics is longer than the most recent list.
        This version of the function asks the LLM a 'follow-up' question at each step,
        which includes a list of words in the original description that it has omitted
        in the initial response. This is to increase the completeness of characteristics retrieved.
        This function returns the latest list of traits that results.

        Parameters:
            desc (str): The botanical description of the plant species.
            chars (List[str]): The list of characteristic names to extract values of.
            show_log (bool): If this is set to True, the function will output a log of the run status. Default is False.

        Returns:
            new_charlist (List[str]): The new list of characteristic names
        """

        # Check if charlist has been initialised
        if self.charlist_history == []:
            raise Exception("Charlist has not been initialised. You must run extract_init_chars() first before running accum_step().")

        # Get the latest list of characteristics
        last_charlist = self.charlist_history[len(self.charlist_history) - 1]

        # Variable to store the char_json output from LLM
        char_json = {}

        # Prepare prompt
        prompt_wcontent = self.accum_prompt.replace('[DESCRIPTION]', desc) # Insert species description
        prompt_wcontent = prompt_wcontent.replace('[CHARACTER_LIST]', '; '.join(chars)) # Insert characteristics

        # Generate initial response
        char_json = self.prompt2charjson(prompt_wcontent, show_log = show_log)

        if(char_json['status'] != 'success'): # If initial JSON output was invalid or badly structured
            # Just proceed to updating list of chracteristics
            pass
        else: # If the initial JSON output successfully parsed
            # Extract the char_json response data
            init_charjson_dat = char_json['data']
            
            # Retrieve omissions
            omissions = process_words.get_omissions(desc, init_charjson_dat)

            # Build the follow-up prompt
            followup_prompt = self.f_prompt.replace('[DESCRIPTION]', desc).replace('[MISSING_WORDS]', '; '.join(sorted(omissions))).replace('[CHARACTER_LIST]', '; '.join(chars))

            # Build the messages
            messages = [
                {'role': 'system', 'content': self.sys_prompt}, 
                {'role': 'user', 'content': self.accum_prompt.replace('[DESCRIPTION]', desc)},
                {'role': 'assistant', 'content': json.dumps(init_charjson_dat, indent=4)}, # 'Simulate' the previous model output
                {'role': 'user', 'content': followup_prompt}
            ]

            # Generate followup response
            f_char_json = self.messages2charjson(messages, show_log)

            # Add '_followup' to status code if the output failed to parse
            if f_char_json['status'] != 'success':
                f_char_json['status'] = '{}_followup'.format(f_char_json['status'])

            # Set char_json as f_char_json
            char_json = f_char_json

        # Extract list of characteristics (copy of latest list if run didn't succeed)
        new_charlist = ([char['characteristic'] for char in char_json['data']]
                         if char_json['status'] == 'success' else copy.deepcopy(last_charlist))
        
        # If the new list of characteristics is shorter than the previous one, override with the previous one
        new_charlist = new_charlist if len(new_charlist) > len(last_charlist) else copy.deepcopy(last_charlist)

        # Store list of characteristics
        self.charlist_history.append(new_charlist)

        # Update sp_chars
        self.sp_chars.append({
            'status': char_json['status'], # Status: one of 'success', 'bad_structure', 'invalid_json', 'bad_structure_followup', 'invalid_json_followup'
            'original_description': desc,
            'char_json': char_json['data'] if char_json['status'] == 'success' else None, # Only use this if parsing succeeded
            'failed_str': char_json['data'] if char_json['status'] != 'success' else None # Only use this if parsing failed
        })

        # Return new list of characteristics
        return new_charlist
    
    def get_summary(self) -> dict:
        """
        Function for getting the summary of the accumulation run.
        The output dictionary is structured as follows:
        {
            'metadata': {
                'params': model parameters,
                'mode': run mode name,
                'sys_prompt': system prompt,
                'init_prompt': initial trait extraction prompt,
                'f_prompt': follow-up prompt
            },
            'data': sp_chars data
            'charlist_len_history': list of the charlist lengths,
            'charlist_history': list of the charlists used
        }
        
        Parameters:
            None
        
        Returns:
            outdict (dict): Dictionary summary of the run
        """

        # Dictionary to store the final output along with metadata
        outdict = super().get_summary()

        # Add follow-up prompt
        outdict['metadata']['f_prompt'] = self.f_prompt

        # Return summary dictionary
        return outdict
    
class TFTraitAccumulator(TabTraitAccumulator, FollowupTraitAccumulator):
    """
    Trait accumulator that does both initial trait tabulation and follow-up questions.
    This is effectively used in desc2matrix_accum_followup.py.
    """

    RUN_MODE_NAME = 'desc2json_accum_tf'