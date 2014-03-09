#!/usr/bin/env python
#coding=utf-8

from generalization import GenTree, Cluster
from datetime import datetime
from random import randrange
import pdb
import math
import sys
from ftp_upload import ftpupload
import socket
# from pylab import *


__DEBUG = False
gl_threshold = 100000
gl_useratt = ['DUID','PID','DUPERSID','DOBMM','DOBYY','SEX','RACEX','RACEAX','RACEBX','RACEWX','RACETHNX','HISPANX','HISPCAT','EDUCYEAR','Year','marry','income','poverty']
gl_conditionatt = ['DUID','DUPERSID','ICD9CODX','year']
gl_att_name = []
gl_att_QI = 7
gl_attlist = [3,4,5,6,13,15,16]
# att_tree store root node for each att
gl_att_tree = []
# leaf_to_path store leaf node and treepath relations for each att
gl_leaf_to_path = []
# databack store all reacord for dataset
gl_databack = []
# store data for python plot
gl_plotdata = [[],[],[]]
gl_treecover = []
# store coverage of each att according to  dataset
gl_att_cover = [[],[],[],[],[],[],[],[]]
# reduce 
gl_LCA = []


def r_distance(source, target):
    """Return distance between source (cluster or record) 
    and target (cluster or record). The distance is based on 
    NCP (Normalized Certainty Penalty) on relational part.
    If source or target are cluster, func need to multiply
    source_len (or target_len).
    """
    source_mid = source
    target_mid = target
    source_len = 1
    target_len = 1
    # check if target is Cluster
    if isinstance(target, Cluster):
        target_mid = target.middle
        target_len = len(target.member)
    # check if souce is Cluster
    if isinstance(source, Cluster):
        source_mid = source.middle
        source_len = len(source.member)
    mid = middle(source_mid, target_mid)
    distance = (source_len+target_len) * NCP(mid)
    return distance


def NCP(mid):
    """Compute NCP (Normalized Certainty Penalty) 
    when generate record to middle.
    """
    ncp = 0.0
    # exclude SA values(last one type [])
    for i in range(len(mid) - 1):
        # if support of numerator is 1, then NCP is 0
        if gl_att_tree[i][mid[i]].support == 1:
            continue
        ncp +=  gl_att_tree[i][mid[i]].support * 1.0 / gl_treecover[i]
    return ncp


def UL(mid):
    """Compute UL (Utility Loss) for record and middle.
    """
    ul = 0.0
    supp_sum = 0
    for t in mid[-1]:
        supp = gl_att_tree[-1].node(t).support
        supp_sum += supp
        ul += pow(2, supp)
    ul /= pow(2, supp_sum)
    return ul


def get_LCA(index, item1, item2):
    """Get lowest commmon ancestor (including themselves)"""
    # get parent list from 
    if item1 == item2:
        return item1
    try:
        parent1 = gl_att_tree[index][item1].parent[:]
        parent2 = gl_att_tree[index][item2].parent[:]
    except:
        pdb.set_trace()
    parent1.insert(0, gl_att_tree[index][item1])
    parent2.insert(0, gl_att_tree[index][item2])
    minlen = min(len(parent1), len(parent2))
    last_LCA = parent1[-1]
    for i in range(minlen):
        if parent1[-i] == parent2[-i]:
            last_LCA = parent1[-i]
        else:
            break 
    return last_LCA.value


def tran_cmp(node1, node2):
    """Compare node1 (str) and node2 (str)"""
    support1 = gl_att_tree[-1][node1].support
    support2 = gl_att_tree[-1][node2].support
    if support1 != support2:
        return support1 -support2
    else:
        return (node1 > node2)
        

def get_LCC(tran1, tran2):
    """Get lowest common cut for tran1 and tran2.
    Transaction generalization need to find out LCC.
    """
    treemark1 = {}
    treemark2 = {}
    trantemp = []
    alltran = tran1[:]
    alltran.extend(tran2)
    # mark the generalization tree with red color
    for t in tran1:
        treemark1[t] = 1
        ptemp = gl_att_tree[-1][t].parent
        for pt in ptemp:
            if not pt.value in treemark1:
                treemark1[pt.value] = 1
            else:
                treemark1[pt.value] += 1
    
    # check the other color

    for t in tran2:
        if treemark1.has_key(t):
            if not t in trantemp:
                trantemp.append(t)
        treemark2[t] = 1
        ptemp = gl_att_tree[-1][t].parent
        for pt in ptemp:
            if not pt.value in treemark2:
                treemark2[pt.value] = 1
            else:
                treemark2[pt.value] = +1
            if treemark1.has_key(pt.value):
                if not pt.value in trantemp:
                    trantemp.append(pt.value)

    if len(trantemp) <= 1:
        return trantemp
    trantemp.sort(cmp=tran_cmp, reverse=True)
    dellist = []
    for t in trantemp:
        ptemp = gl_att_tree[-1][t].child
        checklist = []
        for pt in ptemp:
            if pt.value in trantemp:
                checklist.append(pt.value)
        if t in dellist:
            for pt in checklist:
                dellist.append(pt)
            continue
        sum1 = 0
        sum2 = 0
        for pt in checklist:
            sum1 += treemark1[pt]
            sum2 += treemark2[pt]
        if sum1 == treemark1[t] and sum2 ==treemark2[t]:
            dellist.append(t)
        else:
            for pt in checklist:
                dellist.append(pt)
    for t in dellist:
        try:
            trantemp.remove(t)
        except:
            print "Error! When del value according to dellist"
            pdb.set_trace()
    return trantemp


