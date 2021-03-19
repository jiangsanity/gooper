import boto3
import json
import re
from datetime import datetime, timezone, timedelta
import urllib
from urllib import request, parse
import base64
import os
from helpers import *
from xml_responses import *
# print('Loading function')

xml_header = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'
xml_start = '<Response><Message><Body>'
xml_end = '</Body></Message></Response>'
xml_name = '<Response><Message><Body>Welcome to Gyoopercuts! Reply with ‘YOUR_NAME’ to get started. (ex. ‘SEON LEE’)</Body></Message></Response>'
# xml_actions = '<Response><Message><Body>Thanks for contacting Gyoopercuts! Reply with ‘SCHEDULE’ to schedule a new appointment, ‘CHANGE’ to change an existing appointment, and DROP to cancel your appointment. At any point, reply ‘START OVER’ to return to this message.</Body></Message></Response>'
xml_actions = '<Response><Message><Body>Thanks for contacting Gyoopercuts! Reply with ‘SCHEDULE’ to schedule a new appointment. At any point, reply ‘START OVER’ to return to this message.</Body></Message></Response>'

# schedule
xml_schedule = 'Here are the time slots that are currently available for sign-ups. Haircuts on {0} will be between {1} and {2}. If your desired time is not listed below as an option, please check back later. Reply with ‘APPOINTMENT LETTER’ from the available time slots below. (ex. Reply ‘APPOINTMENT C’ for time slot C)\n'
xml_available_slot = '\nTime Slot {0} :\n {1} - {2}'
xml_appointment = '<Response><Message><Body>Thanks for scheduling an appointment. Keep in mind that you will need to find someone to replace your time slot if you’d like to change or cancel the appointment. </Body></Message></Response>'
xml_already_signed_up = '<Response><Message><Body>You are already signed up, you may not sign up for multiple time slots.</Body></Message></Response>'
xml_all_booked_message = '<Response><Message><Body>Sorry, all appointments for this week are booked. Please check again next week.</Body></Message></Response>'
xml_confirm = '<Response><Message><Body>Thanks for scheduling an appointment for {0} &appointment_start_time;. I’ll see you then!</Body></Message></Response>'
# changing appointment
xml_change = '<Response><Message><Body>Please reach out to the person to swap time slots prior to replying to this message. When you’ve arranged the swap with the person, reply with ‘SWAP #’. (ex. Reply ‘SWAP 3’ to swap with time slot 3) Swap is not complete until the other person accepts the swap request.</Body></Message></Response>'
xml_swap_sender = '<Response><Message><Body>Your swap request for [name]’s [date] [start_time] appointment has been sent. You’ll receive a notification once the request is processed.</Body></Message></Response>'
xml_swap_receiver = '<Response><Message><Body>[name] with [date] [start_time] slot would like to swap slots with you and should have confirmed it with you already. Reply ‘SWAP CONFIRM’ to accept this swap request.</Body></Message></Response>'
xml_swap_confirm_sender = '<Response><Message><Body>Your swap request has been approved. Your new appointment is now scheduled for [date] [start_time]</Body></Message></Response>'
xml_swap_confirm_receiver = '<Response><Message><Body>Your new appointment is now scheduled for [date] [start_time]. [name] has also been notified.</Body></Message></Response>'
# canceling appointment
xml_drop = '<Response><Message><Body>Please reach out to the person scheduled for either the first or last slot to take over your time slot prior to replying to this message. When you’ve arranged the takeover with the person, reply with ‘TAKEOVER #’. (ex. Reply ‘TAKEOVER 3’ if person at time slot 3 has agreed to take over your time slot.) Cancel is not complete until the takeover request is accepted.</Body></Message></Response>'
xml_takeover_sender = '<Response><Message><Body>Your takeover request for [name]’s [date] [start_time] appointment has been sent. You’ll receive a notification once the request is processed.</Body></Message></Response>'
xml_takeover_receiver = '<Response><Message><Body>[name] with [date] [start_time] slot would like you to take over his spot and should have confirmed it with you already. Reply ‘TAKEOVER CONFIRM’ to accept this takeover request.</Body></Message></Response>'
xml_takeover_confirm_sender = '<Response><Message><Body>Your takeover request has been approved. You have successfully canceled your appointment for [date] [start_time].</Body></Message></Response>'
xml_takeover_confirm_receiver = '<Response><Message><Body>Your new appointment is now scheduled for [date] [start_time]. Takeover request sender has also been informed.</Body></Message></Response>'
# respond to admin
xml_admin = '<Response><Message><Body>Time slots have been created for {0} {1} to {2}.</Body></Message></Response>'
# any other message
xml_retry = '<Response><Message><Body>You’ve entered an invalid input. Please try again.</Body></Message></Response>'

