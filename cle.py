#!/usr/bin/python
'''
Cle v0.1 - Copyright 2017 James Slaughter,
This file is part of Cle v0.1.

Cle v0.1 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Cle v0.1 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Cle v0.1.  If not, see <http://www.gnu.org/licenses/>.
'''

#python import
import sys
import os
import requests
import smtplib
import datetime
import time
import urllib2

from email.mime.text import MIMEText
from BeautifulSoup import BeautifulSoup

#programmer generated imports
from controller import controller
from fileio import fileio

'''
ConfRead()
Function: - Reads in the cle.conf config file and assigns some of the important
            variables
'''
def ConfRead():
        
    ret = 0
    intLen = 0
    FConf = fileio()
    try:
        #Conf file hardcoded here
    	FConf.ReadFile('/opt/cle/cle.conf')
    except:
        print '[x] Unable to read configuration file!  Terminating...'
        return -1
    
    for line in FConf.fileobject:
        intLen = len(line)            
        if (CON.debug == True):
            print '[DEBUG]: ' + line
        if (line.find('keywords') != -1):                
            CON.keywords = line[9:intLen]            
        elif (line.find('recipients') != -1):                
            CON.recipients = line[11:intLen]
        elif (line.find('email') != -1):
            CON.email = line[6:intLen]
        elif (line.find('password') != -1):
            CON.password = line[9:intLen]
        elif (line.find('subject') != -1):
            CON.email_subject = line[8:intLen]
        elif (line.find('searxurl') != -1):
            CON.searxurl = line[9:intLen]         
        elif (line.find('maxsleeptime') != -1):
            CON.maxsleeptime = line[13:intLen]
        else:
            if (CON.debug == True): 
                print ''

    if (len(CON.email) < 3):
        print '[x] Please enter a valid sender e-mail address in the cle.conf file.  Terminating...'            
        print ''
        return -1    

    if (len(CON.password) < 3):
        print '[x] Please enter a valid sender e-mail password in the cle.conf file.  Terminating...'            
        print ''
        return -1

    if (len(CON.keywords) < 3):
        print '[x] Please enter a valid keywords file in the cle.conf file.  Terminating...'            
        print ''
        return -1

    if (len(CON.recipients) < 3):
        print '[x] Please enter a valid recipients file in the cle.conf file.  Terminating...'            
        print ''
        return -1

    if (len(CON.email_subject) < 3):
        print '[-] No custom e-mail subject entered.  Using: "Keyword Alert"'
        CON.email_subject == 'Keyword Alert'            
        print ''

    try:
        # Read in our list of keywords
        with open(CON.keywords.strip(),"r") as fd:
            file_contents = fd.read()
            CON.keyword_list      = file_contents.splitlines()

        if not os.path.exists("keywords"):
            os.mkdir("keywords")

    except:
        print '[x] Unable to read keywords file: ' + CON.keywords
        return -1

    try:

        # Read in our list of recipients
        with open(CON.recipients.strip(),"r") as fd:
            file_contents2 = fd.read()
            CON.recipient_list    = file_contents2.splitlines()

    except:
        print '[x] Unable to read recipients file: ' + CON.recipients
        return -1
         
    print '[*] Finished configuration successfully.\n'
            
    return 0

'''
Parse() - Parses program arguments
'''
def Parse(args):        
    option = ''
                    
    print '[*] Arguments: \n'
    for i in range(len(args)):
        if args[i].startswith('--'):
            option = args[i][2:]                         

            if option == 'debug':
                CON.debug = True
                print option + ': ' + str(CON.debug)

'''
send_alert()
Function: - Sends the alert e-mail from the address specified
            in the configuration file to potentially several addresses
            specified in the "recipients.txt" file.
'''
def send_alert(alert_email):
    
    email_body = "The following keyword hits were just found:\r\n\r\n"
    
    # Walk through the searx results
    if alert_email.has_key("searx"):
        
        for keyword in alert_email['searx']:
            
            email_body += "\r\nKeyword: %s\r\n\r\n" % keyword
            
            for keyword_hit in alert_email['searx'][keyword]:
                try:
                    title = BeautifulSoup(urllib2.urlopen(keyword_hit))
                    print 'Title: ' + title.title.string.encode('utf-8').strip()  + '\r'          
                    email_body += 'Title: ' + title.title.string.encode('utf-8').strip() + '\r'
                except:
                    print '[x] Unable to read title from: ' + keyword_hit.encode('utf-8').strip()
                    email_body += 'Title: Not Available...\r'

                email_body += "%s\r\n" % keyword_hit.encode('utf-8').strip() 

    for recipient_entry in CON.recipient_list:

        print "[-] Sending e-mail to: " + recipient_entry                          
           
        # Build the email message
        msg = MIMEText(email_body)
        msg['Subject'] = CON.email_subject.strip()
        msg['From']    = CON.email.strip()
        msg['To']      = recipient_entry
    
        server = smtplib.SMTP("smtp.gmail.com",587)
    
        server.ehlo()
        server.starttls()
        server.login(CON.email.strip(),CON.password.strip())
        server.sendmail(recipient_entry,recipient_entry,msg.as_string())
        server.quit()
    
        print "[*] Alert email sent!"
    
    return

