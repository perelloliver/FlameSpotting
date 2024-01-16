#!pip install langchain openai tiktoken
######### I want to try this with Cohere
######## Using a frozen gpt-3.5 edition, chatGPT and gpt-4 been really bad lately

import langchain
import openai
import tiktoken
import os
import json
import numpy as np
import pandas as pd
import random
import math
from math import ceil


from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain import OpenAI
import re
import itertools
from itertools import islice

#Import our modules

from prompts import *
from policies import *

#Set API key here

os.environ["OPENAI_API_KEY"] = "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"
llm =ChatOpenAI(model_name="gpt-3.5-turbo-1106", temperature=0)

#These prompts are to be situated within an overall agent structure in future, not just as API chains
#Also only using langchain for testing purposes, not suitable for deployment
#We're testing base effectiveness of the process here

#####DEBUG NOTES: I'm debugging this script rn - issue with 'template' - does it need to be prompt? P sure it's template.

## Prompt templates ##
attention_prompt = PromptTemplate(input_variables=["chat_stream"], template = attention)
moderation_prompt = PromptTemplate(input_variables=["chat_stream"], template = moderation)
summary_prompt = PromptTemplate(input_variables=["chat_stream", "result"], template= summary)
s2a_2score_prompt = PromptTemplate(input_variables=["debiased_summary", "score", "assignment_score"], template =s2a_2score)
s2a_prompt = PromptTemplate(input_variables=["summary"], template= s2a_summary)
# verify_score_prompt = PromptTemplate(input_variables=["policies", "summary", "score"], template =verify_score)

## Chains ##
attention_chain = LLMChain(llm=llm, prompt=attention_prompt, verbose=False)
moderation_chain = LLMChain(llm=llm, prompt=moderation_prompt, verbose=False)
summary_chain = LLMChain(llm=llm, prompt=summary_prompt, verbose=False)
s2a_chain = LLMChain(llm=llm, prompt=s2a_prompt)
s2a_2score_chain = LLMChain(llm=llm, prompt=s2a_2score_prompt)
# verify_score_chain = LLMChain(llm=llm, prompt=verify_score_prompt)

# Function to check if a dictionary contains all required keys
def has_required_keys(data, required_keys):
    return all(key in data for key in required_keys)

#text formatting
def remove_backslashes(dictionary):
    keys_to_remove = []
    for key, value in dictionary.items():
        new_key = re.sub(r"\\", "", key)
        if new_key != key:
            keys_to_remove.append(key)
        
        if isinstance(value, str):
            dictionary[new_key] = re.sub(r"\\", "", value)
        elif isinstance(value, list):
            for i in range(len(value)):
                if isinstance(value[i], str):
                    value[i] = re.sub(r"\\", "", value[i])
        else:
            continue  # Skip non-string values

    for key in keys_to_remove:
        del dictionary[key]

    return dictionary


#### Run #######

