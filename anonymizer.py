#!/usr/bin/env python
#coding=utf-8

from generalization import GenTree, Cluster, CountTree
from datetime import datetime
from random import randrange
import pdb
import sys
from ftp_upload import ftpupload
import socket
from itertools import permutations, combinations
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
# count tree root
gl_count_tree = []

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
        ncp +=  gl_att_tree[i][mid[i]].support * 1.0 / gl_treecover[i]
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


def cut_cmp(cut1, cut2):
    """Compare cut1 (list) and cut2 (list)
    """
    support1 = 0
    support2 = 0
    for t in cut1:
        support1 += gl_att_tree[-1][t].support
    for t in cut2:
        support2 += gl_att_tree[-1][t].support
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
    satree = gl_att_cover[-1]
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
    cut = AA(trans, k, m)
    if __DEBUG:
        print "Cut generated"
        print cut
    return trans_gen(trans[:], cut)


def expand_tran(tran, cut=None):
    """expand transaction according to generalization cut
    """
    ex_tran = tran[:]
    # extend t with all parents
    for temp in tran:
        for t in gl_att_tree[-1][temp].parent:
            if not t.value in ex_tran: 
                ex_tran.append(t.value)
    ex_tran.remove('*')
    # sort ex_tran
    ex_tran.sort(cmp=tran_cmp, reverse=True)
    """if __DEBUG:
        print ex_tran
    """
    if cut:
        for temp in ex_tran:
            ancestor = [parent.value for parent in gl_att_tree[-1][temp].parent]
            for t in cut:
                if t in ancestor:
                    ex_tran.remove(temp)
    return ex_tran


def init_count_tree():
    """initialize a new cout tree
    """
    # initialize count tree
    ctree = CountTree('*')
    for t in gl_count_tree:
        CountTree(t, ctree)
    return ctree


def check_overlap(tran):
    """Check if items can joined with each other
    """
    len_tran = len(tran)
    for i in range(len_tran):
        for j in range(len_tran):
            if i == j:
                continue
            ancestor = [parent.value for parent in gl_att_tree[-1][tran[j]].parent]
            if tran[i] in ancestor:
                return False
    return True


def check_cover(tran, cut):
    """Check if tran if covered by cut
    return True if covered, False if not
    """
    if len(cut) == 0:
        return False

    for temp in tran:
        ancestor = [parent.value for parent in gl_att_tree[-1][temp].parent]
        for t in cut:
            if t in ancestor:
                break
        else:
            return True
    return False


def create_count_tree(trans, m):
    """Creat a count_tree
    """
    ctree = init_count_tree()
    # extend t and insert to count tree
    for temp in trans:
        ex_t = expand_tran(t)
        for i in range(1, m+1):
            temp = permutations(ex_t, i)
            # convet tuple to list
            temp = [list(combination) for combination in temp]
            for t in temp:
                if check_overlap(t):
                    t.sort(cmp=tran_cmp, reverse=True)
                    ctree.add_to_tree(t)
    return ctree


def get_cut(tran, ctree, k):
    """Given a tran, return cut making it k-anonymity with mini information
    return cut is a list e.g. ['A', 'B']
    """
    ancestor = []
    cut = []
    # get all ancestors
    for t in tran:
        parents = gl_att_tree[-1][t].parent[:]
        parents.append(gl_att_tree[-1][t])
        for p in parents:
            if not p.value in ancestor:
                ancestor.append(p.value)
    ancestor.remove('*')
    # generate all possible cut for tran
    len_ance = len(ancestor)
    for i in range(1, len_ance+1):
        temp = permutations(ancestor, i)
        # convet tuple to list
        temp = [list(combination) for combination in temp]
        # remove combination with overlap
        for t in temp:
            if check_overlap(t) == False:
                del t
            elif len(t):
                cut.append(t)
    # remove cut cannot cover tran
    for t in cut:
        if check_cover(tran, t):
            del t
    # sort by support, the same effect as sorting by NCP
    # pdb.set_trace()
    cut.sort(cmp=cut_cmp)
    if __DEBUG:
        print cut
    # return 
    for t in cut:
        if t >= k:
            return t


