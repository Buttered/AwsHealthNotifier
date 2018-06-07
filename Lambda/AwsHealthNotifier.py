import boto3
from datetime import datetime
import requests
import json
import os
session = boto3.session.Session(region_name='us-east-1')
hClient = session.client('health')
snsClient = boto3.client('sns')
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
def publish_sns(state,days,entities,time,code,region):
    snsArn = os.environ['SnsTopicArn']
    message='%s AWS scheduled event %s\nentities: %s\ntime: %s\ncode: %s\nregion: %s' % (state,days,entities,time,code,region)
    if snsArn:
        response = snsClient.publish(
            TargetArn=snsArn,
            Message=str(message),
            MessageStructure='text'
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('sns published - %s' % (message))
        else:
            raise_error('bad response when publishing sns')
    else:
        print('No sns topic arn provided')

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
            publish_sns('Info\n','in %s days' % (delta),eventEntities,eventStartTime,eventTypeCode,eventRegion)
        elif delta == 1:
            publish_sns('Warning :bangbang:\n','tomorrow',eventEntities,eventStartTime,eventTypeCode,eventRegion)
        elif delta == 0:
            publish_sns('Critial :bangbang:\n','today',eventEntities,eventStartTime,eventTypeCode,eventRegion)
        
        