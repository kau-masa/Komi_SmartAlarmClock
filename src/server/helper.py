# Websocket server between client and server
import threading
import gevent
from gevent.queue import Queue
from gevent.pywsgi import WSGIServer
import geventwebsocket
from geventwebsocket import WebSocketError
import requests
from gevent import monkey
from datetime import datetime
from dateutil import tz, parser, relativedelta
monkey.patch_all()

import bottle
from bottle import Bottle, route, run, template, static_file, get, jinja2_template as template, post, request, response, redirect

import runtime
import os
import sys
import glob
import imp
import json
import time
import stateVar

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials

app = Bottle()

URL    = os.getenv('CRAFT_DEMO_SAC_URL', '')
WS_URL = os.getenv('CRAFT_DEMO_SAC_WS_URL', '')

GOOGLE_CLIENT_ID     = os.getenv('CRAFT_DEMO_SAC_GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('CRAFT_DEMO_SAC_GOOGLE_CLIENT_SECRET', '')
GOOGLE_API_KEY       = os.getenv('CRAFT_DEMO_SAC_GOOGLE_API_KEY', '')

CRAFT_DEMO_SAC_USER    = os.getenv('CRAFT_DEMO_SAC_USER', '')
CRAFT_DEMO_SAC_PROJECT = os.getenv('CRAFT_DEMO_SAC_PROJECT', '')
CRAFT_DEMO_SAC_VERSION = os.getenv('CRAFT_DEMO_SAC_VERSION','')

simulation_step = 0.1
simulation_id = -1
localTz = 'UTC'

working_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

### Google
SCOPES = [
	'https://www.googleapis.com/auth/drive',
	'https://mail.google.com/',
	'https://www.googleapis.com/auth/userinfo.email',
	'https://www.googleapis.com/auth/calendar'
	]

flow = OAuth2WebServerFlow(client_id=GOOGLE_CLIENT_ID,
                           client_secret=GOOGLE_CLIENT_SECRET,
                           scope=' '.join(SCOPES),
                           redirect_uri= URL + '/auth')

@app.route('/', method=['GET', 'POST'])
def google_authentification():
	result = request.json
	if result != None and 'type' in result and 'value' in result:
		global localTz
		param = request.json['type']
		val = request.json['value']
		if param == "tz":
			localTz = val
	auth_uri = flow.step1_get_authorize_url()
	auth_uri = auth_uri + '&approval_prompt=force&state=0'
	return template(os.path.join(working_dir, 'html/index.html'), auth = stateVar.authenticated, auth_uri = auth_uri)

### To load css, photo files. They have to be put in the static directory
@app.route('/static/<filename:path>')
def get_static_file(filename):
	return static_file(filename, root = os.path.join(working_dir, 'static/'))

@app.route('/alert')
def handle_websocket():
	ws = request.environ.get('wsgi.websocket')
	if not ws:
		bottle.abort(400, 'Expected WebSocket request.')

	try:
		while not ws.closed:
			try:
				event = runtime.eventQueue.get(True, 55)
				ws.send(event)
				if ws.receive() == None:
					runtime.eventQueue.put(event)
					ws.close()
			except Exception, ex:
				if ex.__class__.__name__ == 'Empty':
					ws.send('ping')
					ws.receive()
				else:
					print '%s: %s' % (ex.__class__.__name__, ex)
	except WebSocketError, ex:
		print '%s: %s' % (ex.__class__.__name__, ex)
		ws.close();

@app.route('/stop')
def stop_simulation():
	with runtime.eventQueue.mutex:
		runtime.eventQueue.queue.clear()
	if not(stateVar.t_simulation is None):
	    stateVar.t_simulation.event.set()
	    stateVar.t_simulation.join()
	    stateVar.t_simulation = None
	return template(os.path.join(working_dir, 'html/index.html'), auth = stateVar.authenticated, sim = stateVar.t_simulation)

@app.route('/run', method=['GET', 'POST'])
def run_simulation():
	if stateVar.t_simulation is None:
		stateVar.currentTime = time.time()
		# Create life simulation    
		global simulation_id
		simulation_id = runtime.create_simulation(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION)

		# Register webActions
		get_and_register_webActions()

		with open(os.path.join(working_dir, '../knowledge/ContextualAlerts.json')) as data_file:
			data = json.load(data_file)

		data['cred_google'] = stateVar.cred

		# Create life entity
		stateVar.entityId = runtime.create_entity(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id,'craft:ContextualAlerts.bt',  data)
		# Start update simulation in a thread
		stateVar.t_simulation = UpdateLifeThreadClass()
		stateVar.t_simulation.start()
	return update_data()

def update_data():
	result = request.json
	if result != None and 'type' in result and 'value' in result:
		param = request.json['type']
		val = request.json['value']
		if param == "snooze":
			if val == "You have to wake up, you have a metting.":
				runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'alert':{'snooze':{'0':True, '1':False}}})
			elif val == "It's time to go.":
				runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'alert':{'snooze':{'0':False, '1':True}}})
		elif param == "time":
			stateVar.currentTime = stateVar.currentTime + int(val)*60
		elif param == "transpMode":
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'transportationMode':val})
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'directions':{'found':False}})
		elif param == "location":
			location = str(val["latitude"]) + "," + str(val["longitude"])
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'origin':location})
		elif param == "origin":
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'origin':val})
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'directions':{'found':False}})
		elif param == "presence":
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'left': not val})
		elif param == "awake":
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'awake': not val})
		elif param == "workLocation":
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'workLocation':val})
			runtime.putEntityKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, stateVar.entityId, {'directions':{'found':False}})
		elif param == "speed":
			stateVar.speedFactor = int(val)
	return template(os.path.join(working_dir, 'html/index.html'),
		auth = stateVar.authenticated,
		sim = stateVar.t_simulation,
		email = stateVar.cred['id_token']['email'],
		url = URL,
		wsUrl = WS_URL,
		googleApiKey = GOOGLE_API_KEY)