def merge_cut(cut, new_cut):
    for t in new_cut:
        if not t in cut:
            cut.append(t)
    # merge coverd and overlaped
    cut.sort(cmp=tran_cmp, reverse=True)
    delete_list = []
    len_cut = len(cut)
    for i in range(len_cut):
        temp = cut[i]
        check_list = []
        for j in range(i, len_cut):
            t = cut[j]
            ancestor = [parent.value for parent in gl_att_tree[-1][t].parent]
            if temp in ancestor:
                check_list.append(t)
        child_list = [child.value for child in gl_att_tree[-1][temp].child]
        for c in child_list:
            if not c in check_list:
                delete_list.extend(check_list)
                break
        else:
            delete_list.append(temp)
    delete_list = list(set(delete_list))
    for t in delete_list:
        cut.remove(t)
    return cut


def R_DA(ctree, cut, k=25, m=2):
    """Recursively get cut. Each branch can be paralleled
    """
    # pdb.set_trace()
    if ctree.level > 0 and check_cover([ctree.value], cut):
        return []
    if len(ctree.child):
        for temp in ctree.child:
            new_cut = R_DA(temp, cut, k, m)
            merge_cut(cut, new_cut)
    elif ctree.level >= 1 and ctree.support < k:
        tran = ctree.prefix[:]
        tran.append(ctree.value)
        return get_cut(tran, ctree, k)
    return cut


def DA(trans, k=25, m=2):
    """Direct anonymization for transaction anonymization.
    Developed by Manolis Terrovitis
    """
    cut_cover = {}
    ctree = create_count_tree(trans, m)
    if __DEBUG:
        print "Cut Tree"
        ctree.print_tree
    cut = []
    R_DA(ctree, cut, k, m)
    return gl_cut[:]


def AA(trans, k=25, m=2):
    """Apriori-based anonymization for transaction anonymization. 
    Developed by Manolis Terrovitis
    """
    cut = []
    for i in range(1, m+1):
        ctree = init_count_tree()
        for t in trans:
            ex_t = expand_tran(t, cut)
            temp = permutations(ex_t, i)
            # convet tuple to list
            temp = [list(t) for t in temp]
            for t in temp:
                if check_overlap(t):
                    t.sort(cmp=tran_cmp, reverse=True)
                    ctree.add_to_tree(t)
        # run DA
        new_cut = R_DA(ctree, cut, k, i)
        merge_cut(cut, new_cut)
    return cut


def trans_gen(trans, cut):
    """Generalize transaction according to ger cut
    """
    gen_trans = []
    for tran in trans:
        gen_tran = []
        for t in tran:
            ancestor = [parent.value for parent in gl_att_tree[-1][t].parent]
            for c in cut:
                if c in ancestor:
                    gen_tran.append(c)
                else:
                    gen_tran.append(t)
        gen_trans.append(list(set(gen_tran)))
    return gen_trans



def middle(record1, record2):
    """Compute relational generalization result of record1 and record2"""
    middle = []
    for i in range(gl_att_QI - 1):
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


def CLUSTER(data, k=25):
    """Group record according to QID distance. KNN"""
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


def init_gl_count_tree():
    """Init count tree order according to generalizaiton hierarchy
    """
    global gl_count_tree
    # creat count tree
    gl_count_tree = []
    for k, v in gl_att_tree[-1].iteritems():
        gl_count_tree.append(k)
    # delete *, and sort reverse
    gl_count_tree.remove('*')
    gl_count_tree.sort(cmp=tran_cmp, reverse=True)
    if __DEBUG:
        print gl_count_tree


def readtree():
    """read tree from data/tree_*.txt, store them in gl_att_tree and gl_leaf_to_path"""
    global gl_att_name
    print "Reading Tree"
    for t in gl_attlist:
        gl_att_name.append(gl_useratt[t])
    gl_att_name.append(gl_conditionatt[2])
    for t in gl_att_name:
        read_tree_file(t)
    init_gl_count_tree()


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