TWILIO_SMS_URL = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json"
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
DAYLIGHT_START_OBJ = datetime.strptime("2021-03-14T02:00:00Z", '%Y-%m-%dT%H:%M:%SZ')
DAYLIGHT_END_OBJ = datetime.strptime("2021-11-07T02:00:00Z", '%Y-%m-%dT%H:%M:%SZ')

db = boto3.resource('dynamodb')
gyoop_appts = db.Table('gyoop_appts')
gyoop_clients = db.Table('gyoop_clients')
gyoop_convos = db.Table('gyoop_convos')

valid_inputs = {
    1: ['SCHEDULE', 'SCHEDULE ', 'CHANGE', 'DROP']
}

def lambda_handler(event, context):
    from_number = '+' + event['From'][3:]
    message_body = event['Body'].upper().strip().replace('+',' ')
    current_state = get_current_state(from_number)

    print('event is: ', event)
    print('message body : ', message_body)
    print('message body length: ', len(message_body))

    #! ADMIN CONTROL
    if from_number == os.environ.get("ADMIN_PHONE_NUMBER"):
        if message_body == 'REMIND':
            return remind_clients()
        elif message_body == 'CLOSE':
            return close_appointments()
        else:
            date, all_start_time, all_end_time = message_body.split(' ')
            all_start_time = all_start_time[:2] + ':' + all_start_time[-2:]
            all_end_time = all_end_time[:2] + ':' + all_end_time[-2:]
            slot_start_obj = datetime.strptime(date + 'T' + all_start_time + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
            slot_end_obj = slot_start_obj + timedelta(seconds=1800)
            all_end_obj = datetime.strptime(date + 'T' + all_end_time + ':00Z', '%Y-%m-%dT%H:%M:%SZ')

            delete_all_appts()
            slot_id = 'A'
            while slot_end_obj <= all_end_obj:
                add_slot_to_db(slot_id, slot_start_obj, slot_end_obj)
                # add_slot_to_db(slot_id, slot_start_obj.strftime('%Y-%m-%dT%H:%M:%SZ'), slot_end_obj.strftime('%Y-%m-%dT%H:%M:%SZ'))
                slot_start_obj += timedelta(seconds=1800)
                slot_end_obj += timedelta(seconds=1800)
                slot_id = chr(ord(slot_id) + 1)

            return get_admin_message(date, all_start_time, all_end_time)

    if message_body == 'START OVER' or message_body == 'START OVER ':
        update_state(from_number, current_state, 1)
        return ask_initial_action()
    
    # no active conversation
    if current_state == None:
        # db_convos add this person with state 0
        if get_client(from_number) != None:
            update_state(from_number, current_state, 1)
            return ask_initial_action()
        else:
            update_state(from_number, current_state, 0)
            return ask_for_name()
    
    # state of asking for name
    if current_state == 0:
        update_state(from_number, current_state, 1)
        #do stuff to add name to client table
        add_new_contact(from_number, message_body)
        return ask_initial_action()

    # state asking for action
    if current_state == 1:
        current_valid_inputs = valid_inputs[current_state]
        if message_body not in current_valid_inputs:
            return ask_try_again()
        else:
            if message_body.find('SCHEDULE') != -1:
                #schedule
                if already_booked(from_number):
                    end_conversation(from_number)
                    return get_already_signed_up_message()
                available_slots = get_available_slots()
                if not available_slots or len(available_slots) == 0:
                    end_conversation(from_number)
                    return get_all_booked_message()
                update_state(from_number, current_state, 2)
                return get_schedule_message()
            elif message_body == 'CHANGE':
                #change
                update_state(from_number, current_state, 3)
                return get_change_message()
            elif message_body == 'DROP':
                #drop
                update_state(from_number, current_state, 4)
                return get_drop_message()
    
    if current_state == 2:
        #add to appt database
        if re.match(r"APPOINTMENT [A-Z]+", message_body):
            slot_id = message_body.split()[1]
            if slot_id in get_available_slots():
                print('about to update item')
                gyoop_appts.update_item(
                    Key = {
                        'slot_id': slot_id
                    },
                    UpdateExpression='SET phone_number = :r',
                    ExpressionAttributeValues={
                        ':r' : from_number
                    }
                )
                end_conversation(from_number)
                print('ended conversation')

                scheduled_slot = get_slot(slot_id)
                name = get_client(scheduled_slot["phone_number"])["name"]
                date, start_time = utc_to_readable(scheduled_slot["start_date_time"])
                start_time_obj = datetime.strptime(date + 'T' + start_time.split()[0] + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
                if start_time_obj > DAYLIGHT_START_OBJ and start_time_obj < DAYLIGHT_END_OBJ:
                    start_time_obj += timedelta(seconds=3600)
                    start_time = start_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ').split('T')[1][:-1]
                notification = '{0} scheduled an appointment for {1} at {2}'.format(name, date, start_time)
                print('notification ', notification)
                send_SMS(notification, os.environ.get("ADMIN_PHONE_NUMBER"))
                return get_schedule_confirm_message()
            else:
                return ask_try_again()
        else:
            return ask_try_again()

def send_SMS(message, to_number):
    if not TWILIO_ACCOUNT_SID:
        return "Unable to access Twilio Account SID."
    if not TWILIO_AUTH_TOKEN:
        return "Unable to access Twilio Auth Token."

    # insert Twilio Account SID into the REST API URL
    populated_url = TWILIO_SMS_URL.format(TWILIO_ACCOUNT_SID)
    post_params = {"To": to_number, "From": os.environ.get("TWILIO_PHONE_NUMBER"), "Body": message}

    # encode the parameters for Python's urllib
    data = parse.urlencode(post_params).encode()
    req = request.Request(populated_url)

    # add authentication header to request based on Account SID + Auth Token
    authentication = "{}:{}".format(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    base64string = base64.b64encode(authentication.encode('utf-8'))
    req.add_header("Authorization", "Basic %s" % base64string.decode('ascii'))

    try:
        # perform HTTP POST request
        with request.urlopen(req, data) as f:
            print("Twilio returned {}".format(str(f.read().decode('utf-8'))))
    except Exception as e:
        # something went wrong!
        return e

    return "SMS sent successfully!"

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def close_appointments():
    appts = get_all_appointments()
    for appt in appts:
        if not appt["phone_number"] or (appt["phone_number"] == ''):
            delete_appt(appt["slot_id"])
    send_SMS("Appointments successfully closed", os.environ.get("ADMIN_PHONE_NUMBER"))

def remind_clients():
    appts = get_all_appointments()
    for appt in appts:
        if appt["phone_number"]:
            date, start_time = utc_to_readable(appt["start_date_time"])
            start_time_obj = datetime.strptime(date + 'T' + start_time.split()[0] + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
            if start_time_obj > DAYLIGHT_START_OBJ and start_time_obj < DAYLIGHT_END_OBJ:
                start_time_obj += timedelta(seconds=3600)
                start_time = start_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ').split('T')[1][:-1]
            reminder_message = 'This is a reminder for your haircut appointment on {0} at {1}.'.format(date, start_time)
            send_SMS(reminder_message, appt["phone_number"])
    send_SMS("Reminders sent successfully", os.environ.get("ADMIN_PHONE_NUMBER"))

def add_slot_to_db(slot_id, start_time_obj, end_time_obj):
    if start_time_obj > DAYLIGHT_START_OBJ and start_time_obj < DAYLIGHT_END_OBJ:
        start_time_obj -= timedelta(seconds=3600)
        end_time_obj -= timedelta(seconds=3600)
    return gyoop_appts.put_item(
        Item = {
            'slot_id': slot_id,
            'start_date_time': start_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end_date_time': end_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'phone_number': ''
        }
    )

def delete_appt(slot_id):
    try:
        temp = gyoop_appts.delete_item(
            Key = {
                'slot_id': slot_id
            }
        )
    except:
        print('not in db')

def delete_all_appts():
    try:
        scan = gyoop_appts.scan()
        with gyoop_appts.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'uId': each['uId'],
                        'compId': each['compId']
                    }
                )
    except:
        return None

def get_admin_message(date, start_time, end_time):
    return xml_header + xml_admin.format(date, start_time, end_time)

def get_all_booked_message():
    return xml_header + xml_all_booked_message

def already_booked(phone_number):
    for appt in get_all_appointments():
        if appt['phone_number'] == phone_number:
            return True
    return False

def get_all_appointments():
    try:
        return gyoop_appts.scan()['Items']
    except:
        return None

def get_client(phone_number):
    try:
        return gyoop_clients.get_item(
            Key = {
                'phone_number' : phone_number
            }
        )['Item']
    except:
        return None


def end_conversation(phone_number):
    try:
        temp = gyoop_convos.delete_item(
            Key = {
                'phone_number': phone_number
            }
        )
    except:
        print('not in db')

def get_available_slots():
    print('inside avail slots')
    all_slots = []
    appts = get_all_appointments()
    appt_str = ''

    for appt in appts:
        all_slots.append(appt['slot_id'])
    all_slots.sort()

    for slot_id in all_slots:
        if not get_slot(slot_id)["phone_number"] or get_slot(slot_id)["phone_number"] == '':
            appt_str += '0'
        else:
            appt_str += '1'

    print('appt_str ', appt_str)
    print('all_slots sorted', all_slots)

    first_booked = appt_str.find('1')
    last_booked = appt_str.rfind('1')
    print("first and last booked indicies are ", first_booked, ' ', last_booked)
    # all slot available
    if first_booked == -1:
        print("should be returning all_slots: ", all_slots)
        return all_slots

    available_slots = []
    if first_booked != 0:
        available_slots.append(all_slots[first_booked - 1])
    if last_booked != len(appt_str) - 1:
        available_slots.append(all_slots[last_booked + 1])

    print('final avail ' , available_slots)
    return available_slots

def get_slot(slot_id):
    try:
        return gyoop_appts.get_item(
            Key = {
                'slot_id' : slot_id
            }
        )['Item']
    except:
        return None

def ask_try_again():
    return xml_header + xml_retry

def get_schedule_confirm_message():
    return xml_header + xml_appointment

def get_already_signed_up_message():
    return xml_header + xml_already_signed_up

def get_schedule_message():
    open_slots = get_available_slots()
    message_lines = []

    all_slots = []
    appts = get_all_appointments()
    for appt in appts:
        all_slots.append(appt['slot_id'])
    all_slots.sort()

    first_slot_id = all_slots[0]
    last_slot_id = all_slots[-1]
    
    all_start_utc = get_slot(first_slot_id)['start_date_time']
    all_end_utc = get_slot(last_slot_id)['end_date_time']
    all_date, all_start_time = utc_to_readable(all_start_utc)
    _, all_end_time = utc_to_readable(all_end_utc)


    # daylight savings fix
    all_start_time_obj = datetime.strptime(all_date + 'T' + all_start_time.split()[0] + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
    all_end_time_obj = datetime.strptime(all_date + 'T' + all_end_time.split()[0] + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
    if all_start_time_obj > DAYLIGHT_START_OBJ and all_start_time_obj < DAYLIGHT_END_OBJ:
        all_start_time_obj += timedelta(seconds=3600)
        all_end_time_obj += timedelta(seconds=3600)
        all_start_time = all_start_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ').split('T')[1][:-1]
        all_end_time = all_end_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ').split('T')[1][:-1]

    for slot_id in open_slots:
        current_slot = get_slot(slot_id)
        start_time_utc = current_slot['start_date_time']
        date, start_time = utc_to_readable(start_time_utc)

        end_time_utc = current_slot['end_date_time']
        _, end_time = utc_to_readable(end_time_utc)

        # daylight savings fix
        start_time_obj = datetime.strptime(date + 'T' + start_time.split()[0] + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
        end_time_obj = datetime.strptime(date + 'T' + end_time.split()[0] + ':00Z', '%Y-%m-%dT%H:%M:%SZ')
        if start_time_obj > DAYLIGHT_START_OBJ and start_time_obj < DAYLIGHT_END_OBJ:
            start_time_obj += timedelta(seconds=3600)
            end_time_obj += timedelta(seconds=3600)
            start_time = start_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ').split('T')[1][:-1]
            end_time = end_time_obj.strftime('%Y-%m-%dT%H:%M:%SZ').split('T')[1][:-1]

        new_line = xml_available_slot.format(slot_id, start_time, end_time)
        message_lines.append(new_line)
    
    message = xml_header + xml_start + xml_schedule.format(date, all_start_time, all_end_time)
    for line in message_lines:
        message += line

    return message + xml_end

def get_change_message():
    return xml_header + xml_change

def get_drop_message():
    return xml_header + xml_drop

def add_new_contact(phone_number, name):
    if name.find('%27') >= 0:
        name = name.replace('%27', '', 2)

    return gyoop_clients.put_item(
        Item = {
            'phone_number': phone_number,
            'name': name
        }
    )
    
def ask_for_name():
    return xml_header + xml_name


def ask_initial_action():
    return xml_header + xml_actions


def update_state(phone_number, current_state, new_state):
    # update gyoop_convos table
    if current_state == None:
        # add_item db
        gyoop_convos.put_item(
            Item = {
                'phone_number': phone_number,
                'current_state': new_state
            }
        )
    else:
        # update db with new_state
        gyoop_convos.update_item(
            Key = {
                'phone_number': phone_number
            },
            UpdateExpression='SET current_state = :r',
            ExpressionAttributeValues={
                ':r' : new_state
            }
        )

def get_current_state(phone_number):
    try:
        return gyoop_convos.get_item(
            Key = {
                'phone_number' : phone_number
            }
        )['Item']['current_state']
    except:
        return None

def utc_to_readable(ts):
    utc_dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')
    return utc_dt.strftime('%Y-%m-%d'), utc_dt.strftime('%I:%M %p')
    