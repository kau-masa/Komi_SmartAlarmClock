# -*- coding: utf8 -*-

def applyDefaultValues(params, default):
	for default_k,default_v in default.items():
		if not default_k in params:
			params[default_k] = default_v
	return params