from __future__ import print_function
import httplib2

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import time
import rfc3339

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'ADEToGoogleCalendar'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_path = "calendar-python-quickstart.json"
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def deleteEvents(service, gcal):
    for i in range(len(gcal)):
        try:
            service.events().delete(calendarId='primary',
                                    eventId=gcal[i].googlCalID).execute()
        except:
            pass
        # To avoid "Rate Limit Exceeded"
        time.sleep(0.01)


def update(evtToAdd, evtToDel, modifEvt):
    # get the credentials
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    # delete all exisiting events
    #service.calendars().clear(calendarId='primary').execute()
    deleteEvents(service, evtToDel)

    # insert new events
    event = {
      'summary': 'New Event',
      'location': '',
      'description': '',
      'start': {
        'dateTime': '2016-05-15T09:00:00-07:00',
        'timeZone': 'Europe/Paris',
      },
      'end': {
        'dateTime': '2016-05-15T17:00:00-07:00',
        'timeZone': 'Europe/Paris',
      },
      'recurrence': [],
      'attendees': [],
      'reminders': {},
    }

    for i in range(len(evtToAdd)):
        event['description'] = evtToAdd[i].description
        event['summary'] = evtToAdd[i].summary
        event['location'] = evtToAdd[i].location
        start = evtToAdd[i].dtstart
        event['start']['dateTime'] = rfc3339.rfc3339(start)
        end = evtToAdd[i].dtend
        event['end']['dateTime'] = rfc3339.rfc3339(end)
        evt = service.events().insert(
                                calendarId='primary', body=event).execute()
        e = evtToAdd[i]
        e = e._replace(googlCalID=evt.get('id'))
        modifEvt.append(e)
        # To avoid "Rate Limit Exceeded"
        time.sleep(0.01)


if __name__ == '__main__':
    pass
