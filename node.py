from xmlrpclib import ServerProxy, Fault
import xmlrpclib
from os.path import join, abspath, isfile,exists
from SimpleXMLRPCServer import SimpleXMLRPCServer
from urlparse import urlparse
from os import listdir,walk
import sys
import traceback
SimpleXMLRPCServer.allow_reuse_address = 1
MAX_HISTORY_LENGTH = 6
UNHANDLED= 100
ACCESS_DENIED = 200
class UnhandledQuery(Fault):
# exception for unhandled query.
	def __init__(self, message="Couldn't handle the query"):
		Fault.__init__(self, UNHANDLED, message)

class AccessDenied(Fault):
#exception for denied access
	def __init__(self, message="Access denied"):
		Fault.__init__(self, ACCESS_DENIED, message)

def inside(dir, name):
#check if file is in directory
	dir = abspath(dir)
	name = abspath(name)
	return name.startswith(join(dir, ''))

def getPort(url):
#extract Port No. from url
	name = urlparse(url)[1]
	parts = name.split(':')
	return int(parts[-1])

class Node:
#A node in a peer-to-peer network.
	def __init__(self, url, dirname, secret):
		self.url = url
		self.dirname = dirname
		self.secret = secret
		self.known = set()

	def query(self, query, history=[]):
	#search for file
		try:
			return self._handle(query)
		except UnhandledQuery:
			history = history + [self.url]
			if len(history) >= MAX_HISTORY_LENGTH: raise
			return self._broadcast(query, history)

	def hello(self, peer):
	# Used to introduce the Node to other Nodes.
		self.known.add(peer)
		return 0

	def fetch(self, query, secret):
	#find a file and download itself.	
		if secret != self.secret: raise AccessDenied
		result = self.query(query)
		f = open(join(self.dirname, query), 'wb')
		f.write(result.data)
		f.close()
		return 0
	
	def _start(self):
	# start the XML-RPC server.
		s = SimpleXMLRPCServer(("", getPort(self.url)), logRequests=False)
		s.register_instance(self)	
		s.serve_forever()
	
	def _handle(self, query):
	#used internally to handle query 
		name = join(self.dirname, query)
		if exists(name): print "EXISTS",self.url
		else:
			raise UnhandledQuery
		if not inside(self.dirname, name): raise AccessDenied
		with open(name,"rb") as handle:
			data=xmlrpclib.Binary(handle.read())
		handle.close()
		return data

	def _broadcast(self, query, history):
	#broadcast query to known peers
		for peer in self.known.copy():
			if peer in history: continue
			try:
				s = ServerProxy(peer)
				return s.query(query, history)  	#yeild
			except Fault, f:
				if f.faultCode == UNHANDLED: 
					pass
				else: self.known.remove(peer)
			except Exception,e:
				self.known.remove(peer)
		raise UnhandledQuery


	def fetchFind(self, query):
	#find a file and download itself.
		l=list()
		for peer in self.known.copy():
			try:
				name = join(self.dirname, query)
				s = ServerProxy(peer)
				if exists(name): l.append(peer)
			except:
				self.known.remove(peer)
				print traceback.print_exc()
		return l
	# def searchServer(self):
	# 	l=list()
	# 	for peer in self.known.copy():
	# 		try:
	# 			s = ServerProxy(peer)
	# 			l.append(listdir(s.dirname))
	# 		except:
	# 			self.known.remove(peer)
	# 			print traceback.print_exc()
	# 	return l

	# def getList(self):
	# 	lis=[]
	# 	for peer in self.known.copy():
	# 		try:
	# 			s = ServerProxy(peer)
	# 			print "s"
	# 			d=s.getFiles()
	# 			print "d"
	# 			for i in d:
	# 				lis.append(i)
	# 			print "list"
	# 		except Exception,e:
	# 			print "listexceptin",traceback.print_exc()
	# 			self.known.remove(peer)
	# 	return lis


	# def getFiles(self):
	# 	print "1"
	# 	l=[]

	# 	print listdir(self.dirname)
	# 	try:
	# 		for i in listdir(self.dirname):
	# 			l.append(i)
	# 	except Exception,e:
	# 			print "insidelistexceptin",traceback.print_exc()
	# 	return l
	def list(self):
	#list all the entries in the peer's directory
		return listdir(self.dirname)
# def main():

# 	url, directory, secret = sys.argv[1:]
# 	n = Node(url, directory, secret)
# 	n._start()
# if __name__ == '__main__': main()