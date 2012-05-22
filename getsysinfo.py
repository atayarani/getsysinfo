#!/usr/bin/env python
from datetime import datetime,timedelta
#from dmidecode import system
#from MySQLdb import OperationalError
from re import match,split
from socket import getfqdn,gethostname
from subprocess import *
from sys import exit,stderr
from time import mktime,sleep,strftime,strptime
from urllib2 import urlopen

def defsystem():
    sysinfo={}
    #Serial
    serial_cmd="dmidecode -s system-serial-number"
    serial=Popen(serial_cmd.split(),stdout=PIPE).communicate()[0].strip()
    sysinfo['serial']=serial

    #Product Name
    pn_cmd="dmidecode -s system-product-name"
    pn=Popen(pn_cmd.split(),stdout=PIPE).communicate()[0].strip()
    sysinfo['pn']=pn

    vendor_cmd="dmidecode -s system-manufacturer"
    vendor=Popen(vendor_cmd.split(),stdout=PIPE).communicate()[0].strip()
    sysinfo['vendor']=vendor

    #SKU
    sku_cmd="dmidecode | grep SKU"
    dmidecode=Popen("dmidecode",stdout=PIPE)
    sku=Popen(["grep","SKU"],stdin=dmidecode.stdout,stdout=PIPE).communicate()[0]
    if len(sku) > 1:
	    sku=sku.split(':')[1].rstrip().lstrip() 
    else:
	    sku=""
    sysinfo['sku']=sku 

	#if '0x0100' in system():
		#key='0x0100'
	#else:
		#key='0x0001'
#
	#SKU=system()[key]['data']['SKU Number']
	#serial=system()[key]['data']['Serial Number']
	#product_name=system()[key]['data']['Product Name']
	#vendor=system()[key]['data']['Manufacturer']

    sysinfo={'sku':sku,'serial':serial,'product_name':pn,'vendor':vendor}
    return sysinfo

def getwarranty():
    sysinfo=defsystem()
    host=gethostname()
    vendor=sysinfo['vendor'].lower()
    sku=sysinfo['sku']
    serial=sysinfo['serial']
    type=(sysinfo['product_name'].split('[')[1][0:4] 
        if vendor == 'ibm' else sysinfo['product_name'])
    U={"6950":4,"2950":2,"R815":2}
    size = ""

    sleep(1)
    if "dell" in vendor:
        url=("http://support.dell.com/support/topics/global.aspx/support/"
             "my_systems_info/details?c=us&cs=RC956904&l=en&s=hied&servicetag=%s" % serial)
    elif "ibm" in vendor:
        url=("http://www-947.ibm.com/support/entry/portal/!ut/p/b1/"
             "04_SjzQ0NLUwN7U0szTXj9CPykssy0xPLMnMz0vMAfGjzOKN3Z2Nv"
             "EOcQwJDTb2MDDxD3E3MAv3CjE0cDYEKInErMDAwI06_AQ7gaEBIf3"
             "Bqnn64fhQ-ZWBXgBXgscbPIz83VT83KsfNIjggHQCPRTEq/dl4/d5"
             "/L2dJQSEvUUt3QS80SmtFL1o2XzNHQzJLVENUUVU1SjIwSVRHNDZRTlYzNEEx/?type=%s&serial=%s" % (type,serial))
    elif "hp" in vendor:
        url=("http://h20000.www2.hp.com/bizsupport/TechSupport/"
             "WarrantyResults.jsp?lang=en&cc=us&prodSeriesId=454811&"
             "prodTypeId=12454&sn=%s&pn=%s&country=US&nickname=&"
             "find=Display+Warranty+Information" % (serial,sku))
    else:
        return

    if "dell" in vendor:
        url_cmd="lynx -dump -accept_all_cookies '%s'" % url
        output=Popen(url_cmd,shell=True,stdout=PIPE).communicate()[0]
        lines=split('\n',output)
        warranty_end=[' '.join(line.split()[0:3]) for line in lines if 'days remaining' in line][0]
        warranty_start="N/A"
    else:
        url_cmd="wget -qO- '%s'" % url
        output=Popen(url_cmd,shell=True,stdout=PIPE).communicate()[0]
        lines=split('>|<',output)
        dates=[convertdate(line) for line in lines if convertdate(line)]
    
        try:
            warranty_start=strftime("%Y-%m-%d",min(dates))
            warranty_end=strftime("%Y-%m-%d",max(dates))
        except:
            warranty_start=None
            warranty_end=None
#
        if warranty_start == warranty_end: warranty_start = None

    for k,v in U.items(): 
        if k in type: size = v

    warranty={'warranty_start':warranty_start,'warranty_end':warranty_end,
    'host':"\t%s" % host,'sku':"\t%s" % sku,'type':"\t%s" % type,
    'serial':"\t%s" % serial, 'vendor':"\t%s" % vendor,'U':"\t%s" % size}
    return warranty
#
def convertdate(line):
    '''Based on RegEx match, convert date string to time object for future parsing'''
    if match('[\d]{1,2}/[\d]{1,2}/[\d]{4}',line.strip()): 
        return strptime(line,"%m/%d/%Y")
    elif match('[\d]{4}-[\d]{1,2}-[\d]{1,2}',line):
        return strptime(line,"%Y-%m-%d")
    elif match('[\d]{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [\d]{4}',line):
        return strptime(line,"%d %b %Y")
    else:
        return False #Not a Date

warinfo=getwarranty()
for k,v in warinfo.items():
    print "%s:\t%s" % (k,v)
