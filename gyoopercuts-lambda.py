import boto3
import json
import re
from datetime import datetime, timezone
print('Loading function')

db = boto3.resource('dynamodb')
gyoop_appts = db.Table('gyoop_appts')
gyoop_clients = db.Table('gyoop_clients')
gyoop_convos = db.Table('gyoop_convos')

xml_header = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'
xml_start = '<Response><Message><Body>'
xml_end = '</Body></Message></Response>'
xml_name = '<Response><Message><Body>Welcome to Gyoopercuts! Reply with ‘YOUR_NAME’ to get started. (ex. ‘SEON LEE’)</Body></Message></Response>'
xml_actions = '<Response><Message><Body>Thanks for contacting Gyoopercuts! Reply with ‘SCHEDULE’ to schedule a new appointment, ‘CHANGE’ to change an existing appointment, and DROP to cancel your appointment. At any point, reply ‘START OVER’ to return to this message.</Body></Message></Response>'

xml_schedule = 'Here are the time slots that are currently available for sign-ups. Haircuts on {0} will be between {1} and {2}. If your desired time is not listed below as an option, please check back later. Reply with ‘APPOINTMENT LETTER’ from the available time slots below. (ex. Reply ‘APPOINTMENT C’ for time slot C)\n'
xml_available_slot = '\nTime Slot {0} :\n {1} - {2}'
xml_appointment = '<Response><Message><Body>Thanks for scheduling an appointment. Keep in mind that you will need to find someone to replace your time slot if you’d like to change or cancel the appointment. </Body></Message></Response>'

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
# any other message
xml_retry = '<Response><Message><Body>You’ve entered an invalid input. Please try again.</Body></Message></Response>'

valid_inputs = {
    1: ['SCHEDULE', 'CHANGE', 'DROP']
}

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def lambda_handler(event, context):
    from_number = '+' + event['From'][3:]
    message_body = event['Body'].upper().strip().replace('+',' ')
    current_state = get_current_state(from_number)
    print('message body : ', message_body)
    
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

    # print(get_available_slots())
    # print(get_slot('A'))
    # state asking for action
    if current_state == 1:
        current_valid_inputs = valid_inputs[current_state]
        if message_body not in current_valid_inputs:
            return ask_try_again()
        else:
            if message_body == 'SCHEDULE':
                #schedule
                # todo : check if user already has appt
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
            #todo check if time slot is available_slots.append(appt['slot_id'])
            slot_id = message_body.split()[1]
            if slot_id in get_available_slots() :
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
                return get_schedule_confirm_message()
            else:
                return ask_try_again()

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
    # print(phone_number)
    try:
        temp = gyoop_convos.delete_item(
            Key = {
                'phone_number': phone_number
            }
        )
        # print('unsuccessful ', temp)
    except:
        print('not in db')

#todo check for continuity and availability
def get_available_slots():
    print('inside avail slots')
    available_slots = []
    appts = gyoop_appts.scan()['Items']
    for appt in appts:
        available_slots.append(appt['slot_id'])
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

def get_schedule_message():
    open_slots = get_available_slots()
    message_lines = []
    all_start_time = ''
    all_end_time = ''
    all_date =''

    for ind, slot_id in enumerate(open_slots):
        current_slot = get_slot(slot_id)
        start_time_utc = current_slot['start_date_time']
        date, start_time = utc_to_readable(start_time_utc)

        end_time_utc = current_slot['end_date_time']
        _, end_time = utc_to_readable(end_time_utc)
        # if ind == 0:
        #     message += xml_schedule.format()
        if ind == 0:
            all_start_time = start_time
            all_date = date
        if ind == len(open_slots) - 1:
            all_end_time = end_time
        new_line = xml_available_slot.format(slot_id, start_time, end_time)
        # print('newLine ', new_line)
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
    