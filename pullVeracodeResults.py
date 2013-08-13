__author__ = 'dbergert'

import argparse
import requests
import xml.etree.ElementTree as etree

parser = argparse.ArgumentParser(description='Retrieve Veracode Scan Results')
parser.add_argument("username", help="Veracode API Username")
parser.add_argument("password", help="Veracode API Password")
parser.add_argument("app_id", help="Veracode Application Id")
parser.add_argument("projectName", help="Project Name")
parser.add_argument("youtrack_username", help="YouTrack Username")
parser.add_argument("youtrack_password", help="YouTrack Password")
parser.add_argument("youtrack_project", help="YouTrack Project Id")

args = parser.parse_args()

username = args.username
password = args.password
app_id = args.app_id
projectName = args.projectName
youtrack_username = args.youtrack_username
youtrack_password = args.youtrack_password
youtrack_project =  args.youtrack_project

build_id = None
version = None

youtrack_url = "https://yourdomain.com/youtrack"

def main():

    print "Getting Last Build ID of Application: "
    xmlBuildList = getBuildList()
    namespace = "{https://analysiscenter.veracode.com/schema/2.0/buildlist}"
    root = etree.fromstring(xmlBuildList)
    for build in root.findall(".//{0}build".format(namespace)):
        build_id = build.get('build_id')
        version = build.get('version')
    print build_id, version

    print "Getting PDF Summary Report"
    pdfSummaryReport = getPDFSummaryReport(build_id)

    print "Getting PDF Detailed Report"
    pdfDetailedReport = getPDFDetailedReport(build_id)

    #Create YouTrack Ticket and Attach Results:

    print "Logging ino to Youtrack API"
    youTrackLogin()

    print "Getting XML Summary Report"
    xmlSummaryReport = getXMLSummaryReport(build_id)

    print "Create YouTrack Ticket"
    location = youTrackCreateTicket(youtrack_project,'Veracode Scan Results for ' + projectName + '-' + version  ,'Please See Attached Results:\n\n' + processXMLSummary(xmlSummaryReport))

    print "Attaching PDF Reports"
    youTrackAttachFile(location, 'VeraCode Summary Report ' + projectName + '-' + version + '.pdf' , pdfSummaryReport)
    youTrackAttachFile(location, 'VeraCode Detailed Report ' + projectName + '-' + version + '.pdf', pdfDetailedReport)

    print "Change other YouTrack Ticket Attributes"

    youTrackRunCommand(location,'task')

    youTrackComment(location,'Please Review Results of the Veracode Scan')



## Veracode Results Processing

def processXMLSummary(xml):
    namespace = "{https://www.veracode.com/schema/reports/export/1.0}"
    root = etree.fromstring(xml)
    str_list = []
    #Write Rating and Score:
    for sa in root.findall(".//{0}static-analysis".format(namespace)):
        str_list.append('Veracode Results: Rating : ' + sa.get('rating') + ', Score : ' + sa.get('score') + '\n')

    #Build Table of Issues
    str_list.append('||Severity||Category||Count||\n')
    for category in root.findall(".//{0}category".format(namespace)):
        str_list.append('|' + category.get('severity')  + '|' + category.get('categoryname')  + '|'  + category.get('count')  + '|\n'  )
    return ''.join(str_list)


## Veracode Api Helper Methods

def getPDFSummaryReport(build_id):
    #curl --compressed --sslv3 -k -v -u username:password https://analysiscenter.veracode.com/api/2.0/summaryreportpdf.do?build_id=111111 -o summaryreport.pdf
    payload = {'build_id': build_id}
    r = requests.get("https://analysiscenter.veracode.com/api/2.0/summaryreportpdf.do", params=payload, auth=(username, password))
    return r.content

def getPDFDetailedReport(build_id):
    #curl --compressed --sslv3 -k -v -u username:password https://analysiscenter.veracode.com/api/2.0/detailedreportpdf.do?build_id=111111 -o detailedreport.pdf
    payload = {'build_id': build_id}
    r = requests.get("https://analysiscenter.veracode.com/api/2.0/detailedreportpdf.do", params=payload, auth=(username, password))
    return r.content

def getXMLSummaryReport(build_id):
    #curl --compressed --sslv3 -k -v -u username:password https://analysiscenter.veracode.com/api/2.0/summaryreport.do?build_id=111111 -o summaryreport.xml
    payload = {'build_id': build_id}
    r = requests.get("https://analysiscenter.veracode.com/api/2.0/summaryreport.do", params=payload, auth=(username, password))
    return r.content

def getXMLDetailedReport(build_id):
    #curl --compressed --sslv3 -k -v -u username:password https://analysiscenter.veracode.com/api/2.0/detailedreport.do?build_id=111111 -o detailedreport.xml
    payload = {'build_id': build_id}
    r = requests.get("https://analysiscenter.veracode.com/api/2.0/detailedreport.do", params=payload, auth=(username, password))
    return r.content

def getBuildList():
    #curl --compressed -u username:password  https://analysiscenter.veracode.com/api/4.0/getbuildlist.do -F "app_id=111111"
    payload = {'app_id': app_id}
    r = requests.post("https://analysiscenter.veracode.com/api/4.0/getbuildlist.do", params=payload, auth=(username, password))
    #print r.text
    return r.text

## Youtrack API Helper Methods

def youTrackLogin():
    #POST /rest/user/login?{login}&{password}
    payload = {'login': youtrack_username, 'password' :youtrack_password}
    r = requests.post(youtrack_url, params=payload, auth=(youtrack_username, youtrack_password))
    print r.text

def youTrackCreateTicket(yt_project, yt_summary, yt_description):
    #PUT /rest/issue?{project}&{summary}&{description}&{attachments}&{permittedGroup}
    payload = {'project': yt_project,'summary': yt_summary, 'description':yt_description}
    r = requests.put(youtrack_url, params=payload, auth=(youtrack_username, youtrack_password))
    return  str(r.headers['location'])

def youTrackAttachFile(location, filename, file):
    #POST /rest/issue/{issue}/attachment?{group}&{name}&{authorLogin}&{created}&{files}
    files = {filename : file }
    r = requests.post(location + '/attachment', files=files, auth=(youtrack_username, youtrack_password))

def youTrackComment(location, comment_text):
    #POST /rest/issue/{issue}/execute?{command}&{comment}&{group}&{disableNotifications}&{runAs}
    payload = {'comment': comment_text}
    r = requests.post(location + '/execute', params=payload, auth=(youtrack_username, youtrack_password))

def youTrackRunCommand(location, command_text):
    #POST /rest/issue/{issue}/execute?{command}&{comment}&{group}&{disableNotifications}&{runAs}
    payload = {'command': command_text}
    r = requests.post(location + '/execute', params=payload, auth=(youtrack_username, youtrack_password))

if __name__ == "__main__":
    main()