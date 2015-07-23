#!/usr/bin/python
import os
import requests
import json
import subprocess
import time

def userInput(config):
	def defaultValue(config, key):
		return config[key] if key in config else ""
	res = {}
	invalid = {}
	res['user_name'] = raw_input("your GitHub username (default = " + defaultValue(config, 'user_name') + "): ")
	res['project_name'] = raw_input("name of your SAC project on GitHub (default = " + defaultValue(config, 'project_name') + "): ")
	res['project_branch'] = raw_input("current working branch of your SAC project on GitHub (default = " + defaultValue(config, 'project_branch') + "): ")
	res['google_client_id'] = raw_input("generated Google client id (default = " + defaultValue(config, 'google_client_id') + "): ")
	res['google_client_secret'] = raw_input("generated Google client secret (default = " + defaultValue(config, 'google_client_secret') + "): ")
	res['google_api_key'] = raw_input("generated Google API key (default = " + defaultValue(config, 'google_api_key') + "): ")
	res['sac_app_id'] = raw_input("generated SAC app ID (default = " + defaultValue(config, 'sac_app_id') + "): ")
	res['sac_app_secret'] = raw_input("generated SAC app secret (default = " + defaultValue(config, 'sac_app_secret') + "): ")
	for k, v in res.items():
		if v == "": res[k] = defaultValue(config, k)
	invalid = [k for k, v in res.items() if v == ""]
	if len(invalid) > 0:
		print "invalid configuration: properties", invalid, "must be set"
		res = userInput(config)
	return res

config_file = open('config.json', 'r')
config = json.load(config_file)
invalid_properties = [k for k, v in config.items() if v == ""]
print "current configuration:", json.dumps(config, indent=2)

if len(invalid_properties) > 0:
	print "invalid configuration: properties", invalid_properties, "must be set"
	config = userInput(config)

if 'user_name' and 'project_name' and 'project_branch' and 'google_client_id' and 'google_client_secret' and 'google_api_key' and 'sac_app_id' and 'sac_app_secret' in config:
	reply = str(raw_input('config file complete. do you wish to reset it? (y/n): ')).lower().strip()
	if reply[0] == 'y':
		config = userInput(config)
else:
	config = userInput(config)


with open('config.json', 'w') as config_file:
	json.dump(config, config_file, indent=2)

p = subprocess.Popen(["ngrok", "http", "8080"])
time.sleep(1.5)

# retrieving public url for exposed localhost:8080
headers = {'Content-Type': 'application/json'}
r = requests.get('http://127.0.0.1:4040/api/tunnels', headers=headers)
public_url = json.loads(r.text)['tunnels'][0]['public_url']

# setting environment variables with user input
os.environ["CRAFT_DEMO_SAC_USER"] = config['user_name']
os.environ["CRAFT_DEMO_SAC_PROJECT"] = config['project_name']
os.environ["CRAFT_DEMO_SAC_VERSION"] = config['project_branch']
os.environ["CRAFT_DEMO_SAC_GOOGLE_CLIENT_ID"] = config['google_client_id']
os.environ["CRAFT_DEMO_SAC_GOOGLE_CLIENT_SECRET"] = config['google_client_secret']
os.environ["CRAFT_DEMO_SAC_GOOGLE_API_KEY"] = config['google_api_key']
os.environ["CRAFT_DEMO_SAC_APP_ID"] = config['sac_app_id']
os.environ["CRAFT_DEMO_SAC_APP_SECRET"] = config['sac_app_secret']
os.environ["CRAFT_DEMO_SAC_PORT"] = '8080'
os.environ["CRAFT_DEMO_SAC_URL"] = 'http://localhost:8080'
os.environ["CRAFT_DEMO_SAC_WS_URL"] = 'ws://localhost:8080'
os.environ["CRAFT_RUNTIME_SERVER_URL"] = 'http://runtime.craft.ai'
os.environ["CRAFT_DEMO_SAC_ACTIONS_URL"] = public_url

subprocess.call(["python", "-u", "src/server/main.py"])
p.terminate()
