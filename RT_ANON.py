#!/usr/bin/env python
#coding=utf-8

import pdb
import copy
import heapq
from models.cluster import Cluster
from models.gentree import GenTree
from apriori_based_anon import apriori_based_anon
import random
import time
import operator


__DEBUG = False
THESHOLD = 0.65
# att_tree store root node for each att
ATT_TREES = []
# databack store all reacord for dataset
DATA_BACKUP = []
LEN_DATA = 0
LEAF_NUM = 0
QI_LEN = 0


def r_distance(source, target):
    """
    Return distance between source (cluster or record)
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
        target_len = len(target)
    # check if souce is Cluster
    if isinstance(source, Cluster):
        source_mid = source.middle
        source_len = len(source)
    if source_mid == target_mid:
        return 0
    mid = middle(source_mid, target_mid)
    # len should be taken into account
    distance = (source_len + target_len) * NCP(mid)
    return distance


def NCP(mid):
    """Compute NCP (Normalized Certainty Penalty)
    when generate record to middle.
    """
    # TODO
    ncp = 0.0
    # exclude SA values(last one type [])
    for i in range(QI_LEN):
        # if support of numerator is 1, then NCP is 0
        if len(ATT_TREES[i][mid[i]]) == 0:
            continue
        ncp += len(ATT_TREES[i][mid[i]]) * 1.0 / len(ATT_TREES[i]['*'])
    return ncp


def UL(tran):
    """Compute UL (Utility Loss) for record and middle.
    """
    ul = 0
    supp_sum = len(ATT_TREES[-1]['*'])
    for t in mid[-1]:
        try:
            supp = len(ATT_TREES[-1][t])
        except:
            pdb.set_trace()
        ul += (2 ** supp)
    ul = ul / (2 ** supp_sum) * 1.0
    return ul


def get_LCA(index, item1, item2):
    """Get lowest commmon ancestor (including themselves)"""
    # get parent list from
    if item1 == item2:
        return item1
    parent1 = ATT_TREES[index][item1].parent[:]
    parent2 = ATT_TREES[index][item2].parent[:]
    parent1.insert(0, ATT_TREES[index][item1])
    parent2.insert(0, ATT_TREES[index][item2])
    minlen = min(len(parent1), len(parent2))
    last_LCA = parent1[-1]
    # note here: when trying to access list reversely, take care of -0
    for i in range(1, minlen + 1):
        if parent1[-i].value == parent2[-i].value:
            last_LCA = parent1[-i]
        else:
            break
    return last_LCA.value


def tran_cmp(node1, node2):
    """Compare node1 (str) and node2 (str)"""
    support1 = len(ATT_TREES[-1][node1])
    support2 = len(ATT_TREES[-1][node2])
    if support1 != support2:
        return cmp(support1, support2)
    else:
        return cmp(node1, node2)


def get_BTD(tran1, tran2):
    """Poulis suggested to use BTD (Bit-vector Transaction Distance)
    to compute distance between transactions rather than Tum. As Tum
    cause huge runing time.
    """
    value_list = tran1[:]
    value_list.extend(tran2[:])
    value_list = list(set(value_list))
    andcount = 1
    xorcount = 1
    for t in value_list:
        if t in tran1 and t in tran2:
            andcount += 1
        elif t not in tran1 and t not in tran2:
            pass
        else:
            xorcount += 1
    return (xorcount * 1.0 / andcount)


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


def T_Gen(trans, k=25, m=2):
    """transaction generalization based on AA
    """
    # using AA to generalization transaction part
    result, eval_result = apriori_based_anon(ATT_TREES[-1], trans, 'AA', k, m)
    return result, eval_result


def gen_cluster(cluster, k=25, m=2):
    """generalize cluster using relational and transaction generalization
    return record list
    """
    gen_result = []
    member = cluster.member
    trans = [t[-1] for t in member]
    rncp = len(cluster) * NCP(cluster.middle)
    gen_trans, eval_result = T_Gen(trans, k, m)
    for i in range(len(member)):
        # relational generalization
        temp = cluster.middle[:]
        temp.append(gen_trans[i])
        gen_result.append(temp)
    return gen_result, rncp, eval_result


def middle(record1, record2):
    """
    Compute relational generalization result of record1 and record2
    """
    middle = []
    for i in range(QI_LEN):
        middle.append(get_LCA(i, record1[i], record2[i]))
    return middle


def middle_for_cluster(records):
    """
    calculat middle of records(list) recursively.
    Compute both relational middle for records (list).
    """
    len_r = len(records)
    mid = records[0]
    for i in range(1, len_r):
        mid = middle(mid, records[i])
    return mid


def find_best_knn(index, k, data):
    """key fuction of KNN. Find k nearest neighbors of record, remove them from data"""
    dist_dict = {}
    record = data[index]
    max_distance = 1000000000000
    # add random seed to cluster
    for i, t in enumerate(data):
        if i == index:
            continue
        dist = r_distance(record, t)
        dist_dict[i] = dist
    sorted_dict = sorted(dist_dict.iteritems(), key=operator.itemgetter(1))
    knn = sorted_dict[:k - 1]
    knn.append((index, 0))
    record_index = [t[0] for t in knn]
    elements = [data[t[0]] for t in knn]
    cluster = Cluster(elements, middle_for_cluster(elements))
    # delete multiple elements from data according to knn index list
    return cluster, record_index


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


def find_merge_cluster(source, Rum_list, func):
    """
    mergeing step. Find best cluster for index cluster.
    """
    min_distance = 1000000000000
    min_index = None
    min_mid = []
    len_source = len(source)
    for i, temp in enumerate(Rum_list):
        _, cluster = temp
        mid = middle(source.middle, cluster.middle)
        distance = func(mid, len(cluster) + len_source)
        if distance < min_distance:
            min_distance = distance
            min_index = i
            min_mid = mid[:]
    if min_distance == 1000000000000:
        print "Cannot find the nearest cluster"
        pdb.set_trace()
    _, min_cluster = Rum_list.pop(min_index)
    return (min_distance, min_cluster, min_mid)


def find_merge_cluster_T(source, Rum_list):
    """mergeing step. Find best cluster for record."""
    min_distance = 1000000000000
    min_index = None
    source_tran = [t[-1] for t in source.member]
    len_source = len(source)
    for i, temp in enumerate(Rum_list):
        _, cluster = temp
        target_tran = [t[-1] for t in cluster.member]
        trans = source_tran + target_tran
        distance = Tum(trans)
        if distance < min_distance:
            min_distance = distance
            min_index = i
    if min_distance == 1000000000000:
        print "Cannot find the nearest cluster"
        pdb.set_trace()
    _, min_cluster = Rum_list.pop(min_index)
    return (min_distance, min_cluster, _)


def cluster_algorithm(data, k=25):
    """
    Group record according to QID distance. KNN
    """
    clusters = []
    # randomly choose seed and find k-1 nearest records to form cluster with size k
    print "Begin to Cluster based on NCP"
    while len(data) >= k:
        index = random.randrange(len(data))
        cluster, record_index = find_best_knn(index, k, data)
        data = [t for i, t in enumerate(data[:]) if i not in set(record_index)]
        clusters.append(cluster)
    # residual assignment
    while len(data) > 0:
        t = data.pop()
        cluster_index = find_best_cluster(t, clusters)
        clusters[cluster_index].add_record(t)
    return clusters


def Rum(mid, size):
    """Return relational information loss.
    Based on NCP (Normalized Certainty Penalty)
    """
    return NCP(mid) * size * 1.0


def Tum(trans):
    """Return transaction information loss.
    Based on UL (Utility Loss)
    """
    return get_MaxBTD(trans)


def RMERGE_R(clusters):
    """Select the cluster c with minimum Rum(c) as a seed.
    Find c' with most similar realtional values to c and
    constructs a temporary dataset Dtemp that reflects the
    mergeing of c and c'. If Dtemp does not violate the Rum
    threshold, it is assinged to result.
    """
    print "Begin RMERGE_R"
    Rum_list = []
    ncp_list = []
    ncp_value = 0.0
    for i, cluster in enumerate(clusters):
        heapq.heappush(Rum_list, (Rum(cluster.middle, len(cluster)), cluster))
    while len(Rum_list) > 1:
        _, current_cluster = heapq.heappop(Rum_list)
        min_rum, best_cluster, mid = find_merge_cluster(current_cluster, Rum_list, Rum)
        total_ncp = 0.0
        for temp in Rum_list:
            total_ncp += temp[0]
        total_ncp += min_rum
        total_ncp = total_ncp * 1.0 / LEN_DATA
        total_ncp /= QI_LEN
        if total_ncp <= THESHOLD:
            best_cluster.merge_group(current_cluster, mid)
            heapq.heappush(Rum_list, (min_rum, best_cluster))
        else:
            break
    return [t[1] for t in Rum_list]


def RMERGE_T(clusters):
    """Select the cluster c with minimum Rum(c) as a seed.
    Find c' that contain similar transacation iterms to c and
    constructs a temporary dataset Dtemp by mergeing with c.
    If Dtemp does not violate the Rum threshold, it is
    assinged to result.
    """
    print "Begin RMERGE_T"
    Rum_list = []
    ncp_list = []
    ncp_value = 0.0
    for i, cluster in enumerate(clusters):
        heapq.heappush(Rum_list, (Rum(cluster.middle, len(cluster)), cluster))
    while len(Rum_list) > 1:
        _, current_cluster = heapq.heappop(Rum_list)
        _, best_cluster, _ = find_merge_cluster_T(current_cluster, Rum_list)
        total_ncp = 0.0
        mid = middle(current_cluster.middle, best_cluster.middle)
        min_rum = Rum(mid, len(current_cluster) + len(best_cluster))
        for temp in Rum_list:
            total_ncp += temp[0]
        total_ncp += min_rum
        total_ncp = total_ncp * 1.0 / LEN_DATA
        total_ncp /= QI_LEN
        if total_ncp <= THESHOLD:
            best_cluster.merge_group(current_cluster, mid)
            heapq.heappush(Rum_list, (min_rum, best_cluster))
        else:
            break
    return [t[1] for t in Rum_list]


def RMERGE_RT(clusters):
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
        if Rum(members, middle) <= THESHOLD:
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


def init(att_trees, data, threshold):
    """
    init global variables
    """
    global ATT_TREES, DATA_BACKUP, LEN_DATA, QI_LEN, THESHOLD
    ATT_TREES = att_trees
    DATA_BACKUP = copy.deepcopy(data)
    THESHOLD = threshold
    QI_LEN = len(data[0]) - 1
    LEN_DATA = len(data)


def rt_anon(att_trees, data, type_alg='RMR', k=25, m=2, threshold=0.65):
    """
    the main function of Relational_Transaction_Anon
    """
    init(att_trees, data, threshold)
    result = []
    start_time = time.time()
    clusters = cluster_algorithm(data, k)
    if type_alg == 'RMR':
        merged_clusters = RMERGE_R(clusters)
    elif type_alg == 'RMT':
        merged_clusters = RMERGE_T(clusters)
    elif type_alg == 'RMRT':
        merged_clusters = RMERGE_RT(clusters)
    elif type_alg == 'TMR':
        merged_clusters = TMERGE_R(clusters)
    elif type_alg == 'TMT':
        merged_clusters = TMERGE_T(clusters)
    elif type_alg == 'TMRT':
        merged_clusters = TMERGE_RT(clusters)
    else:
        print "Please choose merge algorithm types"
        print "RMR | RMT | RMRT | TMR | TMT | TMRT"
        return
    rtime = float(time.time() - start_time)
    total_rncp = 0.0
    total_tncp = 0.0
    item_num = 0
    for c in clusters:
        temp, rncp, eval_result = gen_cluster(c, k, m)
        total_rncp += rncp
        total_tncp += eval_result[0]
        item_num += eval_result[1]
        result.extend(temp)
    total_rncp = total_rncp * 1.0 / LEN_DATA
    total_rncp = total_rncp / QI_LEN
    total_tncp = total_tncp * 1.0 / item_num
    total_tncp *= 100
    total_rncp *= 100
    if __DEBUG:
        print "RNCP", total_rncp
        print "TNCP", total_tncp
    print "Finish RT-Anon based on", type_alg
    return result, (total_rncp, total_tncp, rtime)
