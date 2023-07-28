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

class sonofindAPILoginExpired(Exception):
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
		
		if (self.sid == ''):
			self.login()
		else:
			self.opener = urllib.request.build_opener()
			self.opener.addheaders.append(('SFAPIV2-SID', self.sid))
			self.opener.addheaders.append(('Cookie', 'PHPSESSID='+self.sid+';'))

	def login(self):
		self.opener = urllib.request.build_opener()
		## fetch session token
		response = self.opener.open(self.url+'opensession')
		html = response.read()
		myroot = ET.fromstring(html)
		self.sid=myroot.findall('sid')[0].text
		print("NEWSID: {}".format(self.sid))
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
		if myroot.findall('ax_success')[0].text != "1":
		  raise sonofindAPIError("Unable to login: {}".format(html),500)
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

	def fetchFromAPI(self, url):
		response = self.opener.open(url)
		xml = response.read()
		#print("Response: {}".format(xml))
		try:
			myroot = self.parseResponse(xml)
		except sonofindAPILoginExpired:
			self.sid = ''
			self.login()
			myroot = self.fetchFromAPI(url)

		return myroot

	def parseResponse(self, html):
		myroot = ET.fromstring(html)
		if myroot.findall('ax_success')[0].text != "1":
			errmsg = myroot.find('ax_errmsg').text
			errcode = int(myroot.find('ax_errcode').text)
			if errcode == 620:
				raise sonofindAPILoginExpired("Unable to login: {}".format(errmsg), errcode)
			else:
				raise sonofindAPIError("Unable to login: {}".format(errmsg), errcode)

		return myroot

	def createDestPath(self, destfile):
		outdir=os.path.dirname(destfile)
		if(not os.path.isdir(outdir)):
			## create directory
			os.makedirs(outdir)

	def copyFile(self, ffilename, destfile):
		self.createDestPath(destfile)
		shutil.copy2(ffilename,destfile)

	def getLabels(self):
		myroot = self.fetchFromAPI(self.url+'labels')
		labellist = []
		for labels in myroot.findall('labelinfo'):
			label = labels.find('label').text
			labellist.append(label)
		return labellist

	def getCDs(self, label):
		myroot = self.fetchFromAPI(self.url+'cds/'+label)
		cdlist = []
		for cds in myroot.findall('cd'):
			cd = cds.find('cdcode').text
			cdlist.append(cd)
		return cdlist

	def getTrackDownloadUrl(self, cdtrackcode, downloadformat="mp3"):
		try:
			self.NC.checkAlbumTrackCode(cdtrackcode)
		except sfnc.sfNCError as e:
			msg = "{0}:{1}".format(trackcode.strip(),str(e))
			raise sonofindAPIError(msg,501)
		else:
			myroot = self.fetchFromAPI(self.url+'mmd/'+cdtrackcode)
			trlist = []
			for tracks in myroot.findall('track'):
				trackcode = tracks.find('trackcode').text
				cdcode =  tracks.find('cdcode').text
				label = tracks.find('label').text
				if downloadformat == "wav":
					audiofile = tracks.findall('./files/file[@type="wav"]')[0].text
				else:
					audiofile = tracks.findall('./files/file[@type="mp3"][@quality="320"]')[0].text
				trlist.append(dict(trackcode=trackcode, url=audiofile, cdcode=cdcode, label=label))
		return trlist

	def getNewTracks(self, label="", limit=1000):
		url = self.url + 'newtracks'
		if (label != ''):
			url = "{}/{}/&limit={}".format(url,label,limit)
		else:
			url = "{}/&limit={}".format(url,limit)
		myroot = self.fetchFromAPI(url)
		trlist = []
		ax_msg=myroot.findall('ax_msg')[0].text
		trackcodes=myroot.findall('trackcodes')[0]
		#print(ax_msg)
		for tracks in trackcodes.findall('data'):
			trackcode = tracks.text
			trlist.append(trackcode)
		return trlist

	def ack(self, cdtrackcode):
		try:
			self.NC.checkAlbumTrackCode(cdtrackcode)
		except sfnc.sfNCError as e:
			msg = "{0}:{1}".format(cdtrackcode.strip(),str(e))
			raise sonofindAPIError(msg,501)
		else:
			myroot = self.fetchFromAPI(self.url+'ack/'+cdtrackcode)

	def downloadFile(self, url, destfile, bOverwrite = True):
		if (not os.path.isfile(destfile)) or bOverwrite is True:
			outdir=os.path.dirname(destfile)
			if(not os.path.isdir(outdir)):
				## create directory
				os.makedirs(outdir)
			## create download
			try:
				myroot = self.fetchFromAPI(url)
			except sonofindAPIError:
				raise sonofindAPIError("Unable to fetch file", 400)
			## use <url>
			dlurl = myroot.findall('url')[0].text
			#print("DLURL: {}".format(dlurl))
			dlmp3 = self.opener.open(dlurl)
			with open(destfile, 'wb') as filee:
				filee.write(dlmp3.read())
		else:
			print("File exists {}".format(destfile))

	def msg(self, msg, verbmode=0):
		if(self.verbmode >= verbmode):
			print(msg)
