import boto3
import json
print('Loading function')

db = boto3.resource('dynamodb')
gyoop_appts = db.Table('gyoop_appts')
gyoop_clients = db.Table('gyoop_clients')
gyoop_convos = db.Table('gyoop_convos')

xml_header = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'
xml_name = '<Response><Message><Body>Welcome to GyooperCuts! Reply with you name to get started! </Body></Message></Response>'
xml_actions = '<Response><Message><Body>What do you want to do, reply withj X</Body></Message></Response>'


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
    message_body = event['Body'].upper().strip()
    current_state = get_current_state(from_number)
    # print('current state ', current_state)
    if current_state == None:
        # db_convos add this person with state 0
        update_state(from_number, current_state, 0)
        return ask_for_name()
    
    # state of asking for name
    if current_state == 0:
        update_state(from_number, current_state, 1)
        #do stuff to add name to client table
        add_new_contact(from_number, message_body.replace('+',' '))
        return ask_initial_action()


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

    
    