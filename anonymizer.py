#!/usr/bin/env python
#coding=utf-8

from generalization import *
from datetime import datetime
import random
import pdb
from threading import Thread
import Queue
import math
import sys
from ftp_upload import ftpupload
import socket
from itertools import combinations

useratt = ['DUID','PID','DUPERSID','DOBMM','DOBYY','SEX','RACEX','RACEAX','RACEBX','RACEWX','RACETHNX','HISPANX','HISPCAT','EDUCYEAR','Year','marry','income','poverty']
conditionatt = ['DUID','DUPERSID','ICD9CODX','year']
att_name = []
att_tree = []
treelist = {}
nodelist = {}
databack = []
plotdata = [[],[],[]]
treesupport = 0
att_cover = [[],[],[],[],[],[],[],[]]


def RMERGE_R():

def RMERGE_T():

def RMERGE_RT():

def CLUSTER():
	
def readtree():
	"read tree data from treefile,store them in treenode and treelist"
	global treesupport
	global nodelist
	global att_cover
	treefile = open('data/treefile_disease.txt','rU')
	nodelist['*'] = GenTree('*')
	print "Reading Tree"
	for line in treefile:
		#delete \n
		if len(line) <= 1:
			break
		line = line.strip()
		temp = line.split(';')
		# copy temp
		treelist[temp[0]] = temp[:]
		temp.reverse()
		for i, t in enumerate(temp):
			if not t in nodelist:
				# always satisfy 
				nodelist[t] = GenTree(t, nodelist[temp[i - 1]])
	treesupport = nodelist['*'].getsupport()
	# att_cover[7] = nodelist['*'].cover
	
	print "Support = %d" % treesupport
	treefile.close()

def readdata():
	"read microda for *.txt and store them in {}[]"
	global databack
	global att_cover
	userfile = open('data/demographics05test.csv','rU')
	conditionfile = open('data/conditions05.csv','rU')
	userdata = {}
	print "Reading Data..."
	for i, line in enumerate(userfile):
		line = line.strip()
		# ignore first line of csv
		if i == 0:
			continue
		row = line.split(',')
		row[2] = row[2][1:-1]
		if row[2] in userdata:
			userdata[row[2]].append(row)
		else:
			userdata[row[2]] = row
	conditiondata = {}
	for i, line in enumerate(conditionfile):
		line = line[:-2]
		# ignore first line of csv
		if i == 0:
			continue
		row = line.split(',')
		row[1] = row[1][1:-1]
		row[2] = row[2][1:-1]
		if row[1] in conditiondata:
			conditiondata[row[1]].append(row)
		else:
			conditiondata[row[1]] = [row]
	attlist = [3,4,5,6,13,15,16]

	hashdata = {}
	for k, v in userdata.iteritems():
		if k in conditiondata:
			temp = []
			for t in conditiondata[k]:
				temp.append(t[2])
				if not t[2] in att_cover[7]:
					att_cover[7].append(t[2])
			hashdata[k] = []
			for i in range(len(attlist)):
				index = attlist[i]
				hashdata[k].append(v[index])
				if not v[index] in att_cover[i]:
					att_cover[i].append(v[index])
			hashdata[k].append(temp)
	for k, v in hashdata.iteritems():
		databack.append(v)
	pdb.set_trace()
	userfile.close()
	conditionfile.close()


if __name__ == '__main__':
	#read gentree tax
	readtree()
	#read record
	readdata()
	pdf.set_trace()
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
	
