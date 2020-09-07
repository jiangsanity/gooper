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