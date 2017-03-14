#!/usr/bin/python
# -*- coding: utf-8 -*-
from RPiHTTPServer import RPiHTTPServer, RPiHTTPRequestHandler
import RPi.GPIO as GPIO
import os

class OnOffHandler(RPiHTTPRequestHandler):

  # GET /
  def default_response(self):
    """Home page: only render template"""
    self.render_template()

  # POST /
  def switch(self):
    """button pressed: toggle status"""
    if self.server.switch_status == 1:
      # if on, switch off
      GPIO.output(self.config.GPIO_PIN, GPIO.LOW)
      self.server.switch_status = 0
    else:
      # if off, switch on
      GPIO.output(self.config.GPIO_PIN, GPIO.HIGH)    
      self.server.switch_status = 1
    self.render_template()
      
  def render_template(self):
    tpl = os.path.join(self.server.root_folder, 'home.html')
    tpl_content = open(tpl,"r").read()
    label = "ON" if self.server.switch_status == 0 else "OFF" 
    self.content = tpl_content.replace("$STATUS", label) 

if __name__ == '__main__':

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BOARD)

  basedir = os.path.dirname(os.path.abspath(__file__))
  config_file = os.path.join(basedir,"config.json")

  # instantiate http server
  SwitchServer = RPiHTTPServer(config_file, OnOffHandler)

  GPIO_PIN = SwitchServer.server.config.GPIO_PIN
  GPIO.setup(GPIO_PIN, GPIO.OUT)

  # start with switch OFF
  GPIO.output(GPIO_PIN, GPIO.LOW)
  SwitchServer.server.switch_status = 0

  SwitchServer.server.root_folder = basedir

  try:
    print "Listening on http://%s:%s" % (SwitchServer.server.config.SERVER_ADDRESS,SwitchServer.server.config.SERVER_PORT)
    SwitchServer.serve_forever()
  except KeyboardInterrupt:
    pass
    SwitchServer.server.server_close()
