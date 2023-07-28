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
sTokenfile='./sonofind.token'
sOpts0="Fetch latest MP3 files from a SONOfind server\n(c) Sonoton Music - Michael Ettl\n"
sOpts=sOpts0+sys.argv[0]+" <options>\n\nOptions:\n-h\thelp\n-v\tbe verbose\n-l filename (--logfile)\tname of logfile"
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

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

print ("{}\n{}\nAgent: {}\nLogfile: {}\n{}\n".format("-"*50,sOpts0,data["sonofind"]["user"],sLogfile,"-"*50))
localmp3download = data["localstorage"]["mp3download"]
downloadlimit = data["sonofind"]["tracklimit"]

sonofind = SF.sonofindPrivateAPI(data["sonofind"]["host"],data["sonofind"]["user"],data["sonofind"]["passwd"],sTokenfile,verbmode)
sonofind.createDestPath(sLogfile)

labels = sonofind.getLabels()
sonofind.msg("Your labels: {}\n".format(labels),0)

trlist = sonofind.getNewTracks('',downloadlimit)
sonofind.msg("There are {} tracks for download".format(len(trlist)))

with open(sLogfile, 'w') as logfile:
    for trackcode in trlist:
        trdownloadlist = sonofind.getTrackDownloadUrl(trackcode)
        for trdownload in trdownloadlist:
            sonofind.msg("Download: {}".format(trdownload),1)
            infile = os.path.join(localmp3download, trdownload.get("label"),
                                  trdownload.get("cdcode"),
                                  trdownload.get("trackcode")+".mp3")
            sonofind.msg("Fetching {} to {}".format(trackcode, infile),0)
            sonofind.msg(trdownload.get("url"),1)
            try:
                sonofind.downloadFile(trdownload.get("url"), infile)
                sonofind.ack(trackcode)
                sonofind.msg("Ack receipt of {}".format(trackcode), 0)
            except SF.sonofindAPIError as e:
                logfile.write("err:{0}:{1}\n".format(infile, str(e)))
                print("Unable to fetch Track " + trackcode)

