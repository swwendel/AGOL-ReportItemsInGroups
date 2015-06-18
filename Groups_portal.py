# -*- coding: utf-8 -*-
"""
Title: ReportFeatureServices.py
Description: Creates a log the Members found in AGOL for an organization and
provides information about each member's items. In this version, the csv contains
username, item id, created date, modified date, title, and groups.
Version: 1.4
Author: Stephanie Wendel
Created: 12/27/2013
Updated: 6/18/2015
Tags: Log, AGOL, Admin Tasks, Membership information, Organization Information.
"""

# Modules needed
import urllib, urllib2, httplib
import json
import socket
import os, sys, time
from time import localtime, strftime


"""
Variable Setup: These are the Admin variables used in this script. Changes
should be made to username and password that reflect an ADMIN user found within
the organization.
"""
# Admin Variables to be changed.
username = ""
password = ""
# portalName - include Web Adaptor name if it has one or use arcgis.com for AGOL
# organizational account.
portalName = 'http://www.arcgis.com'

# Host name will be generated based on the computer name. No Changes need to be
# made.
hostname = "Http://" + socket.getfqdn()


"""
Setup of Monkey Patch, Token, Logs, and Service Requests.
"""
# Monkey Patch httplib read
def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except httplib.IncompleteRead, e:
            return e.partial

    return inner

httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)


# Generate Token
if "arcgis.com" in portalName:
    token_URL = 'https://www.arcgis.com/sharing/generateToken'
else:
    token_URL = "{0}/sharing/generateToken".format(portalName)
token_params = {'username':username,'password': password,'referer': hostname,'f':'json'}
token_request = urllib2.Request(token_URL, urllib.urlencode(token_params))
token_response = urllib2.urlopen(token_request)
token_string = token_response.read()
token_obj = json.loads(token_string)
token = token_obj['token']


# log functions: createLog - builds basic log structure, Log - adds value to log
def createLog(OrgName, name, headers=None, fType=".txt"):
    location = sys.path[0]
    timesetup = strftime("%m_%d_%Y", localtime())
    logfile = OrgName +"_" + name + "_"+ timesetup + fType
    f = open(logfile, 'wb')
    if headers != None:
        f.write(headers)
        f.write("\n")
    f.close()
    return logfile

def Log(logfile, message):
    f = open(logfile, 'ab')
    f.write(message)
    f.write("\n")
    f.close()


# Define basic http request
def makeRequest(URL, PARAMS={'f': 'json','token': token}):
    request = urllib2.Request(URL, urllib.urlencode(PARAMS))
    response = urllib2.urlopen(request).read()
    JSON = json.loads(response)
    return JSON


"""
Portal Information: Builds log about organization properties. Finds Organization
ID for further use in script. Also builds basic building block of finding users
in the organziation. Included in this log is the total number of users.
"""
# Find Organization ID
#print 'Starting orgnaization log'
url = '{0}/sharing/rest/portals/self'.format(portalName)
JVal = makeRequest(url)
OrgID = JVal['id']
OrgName = JVal['name'].replace(' ', '_')


# Find Organization users
def orgUsers(start=1):
    global OrgID, token
    url = '{0}/sharing/rest/portals/{1}/users'.format(portalName, OrgID)
    params = {'start':start, 'num': 100, 'f': 'json','token': token}
    userrequest = makeRequest(url, params)
    return userrequest

totalusers = orgUsers()['total']
print("Total users: {}\r".format(totalusers))

"""
Process item information per user. Contains information about groups item is
shared with. CSV format
"""
print 'Starting Membership log processing'
MemberslogFile = createLog(OrgName, 'Membership', 'Username, itemid, CreatedDate, ModifiedDate, Title, OtherGroup', '.csv')

# Process the first 100 users
users1 = orgUsers()['users']
for user in users1:
    username = user['username']
    print("Processing {}".format(username))
    URL_items = "{0}/sharing/rest/content/users/{1}".format(portalName, username)
    items = makeRequest(URL_items)['items']
    for item in items:
        itemid = item['id']
        itemtitle = item['title']
        itemcreateddate = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(item['created']/1000))
        itemmodifieddate = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(item['modified']/1000))
        groupsobject = makeRequest("{0}/sharing/rest/content/items/{1}/groups".format(portalName, itemid))
        #print groupsobject
        otherlist = []
        for othervalue in groupsobject["other"]:
            otherlist.append(othervalue['title'])
        Log(MemberslogFile, "{0}, {1}, {2}, {3}, {4}, {5}".format(username, itemid, itemcreateddate, itemmodifieddate, itemtitle.encode('ascii','replace'), str(otherlist).replace(",",";")))

# Process the rest of the users over 100
newStart = 0
while totalusers > 100:
    newStart += 100
    users2 = orgUsers(newStart)['users']
    for user2 in users2:
        username2 = user2['username']
        print("Processing {}".format(username2))
        URL_items2 = "{0}/sharing/rest/content/users/{1}".format(portalName, username2)
        items2 = makeRequest(URL_items2)['items']
        for item2 in items2:
            itemid2 = item2['id']
            itemtitle2 = item2['title']
            itemcreateddate2 = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(item2['created']/1000))
            itemmodifieddate2 = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(item2['modified']/1000))
            groupsobject2 = makeRequest("{0}/sharing/rest/content/items/{1}/groups".format(portalName, itemid2))
            otherlist2 =[]
            for othervalue2 in groupsobject2["other"]:
                otherlist2.append(othervalue2['title'])
            Log(MemberslogFile, "{0}, {1}, {2}, {3}, {4}, {5}".format(username2, itemid2, itemcreateddate2, itemmodifieddate2, itemtitle2, str(otherlist2).replace(",",";").encode('utf8', 'replace')))

    totalusers -= 100


print("\nReporting is Done")