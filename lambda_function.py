import json
import requests

JIRA_DOMAIN = "<YOUR JIRA DOMAIN>"
JIRA_PROJECT = "<YOUR JIRA PROJECT>"
JIRA_USERNAME = '<YOUR JIRA E-MAIL>'
JIRA_API_KEY = '<YOUR API KEY>'

def lambda_handler(event, context):
    
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    
    return dispatch(event)

def dispatch(intent_request):
    
    """
    Called when the user specifies an intent for this bot.
    """
    
    intent_name = intent_request['currentIntent']['name']
    
    if intent_name == 'SetDone':
        return set_done(intent_request)
    elif intent_name == 'SetInProgress':
        return set_in_progress(intent_request)
    elif intent_name == 'AssignToMe':
        return assign_to_me(intent_request)
        
    raise Exception('Intent with name ' + intent_name + ' not supported')
    
def set_done(intent_request):
    
    """
    Performs dialog management and fulfillment to set the user story as done on Jira
    """
    
    user_story = try_ex(lambda: intent_request['currentIntent']['slots']['user_story'])
    
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    user_story_id = get_issue_id(user_story)
    execute_transition(user_story_id, "31")
    
    update_assignee(user_story_id, get_my_account_id())

    # Load user story and track the current intent.
    transition = json.dumps({
        'intentName': intent_request['currentIntent']['name'],
        'userStory': user_story,
        'userStoryId': user_story_id,
        'transition': "31"
    })

    session_attributes['currentTransition'] = transition

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': "Okay, the user story related to the {} was set to Done".format(user_story)
        }
    )
    
def set_in_progress(intent_request):
    
    """
    Performs dialog management and fulfillment to set the user story as in progress on Jira
    """
    
    user_story = try_ex(lambda: intent_request['currentIntent']['slots']['user_story'])
    
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    user_story_id = get_issue_id(user_story)
    execute_transition(user_story_id, "21")
    
    update_assignee(user_story_id, get_my_account_id())

    # Load user story and track the current intent.
    transition = json.dumps({
        'intentName': intent_request['currentIntent']['name'],
        'userStory': user_story,
        'userStoryId': user_story_id,
        'transition': "21"
    })

    session_attributes['currentTransition'] = transition

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': "Okay, the user story related to the {} was set to In Progress".format(user_story)
        }
    )
    
def assign_to_me(intent_request):
    
    """
    Performs dialog management and fulfillment to set the user story as in progress on Jira
    """
    
    user_story = try_ex(lambda: intent_request['currentIntent']['slots']['user_story'])
    
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    user_story_id = get_issue_id(user_story)
    update_assignee(user_story_id, get_my_account_id())

    # Load user story and track the current intent.
    transition = json.dumps({
        'intentName': intent_request['currentIntent']['name'],
        'userStory': user_story,
        'userStoryId': user_story_id
    })

    session_attributes['currentTransition'] = transition

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': "Okay, the user story related to the {} was assigned to you.".format(user_story)
        }
    )
    
def try_ex(func):
    
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response
    
def get_issue_id(user_story):
    
    service_path = "/rest/api/3/search"
    jql_params = "?jql=project = '{}' AND summary ~ '{}'".format(JIRA_PROJECT, user_story)
    endpoint = JIRA_DOMAIN + service_path + jql_params
    
    response = requests.get(endpoint, auth=(JIRA_USERNAME, JIRA_API_KEY))
    return try_ex(lambda: response.json()['issues'][0]['id'])
    
def execute_transition(user_story_id, transition):
    
    service_path = "/rest/api/3/issue/{}/transitions".format(user_story_id)
    endpoint = JIRA_DOMAIN + service_path
    
    request_body = { "transition": { "id": transition } }
    
    requests.post(endpoint, json=request_body, auth=(JIRA_USERNAME, JIRA_API_KEY))
    
def get_my_account_id():
    
    service_path = "/rest/api/latest/user/search"
    query_params = "?query={}".format(JIRA_USERNAME)
    endpoint = JIRA_DOMAIN + service_path + query_params
    
    response = requests.get(endpoint, auth=(JIRA_USERNAME, JIRA_API_KEY))
    
    return try_ex(lambda: response.json()[0]['accountId'])
    
def update_assignee(user_story_id, account_id):
    
    service_path = '/rest/api/3/issue/{}/assignee'.format(user_story_id);
    endpoint = JIRA_DOMAIN + service_path
    
    request_body = { "accountId": account_id }
    
    requests.put(endpoint, json=request_body, auth=(JIRA_USERNAME, JIRA_API_KEY))