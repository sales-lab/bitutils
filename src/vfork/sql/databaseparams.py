from getpass import getpass

def add_database_options(arg_parser, conf_file=False):
	if conf_file:
		arg_parser.add_option('-c', '--conf', dest='conf', help='read database configuration from FILE', metavar='FILE')
	arg_parser.add_option('-d', '--db', dest='db', help='the DATABASE name', metavar='DATABASE')
	arg_parser.add_option('-H', '--host', dest='host', default='localhost', help='the HOST of the database', metavar='HOST')
	arg_parser.add_option('-u', '--user', dest='user', help='the USERNAME for the database connection', metavar='USERNAME')

def collect_database_params(options, conf_map=None):
	params = {}
	
	if conf_map is not None:
		for key in ('host', 'user', 'passwd', 'db'):
			try:
				params[key] = conf_map[key]
			except KeyError:
				pass
	
	for key in ('host', 'user', 'db'):
		try:
			value = getattr(options, key)
			if value is not None:
				params[key] = value
		except AttributeError:
			pass
	
	for key in ('host', 'user', 'db'):
		if not params.has_key(key):
			raise KeyError("you must specify a value for '%s'." % key)

	if not params.has_key('passwd'):
		params['passwd'] = getpass('Enter database password: ')
	
	return params