def middle(record1, record2):
    """Compute generalization result of record1 and record2"""
    middle = []
    for i in range(gl_att_QI - 1):
        middle.append(get_LCA(i, record1[i], record2[i]))
    middle.append(get_LCC(record1[-1], record2[-1]))
    return middle


def middle_for_cluster(records):
    """calculat middle of records(list) recursively"""
    len_r = len(records)
    if len_r == 1:
        return records[0]
    elif len_r == 2:
        return middle(records[0], records[1])
    else:
        mid = len_r / 2
        return middle(middle_for_cluster(records[:mid]), middle_for_cluster(records[mid:]))


def insert_to_sorted(sorted_tuple, temp, k=10000000000000):
    """insert element(index,distance) pair to sorted_tuple(list)"""
    # insert sort
    i = 0
    for i in range(len(sorted_tuple)):
        if sorted_tuple[i][1] > temp[1]:
            break
    else:
        i += 1
    sorted_tuple.insert(i, temp)
    # if sorted_tuple > k, del last element
    if len(sorted_tuple) > k:
        del sorted_tuple[-1]
    # return largest
    return sorted_tuple[-1][1]


def update_to_sorted(sorted_tuple, temp, k=10000000000000):
    """update element(index,distance) pair to sorted_tuple(list)"""
    # remove old pair
    i = 0
    for i in range(len(sorted_tuple)):
        if sorted_tuple[i][0] == temp[0]:
            break
    else:
        i += 1
    if i < len(sorted_tuple):
        del sorted_tuple[i]
    else:
        print "Can not find the pair"
        return
    # insert new pair
    i = 0
    for i in range(len(sorted_tuple)):
        if sorted_tuple[i][1] > temp[1]:
            break
    else:
        i += 1
    sorted_tuple.insert(i, temp)
    # if sorted_tuple > k, del last element
    if len(sorted_tuple) > k:
        del sorted_tuple[-1]
    # return largest
    return sorted_tuple[-1][1]

def find_best_KNN(record, k, data):
    """key fuction of KNN. Find k nearest neighbors of record, remove them from data"""
    elements = []
    knn = []
    element = []
    max_distance = 1000000000000
    for i, t in enumerate(data):
        dis = r_distance(record, t)
        if dis < max_distance:
            temp = [i, dis]
            max_distance = insert_to_sorted(knn, temp, k)
    for t in knn:
        elements.append(data[t[0]])
    c = Cluster(elements, middle_for_cluster(elements))
    # delete multiple elements from data according to knn index list
    data[:] = [t for i, t in enumerate(data) if i not in knn[:][0]]
    return c


def find_best_cluster(record, clusters):
    """residual assignment. Find best cluster for record."""
    min_distance = 1000000000000
    min_index = 0
    best_cluster = clusters[0]
    for i, t in enumerate(clusters):
        distance = r_distance(record, t.middle)
        if distance < min_distance:
            min_distance = distance
            min_index = i
            best_cluster = t
    # add record to best cluster
    return min_index


def find_merge_cluster(record, clusters, func):
    """mergeing step. Find best cluster for record."""
    min_distance = 1000000000000
    min_index = 0
    best_cluster = clusters[0]
    for i, t in enumerate(clusters):
        mid = middle(record, t.middle)
        distance = func(mid)
        if distance < min_distance:
            min_distance = distance
            min_index = i
            best_cluster = t
    # add record to best cluster
    return min_index    



def CLUSTER(data, k):
    """Group record according to QID distance. KNN"""
    global gl_att_tree
    global gl_treecover
    global gl_leaf_to_path
    clusters = []
    # randomly choose seed and find k-1 nearest records to form cluster with size k
    print "Begin to Cluster based on NCP"
    while len(data) >= k:
        index = randrange(0, len(data), 2)
        c =  find_best_KNN(data[index], k, data)
        clusters.append(c)
    # residual assignment
    while len(data) > 0:
        t = data.pop()
        cluster_index = find_best_cluster(t, clusters)
        clusters[cluster_index].member.append(t)
    return clusters


def Rum(mid):
    """Return relational information loss. 
    Based on NCP (Normalized Certainty Penalty)
    """
    return NCP(mid)


def Tum(mid):
    """Return transaction information loss. 
    Based on UL (Utility Loss)
    """
    return UL(mid)


