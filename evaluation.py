"""
evaluate Average Relative Error
"""
#!/usr/bin/env python
#coding=utf-8

from models.gentree import GenTree
from os import walk
import pdb
import math, random, pickle, sys, copy
from utils.utility import list_to_str

_DEBUG = False


# def gen_to_cover(att_tree, tran):
#     """Transform generlized transaction value to coverage (list)
#     """
#     temp = []
#     # store the probability of each value
#     prob = {}
#     for t in tran:
#         if att_tree[t].support:
#             support = att_tree[t].support
#             temp.extend(att_tree[t].cover.keys()[:])
#             for k in att_tree[t].cover.keys():
#                 try:
#                     prob[k] += 1.0 / support
#                 except:
#                     prob[k] = 1.0 / support
#         else:
#             temp.append(t)
#             try:
#                 prob[t] += 1
#             except:
#                 prob[t] = 1
#     temp = list(set(temp))
#     return (temp, prob)


def count_query(data, att_select, value_select):
    """input query att_select and value_select,return count()
    """
    count = 0
    lenquery = len(att_select)
    for record in data:
        for i in range(lenquery - 1):
            # check qid part
            index = att_select[i]
            value = value_select[i]
            qi_value = record[index]
            if qi_value in value:
                continue
            else:
                break
        else:
            value = value_select[-1]
            sa_set = record[-1]
            str_temp = list_to_str(sa_set)
            if str_temp in value:
                count += 1
    return count


def est_query(gen_data, att_select, value_select):
    """estimate aggregate result according to
    att_select and value_select, return count()
    """
    count = 0.0
    lenquery = len(att_select)
    # pdb.set_trace()
    for record in gen_data:
        est_value = 0.0
        for i in range(lenquery - 1):
            # check qid part
            index = att_select[i]
            value = value_select[i]
            qi_value = record[index]
            if qi_value in set(value):
                continue
            else:
                break
        else:
            # check sa part
            # this records is in query on QID
            value = value_select[-1]
            group_set = record[-1]
            for temp in value:
                try:
                    est_value += group_set[temp]
                except:
                    continue
        count += est_value
    return count


def average_relative_error(att_trees, data, gen_data, qd=2, s=5):
    """return average relative error of anonmized microdata,
    qd denote the query dimensionality, b denot seleciton of query
    """
    print "qd=%d s=%d" % (qd, s)
    print "size of dataset %d" % len(data)
    print "size of dataset %d" % len(gen_data)
    are = 0.0
    len_att = len(att_trees)
    blist = []
    att_roots = [t['*'] for t in att_trees]
    att_cover = [t.cover.keys() for t in att_roots]
    SA_set = {}
    # remove duplicate SA sets, only keep str values
    for temp in data:
        str_temp = list_to_str(temp[-1])
        try:
            SA_set[str_temp]
        except:
            SA_set[str_temp] = temp[-1]
    att_cover[-1] = SA_set.keys()
    seed = math.pow(s * 1.0 / 100, 1.0 / (qd + 1))
    # transform generalized result to coverage
    tran_result = copy.deepcopy(gen_data)
    # compute b
    for i in range(len_att):
        blist.append(int(math.ceil(att_roots[i].support * seed)))
    if _DEBUG:
        print "b %s" % blist
    # query times, normally it's 1000. But query 1000 need more than 10h
    # so we limited query times to 100
    q_times = 1000
    zeroare = 0
    for turn in range(q_times):
        att_select = []
        value_select = []
        i = 0
        # select QI att
        att_select = random.sample(range(0, len_att - 1), qd)
        # append SA. So len(att_select) == qd+1
        att_select.append(len_att - 1)
        if _DEBUG:
            print "ARE %d" % turn
            print "Att select %s" % att_select
        for i in range(qd + 1):
            index = att_select[i]
            temp = []
            count = 0
            temp = random.sample(att_cover[index], blist[index])
            value_select.append(set(temp))
        # pdb.set_trace()
        act = count_query(data, att_select, value_select)
        est = est_query(tran_result, att_select, value_select)
        if act != 0:
            are += abs(act - est) * 1.0 / act
        else:
            zeroare += 1
    print "Times = %d when Query on microdata is Zero" % zeroare
    if q_times == zeroare:
        return 0
    return are / (q_times - zeroare)