def process_data(data, start_batch_index:int, num_batches:int, batch_size:int):
    final_json_result = {}
    parsed_results = {}
    failures = []
    attended_chats = []

    chain_mapping = {
        'moderation_chain': moderation_chain,
        'summary_chain': summary_chain,
        's2a_chain': s2a_chain,
        's2a_2score_chain': s2a_2score_chain,
        # 'verify_score_chain': verify_score_chain
    }


    for batch_index in range(start_batch_index, num_batches):
        start_index = batch_index * batch_size
        end_index = min((batch_index + 1) * batch_size, num_instances)
        current_batch_keys = list(data.keys())[start_index:end_index]
        current_batch = {key: data[key] for key in current_batch_keys}

        for index, (id, i) in enumerate(current_batch.items()):

            attention = attention_chain.run(
                chat_stream=i['chat_stream'],
                policies=fates_policies
            ).lower()

            if 'true' in attention:
                print("Chat instance:", start_index + index, "Out of instances:", len(data))
                attended_chats.append(id)

                current_failures = []
                parsed_results = {}

                result_a = moderation_chain.run(
                    chat_stream=i['chat_stream'],
                    policies=fates_policies
                ).lower().replace('\\', '').replace('\n', '').strip()
                # Parse result_a as a JSON object
                try:
                    json_result_a = json.loads(result_a)
                    required_keys_result_a = ['users', 'initial score', 'evidence', 'initial assignment', 'initial decision']
                    if has_required_keys(json_result_a, required_keys_result_a):
                        parsed_results.update(json_result_a)
                    else:
                        # print("It happened at result A")
                        current_failures.append((id, 'result_a_missing_keys'))
                except json.JSONDecodeError as e:
                    error_message = f"JSON decoding error for instance ID {id}: {e}"
                    print(error_message)
                    print(result_a)
                    # Handle the error based on your requirements within current_failures
                    current_failures.append((id, error_message))

                result_b = summary_chain.run(
                    chat_stream=i['chat_stream'],

                    result=result_a
                ).lower().replace("\\", '').replace('\n', '').strip()

                result_c = s2a_chain.run(
                    summary=result_b
                ).lower().replace('\\', "").replace('\n', '').strip()

                result_d = s2a_2score_chain.run(
                    debiased_summary=result_c,
                    score=json_result_a['initial score'],
                    assignment_score=json_result_a['initial assignment'],
                ).lower().replace('\\', '').replace('\n', '').strip()
 
                # result_e = verify_score_chain.run(
                #     policies=fates_policies,
                #     summary=result_c ,
                #     score=result_d
                # ).lower()
                
                #Parse result_d as a JSON object
                try:
                    json_result_d = json.loads(result_d)
                    required_keys_result_d = ["final score", "final assignment score"]
                    if has_required_keys(json_result_d, required_keys_result_d):
                        parsed_results.update(json_result_d)
                    else:
                        # print("IT HAPPENED AT RESULT D")
                        # print(result_d)
                        # print(json_result_d)
                        current_failures.append((id, 'result_d_missing_keys'))
                except json.JSONDecodeError as d:
                    error_message = f"JSON decoding error for instance ID {id}: {d}"
                    print(error_message)
                    print(result_d)
                    # Handle the error based on your requirements within current_failures
                    current_failures.append((id, error_message))

                # Assign other results as single values to keys
                parsed_results.update({
                    "second summary": result_b,
                    "debiased summary": result_c,
                })

                # Check for None values in other results and add to failures if necessary
                for key, value in parsed_results.items():
                    if value is None:
                        # print("IT HAPPENED IN FINAL PARSED RESULTS")
                        current_failures.append((id, key))

                # Convert parsed_results to JSON
                final_json_result[id] = json.dumps(parsed_results)
                # print(final_json_result[id])
                # print(final_json_result)

#### Allow ONE repeat if this fails.
#### Definitely a more pythonic route for this just need to wrap up the JSON issue

                if len(current_failures) > 0:
                  print("Failure encountered, reattempting!")
                  current_failures = []
                  parsed_results = {}

                  result_a = moderation_chain.run(
                      chat_stream=i['chat_stream'],
    
                      policies=fates_policies
                  ).lower()
                  print(result_a)
                  # Parse result_a as a JSON object
                  try:
                      json_result_a = json.loads(result_a)
                      required_keys_result_a = ['users', 'initial score', 'evidence', 'initial action score', 'initial decision']
                      if has_required_keys(json_result_a, required_keys_result_a):
                          parsed_results.update(json_result_a)
                      else:
                          current_failures.append((id, 'result_a_missing_keys'))
                  except json.JSONDecodeError as e:
                      error_message = f"JSON decoding error for instance ID {id}: {e}"
                      print(error_message)
                      # Handle the error based on your requirements within current_failures
                      current_failures.append((id, error_message))

                  result_b = summary_chain.run(
                      chat_stream=i['chat_stream'],
    
                      result=result_a
                  ).lower()
                  print(result_b)

                  result_c = s2a_chain.run(
                    summary=result_b
                    ).lower().replace('\\', '').replace('\n', '').strip()

                  result_d = s2a_2score_chain.run(
                    debiased_summary=result_c,
                    score=json_result_a['initial score'],
                    assignment_score=json_result_a['initial assignment'],
                    ).lower().replace('\\', '').replace('\n', '').strip()
  
                #   result_e = verify_score_chain.run(
                #       policies=fates_policies,
                #       summary=result_c ,
                #       score=result_d
                #   ).lower()
                  
                  #Parse result_e as a JSON object
                #   try:
                #       json_result_d = json.loads(result_d)
                #       required_keys_result_d = ["FINAL SCORE", "FINAL ASSIGNMENT SCORE"]
                #     if has_required_keys(json_result_d, required_keys_result_d):
                #         parsed_results.update(json_result_d)
                #     else:
                #           # Handle missing keys in result_e
                #           current_failures.append((id, 'result_e_missing_keys'))
                #   except json.JSONDecodeError as e:
                #       error_message = f"JSON decoding error for instance ID {id}: {e}"
                #       print(error_message)
                #       # Handle the error based on your requirements within current_failures
                #       current_failures.append((id, error_message))
                  
                try:
                    json_result_d = json.loads(result_d)
                    required_keys_result_d = ["final score", "final assignment score"]
                    if has_required_keys(json_result_d, required_keys_result_d):
                        parsed_results.update(json_result_d)
                    else:
                        # Handle missing keys in result_e
                        current_failures.append((id, 'result_d_missing_keys'))
                except json.JSONDecodeError as d:
                    error_message = f"JSON decoding error for instance ID {id}: {d}"
                    print(error_message)
                    print(result_d)
                    # Handle the error based on your requirements within current_failures
                    current_failures.append((id, error_message))

                  # Assign other results as single values to keys
                parsed_results.update({
                      "second summary": result_b,
                      "debiased summary": result_c,
                  })

                  # Check for None values in other results and add to failures if necessary
                for key, value in parsed_results.items():
                      if value is None:
                          current_failures.append((id, key))

                parsed_results = remove_backslashes(parsed_results)
                  # Convert parsed_results to JSON
                final_json_result[id] = json.dumps(parsed_results)
                #   print(final_json_result[id])
                #   print(final_json_result)

                if current_failures:
                    failures.append(id)
                
        final_json_result['failures'] = failures

    return final_json_result


