import re

class TableDefinitionConverter(object):
	def __init__(self):
		self.initRxmap()
	
	def initRxmap(self):
		self.rxmap = {}
		self.rxmap['create']    = re.compile(r'create table (\S+)', re.I)
		self.rxmap['integer']   = re.compile(r'(?:small|big)?int\S*(?:\s+unsigned)?', re.I)
		self.rxmap['double']    = re.compile(r'double', re.I)
		self.rxmap['date']      = re.compile(r"date not null", re.I)
		self.rxmap['longtext']  = re.compile(r'longtext', re.I)
		self.rxmap['blob']      = re.compile(r'(?:long)?blob', re.I)
		self.rxmap['enum']      = re.compile(r'\s+enum\s*\(([^)]+)\)', re.I)
		self.rxmap['default']   = re.compile(r"\s*default '[^']*'", re.I)
		self.rxmap['increment'] = re.compile(r'\s*auto_increment', re.I)
		self.rxmap['reserved']  = re.compile(r'^\s*(count|end|offset)', re.I)
		self.rxmap['key']       = re.compile(r'(unique\s+)?key (\S+) \((.+)\)', re.I)
		self.rxmap['keys']      = re.compile(r'([^,(]+)(?:\([^)]+\))?')
		self.rxmap['primary']   = re.compile(r'\s*primary\s+key\s+\((.+)\)', re.I)
		self.rxmap['myisam']    = re.compile(r'\)\s*type=myisam', re.I)

	def parse(self, fd, tablePrefix=''):
		''' Reads a table definition in MySQL style from a flat file and converts it
		    to PostgreSQL style.
		    
		    @param fd: a file-like object providing the table schema.
		    @param tablePrefix: a prefix to add to the table name.
		    @return: a tuple made of:
		    	  - the table name;
		    	  - the converted table definition;
		    	  - a list of 'create index' statements.
		'''
		tableName = None
		tableLines = []
		indexes = []
		
		for line in fd:
			line = line.strip()
			if len(line) == 0 or line.startswith('--'):
				continue
			
			if tableName is None:
				m = self.rxmap['create'].match(line)
				if m is not None:
					tableName = '%s%s' % (tablePrefix, m.group(1))
					line = self.rxmap['create'].sub(r'create table %s' % tableName, line)
					tableLines.append(line)
			else:
				m = self.rxmap['key'].match(line)
				if m is not None:
					line = self.replaceKey(tableName, m)
					indexes.append(line)
				else:
					m = self.rxmap['myisam'].match(line)
					if m is not None:
						lastLine = tableLines.pop()
						if lastLine[-1] == ',':
							lastLine = lastLine[:-1]
						tableLines += [lastLine, ')']
						break
					else:
						line = self.rxmap['integer'].sub('integer', line)
						line = self.rxmap['double'].sub('float4', line)
						line = self.rxmap['date'].sub('date', line)
						line = self.rxmap['longtext'].sub('text', line)
						line = self.rxmap['blob'].sub('text', line)
						line = self.replaceEnum(line)
						line = self.rxmap['default'].sub('', line)
						line = self.rxmap['increment'].sub('', line)
						line = self.rxmap['primary'].sub(self.replacePrimaryKey, line)
						line = self.rxmap['reserved'].sub('\\1_', line)
						tableLines.append(line)
		
		return tableName, ' '.join(tableLines), indexes
	
	##
	## Internal use only
	##
	def replaceIndexKeys(self, keys):
		cols = self.rxmap['keys'].findall(keys)
		return ','.join(cols)
	
	def replacePrimaryKey(self, match):
		return 'primary key (%s)' % self.replaceIndexKeys(match.group(1))
	
	def replaceKey(self, tableName, match):
		if match.group(1) is None:
			line = 'create index '
		else:
			line = 'create unique index '
		line += '%s_%s_index on %s (%s)' % (tableName, match.group(2), tableName, self.replaceIndexKeys(match.group(3)))
		
		return line
	
	def replaceEnum(self, line):
		m = self.rxmap['enum'].search(line)
		if m is None:
			return line
		
		enumDef = m.group(1)
		maxLen = max(len(k) for k in self.rxmap['enum_keys'].findall(enumDef))
		
		return '%s char(%d) not null,' % (line[:m.start()], maxLen)

if __name__ == '__main__':
	import sys
	
	tdc = TableDefinitionConverter()
	tableName, tableDef, indexes = tdc.parse(sys.stdin, 'DATABASE')

	print('=== %s ===' % tableName)
	print(tableDef.replace(', ', ',\n'))
	print()
	print('=== INDEXES ===')
	for index in indexes:
		print(index)