def evaluate_one(file_list, qd=2, s=5):
    """run are for one time
    """
    for t in file_list:
        if '58568K10M2.txt' in t:
            file_name = t
            break
        else:
            return
    file_result = open('output/' + file_name, 'rb')
    (att_trees, data, result, K, m) = pickle.load(file_result)
    file_result.close()
    print "K=%d, m=%d" % (K, m)
    are = average_relative_error(att_trees, data, result, qd, s)
    print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_s(file_list, qd=2):
    """evaluate s, while fixing qd
    """
    for t in file_list:
        if '58568K10M2.txt' in t:
            file_name = t
            break
        else:
            return
    file_result = open('output/' + file_name, 'rb')
    (att_trees, data, result, K, m) = pickle.load(file_result)
    file_result.close()
    print "K=%d, m=%d" % (K, m)
    for s in range(1, 10):
        print '-' * 30
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_qd(file_list, s=5):
    """evaluate qd, while fixing s
    """
    for t in file_list:
        if '58568K10M2.txt' in t:
            file_name = t
            break
        else:
            return
    file_result = open('output/' + file_name, 'rb')
    (att_trees, data, result, K, m) = pickle.load(file_result)
    file_result.close()
    print "K=%d, m=%d" % (K, m)
    for qd in range(1, 6):
        print '-' * 30
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_dataset(file_list, qd=2, s=5):
    """evaluate dataset, while fixing qd, s, k, m
    """
    file_list = [t for t in file_list if 'K10M2.txt' in t]
    for file_name in file_list:
        file_result = open('output/' + file_name, 'rb')
        (att_trees, data, result, K, m) = pickle.load(file_result)
        file_result.close()
        print '-' * 30
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_k(file_list, qd=2, s=5):
    """evaluate K, while fixing m, qd, s
    """
    str_list = []
    # we only compute K=5*n <= 50
    for i in range(5, 55, 5):
        temp = '58568K' + str(i) + 'M2.txt'
        str_list.append(temp)
    check_list = []
    for filename in file_list:
        for temp in str_list:
            if temp in filename:
                check_list.append(filename)
                break
    for file_name in check_list:
        file_result = open('output/' + file_name, 'rb')
        (att_trees, data, result, K, m) = pickle.load(file_result)
        file_result.close()
        print '-' * 30
        print "K=%d, m=%d" % (K, m)
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_m(file_list, qd=2, s=5):
    """evaluate m, while fixing K, qd, s
    """
    str_list = []
    # we only compute K=5*n <= 50
    for i in range(1, 6):
        temp = '58568K10M' + str(i) + '.txt'
        str_list.append(temp)
    check_list = []
    for filename in file_list:
        for temp in str_list:
            if temp in filename:
                check_list.append(filename)
                break
    for file_name in check_list:
        file_result = open('output/' + file_name, 'rb')
        (att_trees, data, result, K, m) = pickle.load(file_result)
        file_result.close()
        print '-' * 30
        print "K=%d, m=%d" % (K, m)
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


if __name__ == '__main__':
    print "Begin Evaluation"
    flag = ''
    qd = 2
    s = 5
    try:
        flag = sys.argv[1]
        qd = int(sys.argv[2])
        s = int(sys.argv[3])
    except:
        pass
    file_list = []
    for (dirpath, dirnames, filenames) in walk('output'):
        file_list.extend(filenames)
        break
    if flag == 's':
        evaluate_s(file_list)
    elif flag == 'qd':
        evaluate_qd(file_list)
    elif flag == 'one':
        evaluate_one(file_list, qd, s)
    elif flag == 'data':
        evaluate_dataset(file_list)
    elif flag == 'k':
        evaluate_k(file_list)
    elif flag == 'm':
        evaluate_m(file_list)
    elif flag == '':
        evaluate_one(file_list)
    else:
        print "Usage: python evaluation [qd | s | one | data | k |m]"
