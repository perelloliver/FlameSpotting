
# Should we moderate this instance?

attention = """

QUERY: We're looking out for cases of flamewar, arguments between users or harassment. 
Is there any content within this chat stream that necessitates additional moderator review?

CHAT STREAM:

{chat_stream}

Output: TRUE or FALSE


"""

#Does this contain elements which would indicate flaming or harassment?
#Return...
##Users involved
##An initial score between 0-1 indicating the level of aggressive or directed insults
##Evidence for that claim by citing messages in chat stream by index
##Initial penalty assignment score
##Initial decision insights

moderation = """

QUERY:

Does the following chat stream contain pointed insults towards a particular present user or present group or users, repeated aggressive remarks towards present users or the group, or unusual insults given in bad nature between users?
If yes, which user(s) are causing this?

PROMPT:

Using the score you assign to answer the query above, as well as the further context of the chat stream and our policies, assign a score between 0-1 to indicate potential required penalty assignment.
Then, clearly justify and explain your decisions.

{chat_stream}

Respond with the following JSON object. Do not provide any response outside of the JSON:


"users": IDs of users causing offense/argumentation/insult,
"initial score": Indicate the level of pointed insults towards a particular present user or present group or users, repeated aggressive remarks, harassment behaviours, or unusual insults given in bad nature through a float range 0-1, 0 being not at all and 1 being very severe,
"evidence": Cite the messages which informed your decisions numerically by appearance, with the first message being 0 and last 14. e.g [1, 8, 2.] If none, output N/A,
"initial assignment": A float score between 0-1 to inform potential penalty assignment, with 0 being not at all and 1 being severe,
"initial decision": A clear, detailed explanation of your decisions, 

"""

#Heuristic first pass
#Get a summary of what happens in chat stream to lead to the decisions in first set of results
#Return summary with direct quotes

summary = """

## PROMPT ##
The chat stream has been analyzed for potential aggressive or insulting behaviour between users, in particular potential cases of flamewar and harassment.
'Score' is a score out between 0-1, indicating the presence of this content, with 1 being very severe presence and 0 being not at all.
'action_score' is a score between 0-1 indicating potential requirement of penalty assignment to users, with 1 being an extremely severe penalty and 0 being no penalty.

Summarize what has occurred in the chat stream to lead to decisions in 'RESULTS', using the CHAT STREAM to directly quote any messages noted by their index in 'evidence'.
Return summary in a JSON object.

###### EXAMPLE ######

# CHAT STREAM #
Hmmmm, let say yes, I hate fat girls and my babe hate fat boys ['content']Only if you give me your pilot role😂😂😂', 'author_id': 889953310164013056, 'index': 0, 'content': 'hey!', 'author_id': 934190926232977408, 'index': 1, 'content': 'On Sunday', 'author_id': 947889715078631424, 'index': 2, 'content': '<a:laugh:1043483024924352573> <a:laugh:1043483024924352573>', 'author_id': 889394992844537856, 'index': 3, 'content': 'AI Arena 😢😭', 'author_id': 947889715078631424, 'index': 4, 'content': 'Oh why? Watching your weight?', 'author_id': 889953310164013056, 'index': 5, 'content': 'Thank you Can I call u illogics girl 😂 just want to look for ur trouble', 'author_id': 947889715078631424, 'index': 6, 'content': 'Show me way and send me funds, come dm self', 'author_id': 889394992844537856, 'index': 7, 'content': 'Oh.. messages too much', 'author_id': 814240780889620608, 'index': 8, 'content': 'Yh I guess', 'author_id': 889394992844537856, 'index': 9, 'content': 'When did you get pilot?', 'author_id': 889953310164013056, 'index': 10, 'content': 'Haha yeah', 'author_id': 947889715078631424, 'index': 11, 'content': 'Hmmm why?', 'author_id': 889394992844537856, 'index': 12, 'content': 'Oh pls check your tag messages I don’t think I can recall<a:AnimePanic:1038480101664362566>', 'author_id': 889394992844537856, 'index': 13, 'content': "Not so lucky I'd say", 'author_id': 889953310164013056, 'index': 14]

# RESULTS #

  "users": [889953310164013056, 947889715078631424, 889394992844537856],
  "score": 3,
  "evidence": [0, 5, 6],
  "action_score": 0.6

# Respond with the following JSON object. Do not provide any response outside of the JSON: #
"second summary": "The conversation has a score of 3/5, with an action score of 0.6 suggesting moderator action, which signifies the presence of aggressive or insulting behaviour, and that reasonable penalties should be assigned.
User 889953310164013056 consistently makes fun of overweight people, but users 947889715078631424, 889394992844537856 are not associated with any offensive messages.
There is no argumentative or aggressive behaviour."

####### END OF EXAMPLE #######

## CHAT STREAM ##

{chat_stream}

## RESULTS ##
{result}

## Respond with the following JSON object. Do not provide any response outside of the JSON: ##

"second summary": 
"""