#load data

def load_data(filepath):
    with open (filepath, 'r') as json_file:
        data = json.load(json_file)

    return data

def create_instances(data, chunk_size):
    instances = {}
    num_instances = ceil(len(data) / chunk_size)
    for i in range(num_instances):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size
        instance_data = data[start_idx:end_idx]
        instances[f"instance_{i}"] = {"chat_stream": instance_data}
    return instances

#can't get itertools take to import for some reason so just writing it here
def take(n, iterable):
    li = list(itertools.islice(iterable, n))
    if len(li) != n:
        raise RuntimeError("too short iterable for take")
    return li

input_folder_path = '/Users/mac/Documents/Moderation/files/FlameSpotting/partitioned_dataset'

output_folder_path = '/Users/mac/Documents/Moderation/files/FlameSpotting/Output_4Jan_30_Context_Window'


#Debug zone - instances_chat_streams has a different file structure so dont need instance creation

# instances = load_data('/Users/mac/Documents/Moderation/files/FlameSpotting/instances_chat_streams.json')
# data = {instance[0]: instance[1] for instance in instances.items()}

# batch_size = 100
# start_batch_index = 0
# num_instances = len(data)
# num_batches = (num_instances + batch_size - 1) // batch_size

# testresults, testfailures = process_data(data, start_batch_index, num_batches, batch_size)


###### Run on folder ########
# for idx, filename in enumerate(os.listdir(input_folder_path)):
#     file_path = os.path.join(input_folder_path, filename)

#     data = load_data(file_path)
#     chunk_size = 15

#     instances = create_instances(data, chunk_size)

#     batch_size = 100
#     start_batch_index = 0

#     num_instances = len(data)
#     num_batches = (num_instances + batch_size - 1) // batch_size

#     testresults, testfailures = process_data(instances, start_batch_index, num_batches, batch_size)

#     output_filename = f'test-results{idx}.json'
#     output_filepath = os.path.join(output_folder_path, output_filename)

#     output_data = {
#         'results': testresults,
#         'failures': testfailures,
#     }

#     #Just for debug
#     print("############ RESULTS RESULTS RESULTS #############")
#     print(output_data)

#     with open (output_filepath, 'w') as output_file:
#         json.dump(output_data, output_file)

####### Run on Single File #############

filename = '/Users/mac/Documents/Moderation/files/FlameSpotting/partitioned_dataset/partitioned_dataset_1/chat_data_partition_5.json'
file_path = os.path.join(input_folder_path, filename)

data = load_data(file_path)
chunk_size = 30

instances = create_instances(data, chunk_size)
test = dict(take(1000, instances.items()))


batch_size = 10
start_batch_index = 0

num_instances = len(test)
num_batches = (num_instances + batch_size - 1) // batch_size

results = process_data(test, start_batch_index, num_batches, batch_size)

output_filename = f'section_5_1000_30context.json'
output_filepath = os.path.join(output_folder_path, output_filename)

#Just for debug
print("############ RESULTS RESULTS RESULTS #############")
print(results)

with open (output_filepath, 'w') as output_file:
    json.dump(results, output_file)
