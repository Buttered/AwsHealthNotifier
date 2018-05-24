import boto3
from datetime import datetime
import requests
import json
import os
session = boto3.session.Session(region_name='us-east-1')
hClient = session.client('health')
def raise_error(emessage):
    raise ValueError(emessage)
def get_events():
    response = hClient.describe_events(
        filter={
            'eventTypeCategories': [
                'scheduledChange'
            ],
            'eventStatusCodes': [
                'upcoming'
            ]
        }
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response['events']
    else:
        raise_error('there was a problem getting a list of events')
def get_event_details(arn):
    response = hClient.describe_event_details(
        eventArns=[
            arn,
        ]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response['successfulSet'][0]
    else:
        raise_error('there was a problem getting event details')
def get_event_affected_entities(arn):
    response = hClient.describe_affected_entities(
        filter={
            'eventArns': [
                arn,
            ]
        }
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return response['entities'][0]['entityValue']
    else:
        raise_error('there was a problem getting the list of entities')

def send_slack(state,days,entities,time,code,region):
    
    slackUrl=os.environ['SlackWebhookUrl']
    slackMessage='%s AWS scheduled event %s\nentities: %s\ntime: %s\ncode: %s\nregion: %s' % (state,days,entities,time,code,region)
    print(slackMessage)
    slackData = {
        'channel' : os.environ['SlackChannel'],
        'text': slackMessage,
        'icon_emoji': os.environ['SlackChannelIcon'],
        'username': "AwsHealth"
    }
    
    response = requests.post(
        slackUrl, data=json.dumps(slackData),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise_error('Bad response from slack - %s' % response.text)

def lambda_handler(context,event):
    e=get_events()
    for i in e :
        item = get_event_details(i['arn'])
        eventArn=item['event']['arn']
        
        eventTypeCode = item['event']['eventTypeCode']
        
        eventRegion = item['event']['region']
        eventStartTime = item['event']['startTime']
        #eventService = item['event']['service']
        #eventTypeCategory = item['event']['eventTypeCategory']
        #eventEndTime = item['event']['endTime']
        #eventStatusCode = item['event']['statusCode']
        #eventDescription = item['eventDescription']['latestDescription']

        eventEntities = get_event_affected_entities(eventArn)


        delta = (eventStartTime.replace(tzinfo=None) - datetime.now()).days
        print(delta)
        if delta == 5:
            send_slack('Info\n','in %s days' % (delta),eventEntities,eventStartTime,eventTypeCode,eventRegion)
        elif delta == 1:
            send_slack('Warning :bangbang:\n','tomorrow',eventEntities,eventStartTime,eventTypeCode,eventRegion)
        elif delta == 0:
            send_slack('Critial :bangbang:\n','today',eventEntities,eventStartTime,eventTypeCode,eventRegion)
        
        