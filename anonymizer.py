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

__DEBUG = False
gl_useratt = ['DUID','PID','DUPERSID','DOBMM','DOBYY','SEX','RACEX','RACEAX','RACEBX','RACEWX','RACETHNX','HISPANX','HISPCAT','EDUCYEAR','Year','marry','income','poverty']
gl_conditionatt = ['DUID','DUPERSID','ICD9CODX','year']
gl_att_name = []
# att_tree store root node for each att
gl_att_tree = []
# leaf_to_path store leaf node and treepath relations for each att
gl_leaf_to_path = []
#databack store all reacord for dataset
gl_databack = []
#store data for python plot
gl_plotdata = [[],[],[]]
gl_treecover = []
#store coverage of each att according to  dataset
gl_att_cover = [[],[],[],[],[],[],[],[]]

def distance():
	return

def NCP():
	return

def middle():
	return

def RMERGE_R():
	return

def RMERGE_T():
	return

def RMERGE_RT():
	return

def num_analysis(attlist):
	"plot distribution of attlist"
	from pylab import *
	import operator
	temp = {}
	for t in attlist:
		t = int(t)
		if not t in temp.keys():
			temp[t] = 1
		else:
			temp[t] += 1
	# sort the dict
	items = temp.items()
	items.sort()
	value = []
	count = []
	for k, v  in items:
		value.append(k)
		count.append(v)
	pdb.set_trace()
	xlabel('value')
	ylabel('count')
	plt.hist(count, bins=value, normed=1, histtype='step', rwidth=0.8)
	# legend(loc='upper left')
	# grid on
	grid(True)
	show()
	
def find_best_record(data, cluster):

	return

def find_best_cluster(data, cluster):
	return

def CLUSTER(data, k):
	"Group record according to QID distance"
	global gl_att_tree
	global gl_treecover
	global gl_leaf_to_path

	result = []

	return 

def read_tree_file(treename):
	"read tree data from treefile,store them in treenode and treelist"
	global gl_treecover
	global gl_att_tree
	global gl_leaf_to_path

	treecover = 0
	leaf_to_path = {}
	nodelist = {}
	prefix = 'data/treefile_'
	postfix = ".txt"
	treefile = open(prefix + treename + postfix,'rU')
	nodelist['*'] = GenTree('*')
	print "Reading Tree"
	for line in treefile:
		#delete \n
		if len(line) <= 1:
			break
		line = line.strip()
		temp = line.split(';')
		# copy temp
		leaf_to_path[temp[0]] = temp[:]
		temp.reverse()
		for i, t in enumerate(temp):
			if not t in nodelist:
				# always satisfy 
				nodelist[t] = GenTree(t, nodelist[temp[i - 1]])
	treecover = nodelist['*'].getsupport()
	print "Nodes No. = %d" % treecover
	gl_treecover.append(treecover)
	gl_leaf_to_path.append(leaf_to_path)
	gl_att_tree.append(nodelist)

	treefile.close()

def readtree():
	global gl_att_name
	"read tree data from treefiles,store them in treenode and leaf_to_treepath"	
	for t in gl_att_name:
		read_tree_file(t)
	

def readdata():
	"read microda for *.txt and store them in {}[]"
	global gl_databack
	global gl_att_cover
	global gl_att_name
	global gl_useratt
	global gl_conditionatt
	userfile = open('data/demographics05test.csv','rU')
	conditionfile = open('data/conditions05.csv','rU')
	userdata = {}
	# We selet 3,4,5,6,13,15,15 att from demographics05, and 2 from condition05
	attlist = [3,4,5,6,13,15,16]
	for t in attlist:
		gl_att_name.append(gl_useratt[t])
	gl_att_name.append(gl_conditionatt[2])
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
	hashdata = {}
	for k, v in userdata.iteritems():
		if k in conditiondata:
			temp = []
			for t in conditiondata[k]:
				temp.append(t[2])
				if not t[2] in gl_att_cover[7]:
					gl_att_cover[7].append(t[2])
			hashdata[k] = []
			for i in range(len(attlist)):
				index = attlist[i]
				hashdata[k].append(v[index])
				if not v[index] in gl_att_cover[i]:
					gl_att_cover[i].append(v[index])
			hashdata[k].append(temp)
	for k, v in hashdata.iteritems():
		gl_databack.append(v)
	# pdb.set_trace()
	num_analysis([t[6] for t in gl_databack[:]])
	userfile.close()
	conditionfile.close()


if __name__ == '__main__':
	#read gentree tax
	readtree()
	#read record
	readdata()
	pdb.set_trace()
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
	
