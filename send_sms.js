// Download the helper library from https://www.twilio.com/docs/node/install
// Your Account Sid and Auth Token from twilio.com/console
// DANGER! This is insecure. See http://twil.io/secure
const accountSid = 'ACe09ad569c47d99471f9ea7bb302cc72f';
const authToken = 'a9518123a2c571259775a1255c36478d';
const client = require('twilio')(accountSid, authToken);

client.messages
  .create({
     body: 'This is the ship that made the Kessel Run in fourteen parsecs?',
     from: '+12059557292',
     to: '+16785990243'
   })
  .then(message => console.log(message.sid));