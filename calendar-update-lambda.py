import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

#if uploading this lambda as a zip, make sure the lambda is configured so that it knows the handler is 'calender-update-lambda.lambda-handler'

def lambda_handler(event, context):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    # SERVICE_ACCOUNT_FILE = 'gyoopercutscalendar-fca1ca3ca42c.json' # You should make it an environment variable
    SERVICE_ACCOUNT_FILE = 'INSERT PATH OF SERVICE ACCOUNT FILE OR PUT AS JSON OBJECT'
    
    SUBJECT = 'INSERT SERVICE ACCOUNT EMAIL HERE'
    
    
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(SUBJECT)
    
    service = build('calendar', 'v3', credentials=delegated_credentials)
    
    
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    
    events = service.events().list(calendarId='INSERT CALENDAR ID',timeMin=now,maxResults=10,orderBy='startTime',singleEvents=True).execute()
    
    all_events = ''
    for event in events['items']:
        all_events += event['summary']
        print(event['summary'])
    return {
        'statusCode': 200,
        'body': json.dumps(all_events)
    }
