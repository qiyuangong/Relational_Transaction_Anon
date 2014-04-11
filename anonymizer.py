#!/usr/bin/env python
#coding=utf-8

from read_data import readdata, readtree
from RT_ANON import CLUSTER, RMERGE_R, RMERGE_T
import sys
from ftp_upload import ftpupload
import socket


if __name__ == '__main__':
    #read gentree tax
    readtree()
    #read record
    readdata()
    # pdb.set_trace()
    clusters = CLUSTER(gl_databack[:200],25)
    clusters = RMERGE_R(clusters)
    for i, t in enumerate(clusters):
        print "cluster %d" % i 
        print t.middle
    print "Finish RT-Anon based on RMERGE_R\n"
    
    clusters = CLUSTER(gl_databack[:200],25)
    clusters = RMERGE_T(clusters)
    trans = []
    for c in clusters:
        for t in c.member:
            trans.append(t[-1])
    trans = get_KM(trans)
    print trans

    print "Finish RT-Anon based on RMERGE_T\n"
    print "Finish RT-Anonymization!!"
    
    '''
    hostname = socket.gethostname()
    filetail = datetime.now().strftime('%Y-%m-%d-%H') + '.txt'
    filepath = 'output/'
    rediroutname = hostname + '-output' + filetail
    redirout = open(filepath + rediroutname, 'w')
    sys.stdout = redirout
    
    print "Anonymizing Data..."
    print "Size of dataset %d" % len(databack) 
    for i in range(2, 51):
        data = databack[:]
        
        print "are = %f" % are

    plotfilename = hostname + '-plot' + filetail
    plotfile = open(filepath + plotfilename,'w')
    
    for line in plotdata:
        ltemp = [str(s) for s in line]
        temp = ','.join(ltemp) + '\n'
        plotfile.write(temp)
    print 'OK...'
    redirout.close()
    plotfile.close()    
    # upload result file to ftp server
    ftpupload(plotfilename, filepath)
    ftpupload(rediroutname, filepath)
    '''
