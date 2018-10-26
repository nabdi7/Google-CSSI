#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
import jinja2
import logging
import time
from google.appengine.ext import ndb

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class CoordsRequest(ndb.Model):
    lat = ndb.StringProperty(required = True)
    lon = ndb.StringProperty(required = True)
    timestamp = ndb.DateTimeProperty(auto_now_add = True)

class AddressRequest(ndb.Model):
    address = ndb.StringProperty(required = True)
    timestamp = ndb.DateTimeProperty(auto_now_add = True)

class RecordRequestHandler(webapp2.RequestHandler):
    def post(self):
        logging.info(self.request)
        if self.request.get('type') == "coords":
            new_record = CoordsRequest(lat = self.request.get('lat'),
                                       lon = self.request.get('lon'))
            new_record.put()
        elif self.request.get('type') == "address":
            new_address_record = AddressRequest(address = self.request.get('address'))
            new_address_record.put()
        else:
            logging.error("Malformed Request!")

class MainHandler(webapp2.RequestHandler):
    def get(self):
        # All we need to do is really just displaying the page once.
        # From now on everything will be client-side, at least for now.
        template = JINJA_ENV.get_template('templates/map.html')
        self.response.write(template.render())

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/record_request', RecordRequestHandler)
], debug=True)