def RMERGE_R(clusters):
    """Select the cluster c with minimum Rum(c) as a seed.
    Find c' with most similar realtional values to c and 
    constructs a temporary dataset Dtemp that reflects the 
    mergeing of c and c'. If Dtemp does not violate the Rum
    threshold, it is assinged to result.
    """
    print "Begin RMERGE_R"
    Rum_list = []
    for i, t in enumerate(clusters):
        temp = [i, Rum(t.middle)]
        insert_to_sorted(Rum_list, temp)
    while len(Rum_list) > 1:
        c = Rum_list[0][0]
        index = find_merge_cluster(clusters[c].middle, clusters, Rum)
        mid = middle(clusters[index].middle, clusters[c].middle)
        r = Rum(mid)
        pdb.set_trace()
        if r <= gl_threshold and c != index:
            clusters[index].merge_group(clusters[c], mid)
            # pdb.set_trace()
            del Rum_list[0]
            temp = [index, r]
            if len(Rum_list) == 0:
                pdb.set_trace()
            update_to_sorted(Rum_list, temp)
        else:
            break
    return clusters


def RMERGE_T():
    """Select the cluster c with minimum Rum(c) as a seed.
    Find c' that contain similar transacation iterms to c and 
    constructs a temporary dataset Dtemp by mergeing with c.
    If Dtemp does not violate the Rum threshold, it is 
    assinged to result.
    """
    print "Begin RMERGE_T"
    Rum_list = []
    for i, t in enumerate(clusters):
        temp = [i, Rum(t.middle)]
        insert_to_sorted(Rum_list, teamp)

    while len(Rum_list) > 0:
        c = Rum_list[-1][0]
        index = find_merge_cluster(c.middle, clusters)
        middle = middle(clusters[index].middle, clusters[c].middle)
        r = Rum(middle)
        if r <= gl_threshold and c != index:
            clusters[index].merge(clusters[c], middle)
            temp = [index, r]
            update_to_sorted(Rum_list, temp)
            del Rum_list[-1]
        else:
            break
    return


def RMERGE_RT():
    """Select the cluster c with minimum Rum(c) as a seed.
    Find the c' that is as close as possible to c, based on 
    (u+v) (u and v are the indices of c' in Rum and Tum list)
    """
    print "Begin RMERGE_RT"
    Rum_list = []
    Tum_list = []
    sum_list = []

    while len(Rum_list) > 0:
        c = Rum_list[-1][0]
        # find c' according sum(u+v)
        index = find_merge_cluster(c.middle, clusters)

        middle = middle(clusters[index].middle, clusters[c].middle)
        members = []
        members.extend(clusters[index].member)
        members.extend(clusters[c].member)
        if Rum(members, middle) <= gl_threshold:
            clusters[index].merge(clusters[c], middle)
            temp = [index, Rum(clusters[index])]
            update_to_sorted(Rum_list, temp)
            del Rum_list[-1]
        else:
            break
    return


def TMERGE_R():
    """
    """
    return


def TMERGE_T():
    """
    """
    return


def TMERGE_RT():
    return


def num_analysis(attlist):
    """plot distribution of attlist"""
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
    # pdb.set_trace()
    xlabel('value')
    ylabel('count')
    plt.hist(count, bins=value, normed=1, histtype='step', rwidth=0.8)
    # legend(loc='upper left')
    # grid on
    grid(True)
    show()

    
def read_tree_file(treename):
    """read tree data from treename"""
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
    if __DEBUG:
        print "Reading Tree" + treename
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
    if __DEBUG:
        print "Nodes No. = %d" % treecover
    gl_treecover.append(treecover)
    gl_leaf_to_path.append(leaf_to_path)
    gl_att_tree.append(nodelist)

    treefile.close()


def readtree():
    """read tree from data/tree_*.txt, store them in gl_att_tree and gl_leaf_to_path"""
    global gl_att_name
    print "Reading Tree"
    for t in gl_attlist:
        gl_att_name.append(gl_useratt[t])
    gl_att_name.append(gl_conditionatt[2])
    for t in gl_att_name:
        read_tree_file(t)


def readdata():
    """read microda for *.txt and store them in gl_databack"""
    global gl_databack
    global gl_att_cover
    global gl_useratt
    global gl_conditionatt
    userfile = open('data/demographics05test.csv', 'rU')
    conditionfile = open('data/conditions05.csv', 'rU')
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
            for i in range(len(gl_attlist)):
                index = gl_attlist[i]
                hashdata[k].append(v[index])
                if not v[index] in gl_att_cover[i]:
                    gl_att_cover[i].append(v[index])
            hashdata[k].append(temp)
    for k, v in hashdata.iteritems():
        gl_databack.append(v)
    # pdb.set_trace()
    # num_analysis([t[6] for t in gl_databack[:]])
    userfile.close()
    conditionfile.close()


if __name__ == '__main__':
    #read gentree tax
    readtree()
    #read record
    readdata()
    # pdb.set_trace()
    clusters = CLUSTER(gl_databack[:10],5)
    RMERGE_R(clusters)
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
