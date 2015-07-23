# -*- coding: utf8 -*-

import json
import requests
import os
import socket
import Queue

mainEntityId = -1
eventQueue = Queue.Queue()

status = {'created': 0, 'failed': 1, 'running': 2, 'succeeded': 3, 'canceled': 4, 'canceling': 5, 'destroyed': 6}

URL = os.getenv('CRAFT_DEMO_SAC_URL', '')
CRAFT_RUNTIME_SERVER_URL = os.getenv('CRAFT_RUNTIME_SERVER_URL', '')
CRAFT_RUNTIME_SERVER_API_BASE_ROUTE = os.getenv('CRAFT_RUNTIME_SERVER_API_BASE_ROUTE', '/api/v1')
HOSTIP = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
CRAFT_DEMO_SAC_ACTIONS_URL = os.getenv('CRAFT_DEMO_SAC_ACTIONS_URL', 'http://' + HOSTIP + ':' + os.getenv('CRAFT_DEMO_SAC_PORT', '8082'))
SAC_APP_SECRET = os.getenv('CRAFT_DEMO_SAC_APP_SECRET', '')
SAC_APP_ID     = os.getenv('CRAFT_DEMO_SAC_APP_ID', '')

HEADER_WITH_SECRETS = {'X-Craft-Ai-App-Id': SAC_APP_ID, 'X-Craft-Ai-App-Secret': SAC_APP_SECRET, 'Content-type': 'application/json', 'Accept': 'text/plain'}
RUNTIME_SERVER_REQUEST_PARAMS = {'scope': 'app'}

def create_simulation(user, project, version):
	print 'Creating Simulation...'
	r = requests.put(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version, headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)
	return r.text

def delete_simulation(user, project, version, sim_id):
	print 'Deleting Simulation...'
	r = requests.delete(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id )

def update_simulation(user, project, version, sim_id, time_t):
	r = requests.post(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id  + '/update', data='{"time":'+ str(time_t)+'}', headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)
	return r.text

def create_entity(user, project, version, sim_id, behavior, knowledgeJson=None ):
	url = CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id + '/entities'
	
	if not knowledgeJson :
		knowledgeJson = json.loads('{}')

	json_data = '{"behavior" : "' + behavior +'", "knowledge":' + json.dumps(knowledgeJson) + '}'

	r = requests.put(url, data=json_data, headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)

	print 'Entity id', r.text

	return int(r.text)

def delete_entity(user, project, version, sim_id, id):
	r = requests.delete(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id +'/entities/' + str(id), headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)

def getEntityKnowledge(user, project, version, sim_id, id):
	r = requests.get(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id + '/entities/'+ str(id) + '/knowledge', headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)
	return r.text

def putEntityKnowledge(user, project, version, sim_id, id, val):
	r = requests.post(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id + '/entities/'+ str(id) + '/knowledge', data=json.dumps(val), headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)

def register_webActions(user, project, version, sim_id, actionName, requestName):
	print 'Registering web actions', actionName

	req = json.dumps({
		'name': actionName,
		'url': CRAFT_DEMO_SAC_ACTIONS_URL + requestName
	})
	r = requests.put(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id + '/actions', data=req, headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)

def getGlobalKnowledge(user, project, version, sim_id):
	r = requests.get(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id +'/globalKnowledge', headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)
	return r.text

def setGlobalKnowledge(user, project, version, sim_id, val):
	r = requests.post(CRAFT_RUNTIME_SERVER_URL + CRAFT_RUNTIME_SERVER_API_BASE_ROUTE + '/' + user + '/' + project + '/' + version + '/' + sim_id +'/globalKnowledge', data=json.dumps(val), headers = HEADER_WITH_SECRETS, params = RUNTIME_SERVER_REQUEST_PARAMS)