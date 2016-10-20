#!/usr/bin/env python

# 2016-10-17
# A tool designed to pull down the entire podesta email corpus from wikileaks in its current state
# "veritatis in virtute"
#
# /user/hisnamewassethrich
# /u/znfinger
#

import socket
import os
import urllib2
import re
import hashlib
import time

socket.setdefaulttimeout(2)

pubDate = re.compile("emailid\/(?P<id>[0-9]+)\">(?P<date>[0-9]{4}\-[0-9]{2}\-[0-9]{2})<")
subject = re.compile("Subject.+emailid\/(?P<id>[0-9]+)\">(?P<subject>[^\<]+)<")
sendDate = re.compile("emailid\/(?P<id>[0-9]+)\">(?P<date>[0-9]{4}\-[0-9]{2}\-[0-9]{2} [012][0-9]\:[0-5][0-9])")

filedata = re.compile("fileid\/(?P<id>[0-9]+)\/(?P<filenum>[0-9]+)\">(?P<filename>[^<]+)")
sums = re.compile("(?P<md5>[0-9,A-F,a-f]{32})")

fout = open('masterTable_{}.tsv'.format(time.asctime().replace(' ','_').replace(':','')),'w')
UserAgent = None

            
class email:
        def __init__(self, emailid):
                self.emailID = emailid
                self.subject = None
                self.sendDate = None
                self.pubDate = None
                self.podesta = None # leak number
                self.att_id = None # attachment ID
                self.att_name = None
                self.att_data = None #attachment as binary
                self.att_md5 = None
                self.text = None
        def getAttachmentData(self):
                if self.att_id != None and self.emailID != None:
                        success = False
                        self.att_url = 'https://www.wikileaks.org/podesta-emails//fileid/{}/{}'.format(self.emailID,self.att_id)
                        try:
                                self.att_data = urllib2.urlopen(self.att_url).read()
                                success = True
                        except:
                                print "Attachment {} interrupted. Retrying.".format(self.att_name)
                        digest =  hashlib.md5()
                        digest.update(self.att_data)
                        self.att_md5 = digest.hexdigest()
        def __str__(self):
                #print  self.podesta , self.emailID , self.sendDate , self.pubDate , self.subject
                return '\t'.join(map(str,[self.podesta , self.emailID , self.sendDate , self.pubDate , self.subject]))

emails = {}

start = 1
end = 1000
page = start

#dates = set()
while True:
        print "grabbing page {}.".format(page)
        #opens the source page for email listings and downloads to grab the email#, publication date, send date, subject
        url = "https://wikileaks.org/podesta-emails/?q=&mfrom=&mto=&title=&notitle=&date_from=&date_to=&nofrom=&noto=&count=200&sort=6&page={}&#searchresult".format(page)
        #        print url
        success = False
        while success == False:
                try:
                        print url
                        a = urllib2.urlopen(url,UserAgent).read()
                        success = True
                except:
                        print "trying to grab directory {} again.".format(page)

        if "Query failed. Please check your syntax." in a or page > end:
                #raise urllib2.URLError('boop! No more emails!')
                break
        a = a.split('\n')
        for line in a:
                pub = re.search(pubDate,line)
                sub = re.search(subject,line)
                sent = re.search(sendDate,line)
                if pub:
                        #publication date
                        if pub.group('id') not in emails:
                                emails[pub.group('id')] = email(pub.group('id'))
                        emails[pub.group('id')].pubDate = pub.group('date')
                        #dates.add(pub.group('date'))
                        #print line
                        continue
                if sub:
                        #subject
                        if sub.group('id') not in emails:
                                emails[sub.group('id')] = email(sub.group('id'))
                        emails[sub.group('id')].subject = sub.group('subject')
                        #  print line
                        continue
                if sent:
                        #send date
                        if sent.group('id') not in emails:
                                emails[sent.group('id')] = email(sent.group('id'))
                        emails[sent.group('id')].sendDate = sent.group('date')
                        #print line
                        #                                print sent.group('id'), sent.group('date'),emails[sent.group('id')].sendDate
                        continue
        page += 1

