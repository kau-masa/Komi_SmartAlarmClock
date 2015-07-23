from bottle import Bottle, route, run, template, static_file, get, jinja2_template as template, post, request, response, redirect

import requests
import runtime
import actions
import json

"""
Sum
@param[in]	term1, term2
@param[out]	result
"""

defaultInputParams = {'term1': 0., 'term2': 0.}
defaultOutputParams = {'result': 0.}
sim_parameters = dict()

# Register actions
def registerAction(user, project, version, sim_id):
	sim_parameters['user'] = user
	sim_parameters['project'] = project
	sim_parameters['version'] = version
	sim_parameters['sim_id'] = sim_id
	runtime.register_webActions(user, project, version, sim_id, 'Sum', '/home/actions/Sum/')

def start():
	inputParams = request.json['input']
	inputParams = actions.applyDefaultValues(inputParams, defaultInputParams)

	request_Id = request.json['requestId']
	output_json = json.dumps({"result": (inputParams['term1'] + inputParams['term2'])})
	output_url = '{}/api/v1/{}/{}/{}/{}/actions/{}/output'.format(runtime.CRAFT_RUNTIME_SERVER_URL, sim_parameters['user'],sim_parameters['project'],sim_parameters['version'],sim_parameters['sim_id'], request_Id)
	success_url = '{}/api/v1/{}/{}/{}/{}/actions/{}/success'.format(runtime.CRAFT_RUNTIME_SERVER_URL, sim_parameters['user'],sim_parameters['project'],sim_parameters['version'],sim_parameters['sim_id'], request_Id)
	json_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
	r = requests.post(output_url, data=output_json, headers = json_headers)
	r = requests.post(success_url)
	return 

def cancel():
	request_Id = request.json['requestId']
	cancel_url = '{}/api/v1/{}/{}/{}/{}/actions/{}/cancelation'.format(runtime.CRAFT_RUNTIME_SERVER_URL, sim_parameters['user'],sim_parameters['project'],sim_parameters['version'],sim_parameters['sim_id'], request_Id)
	r = requests.post(cancel_url)
	return 