__author__ = 'dbergert'

import os
import time
import argparse
import requests
import xml.etree.ElementTree as etree

parser = argparse.ArgumentParser(description='Submit Veracode Scan')
parser.add_argument("username", help="Veracode API Username")
parser.add_argument("password", help="Veracode API Password")
parser.add_argument("app_id", help="Veracode Application Id")
parser.add_argument("project_jar", help="Main Project Jar")
parser.add_argument("project_version", help="Project Version")
parser.add_argument("project_build_path", help="Project Build Path")
parser.add_argument("sleep_time", help="Sleep Time to wait for Prescan in Seconds")
parser.add_argument("--skip_upload_dependencies", help="skip uploading dependenices in lib dir from build path" ,action="store_true")

args = parser.parse_args()

username = args.username
password = args.password
app_id = args.app_id
project_jar=args.project_jar
project_version=args.project_version
project_build_path=args.project_build_path
sleep_time = int(args.sleep_time)

module_id = None

def main():

	print "Starting to Upload Build for Veracode Scan..."

	print "Creating Application Build Profile..."
	createBuild()

	print "Uploading Main Application File... : " + project_jar + " - " + project_version

	uploadFiles(project_build_path + project_jar)

	if not args.skip_upload_dependencies:
		print "Uploading Dependencies..."
		dirList=os.listdir(project_build_path + "/lib/")
		for fname in dirList:
			print "  Uploading : " + fname
			uploadFiles(project_build_path + "/lib/" + fname)
	else:
		print "Skipping Uploading Dependencies..."
	
	print "Running PreScan..."
	runPreScan()
	
	print "Waiting for PreScan to Complete..."
	time.sleep(sleep_time)

	print "Checking Results of PreScan..."
	xmlPreScan = getPreScanResults()
	namespace = "{https://analysiscenter.veracode.com/schema/2.0/prescanresults}"
	root = etree.fromstring(xmlPreScan)
	for module in root.findall(".//{0}module[@name='{1}']".format(namespace, project_jar)):
		print module.attrib
		module_id = module.get('id')

	print "Submitting Static Scan Request to Veracode..."
	#Kick off Full Scan
	beginScan(module_id)

def listApps():
	# curl --compressed -u username:password https://analysiscenter.veracode.com/api/4.0/getapplist.do
	r = requests.get("https://analysiscenter.veracode.com/api/4.0/getapplist.do", auth=(username, password))
	print r.text

def createBuild():
	#curl --compressed -u [api user]:[api user password] https://analysiscenter.veracode.com/api/4.0/createbuild.do -F "app_id=111111" -F "version=v1"
	payload = {'app_id': app_id, 'version' : project_version}
	r = requests.post("https://analysiscenter.veracode.com/api/4.0/createbuild.do", params=payload, auth=(username, password))
	#print r.text

def uploadFiles(uploadFileName):
	#curl --compressed -u username:password https://analysiscenter.veracode.com/api/4.0/uploadfile.do -F "app_id=111111" -F "file=your.jar"
	files = {'file' : open(uploadFileName, 'rb')}
	payload = {'app_id': app_id}
	r = requests.post("https://analysiscenter.veracode.com/api/4.0/uploadfile.do", params=payload, files=files, auth=(username, password))
	#print r.text

def runPreScan():
	#curl --compressed -u username:password https://analysiscenter.veracode.com/api/4.0/beginprescan.do -F "app_id=111111"
	payload = {'app_id': app_id}
	r = requests.post("https://analysiscenter.veracode.com/api/4.0/beginprescan.do", params=payload, auth=(username, password))
	#print r.text

def getPreScanResults():
	#curl --compressed -u username:password  https://analysiscenter.veracode.com/api/4.0/getprescanresults.do -F "app_id=111111"
	payload = {'app_id': app_id}
	r = requests.post("https://analysiscenter.veracode.com/api/4.0/getprescanresults.do", params=payload, auth=(username, password))
	#print r.text
	return r.text

def beginScan(module_id):
	#curl --compressed -u username:password https://analysiscenter.veracode.com/api/4.0/beginscan.do -F "app_id="111111" -F "scan_all_top_level_modules="true""
	payload = {'app_id': app_id, 'modules' : module_id}
	r = requests.post("https://analysiscenter.veracode.com/api/4.0/beginscan.do", params=payload, auth=(username, password))
	#print r.text

if __name__ == "__main__":
	main()