#System to attention heuristic
#Take a second look and remove biased or unevidenced content model may have added ie "X is making offensive comments"

s2a_summary = """
PROMPT:

Given the following summary of events by a moderator, extract the part that is unbiased, clearly evidenced, and not opinion-based,
so that using that text alone would be good context for providing an unbiased content moderation solution.

Please include the points the moderator has made regarding the nature of the content and interactions between users.

Remove decisions the moderator has made regarding moderation, such as penalty suggestions.


TEXT

{summary}

Summary:

"""

#Convert s2a summary to a score
#here the score is based on how, based on debiased summary, the events adhere to platform rules
#while this is useful, we actually are looking for flaming and harassment specifically, not to generally moderate

# s2a_2score_1 = """
# PLATFORM POLICIES:
# {policies}

# INSTANCE SUMMARY:
# {summary}

# Can you assess how the events in this summary aligns with the platform's guidelines or rules? 
# Answer with a float number between 0-9, with 0 being fully in alignment, and 9 being completely disaligned.

# Respond with the following JSON object. Do not provide any response outside of the JSON:
# "secondary score": Answer between 0-9

# """

s2a_2score = """

SUMMARY OF EVENTS:
Summary of events in chat-stream and reasoning around moderation up to this point.
{debiased_summary}

INITIAL SCORE:
Initial score indicating the level of pointed insults towards a particular group or users, repeated aggressive remarks, harassment behaviours, or unusual insults given in bad nature through a float range 0-1, 0 being not at all and 1 being very severe
{score}

INITIAL ASSIGNMENT SCORE:
Initial score between 0-1 to inform potential penalty assignment, with 0 being not at all and 1 being severe
{assignment_score}

Using the summary of events, assess the INITIAL SCORE and INITIAL ASSIGNMENT SCORE.

Based on your assessment, respond with the following in JSON object:

      "FINAL SCORE" : Output a FINAL SCORE between 0-1, indicative of the level of pointed insults towards a particular group or users, repeated aggressive remarks, harassment behaviours, or unusual insults given in bad nature ,

      "FINAL ASSIGNMENT SCORE" : Output a FINAL ASSIGNMENT SCORE between 0-1. This is indicative of potential penalty assignment, with 0 being no penalty and 1 being the most severe ,
ß
"""
#Verify the validity of this score based on policies
#Policies
#We're moderating for potential flamewar and harassment scenarios
#Here's the chat stream
#Here's the scores we've assigned
#Verify?

##### This needs to be a multi-option because it could be too light
# I'll remove from pipeline for now.

# verify_score = """
# PLATFORM POLICIES:
# {policies}

# INSTANCE SUMMARY:
# {summary}

# Based on the policies and summary above, can you evaluate the assessment score below?

# Assess how the events in this summary aligns with the platform's guidelines or rules.
# Output a float number between 0-9, with 0 being fully in alignment, and 9 being completely disaligned.

# Provide a brief explanation for your answer.

# INITIAL SCORE:
# {score}

# Respond with the following JSON object. Do not provide any response outside of the JSON:

# "final score": score of 0-1,
# "final score insight": Brief explanation of your score evaluation.

# """