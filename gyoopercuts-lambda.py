from __future__ import print_function
import re
# import boto3
# import json

def lambda_handler(event, context):
    
    print("Received event: " + str(event))
    
    # dynamo = boto3.client('dynamodb')

    xml_header = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
        '<!DOCTYPE Response [<!ENTITY appointment_date "2020-09-05">'\
            '<!ENTITY appointment_start_time "06:00pm">'\
            '<!ENTITY appointment_end_time "08:00pm">]>'
    # scheduling appointment
    xml_schedule = '<Response><Message><Body>Here are the time slots that are currently available for sign-ups. Haircuts on &appointment_date; will be between &appointment_start_time; and &appointment_end_time;. If your desired time is not listed below as an option, please check back later. Reply with ‘APPOINTMENT #’ from the available time slots below. (ex. Reply ‘APPOINTMENT 3’ for time slot 3)\n</Body></Message></Response>'
    xml_appointment = '<Response><Message><Body>Reply ‘CONFIRM’ to confirm your haircut appointment for &appointment_date; &appointment_start_time;. Keep in mind that you will need to find someone to replace your time slot if you’d like to change or cancel the appointment. </Body></Message></Response>'
    xml_appointment_name = '<Response><Message><Body>Reply ‘CONFIRM:YOUR_NAME’’ to confirm your haircut appointment for &appointment_date; &appointment_start_time;. Keep in mind that you will need to find someone to replace your time slot if you’d like to change or cancel the appointment. (ex. ‘CONFIRM:SEON LEE’)</Body></Message></Response>'
    xml_confirm = '<Response><Message><Body>Thanks for scheduling an appointment for &appointment_date; &appointment_start_time;. I’ll see you then!</Body></Message></Response>'
    # changing appointment
    xml_change = '<Response><Message><Body>Please reach out to the person to swap time slots prior to replying to this message. When you’ve arranged the swap with the person, reply with ‘SWAP #’. (ex. Reply ‘SWAP 3’ to swap with time slot 3) Swap is not complete until the other person accepts the swap request.</Body></Message></Response>'
    xml_swap_sender = '<Response><Message><Body>Your swap request for [name]’s [date] [start_time] appointment has been sent. You’ll receive a notification once the request is processed.</Body></Message></Response>'
    xml_swap_receiver = '<Response><Message><Body>[name] with [date] [start_time] slot would like to swap slots with you and should have confirmed it with you already. Reply ‘SWAP CONFIRM’ to accept this swap request.</Body></Message></Response>'
    xml_swap_confirm_sender = '<Response><Message><Body>Your swap request has been approved. Your new appointment is now scheduled for [date] [start_time]</Body></Message></Response>'
    xml_swap_confirm_receiver = '<Response><Message><Body>Your new appointment is now scheduled for [date] [start_time]. [name] has also been notified.</Body></Message></Response>'
    # canceling appointment
    xml_cancel = '<Response><Message><Body>Please reach out to the person scheduled for either the first or last slot to take over your time slot prior to replying to this message. When you’ve arranged the takeover with the person, reply with ‘TAKEOVER #’. (ex. Reply ‘TAKEOVER 3’ if person at time slot 3 has agreed to take over your time slot.) Cancel is not complete until the takeover request is accepted.</Body></Message></Response>'
    xml_takeover_sender = '<Response><Message><Body>Your takeover request for [name]’s [date] [start_time] appointment has been sent. You’ll receive a notification once the request is processed.</Body></Message></Response>'
    xml_takeover_receiver = '<Response><Message><Body>[name] with [date] [start_time] slot would like you to take over his spot and should have confirmed it with you already. Reply ‘TAKEOVER CONFIRM’ to accept this takeover request.</Body></Message></Response>'
    xml_takeover_confirm_sender = '<Response><Message><Body>Your takeover request has been approved. You have successfully canceled your appointment for [date] [start_time].</Body></Message></Response>'
    xml_takeover_confirm_receiver = '<Response><Message><Body>Your new appointment is now scheduled for [date] [start_time]. Takeover request sender has also been informed.</Body></Message></Response>'
    # any other message
    xml_welcome = '<Response><Message><Body>Thanks for contacting Gyoopercuts! Reply with ‘SCHEDULE’ to schedule a new appointment, ‘CHANGE’ to change an existing appointment, and ‘DROP’ to cancel your appointment.</Body></Message></Response>'

    resp_xml = xml_header
    # schedule appointment
    if event['Body'] == 'SCHEDULE':
        resp_xml += xml_schedule
    elif re.match(r"APPOINTMENT\+[0-9]+", event['Body']):
        # check for name already in DB
        resp_xml += xml_appointment
    elif re.match(r"CONFIRM*", event['Body']):
        index = event['Body'].find('%3A')
        if index != -1:
            # add name to DB
            name = event['Body'][index + 3:]
            print(name)
        resp_xml += xml_confirm
    # change appointment
    elif event['Body'] == 'CHANGE':
        resp_xml += xml_change
    elif re.match(r"SWAP\+[0-9]+", event['Body']):
        resp_xml += xml_swap_sender
        # send swap request to receiver
    elif event['Body'] == 'SWAP+CONFIRM':
        resp_xml += xml_swap_confirm_receiver
        # send swap request processed notification to sender - xml_swap_confirm_sender
    # cancel appointment
    elif event['Body'] == 'DROP':
        resp_xml += xml_cancel
    elif re.match(r"TAKEOVER\+[0-9]+", event['Body']):
        resp_xml += xml_takeover_sender
        # send takeover request to receiver
    elif event['Body'] == 'TAKEOVER+CONFIRM':
        resp_xml += xml_takeover_confirm_receiver
        # send takeover request processed notification to sender - xml_takeover_confirm_sender
    # any other message
    else:
        resp_xml += xml_welcome

    return resp_xml
