
import re

class sfNCError(Exception):
	pass

## SONOfind Naming Convention checkExtension

class sonofindNC:

	def __init__(self):
		self.filename=''
		self.fullname=''

	def checkFullPath(self, cfullname):
		self.fullname = cfullname.strip().replace('\\','/')
		filearr=(self.fullname.split("/"))
		if (len(filearr) == 1):
			self.checkFilename(self.filename, 1)
			return

		self.filename = filearr[-1]
		pathname = filearr[-2]
		labelname = filearr[-3]
		# Labelname with max 3 characters must be first part of pathname and self.filename 
		label = labelname[0:4]
		if (len(labelname) > 5):
			raise sfNCError("Label too long (max 5 characters)")
		if (pathname.find(label,0,4) < 0):
			## Try label without "-"
			label=labelname.replace('-','')[0:4]
			if (pathname.find(label,0,4) < 0):
				## Try label portion (e.g. SCDC ---> SCDD SCDB, PMLCD --> PMLB)
				label=labelname.replace('-','')[0:3]
				if (pathname.find(label,0,4) < 0):
					raise sfNCError("Label not contained in Albumcode")
		if (self.filename.find(label,0,4) < 0):
			raise sfNCError("Label not contained in Filename")
		# Pathname must be first part of filename
		if (self.filename.find(pathname,0,9) < 0):
			raise sfNCError("Pathname not contained in Filename")
		self.checkFilename(self.filename, 1)
		
	def checkFilename(self, fname, checkExtension = 0):
		self.filename = fname
		matchObj = re.match( r'([A-Z\-]+){1,4}([0-9]{4})([0-9]{2,3})((\.\w+){1,2}){0,1}$', self.filename, re.M)
		if not(matchObj):
			raise sfNCError("Filename not matching SONOTON NamingConvention")
		else:
			fext=matchObj.group(4)
			if(checkExtension or fext):
				self.checkExtension(fext)

	def checkFilenameAlbum(self, fname, checkExtension = 0):
		self.filename = fname.upper()
		matchObj = re.match( r'([A-Z\-]+){1,4}([0-9]{4})((\.\w+){1,2}){0,1}$', self.filename, re.M)
		if not(matchObj):
			raise sfNCError("Albumname not matching SONOTON NamingConvention")
		else:
			fext=matchObj.group(3).lower()
			if(checkExtension or fext):
				self.checkExtension(fext)

	def checkAlbumTrackCode(self, fname):
		## we need a extension
		fname = fname + '.mp3'
		try:
			self.checkFilenameAlbum(fname, 0)
			return 1
		except sfNCError as e:
			self.checkFilename(fname, 0)
			return 1
		return 0

	def checkExtension(self, fext):
		if (not(fext=='.wav' or fext=='.mp3' or fext=='.aif' or fext=='.aiff' or fext=='.wav.zip' or fext=='.jpg' or fext=='.png' or fext=='.wfm' )):
			raise sfNCError("Invalid file extension not .wav/.mp3/.aiff/.aif/.wav.zip/.jpg/.png/.wfm")
