def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

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
        print(appt)
        if not appt['phone_number']:
            available_slots.append(appt['slot_id'])
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
    