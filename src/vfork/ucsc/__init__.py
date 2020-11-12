__all__ = ['IndexPage', 'OrganismPage']

from BeautifulSoup import BeautifulSoup, Null
from urllib2 import urlopen
from urlparse import urljoin
import re
import sha

class HtmlCleaner(object):
	TAGRX = re.compile(r'<[^>]+>')
	SPECIALCHARSRX = re.compile(r'&\S+;')
	
	@classmethod
	def clean(klass, content):
		content = klass.TAGRX.sub('', content)
		content = klass.SPECIALCHARSRX.sub('', content)
		return content.strip()

class IndexPage(object):
	URL = 'http://hgdownload.cse.ucsc.edu/downloads.html'
	
	def __init__(self):
		self.links = []
		self.contentHash = None
	
	def fetch(self):
		fd = urlopen(self.URL)
		content = fd.read()
		fd.close()
		
		sh = sha.new()
		sh.update(content)
		self.contentHash = sh.hexdigest()
		
		soup = BeautifulSoup()
		soup.feed(content)
		
		def nameFilter(x):
			return x is not None and len(x) > 0
		
		for anchor in soup.fetch('a', {'name': nameFilter}):
			table = anchor.findNext('table')
			for ul in table.fetch('ul'):
				dataSets = self.findDataSets(ul)
				if len(dataSets) == 0:
					continue
				
				version = self.findVersion(ul)
				if version is None:
					continue
				
				humanReadableName = self.findHumanReadableName(ul)
				if humanReadableName is None:
					continue
				
				self.links.append((anchor.get('name'), humanReadableName, version, dataSets))
	
	def findDataSets(self, ul):
		sets = {}
		for link in ul.fetch('a'):
			label = link.renderContents()
			for l in ('Annotation database', 'Data set by chromosome', 'Full data set'):
				if l in label:
					sets[l] = urljoin(self.URL, link.get('href').strip())
		return sets
	
	def findVersion(self, ul):
		tag = ul.firstPreviousSibling()
		if tag is Null:
			return None
		else:
			return HtmlCleaner.clean(tag.renderContents())
	
	def findHumanReadableName(self, ul):
		tag = ul.parent
		if tag.name == 'p':
			tag = tag.parent
		
		tag = tag.parent
		tag = tag.parent
		tag = tag.firstPreviousSibling()
		tag = tag.first('b')
		
		if tag is Null:
			return None
		else:
			return HtmlCleaner.clean(tag.renderContents())

class OrganismPage(object):
	def __init__(self, url):
		self.url = url
		self.links = []
	
	def fetch(self):
		fd = urlopen(self.url)
		soup = BeautifulSoup()
		soup.feed(fd.read())
		fd.close()
		
		for link in soup.fetch('a', {'href' : re.compile(r'chr[0-9]+\.fa\.gz') }):
			self.links.append(urljoin(self.url, link.get('href')))

if __name__ == '__main__':
	page = IndexPage()
	page.fetch()
	print page.links
