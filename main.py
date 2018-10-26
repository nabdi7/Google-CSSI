from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools
from google.appengine.ext import ndb
import webapp2
import jinja2
import os
import argparse
from webapp2_extras import sessions
from models import *
from google.appengine.api import mail
from models import*
from datetime import datetime
from datetime import time
from datetime import date
from datetime import timedelta
import time
import json

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

SCOPES = 'https://www.googleapis.com/auth/calendar'

store = oauth_file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    parser = argparse.ArgumentParser()
    class FlagsStuff(object):
        auth_host_name = 'localhost'
        logging_level = 'INFO'
        noauth_local_webserver = 'localhost'
        auth_host_port = ''
    flags = FlagsStuff()
    #flags = {'auth_host_name': 'localhost', 'logging_level': 'INFO'}
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store, flags)

service = build('calendar', 'v3', http=creds.authorize(Http()))


def verification(email,password):
    users = User.query().fetch()
    for user in users:
        if user.email == email and user.password == password:
            return True
    return False


def create_calendar_event(summary,location,description,start_dateTime,end_dateTime,attendee_email):
    event = {
      'summary': summary,
      'location': location,
      'description': description,
      'start': {
        'dateTime': start_dateTime.isoformat(),
        'timeZone': 'America/Los_Angeles',
      },
      'end': {
        'dateTime': end_dateTime.isoformat(),
        'timeZone': 'America/Los_Angeles',
      },
      'attendees': [
        {'email': attendee_email},
      ],
      'reminders': {
        'useDefault': False,
        'overrides': [
          {'method': 'email', 'minutes': 6 * 60},
          {'method': 'popup', 'minutes': 60},
        ],
      },
    }

    event = service.events().insert(calendarId='college.connect.cssi@gmail.com', body=event).execute()
    event_link = event.get('htmlLink')
    event_id = event['id']
    return {'event_link':event_link,'event_id':event_id}


def update_calendar_event(event_id,summary,location,description,start_dateTime,end_dateTime,attendee_email):
    page_token = None
    while True:
      events = service.events().list(calendarId='college.connect.cssi@gmail.com', pageToken=page_token).execute()
      for event in events['items']:
        if event['id'] == event_id:
            the_event = event
      page_token = events.get('nextPageToken')
      if not page_token:
        break

    event_link = the_event.get('htmlLink')
    new_att_email_dict = {'email': attendee_email}
    event_attendees = the_event['attendees'].append(new_att_email_dict)
    updated_event = {'attendees': event_attendees}

    service.events().patch(calendarId='college.connect.cssi@gmail.com', eventId=event_id,
                            sendNotifications=True, body=updated_event).execute()

    return event_link


def email(type,event_id,connect_title,start_dateTime,end_dateTime,location,user_email,user_name,mail_subject):
    event_link = ""
    event_id = event_id

    if type == "host":
        event_dict = create_calendar_event(connect_title,location,"College Connect Session",start_dateTime,end_dateTime,user_email)
        event_link = event_dict['event_link']
        event_id = event_dict['event_id']

    elif type == "join":
        event_link = update_calendar_event(event_id,connect_title,location,"College Connect Session",start_dateTime,end_dateTime,user_email)

    sender_address = "college.connect.cssi@gmail.com"
    mail_to = user_name[0]+" "+user_name[1]+" "+"<"+user_email+">"
    mail_body = user_name[0]+" "+user_name[1]+""":
        Your Connect Event, """+connect_title+""", is scheduled from
        """+str(start_dateTime)+""" to """+str(end_dateTime)+""" at """+str(location)+"""!

        Thank you for choosing College Connect!!
        The College Connect Team
        """
    mail_html = """
        <html><head></head><body>"""+user_name[0]+" "+user_name[1]+""":<br><br>
        Your Connect Event, <b>"""+connect_title+"""</b>, is scheduled from
        """+str(start_dateTime)+""" to """+str(end_dateTime)+""" at """+location+"""!<br><br>

        View and accept your calendar invite at: """+event_link+"""<br><br>

        Thank you for choosing College Connect!!!<br>
        The College Connect Team
        </body></html>"""

    message = mail.EmailMessage(sender=sender_address,
                                subject = mail_subject,
                                to = mail_to,
                                body = mail_body,
                                html = mail_html)
    message.send()

    if type == "host":
        return event_id

def date_parser (date):
    index = date.find('-')
    year = int(date[:index])
    next_index = date.find('-',index+1)
    month = int(date[index+1:next_index])
    day = int(date[next_index+1:])
    return {'month':month,'day':day,'year':year}


class BaseHandler(webapp2.RequestHandler):              # taken from the webapp2 extrta session example
    def dispatch(self):                                 # override dispatch
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)       # dispatch the main handler
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