### Google authentification
@app.route('/auth')
def google_authentification():
	code = request.query.code
	stateVar.cred = json.loads(flow.step2_exchange(code).to_json())
	stateVar.authenticated = True
	return template(os.path.join(working_dir, 'html/index.html'), auth = stateVar.authenticated)

def register_routes_webActions(app, actionName, startCallback, cancelCallback):
	actionRoute = '/home/actions/' + actionName
	app.route(actionRoute + '/start', ['POST'], startCallback)
	app.route(actionRoute + '/cancel', ['POST'], cancelCallback)

def get_and_register_webActions():
	actionsdir = os.path.abspath(__file__ + "/../../actions/")
	print 'Registering web actions located at ' + actionsdir
	for file in glob.glob(actionsdir + '/*.py'):
		name = os.path.splitext(os.path.basename(file))[0]
		module = imp.load_source(name, actionsdir +'/' + name + '.py')
		module.registerAction(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id)
		register_routes_webActions(app, name, module.start, module.cancel)
		print '- Registering web actions: ' + name

### LIFE update in a thread
class UpdateLifeThreadClass(gevent.Greenlet):
	def __init__(self):
		gevent.Greenlet.__init__(self)
		self.event = gevent.event.Event()
	def _run(self):
		previousTickTime = stateVar.currentTime
		once = True
		while not self.event.isSet():
			try:
				success = runtime.update_simulation(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, simulation_step)
			except OSError, e:
				print e
				runtime.delete_simulation(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id)

			gevent.sleep(simulation_step)
			currentTickTime = time.time()
			stateVar.currentTime = stateVar.currentTime+stateVar.speedFactor*(currentTickTime-previousTickTime)
			previousTickTime = currentTickTime
			if once:
				runtime.setGlobalKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, {'tz':localTz})
				once = False
			runtime.setGlobalKnowledge(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id, {'time':stateVar.currentTime})

		runtime.delete_simulation(CRAFT_DEMO_SAC_USER, CRAFT_DEMO_SAC_PROJECT, CRAFT_DEMO_SAC_VERSION, simulation_id)

	def __str__(self):
		return 'UpdateLifeThreadClass'
