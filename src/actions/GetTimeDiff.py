from bottle import Bottle, route, run, template, static_file, get, jinja2_template as template, post, request, response, redirect

import runtime
import actions
import json
import requests

from datetime import datetime
from dateutil import parser

"""
GetTimeDiff
@param[in]	time1, time2
@param[out]	timeDiff
"""

defaultInputParams = {'time1': '', 'time2': ''}
defaultOutputParams = {'timeDiff': 0.}
sim_parameters = dict()

# Register actions
def registerAction(user, project, version, sim_id):
	sim_parameters['user'] = user
	sim_parameters['project'] = project
	sim_parameters['version'] = version
	sim_parameters['sim_id'] = sim_id
	runtime.register_webActions(user, project, version, sim_id,'GetTimeDiff', '/home/actions/GetTimeDiff/')

def start():
	request_Id = request.json['requestId']
	inputParams = request.json['input']
	inputParams = actions.applyDefaultValues(inputParams, defaultInputParams)
	time1 = parser.parse(inputParams['time1'])
	time2 = parser.parse(inputParams['time2'])
	timeDiff = time2 - time1
	output_json = json.dumps({'timeDiff': timeDiff.total_seconds()})
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