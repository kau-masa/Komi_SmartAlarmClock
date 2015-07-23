from bottle import Bottle, route, run, template, static_file, get, jinja2_template as template, post, request, response, redirect

import json
import requests
import runtime
import actions

"""
Alert
"""

defaultInputParams = {'sound':'', 'message':'', 'loop':False}
defaultOutputParams = {}
sim_parameters = dict()

# Register actions
def registerAction(user, project, version, sim_id):
	sim_parameters['user'] = user
	sim_parameters['project'] = project
	sim_parameters['version'] = version
	sim_parameters['sim_id'] = sim_id
	runtime.register_webActions(user, project, version, sim_id, 'Alert', '/home/actions/Alert/')

def start():
	inputParams = request.json['input']
	request_Id = request.json['requestId']
	inputParams = actions.applyDefaultValues(inputParams, defaultInputParams)

	jsonObj = '{"message": "' + inputParams['message'] +'", "song": "'+  inputParams['sound'] +'", "loop": "'+  str(inputParams['loop']) +'"}'
	runtime.eventQueue.put(jsonObj)

	success_url = '{}/api/v1/{}/{}/{}/{}/actions/{}/success'.format(runtime.CRAFT_RUNTIME_SERVER_URL, sim_parameters['user'],sim_parameters['project'],sim_parameters['version'],sim_parameters['sim_id'], request_Id)
	r = requests.post(success_url)
	return 

def cancel():
	request_Id = request.json['requestId']
	cancel_url = '{}/api/v1/{}/{}/{}/{}/actions/{}/cancelation'.format(runtime.CRAFT_RUNTIME_SERVER_URL, sim_parameters['user'],sim_parameters['project'],sim_parameters['version'],sim_parameters['sim_id'], request_Id)
	r = requests.post(cancel_url)
	return 