class WelcomeHandler(BaseHandler):
    def get(self):
        self.session['user']= ""
        welcome_template = JINJA_ENVIRONMENT.get_template('templates/welcome.html')
        error_dict = {'error':""}
        self.response.write(welcome_template.render(error_dict))

    def post(self):
        welcome_template = JINJA_ENVIRONMENT.get_template('templates/welcome.html')
        email = self.request.get('email')
        password = self.request.get('password')

        if ((verification(email,password))):
            user = User.query().filter(User.email == email).fetch()[0]
            self.session['user']= email
            user_dict = {'user':user}
            self.redirect('/dashboard')
        else:
            error_dict = {'error':"error"}
            self.response.write(welcome_template.render(error_dict))
            #display error message in welcome

class SignUpHandler(BaseHandler):
    def get (self):
        signup_template=JINJA_ENVIRONMENT.get_template('templates/signup.html')
        self.response.write(signup_template.render())
    def post(self):
        first_name = self.request.get('first_name')
        last_name = self.request.get('last_name')
        email = self.request.get('email')
        password = self.request.get('password')
        college = self.request.get('college')
        courses = self.request.get('courses').split(", ") # list
        profile_pic = self.request.get('profile_pic')
        name = [first_name,last_name]

        new_user = User(name = name, email = email,
                        password = password, college = college,
                        profile_pic = profile_pic,
                        friends=[])

        # for course in Course.query().fetch():
        #     if (course.name == )


        new_user.put()
        self.session['user'] = email
        self.redirect('/dashboard')

class DashboardHandler(BaseHandler):
    def get(self): #get rid of eventually or check to see if signed in
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        all_posts_query = FeedMessage.query().order(-FeedMessage.date)
        all_posts = all_posts_query.fetch()
        user_dict = {'post': all_posts,'user':user}
        dashboard_template = JINJA_ENVIRONMENT.get_template('templates/dashboard.html')
        self.response.write(dashboard_template.render(user_dict))

        # # user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        # # email("Party","7/31/18 4:00pm","The moon","abdinajka@gmail.com","Najib","Here is your email")

    def post(self):
        post_content = self.request.get('status')

        if len(post_content)>0:
            new_post = FeedMessage(post=post_content)
            new_post.put()
        time.sleep(1)
        self.redirect('/dashboard')

class FeedHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        feed_template = JINJA_ENVIRONMENT.get_template('templates/partials/feed.html')
        self.response.write(feed_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

class MessagesHandler(BaseHandler):

    def get (self):
        msg = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        all_messages_query = Messages.query().order(Messages.date)
        all_messages = all_messages_query.fetch()
        message_dict = {'message': all_messages}
        messages_template = JINJA_ENVIRONMENT.get_template('templates/messages.html')
        self.response.write(messages_template.render(message_dict))

    def post(self):
        message = self.request.get('message')
        # to_user = self.request.get('to_user')
        # from_user = self.request.get('from_user')
        if len(message)>0:
            new_msg = Messages(message=message)
            new_msg.put()
        time.sleep(1)
        self.redirect('/messages')

            # previous : user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
            # previous : user_dict={'user':user}

class HostConnectHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        hostconnect_template = JINJA_ENVIRONMENT.get_template('templates/hostconnect.html')
        self.response.write(hostconnect_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        connect_title = self.request.get('title')

        request_json = json.loads(self.request.get('json_loc'))
        location = request_json['location']
        course = request_json['course']

        date = self.request.get('date')

        date_dict = date_parser(date)

        month = date_dict['month']
        day = date_dict['day']
        year = date_dict['year']

        time_st = self.request.get('time-st')
        time_end = self.request.get('time-end')

        start_time = time_st.split(":")
        start_time_hour = int(start_time[0])
        start_time_min = int(start_time[1])

        end_time = time_end.split(":")
        end_time_hour = int(end_time[0])
        end_time_min = int(end_time[1])


        start_dateTime = datetime(year,month,day,start_time_hour,start_time_min,0,0)
        end_dateTime = datetime(year,month,day,end_time_hour,end_time_min,0,0)


        new_ConnectEvent = ConnectEvent(start_dateTime = start_dateTime,end_dateTime = end_dateTime,
         connect_location = location, connect_title = connect_title, course = course)

        new_ConnectEvent_key = new_ConnectEvent.put()
        users_keys = [user.key]
        new_UserConnectEvent = UserConnectEvent(users_keys=users_keys,
                                                connect_event=new_ConnectEvent_key)

        new_UserConnectEvent.event_id = email("host","",connect_title,start_dateTime,end_dateTime,location,user.email,user.name,"College Connect: Your Connect Event is Scheduled!")

        new_UserConnectEvent.put()

        self.redirect('/dashboard')


class JoinConnectHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        joinconnect_template = JINJA_ENVIRONMENT.get_template('templates/joinconnect.html')
        self.response.write(joinconnect_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        self.redirect('/joinconnectlocation')

        #email("join",connect_title,time,location,user.email,user.name,"College Connect: Your Connect Event is Scheduled!")

class JoinConnectLocationHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        joinconnectlocation_template = JINJA_ENVIRONMENT.get_template('templates/joinconnect_location.html')
        self.response.write(joinconnectlocation_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

        #email("join",connect_title,time,location,user.email,user.name,"College Connect: Your Connect Event is Scheduled!")

class JoinConnectFriendsHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        joinconnectfriends_template = JINJA_ENVIRONMENT.get_template('templates/joinconnect_friends.html')
        self.response.write(joinconnect_friends_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

        #email("join",connect_title,time,location,user.email,user.name,"College Connect: Your Connect Event is Scheduled!")

class JoinConnectCoursesHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        jjoinconnectcourses_template = JINJA_ENVIRONMENT.get_template('templates/joinconnect_courses.html')
        self.response.write(joinconnectcourses_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

        #email("join",connect_title,time,location,user.email,user.name,"College Connect: Your Connect Event is Scheduled!")

class JoinConnectRecentHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        joinconnectrecent_template = JINJA_ENVIRONMENT.get_template('templates/joinconnect_recent.html')
        self.response.write(joinconnectrecent_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

        #email("join",connect_title,time,location,user.email,user.name,"College Connect: Your Connect Event is Scheduled!")

class FriendsHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        # all_friends_query =
        user_dict={'user':user}
        friends_template = JINJA_ENVIRONMENT.get_template('templates/friends.html')
        self.response.write(friends_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

class AddFriendsHandler(BaseHandler):
    def get(self):
        all_friends = User.query().fetch()[0]
        my_friends = all_friends.friends
        self.response.write(my_friends)
        # for friend in my_friends:
        #     if
        # get_friends = all_users.
        # user_dict={'all_users':all_users}
        # friends_template = JINJA_ENVIRONMENT.get_template('templates/addfriends.html')
        # self.response.write(friends_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        # friend_added = self.request.get('friends_added') #if just one friend
        friends_added = self.request.get('friends_added')
        user.friends.extend(friend_added)

class CoursesHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        # courses = Course.query().fetch()
        # courserosters = CourseRoster.query().fetch()
        # user_courselist_keys = []
        #
        # for courseroster in courserosters:
        #     if user.key in courseroster.users_keys:
        #         user_courselist.append(courseroster.course)
        #
        # user_courselist = []
        #
        # for course_key in user_courselist_keys:
        #     for course in courses:
        #         if course.key == course_key:
        #             user_courselist.append(course.name)
        #
        # course_dict={'user':user,'course_list':user_courselist}
        #
        # courses_template = JINJA_ENVIRONMENT.get_template('templates/courses.html')
        # self.response.write(courses_template.render(course_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

class OrganizationsHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        courses_template = JINJA_ENVIRONMENT.get_template('templates/organizations.html')
        self.response.write(courses_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]

class SettingsHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        settings_template = JINJA_ENVIRONMENT.get_template('templates/settings.html')
        self.response.write(settings_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user.college = self.request.get('college_name')
        user.major = self.request.get('major')
        user.home_town = self.request.get('home_town')
        user.bio = self.request.get('bio')
        user.profile_pic = self.request.get('user_pic')
        user.college_pic = self.request.get('college_pic')

        user.put()

        self.redirect('/dashboard')


class AboutUsHandler(BaseHandler):
    def get(self):
        creators_template = JINJA_ENVIRONMENT.get_template('templates/aboutus.html')
        self.response.write(creators_template.render())

class ViewConnectsHandler(BaseHandler):
    def get(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]
        user_dict={'user':user}
        viewconnects_template = JINJA_ENVIRONMENT.get_template('templates/partials/viewconnects.html')
        self.response.write(viewconnects_template.render(user_dict))

    def post(self):
        user = User.query().filter(User.email == self.session.get('user')).fetch()[0]


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'some-secret-key',
}

app = webapp2.WSGIApplication([
    ('/', WelcomeHandler),
    ('/signup', SignUpHandler),
    ('/dashboard', DashboardHandler),
    ('/feed', FeedHandler),
    ('/hostconnect', HostConnectHandler),
    ('/joinconnectlocation', JoinConnectLocationHandler),
    ('/joinconnectfriends', JoinConnectFriendsHandler),
    ('/joinconnectcourses', JoinConnectCoursesHandler),
    ('/joinconnectrecent', JoinConnectRecentHandler),
    ('/joinconnect', JoinConnectHandler),
    ('/friends', FriendsHandler),
    ('/addfriends', AddFriendsHandler),
    ('/courses', CoursesHandler),
    ('/organizations',OrganizationsHandler),
    ('/aboutus', AboutUsHandler),
    ('/messages',MessagesHandler),
    ('/settings',SettingsHandler),
    ('/viewconnects',ViewConnectsHandler),
], debug=True, config=config)
