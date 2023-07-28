#!/usr/bin/python
import os
import json
import urllib
import urllib.request
import hashlib
import sys, getopt

import sonofindPrivateAPI as SF

verbmode=0
sLogfile='log/missing_mp3.txt'
sOpts="Fetch MP3 files from a SONOfind server using a copylist\n\n"
sOpts=sOpts+sys.argv[0]+" <options>\n\nOptions:\n-h\thelp\n-v\tbe verbose\n-l filename (--logfile)\tname of logfile"
try:
  opts, args = getopt.getopt(sys.argv[1:],"vhl:",["logfile="])
except getopt.GetoptError:
  print(sOpts)
  sys.exit(2)
for opt, arg in opts:
  if opt == '-h':
    print(sOpts)
    sys.exit()
  elif opt in ("-v"):
    verbmode = 1
  elif opt in ("-l", "--logfile"):
    sLogfile = arg

with open('config.private.json') as json_data_file:
    data = json.load(json_data_file)

sonofind = SF.sonofindPrivateAPI(data["sonofind"]["host"],data["sonofind"]["user"],data["sonofind"]["passwd"],data["localstorage"]["tokenfile"],verbmode)

## DEMO for fetching labels
if (False):
	labels = sonofind.getLabels()
	print("Labels: {}\n".format(labels))

## DEMO for fetching albums
if (False):
	label = 'STT'
	cds = sonofind.getCDs(label)
	print("CDs of {}:\n{}\n".format(label,cds))

## DEMO for fetching album data and downloading tracks
if (False):
	localdownload=data["localstorage"]["mp3storage"]

	cdtrack = 'SCD0720'
	tracks = sonofind.getTrackDownloadUrl(cdtrack)
	print("Tracks of {}:\n{}\n".format(cdtrack,tracks))

	for track in tracks:
		dlurl = track.get("url")
		trackcode = track.get("trackcode")
		dlfile = localdownload+trackcode+".mp3"
		print("Download {} from {}".format(dlfile,dlurl))
		sonofind.downloadFile(dlurl,dlfile)
		## acknowledge receipt
		print("Ack delivery: "+trackcode)
		sonofind.ack(trackcode)

## DEMO for fetching all new tracks (which are not yet acknowledged
if (True):
	label = 'STT'
	tracks = sonofind.getNewTracks(label)
	print("Pending tracks for label {}:\n{}\n".format(label,tracks))
