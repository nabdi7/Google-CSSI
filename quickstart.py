from __future__ import print_function
import datetime
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

store = oauth_file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)

service = build('calendar', 'v3', http=creds.authorize(Http()))

event = {
  'summary': 'Come to the Party',
  'location': '800 Howard St., San Francisco, CA 94103',
  'description': 'Its gonna be L1T.',
  'start': {
    'dateTime': '2018-08-03T09:00:00-07:00',
    'timeZone': 'America/Los_Angeles',
  },
  'end': {
    'dateTime': '2018-09-01T17:00:00-07:00',
    'timeZone': 'America/Los_Angeles',
  },
  'recurrence': [
    'RRULE:FREQ=DAILY;COUNT=1'
  ],
  'attendees': [
    {'email': 'zpghera00@gmail.com'},
    {'email': 'karlee.l.wong@gmail.com'},
  ],
  'reminders': {
    'useDefault': False,
    'overrides': [
      {'method': 'email', 'minutes': 24 * 60},
      {'method': 'popup', 'minutes': 60},
    ],
  },
}

event = service.events().insert(calendarId='college.connect.cssi@gmail.com', body=event).execute()
event_link = event.get('htmlLink')
print ("Event created: ",event_link)


def calendarListResource(calId):
    calendar_list_entry = service.calendarList().get(calendarId=calId).execute()
    print (calendar_list_entry['summary'])

#calendarListResource("college.connect.cssi@gmail.com")