'''
check_urls()
Function: - Checks previously polled URLs to see if it's new
'''
def check_urls(keyword,urls):
    
    new_urls = []
    
    if os.path.exists("keywords/%s.txt" % keyword):
        
        with open("keywords/%s.txt" % keyword,"r") as fd:
            
            stored_urls = fd.read().splitlines()
        
        for url in urls:
            
            if url not in stored_urls:
                
                print '[*] New URL for ' + keyword + ' discovered: ' + url
                
                new_urls.append(url)
                
    else:
        
        new_urls = urls
        
    # Now store the new urls back in the file
    with open("keywords/%s.txt" % keyword,"ab") as fd:
        
        for url in new_urls:
            fd.write("%s\r\n" % url)
            
    
    return new_urls

'''
check_searx()
Function: - Builds a query based on the keywords that are read in 
            from the "keywords.txt" file and then submited it to the Searx service.
'''
def check_searx(keyword):
    
    hits = []
    
    # Build parameter dictionary
    params               = {}
    params['q']          = keyword
    params['categories'] = 'general'
    params['time_range'] = 'day' #day,week,month or year will work
    params['format']     = 'json'
    
    print "[*] Querying Searx for: %s" % keyword
    
    # Send the request off to searx
    try:
        response = requests.get(CON.searxurl.strip(),params=params)
        
        results  = response.json()
        
    except: 
        return hits
    
    # If we have results we want to check them against our stored URLs
    if len(results['results']):
        
        urls = []
        
        for result in results['results']:
            
            if result['url'] not in urls:
            
                urls.append(result['url'])
            
        hits = check_urls(keyword,urls)
    
    return hits


'''
check_keywords()
Function: - Loops through the list of read-in keywords and submits
            to the check_searx() function.  Measures the time of the 
            query and executes a sleep for the specified amount of 
            time after each loop.
'''
def check_keywords():
    
    alert_email          = {}
    
    time_start = time.time()
    
    # Use the list of keywords and check each against searx
    for keyword in CON.keyword_list:
        
        # Query searx for the keyword
        result = check_searx(keyword)
        
        if len(result):
            
            if not alert_email.has_key("searx"):
                alert_email['searx'] = {}            
            
            alert_email['searx'][keyword] = result

    if (CON.still_initial_loop == False):       
        time_end   = time.time()
        total_time = time_end - time_start
            
        # If we complete the above inside of the max_sleep_time setting
        # we sleep. 
        if total_time < CON.maxsleeptime:        
            sleep_time = int(CON.maxsleeptime) - total_time                
            Sleep(sleep_time)
    
    return alert_email

'''
Sleep()
Function: - Sleeps the program for a time specifed in the cle.conf file
'''     
def Sleep(sleep_time):
    
    last_loop_time = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    print '\n[*] Last loop time: ' + last_loop_time
    print '[*] Sleeping for: ' + str(sleep_time) + ' seconds...\n'
    time.sleep(sleep_time)

'''
Terminate()
Function: - Attempts to exit the program cleanly when called  
'''     
def Terminate(exitcode):
    sys.exit(exitcode)

'''
This is the mainline section of the program and makes calls to the 
various other sections of the code
'''
if __name__ == '__main__':

    ret = 0 
    count = 0  

    CON = controller() 

    ret = Parse(sys.argv)
    if (ret == -1):
        #Usage()
        Terminate(ret) 

    ret = ConfRead()
    # Something bad happened...bail
    if (ret != 0):
        Terminate(ret)    

    # Execute your search once first to populate results
    print '[-] Inititating startup loop to populate inital results...\n'
    while (count < 2):
        alert_email = check_keywords()
        count += 1
        Sleep(200)

    CON.still_initial_loop = False

    # Now perform the main loop
    print '[-] Inititating main loop to start sending results e-mails...\n'
    while True:  
            
        if len(alert_email.keys()):        
            # If we have alerts send them out
            print '[-] There are alerts to send...'
            send_alert(alert_email)

        alert_email = check_keywords()

'''
END OF LINE
'''

