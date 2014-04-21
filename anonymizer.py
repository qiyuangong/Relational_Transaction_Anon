#!/usr/bin/env python
#coding=utf-8

from read_data import readdata, readtree
from RT_ANON import CLUSTER, RMERGE_R, RMERGE_T, gen_cluster
from evaluation import average_relative_error
import sys
from ftp_upload import ftpupload
import socket


_DEBUG = False

if __name__ == '__main__':
    #read gentree tax
    att_trees = readtree()
    #read record
    data = readdata()
    # pdb.set_trace()
    # clusters = CLUSTER(att_tree, data[:200], 25)
    # clusters = RMERGE_R(clusters)
    # for i, t in enumerate(clusters):
    #     print "cluster %d" % i 
    #     print t.middle
    # print "Finish RT-Anon based on RMERGE_R\n"
    
    clusters = CLUSTER(att_trees, data[:], 25)
    clusters = RMERGE_T(clusters)
    result = []
    
    for c in clusters:
        temp = gen_cluster(c)
        result.extend(temp)
    if _DEBUG:
        print result
    print "Begin Evaluation"
    are = average_relative_error(att_trees, data, result)
    print "Average Realtive Error: %.2f" %are
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
        
        print "are = %.2f" % are

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
