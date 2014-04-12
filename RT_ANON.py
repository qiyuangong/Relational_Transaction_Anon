#!/usr/bin/env python
#coding=utf-8

from generalization import GenTree, Cluster, CountTree
from Apriori_based_Anon import AA, DA, trans_gen
from datetime import datetime
from random import randrange
import pdb
import sys
from ftp_upload import ftpupload
import socket
# from pylab import *


__DEBUG = False
gl_threshold = 100000
# att_tree store root node for each att
gl_att_tree = []
# databack store all reacord for dataset
gl_databack = []

# Poulis set k=25, m=2 as default!

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
        ncp +=  gl_att_tree[i][mid[i]].support * 1.0 / gl_att_tree[i]['*'].support
    return ncp


def UL(mid):
    """Compute UL (Utility Loss) for record and middle.
    """
    ul = 0
    supp_sum = 0
    for t in mid[-1]:
        supp = gl_att_tree[-1][t].support
        supp_sum += supp
        ul += pow(2, supp)
    ul = ul / pow(2, supp_sum) * 1.0
    return ul


def get_LCA(index, item1, item2):
    """Get lowest commmon ancestor (including themselves)"""
    # get parent list from 
    if item1 == item2:
        return item1
    parent1 = gl_att_tree[index][item1].parent[:]
    parent2 = gl_att_tree[index][item2].parent[:]
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
        return support1 - support2
    else:
        return (node1 > node2)


def get_MaxBTD(trans):
    """Get BTD from cluster.
    Poulis define BTD of a cluster as the max BTD of all possbile
    combination of (r1,r2) in cluster.
    """
    len_tran = len(trans)
    if len_tran < 2:
        print "Error: len(trans) < 2"
        return 0
    elif len_tran == 2:
        return get_BTD(trans[0], trans[1])
    result_BTD = []
    for i in range(len_tran):
        for j in range(i + 1, len_tran):
            result_BTD.append(get_BTD(trans[i], trans[j]))
    return max(result_BTD)

def get_BTD(tran1, tran2):
    """Poulis suggested to use BTD (Bit-vector Transaction Distance)
    to compute distance between transactions rather than Tum. As Tum
    cause huge runing time.
    """
    satree = gl_att_tree[-1].keys()
    andcount = 1
    xorcount = 1
    for t in satree:
        if t in tran1 and t in tran2:
            andcount += 1
        elif t not in tran1 and t not in tran2:
            pass
        else:
            xorcount += 1
    return (xorcount * 1.0 / andcount)

def get_KM(trans, k=25, m=2):
    """Get lowest common cut for tran1 and tran2.
    Transaction generalization need to find out LCC.
    """
    cut = AA(gl_att_tree[-1], trans, k, m)
    if __DEBUG:
        print "Cut generated"
        print cut
    return trans_gen(trans[:], cut)


def middle(record1, record2):
    """Compute relational generalization result of record1 and record2"""
    middle = []
    for i in range(len(gl_att_tree) - 2):
        middle.append(get_LCA(i, record1[i], record2[i]))
    return middle


def middle_for_cluster(records):
    """calculat middle of records(list) recursively.
    Compute both relational middle for records (list).
    """
    len_r = len(records)
    if len_r <= 0:
        print "Error: empty list!"
        return []
    elif len_r == 1:
        return records[0]
    elif len_r == 2:
        return  middle(records[0], records[1])
    else:
        midpoint = len_r / 2
        return  middle(middle_for_cluster(records[:midpoint]), middle_for_cluster(records[midpoint:]))


def insert_to_sorted(sorted_tuple, temp, tail=10000000000000):
    """insert element(index,distance) pair to sorted_tuple(list)"""
    # insert sort
    i = 0
    for i in range(len(sorted_tuple)):
        if sorted_tuple[i][1] > temp[1]:
            break
    else:
        i += 1
    sorted_tuple.insert(i, temp)
    # if sorted_tuple > tail, del last element
    if len(sorted_tuple) > tail:
        del sorted_tuple[-1]
    # return largest
    return sorted_tuple[-1][1]


def update_to_sorted(sorted_tuple, temp, tail=10000000000000):
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
    # if sorted_tuple > tail, del last element
    if len(sorted_tuple) > tail:
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


def find_merge_cluster(index, clusters, func):
    """mergeing step. Find best cluster for record."""
    min_distance = 1000000000000
    source = clusters[index]
    min_index = 0
    min_mid = []
    for i, t in enumerate(clusters):
        mid = middle(source.middle, t.middle)
        distance = func(mid)
        if distance < min_distance:
            min_distance = distance
            min_index = i
            min_mid = mid[:]
    return (min_index, min_distance, min_mid)


def find_merge_cluster_T(index, clusters):
    """mergeing step. Find best cluster for record."""
    min_distance = 1000000000000
    source = clusters[index]
    min_index = 0
    min_mid = []
    for i, t in enumerate(clusters):
        records = []
        records.extend(t.member)
        records.extend(source.member)
        distance = get_MaxBTD(records[:][-1])
        if distance < min_distance:
            min_distance = distance
            min_index = i
            min_mid = middle_for_cluster(records)
    # compute Rum distacne for best cluster
    min_distance = Rum(min_mid)
    return (min_index, min_distance, min_mid)


def CLUSTER(att_tree, data, k=25):
    """Group record according to QID distance. KNN"""
    global gl_att_tree
    gl_att_tree = att_tree
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
        t_tuple = find_merge_cluster(c, clusters, Rum)
        index = t_tuple[0]
        r = t_tuple[1]
        mid = t_tuple[2]
        if r <= gl_threshold and c != index:
            clusters[index].merge_group(clusters[c], mid)
            del Rum_list[0]
            temp = [index, r]
            update_to_sorted(Rum_list, temp)
        else:
            break
    return clusters


def RMERGE_T(clusters):
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
        insert_to_sorted(Rum_list, temp)
    while len(Rum_list) > 1:
        c = Rum_list[0][0]
        t_tuple = find_merge_cluster_T(c, clusters)
        index = t_tuple[0]
        r = t_tuple[1]
        mid = t_tuple[2]
        if r <= gl_threshold and c != index:
            clusters[index].merge_group(clusters[c], mid)
            del Rum_list[0]
            temp = [index, r]
            update_to_sorted(Rum_list, temp)  
        else:
            break
    return clusters


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