import json
import boto3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os

db = boto3.resource('dynamodb')
gyoop_appts = db.Table('gyoop_appts')
gyoop_clients = db.Table('gyoop_clients')

#if uploading this lambda as a zip, make sure the lambda is configured so that it knows the handler is 'calendar-update-lambda.lambda_handler'

def lambda_handler(event, context):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    # SERVICE_ACCOUNT_FILE = 'gyoopercutscalendar-fca1ca3ca42c.json' # You should make it an environment variable
    SERVICE_ACCOUNT_FILE = json.loads(os.environ.get("SERVICE_ACCOUNT_FILE"))
    SUBJECT = os.environ.get("SUBJECT")
    CALENDAR_ID = os.environ.get("CALENDAR_ID")
    
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(SUBJECT)
    
    service = build('calendar', 'v3', credentials=delegated_credentials)
    
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    
    #delete all events on specified calendar
    sunday_start = datetime.today() - timedelta(days=datetime.today().isoweekday() % 7)
    saturday_end = sunday_start + timedelta(days=6)
    sunday_start_utc = sunday_start.isoformat() + 'Z'
    saturday_end_utc = saturday_end.isoformat() + 'Z'


    events = service.events().list(calendarId=CALENDAR_ID,timeMin=sunday_start_utc, timeMax=saturday_end_utc,singleEvents=True).execute()
    all_event_ids = [e['id'] for e in events['items']]
    all_new_events = []
    # print(all_event_ids)
    for eid in all_event_ids:
        old_event = service.events().delete(calendarId=CALENDAR_ID, eventId=eid).execute()

    #read all appointments from db, populate calendar
    all_current_appts = gyoop_appts.scan()['Items']
    for new_event in all_current_appts:
        time_diff = 4
        start_date_time = datetime.strptime(new_event['start_date_time'], "%Y-%m-%dT%H:%M:%S%z")
        end_date_time = datetime.strptime(new_event['end_date_time'], "%Y-%m-%dT%H:%M:%S%z")
        if bool(start_date_time.dst()):
            time_diff = 5
        start_date_time += timedelta(time_diff)
        end_date_time += timedelta(time_diff)
        start_date_time = start_date_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date_time = end_date_time.strftime("%Y-%m-%dT%H:%M:%S%z")

        slot_id = new_event['slot_id']
        phone_number = new_event['phone_number']

        #try to get contact name, if slot is open, contact name is open
        if phone_number != '':
            contact_name = gyoop_clients.get_item(
                Key = {
                    'phone_number' : phone_number
                }
            )['Item']['name']
        else:
            contact_name = 'Open Slot'

        event = {
            'summary': slot_id + ' - ' + contact_name,
            'description' : phone_number,
            'start': {
                'dateTime': start_date_time
            },
            'end': {
                'dateTime': end_date_time
            }
        }
        all_new_events.append(event)
        print('making event ', event)
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    # print(all_new_events)
    return {
        'statusCode': 200,
        'body': json.dumps(all_new_events)
    }
    
