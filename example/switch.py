#!/usr/bin/python
# -*- coding: utf-8 -*-
from RPiHTTPServer import RPiHTTPServer, RPiHTTPRequestHandler
# import RPi.GPIO as GPIO
import os

class OnOffHandler(RPiHTTPRequestHandler):

  tpl_vars = { "{{STATUS}}": "ON" }

  # GET /
  def default_response(self):
    """Home page: only render template"""
    self.render_template("home.html",self.tpl_vars)

  # GET /admin
  def admin(self):
    """Home page: only render template"""
    self.render_template("admin.html",self.tpl_vars)

  # POST /
  def switch(self):
    """button pressed: toggle status"""

    if self.server.switch_status == 1:
      # if on, switch off
      # GPIO.output(self.config.GPIO_PIN, GPIO.LOW)
      self.server.switch_status = 0
      self.tpl_vars["{{STATUS}}"] = "ON"

    else:
      # if off, switch on
      # GPIO.output(self.config.GPIO_PIN, GPIO.HIGH)
      self.server.switch_status = 1
      self.tpl_vars["{{STATUS}}"] = "OFF"

    self.render_template('home.html',self.tpl_vars)

if __name__ == '__main__':

  # GPIO.setwarnings(False)
  # GPIO.setmode(GPIO.BOARD)

  basedir = os.path.dirname(os.path.abspath(__file__))
  config_file = os.path.join(basedir,"config.json")

  # instantiate http server
  SwitchServer = RPiHTTPServer(config_file, OnOffHandler)

  # GPIO_PIN = SwitchServer.server.config.GPIO_PIN
  # GPIO.setup(GPIO_PIN, GPIO.OUT)

  # start with switch OFF
  # GPIO.output(GPIO_PIN, GPIO.LOW)
  SwitchServer.server.switch_status = 0

  SwitchServer.server.root_folder = basedir

  try:
    print "Listening on http://%s:%s" % (SwitchServer.server.config.SERVER_ADDRESS,SwitchServer.server.config.SERVER_PORT)
    SwitchServer.serve_forever()
  except KeyboardInterrupt:
    pass
    # cleanup GPIO status
    # GPIO.output(GPIO_PIN, GPIO.LOW)
    # GPIO.cleanup()
    SwitchServer.server.server_close()
