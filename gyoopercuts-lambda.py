from __future__ import print_function
# import boto3
# import json

def lambda_handler(event, context):
    
    print("Received event: " + str(event))
    
    # dynamo = boto3.client('dynamodb')

    xml_resp_confirm = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
        '<!DOCTYPE foods [<!ENTITY appointment_date "2020-09-05"><!ENTITY appointment_start_time "06:00pm">]>'\
       '<Response><Message><Body>Thanks for scheduling an appointment for &appointment_date; &appointment_start_time;. I’ll see you then!</Body></Message></Response>'

    if event['Body'] == 'CONFIRM':
        return xml_resp_confirm
    else:
        return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
           '<Response><Message><Body>Thanks for contacting Gyoopercuts! Reply with ‘SCHEDULE’ to schedule a new appointment, ‘CHANGE’ to change an existing appointment, and ‘CANCEL’ to cancel your appointment.</Body></Message></Response>'
    