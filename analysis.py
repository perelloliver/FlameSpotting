import json
import pandas as pd

def load_data(filepath_data, filepath_results):
    with open(filepath_data, 'r') as f:
        data = json.load(f)

    with open(filepath_results, 'r') as f:
        _results = json.load(f)

    results = _results

    instances = list(results.keys())

    result_data = []



    for instance in instances:
        if instance in results:
            if instance == 'failures':
                continue

            chat_data = results[instance]

            # Check the type and content of chat_data


            # Extract relevant message dictionaries from JSON 2
            start_index = int(instance.split('_')[1]) * 30
            end_index = start_index + 30
            relevant_messages = data[start_index:end_index]

            # Create a dictionary for each instance
            instance_data = {'message_data': relevant_messages}

            # Assuming chat_data is already a dictionary, update instance_data
            if isinstance(chat_data, dict):
                instance_data.update(chat_data)
            else:
                # Handle the case if chat_data is a string
                # You might need to parse it if it's in JSON format
                try:
                    chat_data_dict = json.loads(chat_data)
                    instance_data.update(chat_data_dict)
                except json.JSONDecodeError as e:
                    print(f"Error parsing chat_data: {e}")
                    # Decide how to handle this case - whether to skip or handle the error

        result_data.append(instance_data)

    # Convert the result_data list of dictionaries to a DataFrame
    df = pd.DataFrame(result_data)
    
    return df

def run_analysis(df):

    # Initialize columns per evaluative area
    df['eval 1'] = None
    df['eval 2'] = None
    df['eval 2.1'] = None
    df['eval 2.2'] = None
    df['banter'] = None
    df['profanity'] = None
    df['authoritarian'] = None
    df['evident bias'] = None
    df['hallucination'] = None
    df['no penalty'] = None
    df['low penalty'] = None
    df['offensive content'] = None
    df['eval 3'] = None
    df['eval 3.1'] = None
    df['eval 4'] = None
    df['eval 5'] = None
    df['eval 5.1']  = None

    # Prompt user input for evaluation questions and update dataframe accordingly
    for index, row in df.iterrows():
        print(f"Instance: {index}")
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.max_columns', None)

        print("MESSAGE DATA")
        for elem in row['message_data']:
            print(elem)
        
        print("MODERATION DATA")
        print("USERS: ", row['users'], "\n")
        print("EVIDENCE: ", row['evidence'], "\n")
        print("SUMMARY OF EVENTS AND INSIGHTS: ", row['debiased summary'])
        print("FLAMEWAR CONTENT INDICATOR SCORE: ", row['final score'])
        print("PENALTY ASSIGNMENT SCORE: ", row['final assignment score'], "\n")
        
        # Eval 1: Chatstream contains moderation-requiring content?
        df.loc[index, 'eval 1'] = input("Chatstream contains flaming, harassment, personal argument or otherwise moderation-requiring content? TRUE / FALSE: ").upper()
        df.loc[index, 'eval 2'] = input("Appropriate penalty score assigned? TRUE / FALSE: ").upper()

        if "FALSE" in df.loc[index, 'eval 2']:
            df.loc[index, 'eval 2.1'] = input("Excessive penalty assignment? TRUE / FALSE: ").upper()

# If 2.1 TRUE:
        # Banter? i.e friendly exchange of insults or profanity
        # Profanity? i.e moderated for use of profanity without ill intentions
        # Authoritarian i.e moderated for complaints about overarching systems, moderators
        # Evident bias? i.e racial, gender, LGBTQ+, dialect or language bias
        # Hallucination? i.e messages which are not actually present in chat stream, events that did not happen, fabricated user IDs
            
            if "TRUE" in df.loc[index, 'eval 2.1']:
                df.loc[index, 'banter'] = input("Banter? i.e friendly exchange of insults or profanity TRUE/FALSE: ").upper()
                df.loc[index, 'profanity'] = input("Profanity? i.e moderated for use of profanity without ill intentions TRUE/FALSE: ").upper()
                df.loc[index, 'authoritarian'] = input("Authoritarian i.e moderated for complaints about overarching systems, moderators, or other systems of power TRUE/FALSE:").upper()
                df.loc[index, 'evident bias'] = input("Evident bias? i.e moderated due to model expressing racial, gender, LGBTQ+, dialect or language bias. If TRUE, SPECIFY: racial, gender, lgbt, dialect, language, other. If FALSE, FALSE").lower()
                df.loc[index, 'hallucination'] = input("Hallucination? i.e messages which are not actually present in chat stream, events that did not happen, fabricated user IDs. If TRUE, specify: messages, user IDs, events. If FALSE, FALSE").lower()
            
        df.loc[index, 'eval 2.2'] = input("Penalty assignment too low? TRUE / FALSE:").upper()

   # If 2.2 TRUE:
        # Penalty not assigned at all?
        # Score too low?
        # Offensive content missed over? i.e insults or slur not noticed

        if "TRUE" in df.loc[index, 'eval 2.2']:
            df.loc[index, 'no penalty'] = input("Penalty score not assigned where due? TRUE or FALSE: ").upper()
            df.loc[index, 'low penalty'] = input("Penalty score assigned, but too low? TRUE or FALSE: ").upper()
            df.loc[index, 'offensive content'] = input("Offensive content missed over? i.e insults or slur not noticed. TRUE or FALSE: ").upper()
        
    # 3 Actioned in line with platform policies? TRUE / FALSE
        df.loc[index, 'eval 3'] = input("Action taken in line with platform policies? Refer to document. TRUE/FALSE: ").upper()

        if "FALSE" in df.loc[index, 'eval 3']:
            df.loc[index, 'eval 3.1'] = input("Action was not taken in line with platform policies: what went wrong?").lower()
        
        df.loc[index, 'eval 4'] = input("Actions clearly justified by LLM? TRUE / FALSE: ").upper()
        df.loc[index, 'eval 5'] = input("Actions and claims are accurately evidenced? TRUE / FALSE: ").upper()

        if "FALSE" in df.loc[index, 'eval 5']:
            df.loc[index, 'eval 5.1'] = input("Actions and claims weren't accurately evidenced - what went wrong? Explain: ").lower()
        

    return df

filepath_results = 'filepath to results from run'
filepath_data = 'filepath to data input to run'

data = load_data(filepath_data, filepath_results)

print(data.columns)
results = run_analysis(data)

results.to_csv('results filename here')

######## DO NOT TOUCH THIS IN FUTURE. DO NOT ALTER JS ON OUTPUT STRUCTURE. END. #########tr