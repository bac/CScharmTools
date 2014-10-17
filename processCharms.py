#!/usr/bin/python

import os
import sys
from fnmatch import fnmatch
from subprocess import call
import requests
import json
import random
import bisect
import threading

def getAllCharmRepositories():
	repos = {
		"mediawiki": "lp:~charmers/charms/precise/mediawiki/trunk",
		"haproxy": "lp:~charmers/charms/precise/haproxy/trunk",
		"mysql": "lp:~charmers/charms/precise/mysql/trunk",
		"apache2": "lp:~charmers/charms/precise/apache2/trunk",
		"cassandra": "lp:~charmers/charms/precise/cassandra/trunk",
		"elasticsearch": "lp:~charmers/charms/precise/elasticsearch/trunk",
		"drupal6": "lp:~lynxman/charms/precise/drupal6/trunk",
		"jujugui": "lp:~juju-gui-charmers/charms/precise/juju-gui/trunk",
		"memcached": "lp:~charmers/charms/precise/memcached/trunk",
		"rabbitmqserver": "lp:~charmers/charms/precise/rabbitmq-server/trunk",
		"solr": "lp:~charmers/charms/precise/solr/trunk",
		"tomcat7": "lp:~charmers/charms/precise/tomcat7/trunk",
		"websphere-libery": "lp:~ibm-demo/charms/trusty/websphere-liberty/trunk",
		"wordpress": "lp:~charmers/charms/precise/wordpress/trunk",
		"zookeeper": "lp:~charmers/charms/precise/zookeeper/trunk"
	}
	return repos

def getCharmProbabilities():
	probs = {
		"mediawiki.zip": 10,
		"haproxy.zip": 10,
		"mysql.zip": 10,
		"apache2.zip": 10,
		"cassandra.zip": 10,
		#"elasticsearch.zip": 3,
		"drupal6.zip": 10,
		#"jujugui.zip": 3,
		"memcached.zip": 10,
		"rabbitmqserver.zip": 10,
		"solr.zip": 10,
		"tomcat7.zip": 10,
		#"websphere-libery.zip": 1,
		#"wordpress.zip": 10,
		"zookeeper.zip": 10
	}
	return probs

def getAllBundleRepositories():
	bundles = {
		"mediawikibundle": "lp:~charmers/charms/bundles/mediawiki-scalable/bundle"
	}
	return bundles

def processCharmRepository(name, repository):
	cmd = "./getCharmAndZip.sh " + name + " " + repository
	print cmd
	ret_code = call(cmd, shell=True)	
	return ret_code

def processBundleRepository(name, repository):
        cmd = "./getBundleAndZip.sh " + name + " " + repository
        print cmd
        ret_code = call(cmd, shell=True)
        return ret_code

def printHelp():
	print "missing parameters"
	print "usage: " + sys.argv[0] + " ACTION + CS_URL"
	print "- ACTION: download, upload, checkSize"
	print "- CS_URL is the URL:PORT of the charmstore"

def getAllCharmZips():
	zips = []
	for root, dirs, files in os.walk("./charmZips"):
		for file in files:
			if file.endswith(".zip"):
				fileName = os.path.join(root, file)
				zips.append(fileName)
	return zips

def prepareNameForZip(zipName):
	params = []
	name = zipName.replace("./charmZips/", "")
	name = name.replace(".zip", "")
	params.append("precise/"+name)

	charmZip = zipName.replace("./", "")
	params.append(charmZip)

	return params

def uploadCharm(zipName, CS_URL):
	params = prepareNameForZip(zipName)
	print params
	cmd = "./upload-charm.sh "+CS_URL+" "+params[0]+" "+params[1]
	print cmd
	ret_code = call(cmd, shell=True)
	return ret_code


def uploadAllCharms(zips, CS_URL):
	for zipName in zips:
		#print "uploading"+zipName
		uploadCharm(zipName, CS_URL)

def getCharmArchiveSize(charmName, CS_URL):
	r = requests.get("http://"+CS_URL+"/v4/~csqaprocess"+charmName+"/meta/archive-size")
	if(r.status_code == 200):
		json_data = json.loads(r.content)
		size = json_data[u'Size']
		return size
	return -1

def getFileSize(zipName):
	return os.path.getsize(zipName)

def compareZipAndUploadedCharmSize(zips, CS_URL):
	for zipFile in zips:
		params = prepareNameForZip(zipFile)
		print "processing " + params[0]
		sizeOnDisk = getFileSize(zipFile)
		sizeInCharmstore = getCharmArchiveSize(params[0], CS_URL)
		if sizeOnDisk == sizeInCharmstore:
			print params[0] + " is properly uploaded"
		else:
			print params[0] + " size on disk is " + sizeOnDisk + " in store is " + sizeInCharmstore

def prepareProbabilityDistribution(probs):
	sum = 0
	itemPoints = []
	itemNames = []
	items = probs.keys()
	for i in items:
		sum += probs[i]
		itemPoints.append(sum)
		itemNames.append(i)
	return itemPoints, itemNames

def getRandomItem(breakpoints, items):
    score = random.random() * breakpoints[-1]
    i = bisect.bisect(breakpoints, score)
    return items[i]

class UploadThread(threading.Thread):
	def __init__(self, zipName, CS_URL):
		super(UploadThread, self).__init__()
		self.zipName = zipName
		self.csUrl = CS_URL

	def run(self):
		print "starting upload task for ", self.zipName
		uploadCharm(self.zipName, self.csUrl)
		print "done uploading task for ", self.zipName

def uploadMonkeyTasks(zips, CS_URL):
	print "starting upload monkeys"
	probs = getCharmProbabilities()
	#print probs
	probsDistribution, items = prepareProbabilityDistribution(probs)
	#print probsDistribution
	#print items

	for _ in range(1):
		selected = []
		threads = []
		for _ in range(200):
			# select a charm
			print "select random"
			randZip = getRandomItem(probsDistribution, items)
			selected.append(randZip)
			print "selected: ", randZip
			#print "complete set: ", selected

			thread = UploadThread(randZip, CS_URL)
			threads.append(thread)

		for thread in threads:
			thread.start()

		for thread in threads:
			thread.join()

def main():
	if len(sys.argv) < 2:
		printHelp()
		sys.exit()

	ACTION = sys.argv[1]

	if ACTION == "download":
		repos =  getAllCharmRepositories()
		for name, repo in repos.items():
			print "processing " + name + " in " + repo
			processCharmRepository(name, repo)
		bundles = getAllBundleRepositories()
                for name, repo in bundles.items():
                        print "processing " + name + " in " + repo
                        processBundleRepository(name, repo)
	else:
		if len(sys.argv) < 3:
			printHelp()
			sys.exit()

		CS_URL = sys.argv[2] 

		zips = getAllCharmZips()

		if ACTION == "upload":
			uploadAllCharms(zips, CS_URL)
		elif ACTION == "checkSize":
			compareZipAndUploadedCharmSize(zips, CS_URL)
		elif ACTION == "uploadmonkey":
			uploadMonkeyTasks(zips, CS_URL)
		else:
			print "unknown command"
			printHelp()

if __name__ == '__main__': 
	main()
