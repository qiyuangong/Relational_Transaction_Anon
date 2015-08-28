"""
run RT_ANON with given parameters
"""

# !/usr/bin/env python
# coding=utf-8

from utils.read_data import read_data, read_tree
from RT_ANON import rt_anon
from utils.evaluation import average_relative_error
# from utils.save_result import save_to_file
import sys
import socket
import pdb
import cProfile


_DEBUG = False

if __name__ == '__main__':
    # read gentree tax
    ATT_TREES = read_tree()
    # read record
    DATA = read_data()
    # pdb.set_trace()
    # clusters = CLUSTER(att_tree, DATA[:200], 25)
    # clusters = RMERGE_R(clusters)
    # for i, t in enumerate(clusters):
    #     print "cluster %d" % i
    #     print t.middle
    # print "Finish RT-Anon based on RMERGE_R\n"
    # DATA = DATA[:2000]
    result = cProfile.run('rt_anon(ATT_TREES, DATA)')
    # pdb.set_trace()
    if _DEBUG:
        print result
    # save_to_file(result)
    # print "Begin Evaluation"
    # are = average_relative_error(ATT_TREES, DATA, result)
    # print "Average Realtive Error: %.2f" % are
    # print "Finish RT-Anon based on RMERGE_T\n"
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
