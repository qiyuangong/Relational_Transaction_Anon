#!/usr/bin/env python
# coding=utf-8

# Read data and read tree fuctions for INFORMS data
# user att ['DUID','PID','DUPERSID','DOBMM','DOBYY','SEX','RACEX','RACEAX','RACEBX','RACEWX','RACETHNX','HISPANX','HISPCAT','EDUCYEAR','Year','marry','income','poverty']
# condition att ['DUID','DUPERSID','ICD9CODX','year']
from models.gentree import GenTree
import pickle
from models.numrange import NumRange

__DEBUG = False
USER_ATT = ['DUID', 'PID', 'DUPERSID', 'DOBMM', 'DOBYY', 'SEX', 'RACEX', 'RACEAX', 'RACEBX', 'RACEWX', 'RACETHNX', 'HISPANX', 'HISPCAT', 'EDUCYEAR', 'Year', 'marry', 'income', 'poverty']
CONDITION_ATT = ['DUID', 'DUPERSID', 'ICD9CODX', 'year']
# Only 5 relational attributes and 1 transaction attribute are selected (according to Poulis's paper)
QI_INDEX = [3, 4, 6, 13, 16]
# if you want to achieve better utility, you can set some numeric attribute
# to be False. Then the program will treat it as a numeric attributes
# and generate range values without generalization hierarchy
IS_CAT = [True, True, True, True, True, True]


def read_tree(flag=0):
    """read tree from data/tree_*.txt, store them in att_tree
    """
    att_names = []
    att_trees = []
    for t in QI_INDEX:
        att_names.append(USER_ATT[t])
    if flag:
        # ICD9 gh
        att_names.append('ICD9')
    else:
        # even gh
        att_names.append('even')
    for i in range(len(att_names)):
        if IS_CAT[i]:
            att_trees.append(read_tree_file(att_names[i]))
        else:
            att_trees.append(read_pickle_file(att_names[i]))
    return att_trees


def read_pickle_file(att_name):
    """
    read pickle file for numeric attributes
    return numrange object
    """
    with open('data/informs_' + att_name + '_static.pickle', 'rb') as static_file:
        (numeric_dict, sort_value) = pickle.load(static_file)
        result = NumRange(sort_value, numeric_dict)
        return result


def read_tree_file(treename):
    """read tree data from treename
    """
    leaf_to_path = {}
    att_tree = {}
    prefix = 'data/informs_'
    postfix = ".txt"
    treefile = open(prefix + treename + postfix, 'rU')
    att_tree['*'] = GenTree('*')
    if __DEBUG:
        print "Reading Tree" + treename
    for line in treefile:
        # delete \n
        if len(line) <= 1:
            break
        line = line.strip()
        temp = line.split(';')
        # copy temp
        temp.reverse()
        for i, t in enumerate(temp):
            isleaf = False
            if i == len(temp) - 1:
                isleaf = True
            if t not in att_tree:
                # always satisfy
                att_tree[t] = GenTree(t, att_tree[temp[i - 1]], isleaf)
    if __DEBUG:
        print "Nodes No. = %d" % att_tree['*'].support
    treefile.close()
    return att_tree


def read_data(flag=0):
    """read microda for *.txt and return read data
    """
    """read microda for *.txt and return read data"""
    data = []
    userfile = open('data/demographics.csv', 'rU')
    conditionfile = open('data/conditions.csv', 'rU')
    userdata = {}
    # We selet 3,4,5,6,13,15,15 att from demographics05, and 2 from condition05
    print "Reading Data..."
    for i, line in enumerate(userfile):
        line = line.strip()
        # ignore first line of csv
        if i == 0:
            continue
        row = line.split(',')
        row[2] = row[2][1:-1]
        try:
            # append duplicate records
            userdata[row[2]].append(row)
        except:
            userdata[row[2]] = row
    conditiondata = {}
    for i, line in enumerate(conditionfile):
        line = line.strip()
        # ignore first line of csv
        if i == 0:
            continue
        row = line.split(',')
        row[1] = row[1][1:-1]
        row[2] = row[2][1:-1]
        # ignore duplicate values in transaction
        try:
            conditiondata[row[1]].append(row)
        except:
            conditiondata[row[1]] = [row]
    hashdata = {}
    for k, v in userdata.iteritems():
        if k in conditiondata:
            # ingnore duplicate values
            temp = set()
            for t in conditiondata[k]:
                temp.add(t[2])
            hashdata[k] = []
            for i in range(len(QI_INDEX)):
                index = QI_INDEX[i]
                hashdata[k].append(v[index])
            stemp = list(temp)
            # sort values
            stemp.sort()
            hashdata[k].append(stemp[:])
    for k, v in hashdata.iteritems():
        data.append(v)
    userfile.close()
    conditionfile.close()
    return data