#rev_dates = {'podesta8': '2016-10-16', 'podesta9': '2016-10-17', 'podesta4': '2016-10-12', 'podesta5': '2016-10-13', 'podesta6': '2016-10-14', 'podesta7': '2016-10-15', 'podesta1': '2016-10-07', 'podesta2': '2016-10-10', 'podesta3': '2016-10-11', 'podesta10': '2016-10-18', 'podesta11': '2016-10-19'}

podesta = {'2016-10-20': 'podesta12','2016-10-19': 'podesta11', '2016-10-18': 'podesta10', '2016-10-14': 'podesta6', '2016-10-15': 'podesta7', '2016-10-07': 'podesta1', '2016-10-17': 'podesta9', '2016-10-16': 'podesta8', '2016-10-11': 'podesta3', '2016-10-10': 'podesta2', '2016-10-13': 'podesta5', '2016-10-12': 'podesta4'}

#pull only from these dates
grabdate=set(["2016-10-20",'2016-10-19']) 
#grabdate = set(podesta.keys())

print "ordinalizing..."

print "writing directory to file."
for emailid, entry in emails.items():
        emails[emailid].podesta = podesta[entry.pubDate]
        fout.write(str(entry)+"\n")

print "making folders for individual leaks."
#create folders for each leak
for x in podesta.values():
        if not os.path.exists(x):
            os.mkdir(x)

#grab text for all emails
print "grabbing email bodies and writing to .EML files"
for emailid in emails.keys():
        url = 'https://wikileaks.org/podesta-emails//get/{}'.format(emailid)
        if os.path.exists('{}/{}.EML'.format(emails[emailid].podesta,emails[emailid].emailID)):
#                print "skipping {}. Already exists.".format(emails[emailid].emailID)
                continue
        if emails[emailid].pubDate not in grabdate:
#                print "skipping {}. Not in specified data range".format(emails[emailid].att_name)
                continue
        success = False
        while success == False:
                try:
                        emails[emailid].text = urllib2.urlopen(url,UserAgent).read().split('\n')
                        success = True
                        print "Email {} pulled down successfully.".format(emailid)
                except:
                        print "trying again to pull down email {}.".format(emailid)
        fOut = open('{}/{}.EML'.format(emails[emailid].podesta,emails[emailid].emailID),'w')
        for line in emails[emailid].text:
                fOut.write(line+'\n')
        fOut.close()
        
#scrape for names of attachments
page = 1
md5s = set()
print "grabbing attachments."
attachments = {}
att_fout = open('masterTable_attachments_{}.tsv'.format(time.asctime().replace(' ','_').replace(':','')),'w')
#pull all attachment name/url info from the WL directory
while True:
        success = False
        while success == False:
                try:
                        url = 'https://wikileaks.org/podesta-emails/?file=&count=200&page={}&#searchresult'.format(page)
                        a = urllib2.urlopen(url,UserAgent).read().split('\n')
                        success = True
                except:
                        print "trying to pull down attachments directory again."
        if "Query failed. Please check your syntax." in a:
                break
        for line in a:
                data = re.search(filedata,line)
                if data:
                        #gather attachment entries into attachments
                        success = False
                        while success == False:
                                try: 
                                        emails[data.group('id')].att_id = data.group('filenum')
                                        emails[data.group('id')].att_name = data.group('filename')
                                        emails[data.group('id')].getAttachmentData()
                                        print "{}: Download was successful.". format(data.group('filename'))
                                        success = True
                                except:
                                        print "{}: Download failed. Trying again.". format(data.group('filename'))
                                        
                        print "writing {}".format(emails[data.group('id')].emailID,emails[data.group('id')].att_name)
                        if len('{}/{}'.format(emails[data.group('id')].podesta,emails[data.group('id')].att_name)) > 150:
                                name = '{}/{}'.format(emails[data.group('id')].podesta,emails[data.group('id')].att_name)[:150]
                        else:
                                name = '{}/{}'.format(emails[data.group('id')].podesta,emails[data.group('id')].att_name)
                        fOut = open(name,'wb')
                        try:
                                fOut.write(emails[data.group('id')].att_data)
                        except:
                                pass
        page += 1
        
