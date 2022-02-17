import os
import json
import urllib
import urllib.request
import hashlib
import shutil
import sys
import sonofindNC as sfnc
import xml.etree.ElementTree as ET

class sonofindAPIError(Exception):
	def __init__(self, message, code):
		self.message = message
		self.code = code
	pass

class sonofindPrivateAPI():

	def __init__(self, url, cuser, cpass, tokenfile, verbmode=0):
		self.url=url
		self.cuser=cuser
		self.cpass=cpass
		self.tokenfile=tokenfile
		self.sid=self.readToken()
		self.verbmode=verbmode
		self.NC = sfnc.sonofindNC()
		
		self.opener = urllib.request.build_opener()
		if (self.sid == ''):
			self.login()
		else:
			self.opener.addheaders.append(('SFAPIV2-SID', self.sid))
			self.opener.addheaders.append(('Cookie', 'PHPSESSID='+self.sid+';'))

	def login(self):
		## fetch session token
		response = self.opener.open(self.url+'opensession')
		html = response.read()
		myroot = ET.fromstring(html)
		self.sid=myroot.findall('sid')[0].text
		## authenticate
		m=hashlib.md5()
		m.update(('%s~%s' % (self.cpass, self.sid)).encode('utf-8'))
		lpass=m.hexdigest()
		url0=self.url+'auth/'+self.cuser+'/'+lpass
		self.opener.addheaders.append(('SFAPIV2-SID', self.sid))
		self.opener.addheaders.append(('Cookie', 'PHPSESSID='+self.sid+';'))
		response = self.opener.open(url0)
		html = response.read()
		myroot = ET.fromstring(html)
		if (myroot.findall('ax_success')[0].text != "1"):
		  raise sonofindAPIError("Unable to login:"+html,500)
		self.writeToken(self.sid)

	def readToken(self):
		if (not os.path.isfile(self.tokenfile)):
			return ''
		with open(self.tokenfile) as f:
			sid = f.read().rstrip()
		return sid

	def writeToken(self, sid):
		with open(self.tokenfile,'w') as f:
			f.write(sid)

	def createDestPath(self, destfile):
		outdir=os.path.dirname(destfile)
		if(not os.path.isdir(outdir)):
			## create directory
			os.makedirs(outdir)

	def copyFile(self, ffilename, destfile):
		self.createDestPath(destfile)
		shutil.copy2(ffilename,destfile)

	def getLabels(self):
		response = self.opener.open(self.url+'labels')
		html = response.read()
		myroot = ET.fromstring(html)
		labellist = []
		for labels in myroot.findall('labelinfo'):
			label = labels.find('label').text
			labellist.append(label)
		return labellist

	def getCDs(self, label):
		response = self.opener.open(self.url+'cds/'+label)
		html = response.read()
		myroot = ET.fromstring(html)
		cdlist = []
		for cds in myroot.findall('cd'):
			cd = cds.find('cdcode').text
			cdlist.append(cd)
		return cdlist

	def getTracks(self, cdtrackcode):
		try:
			self.NC.checkAlbumTrackCode(cdtrackcode)
		except sfnc.sfNCError as e:
			msg = "{0}:{1}".format(trackcode.strip(),str(e))
			raise sonofindAPIError(msg,501)
		else:
			response = self.opener.open(self.url+'mmd/'+cdtrackcode)
			html = response.read()
			myroot = ET.fromstring(html)
			trlist = []
			for tracks in myroot.findall('track'):
				print(tracks)
				track = tracks.find('trackcode').text
				audiofile = tracks.findall('./files/file[@type="mp3"][@quality="320"]')[0].text
				trlist.append([track, audiofile])
		return trlist

	def getNewTracks(self, label = ""):
		url = self.url + 'newtracks'
		if (label != ''):
			url = url + "/" + label
		response = self.opener.open(url)
		html = response.read()
		myroot = ET.fromstring(html)
		trlist = []
		for tracks in myroot.findall('data'):
			trackcode = tracks.text
			trlist.append(trackcode)
		return trlist

	def ack(self, cdtrackcode):
		try:
			self.NC.checkAlbumTrackCode(cdtrackcode)
		except sfnc.sfNCError as e:
			msg = "{0}:{1}".format(trackcode.strip(),str(e))
			raise sonofindAPIError(msg,501)
		else:
			response = self.opener.open(self.url+'ack/'+cdtrackcode)
			html = response.read()
			myroot = ET.fromstring(html)
			if (myroot.findall('ax_success')[0].text != "1"):
				raise sonofindAPIError("Unable to login:"+html,500)

	def downloadFile(self, url, destfile):
		if (not os.path.isfile(destfile)):
			outdir=os.path.dirname(destfile)
			if(not os.path.isdir(outdir)):
				## create directory
				os.makedirs(outdir)
			## create download
			response = self.opener.open(url)
			html = response.read()
			myroot = ET.fromstring(html)
			if (myroot.findall('ax_success')[0].text != "1"):
				raise sonofindAPIError("Unable to fetch file",400)
			## use <url>
			dlurl = myroot.findall('url')[0].text
			#print("DLURL: {}".format(dlurl))
			dlmp3 = self.opener.open(dlurl)
			with open(destfile, 'wb') as filee:
				filee.write(dlmp3.read())
		else:
			print("File exists {}".format(destfile))

	def msg(self, msg, verbmode):
		if(self.verbmode >= verbmode):
			print(msg)
