# -*- coding: utf-8 -*-
"""HTTP server eand request handler built on top of Python standard library's
BaseHTTPServer.
Originally intended for Raspberry Pi projects with a web interface, the small
web server and associated request handler add some interesting features to
BaseHTTPServer and can be used independently of Raspberry Pi

Features:
- config in json file
- optional multithreaded server
- static file serving with cache
- Basic authentication (multiple users/roles)
- POST parsing
- QS parsing
- basic template rendering
- dynamic routing based on configuration or convention

TODOs:
- support for Python 3k
- handle config file parse error
- parametric routes
- sanitize path in url request
- handle file upload
- safely handle non utf-8 chars in POST request

"""

__version__ = "0.3.2"

__all__ = ["RPiHTTPRequestHandler", "RPiHTTPServer"]

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
from calendar import timegm
from email.utils import parsedate
import base64 as b64

import cgi
import os
import json
import mimetypes
import shutil
import time
import sys
import re

class RPiHTTPRequestHandler(BaseHTTPRequestHandler):
  """Base class for Raspberry Pi web based projects"""

  # class initialization

  server_version = "RPiHTTPServer 0.3.2"

  # mimetypes for static files
  if not mimetypes.inited:
    mimetypes.init() # read system mime.types
  extensions_map = mimetypes.types_map.copy()

  def __init__(self, *args):

    # default properties
    self.content_type = "text/html; charset=UTF-8" # Only UTF-8 is supported
    self.content = ""
    self.response_status = 200
    self.response_headers = {}
    self.form = {}
    self.user = None
        
    # init parent class
    BaseHTTPRequestHandler.__init__(self, *args)
    
  def do_GET(self):
    """Process GET requests"""
    self.handle_request()

  def do_POST(self):
    """Process POST requests"""
    # parse form
    # TODO: parse file upload, parse form more robust
    if 'content-type' in self.headers:
      self.form = cgi.FieldStorage(
        fp=self.rfile,
        headers=self.headers,
        environ={
               'REQUEST_METHOD':'POST',
               'CONTENT_TYPE':self.headers['Content-Type']
               })
    self.handle_request()

  def do_AUTH(self):
    """Manage authentication when required"""
    keys = self.server.protected_routes[self.url.path]

    if 'authorization' in self.headers:
      if self.headers['Authorization'] in keys: 
        self.user = b64.b64decode(self.headers['Authorization'][6:]).split(":")[0]
        return True
    
    self.response_status = 401
    self.response_headers["WWW-Authenticate"] = 'Basic realm=\"%s\"' % self.server.REALM 
    self.content = """
      <h1>Authorization required</h1>
      <p>You don't have permission to access the requested resource.</p>
      """
    return False

  def get_safe_param(self, param, charset='utf-8'):
    """Safely get a html escaped post param"""
    # TODO: safely handle non utf-8 chars
    if param in self.form:
      return cgi.escape(self.form[param].value.decode(charset),quote=True)
    else:
      return ''

  def handle_request(self):
    """Process generic requests"""
    # populate useful properties
    self.config = self.server.config  # access config shorter
    self.request_xhr = 'x-requested-with' in self.headers # request is xhr?
    self.url = cgi.urlparse.urlparse(self.path) # parse url
    self.qs = cgi.urlparse.parse_qs(self.url.query) # parse query string

    # serve static content first
    if self.url.path.startswith(self.config["STATIC_URL_PREFIX"]):
      if self.command == 'POST':
        # POST not allowed on static content
        self.send_error(405,"Method not allowed")
      else:
        self.serve_static()
    else:
      # manage routed requests with controller methods
      self.handle_routed_request()

  def handle_routed_request(self):
    """Handle request with a method of the class:
    the method needs to be actually implemented in the final class"""
    if self.command in self.config["ROUTE"]:
      routing = self.config["ROUTE"][self.command]
    else:
      routing = None
    # TODO: implement parametric routes
    if routing and self.url.path in routing:
      controller = routing[self.url.path]
    else:
      # by default look for a controller method named as the requested path
      # prefixed by "routed_"
      # /controller => self.routed_controller()
      # TODO: sanitize path
      controller = "routed_" + self.url.path.strip("/")
    # call instance method mapped by the route or give 404 if not such a method
    controller_method = getattr(self, controller, None)

    if controller_method:
      # check if route is a protected route 
      call_controller = self.do_AUTH() if self.url.path in self.server.protected_routes else True
      # TODO: improve way to shortcut answer in the controller
      if call_controller: controller_method()
      
      self.serve_response()
    
    else:
      self.give_404()

  def default_response(self):
    """Default response for test purposes"""
    self.content = """<!DOCTYPE html>
    <html>
      <body><h1>Hello world!</h1>
      HTTP Method: %s
      </body>
    </html>""" % self.command

  def serve_response(self):
    """General handling of non static HTTP response"""
    self.send_response(self.response_status)

    if not 'Content-Type' in self.response_headers:
      self.response_headers['Content-Type'] = self.content_type
    if not 'Content-Length' in self.response_headers:
      self.response_headers["Content-Length"] = str(len(self.content))

    for header_name, header_value in self.response_headers.iteritems():
      self.send_header(header_name, header_value)

    self.end_headers()
    self.wfile.write(self.content)

  def send_error(self, code, message):
    self.response_status = code
    BaseHTTPRequestHandler.send_error(self, code, message)

  def give_404(self,message="Not found"):
    self.send_error(404,message)

  # very basic template rendering: tpl_vars should be a
  # dictionay whose keys are the strings to be replaced
  # and whose values are the replacements. There are many
  # better libraries out there (e.g. Jinja2, Pystache)
  def render_template(self, template, tpl_vars):
    tpl = os.path.join(self.config["TEMPLATE_FOLDER"], template)
    if os.path.isfile(tpl):
      tpl_content = open(tpl,"r").read()
      pattern = re.compile('|'.join(tpl_vars.keys()))
      self.content = pattern.sub(lambda x: tpl_vars[x.group()], tpl_content)
    else:
      self.give_404("Template missing")

  # HANDLE STATIC CONTENT

  def translate_path(self):
    """Translate URL path to file system path"""
    # very basic: we just remove the prefix url and prepend file system static folder
    url_path = self.url.path
    prefix = self.config["STATIC_URL_PREFIX"]
    url_path_unprefix = url_path[url_path.startswith(prefix) and len(prefix):]
    return self.config["STATIC_FOLDER"] + url_path_unprefix

  def serve_static(self):
    """Handle static files requests taking into account
    HTTP headers last-modified and if-modified-since"""
    f = None

    path = self.translate_path()
    if os.path.isfile(path):
      try:
        f = open(path, 'rb')
      except IOError:
        self.give_404()
        return None
      # compare file's last change date with a possible If-Modified-Since headers
      # sent by the browser (we give a conditional 304 status response)
      fs = os.fstat(f.fileno())
      last_modified = int(fs.st_mtime)
      if_modified_since = 0
      if 'if-modified-since' in self.headers:
        if_modified_since = timegm(parsedate(self.headers['if-modified-since']))

      if last_modified > if_modified_since:
        # file has been modified or browser does not have it in cache
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.send_header("Expires", self.date_time_string(time.time()+self.config["STATIC_CACHE"]))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)
      else:
        # browser cache copy is valid
        self.send_response(304)
      f.close()
    else:
      self.give_404()
      return None

  def guess_type(self, path):
    """establish mime type's file by the extension"""
    base, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in self.extensions_map:
      return self.extensions_map[ext]
    else:
      return 'application/octet-stream'

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle every HTTP request in a separate thread."""

class TestHandler(RPiHTTPRequestHandler):
  """Test class to extend request handler:
  unless explicitly defined in config routes
  every URL request is mapped to a method of the class of the form route_$method:
  /test => routed_test
  """

  def routed_testget(self):
    self.content = """<!DOCTYPE html>
    <html>
    <h1>Test GET</h1>
    This is UTF-8 text (àèìòù €)<br><br>
    Query string: %s<br><br>
    <form action="/testpost" method="POST">
    Post param: <input name="post_param"><br>
    Post param array 1 (first element): <input name="param_array"><br>
    Post param array 1 (second element): <input name="param_array"><br>
    Post param array 2 (first element): <input name="param[]"><br>
    Post param array 2 (second element): <input name="param[]"><br>
    <input type="submit">
    </form>
    </html>""" % self.qs

  def routed_testpost(self):

    if self.form:
      # this show how to handle array POST params
      # see https://docs.python.org/2/library/cgi.html#higher-level-interface
      post_param = self.form.getfirst('post_param')
      post_param_a1 = self.form.getlist('param_array')
      post_param_a2 = self.form.getlist('param[]')
      post_param_a3 = [ self.form.getfirst('param[test][first]') or "", self.form.getfirst('param[test][second]') or "" ]

      params = (post_param,)
      params = params + (post_param_a1[0] if len(post_param_a1) > 0 else "",)
      params = params + (post_param_a1[1] if len(post_param_a1) > 1 else "",)
      params = params + (post_param_a2[0] if len(post_param_a2) > 0 else "",)
      params = params + (post_param_a2[1] if len(post_param_a2) > 1 else "",)
      params = params + (post_param_a3[0],)
      params = params + (post_param_a3[1],)

    else:
      params = ("",)*7

    self.content = """<!DOCTYPE html>
    <html>
    <h1>Test POST</h1>

    This is UTF-8 text (èìòù €)<br><br>

    <form method="POST">
    Post param: <input name="post_param" value="%s"><br>
    Post param array 1 (first element): <input name="param_array" value="%s"><br>
    Post param array 1 (second element): <input name="param_array" value="%s"><br>
    Post param array 2 (first element): <input name="param[]" value="%s"><br>
    Post param array 2 (second element): <input name="param[]" value="%s"><br>    
    Post param array 3 (first element): <input name="param[test][first]" value="%s"><br>
    Post param array 3 (second element): <input name="param[test][second]" value="%s"><br>
    <input type="submit">
    </form>
    </html>""" % tuple(params)


class RPiHTTPServer:
  """
  Class which construct the server from config file and handler class
  Provide:
  - config file as a json
  - handler class as a subclass of RPiHTTPRequestHandler

  Usage:

    class MyHandler(RPiHTTPRequestHandler):
      # your class definition
      ...

    MyServer = RPiHTTPServer(path_to_config_file, MyHandler)
    MyServer.serve_forever()

    You have access to HTTPServer instance via MyServer.server

  """

  # TODO:
  # - handle config file parse error

  def __init__(self, config_file = '', request_handler = RPiHTTPRequestHandler):

    # default config
    config_start = self.default_config(config_file)

    # config from file
    config_load = {}
    if os.path.isfile(config_file):
      try:
        config_load = json.load(open(config_file,'r'))
      except:
        print "Error parsing configuration file, falling back to defaults"

    # merge default config with config from file
    config = config_start.copy()
    config.update(config_load)

    if config["SERVER_MULTITHREADED"]:
      server_builder_class = ThreadedHTTPServer
    else:
      server_builder_class = HTTPServer

    self.server = server_builder_class((config["SERVER_ADDRESS"], config["SERVER_PORT"]), request_handler)
    self.server.config = config
    self.server.protected_routes = {}
    self.setup_auth(config)

  def setup_auth(self, config):
    if "ROLES" in config:
      for role in config["ROLES"]:
        key = "Basic " + b64.b64encode("%s:%s" % (role["USERNAME"],role["PASSWORD"]))
        for route in role["ROUTES"]: 
          if route in self.server.protected_routes:
            self.server.protected_routes[route].append(key)
          else:    
            self.server.protected_routes[route] = [key]
      if "REALM" in config:
        self.server.REALM = config["REALM"]
      else:
        self.server.REALM = "Authentication required"   

  def serve_forever(self):
    self.server.serve_forever()

  def default_config(self, config_file):
    if os.path.isfile(config_file):
      default_folder = os.path.dirname(config_file)
    else:
      default_folder = os.getcwd()

    return {
        "SERVER_ADDRESS": "0.0.0.0",
        "SERVER_PORT": 8000,
        "SERVER_MULTITHREADED": True,
        "STATIC_URL_PREFIX": '/static',
        "STATIC_FOLDER":  os.path.join(default_folder,"static"),
        "STATIC_CACHE": 604800,
        "TEMPLATE_FOLDER": os.path.join(default_folder,"templates"),
        "ROUTE": { # basic dynamic routing
          "GET": {
            "/": "default_response"
            },
          "POST": {
            "/": "default_response",
            }
          }
      }

def test(config_file):
  test_server = RPiHTTPServer(config_file, TestHandler)
  test_server.serve_forever()

if __name__ == "__main__":
  test('config.json')
