from xmlrpclib import ServerProxy, Fault
from node import Node, UNHANDLED
from threading import Thread
from time import sleep

from random import choice
from string import lowercase
import sys
import wx
HEAD_START = 0.1 # Seconds
SECRET_LENGTH = 100

def randomString(length):
#generate a random string
	chars = []
	letters = lowercase[:26]
	while length > 0:
		length -= 1
		chars.append(choice(letters))
	return ''.join(chars)

class Client(wx.App):
	"""
	The main client class, which takes care of setting up the GUI and
	starts a Node for serving files.
	"""
	def __init__(self, url, dirname, urlfile):
		"""
		Creates a random secret, instantiates a Node with that secret,
		starts a Thread with the Node's _start method (making sure the
		Thread is a daemon so it will quit when the application quits),
		reads all the URLs from the URL file and introduces the Node to
		them. Finally, sets up the GUI.
		"""
		self.secret = randomString(SECRET_LENGTH)
		self.url=url
		n = Node(url, dirname, self.secret)
		t = Thread(target=n._start)
		t.setDaemon(1)
		t.start()
		sleep(HEAD_START)# Give the server a head start:
		self.server = ServerProxy(url)
		for line in open(urlfile):
			line = line.strip()
			self.server.hello(line)
		super(Client, self).__init__() #start GUI

	def updateList(self):
	#Updates the list box with the names of the files available from the server Node.
		self.files.Set(["\t\t\t\t\tAvailable Files in Directory"]+self.server.list())
	def getList(self):
		self.files.Set(["\t\t\t\t\tAvailable Files On Server"]+self.server.getList())
	def search(self,filename):
		l=["\t\t\t\t\tAvailable Peers for "+filename+"\n"]
		# print type(l)
		l1=(self.server.fetchFind(filename))
		self.files.Set(l+l1)
	def searchS(self):
		self.files.Set(self.server.searchServer())
	def OnInit(self):
		"""
		Sets up the GUI. Creates a window, a text field, a button, and
		a list box, and lays them out. Binds the submit button to
		self.fetchHandler.
		"""
		win = wx.Frame(None, title="File Sharing Client"+self.url, size=(400, 300))
		bkg = wx.Panel(win)
		self.input = input = wx.TextCtrl(bkg);
		submit = wx.Button(bkg, label="Download", size=(80, 25))
		search = wx.Button(bkg, label="Search", size=(80, 25))
		submit.Bind(wx.EVT_BUTTON, self.fetchHandler)
		search.Bind(wx.EVT_BUTTON, self.searchHandler)
		# searchS = wx.Button(bkg, label="Files", size=(80, 25))
		# searchS.Bind(wx.EVT_BUTTON, self.searchServer)
		hbox = wx.BoxSizer()
		hbox.Add(input, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
		hbox.Add(submit, flag=wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)
		hbox.Add(search, flag=wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)
		# hbox.Add(searchS, flag=wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)
		self.files = files = wx.ListBox(bkg)
		# self.filelist=filelist=wx.ListBox(bkg)
		self.updateList()
		vbox = wx.BoxSizer(wx.VERTICAL)
		# self.vbox2 = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(hbox, proportion=0, flag=wx.EXPAND)
		vbox.Add(files, proportion=1,flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
		bkg.SetSizer(vbox)
		win.Show()
		return True

	# def searchServer(self,event):
	# 	try:
	# 		self.searchS()
	# 	except Fault, f:
	# 		if f.faultCode != UNHANDLED: raise
	# 		print "Couldn't find the file", query

	def searchHandler(self,event):
		query = self.input.GetValue()
		try:
			self.search(query)
		except Fault, f:
			if f.faultCode != UNHANDLED: raise
			print "Couldn't find the file", query

	def listHandler(self, event):
		# query=self.input.GetValue()
		try:
			self.getList()
		except Fault, f:
			if f.faultCode != UNHANDLED: raise
			print "Couldn't find the file", query
	def fetchHandler(self, event):
		"""
		Called when the user clicks the 'Fetch' button. Reads the
		query from the text field, and calls the fetch method of the
		server Node. After handling the query, updateList is called.
		If the query is not handled, an error message is printed.
		"""
		query = self.input.GetValue()
		try:
			self.server.fetch(query, self.secret)
			self.updateList()
		except Fault, f:
			if f.faultCode != UNHANDLED: raise
			print "Couldn't find the file", query

def main():
	urlfile, directory, url = sys.argv[1:]
	client = Client(url, directory, urlfile)
	client.MainLoop()
if __name__ == '__main__': main()