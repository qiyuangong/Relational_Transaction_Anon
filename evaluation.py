"""
evaluate Average Relative Error
"""
#!/usr/bin/env python
#coding=utf-8

from models.gentree import GenTree
from os import walk
import pdb
import math
import random
import pickle
import sys
import cProfile
from utils.utility import list_to_str

_DEBUG = False
QUERY_TIME = 1000
COVER_DICT = []
DEAULT_K = 10
DEAULT_M = 2
# the query time for est is very long.
# so we can use FAST_BREAK to quit the query
# when the number of no empty query meet the mini
# requirement.
FAST_BREAK = 100


def init_cover_dict(att_trees):
    global COVER_DICT
    COVER_DICT = []
    for att_tree in att_trees:
        cover = dict()
        prob = 1.0 / len(att_tree['*'])
        root_cover = dict()
        for key, item in att_tree['*'].leaf.items():
            root_cover[key] = prob
        cover['*'] = root_cover
        COVER_DICT.append(cover)


def get_tran_range(att_tree, tran):
    temp = list_to_str(tran)
    try:
        return COVER_DICT[temp]
    except:
        pass
    cover_dict = dict()
    for item in tran:
        prob = 1.0
        leaf_num = len(att_tree[item])
        if leaf_num > 0:
            prob = prob / leaf_num
            for t in att_tree[item].leaf.keys():
                cover_dict[t] = prob
        else:
            cover_dict[item] = prob
    COVER_DICT[-1][temp] = cover_dict
    return cover_dict


def get_qi_range(att_trees, record, qi_len):
    prob = 1.0
    cover_set = []
    for i in range(qi_len):
        qi_value = record[i]
        try:
            cover_set.append(COVER_DICT[i][qi_value])
            continue
        except:
            pass
        cover_dict = dict()
        node = att_trees[i][qi_value]
        prob = 1.0
        if len(node) > 0:
            prob /= len(node)
            for t in node.leaf.keys():
                cover_dict[t] = prob
        else:
            cover_dict[qi_value] = prob
        COVER_DICT[i][qi_value] = cover_dict
        cover_set.append(cover_dict)
    return cover_set


def get_result_cover(att_trees, result):
    init_cover_dict(att_trees)
    qi_len = len(result[0]) - 1
    gen_result = []
    for record in result:
        cover_set = []
        qi_result = get_qi_range(att_trees, record, qi_len)
        cover_set.extend(qi_result)
        tran_result = get_tran_range(att_trees[-1], record[-1])
        cover_set.append(tran_result)
        gen_result.append(cover_set)
    return gen_result


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
            if qi_value in set(value):
                continue
            else:
                break
        else:
            value = value_select[-1]
            sa_set = record[-1]
            for temp in value:
                for t in sa_set:
                    if t not in set(temp):
                        break
                else:
                    count += 1
                    break
    return count


# def check_gen_qi(att_tree, gen_value, value):
#     att_prob = 0.0
#     qi_gen_node = att_tree[gen_value]
#     ls = len(qi_gen_node)
#     if ls == 0:
#         if gen_value in set(value):
#             return 1.0
#     else:
#         for temp in value:
#             try:
#                 qi_gen_node.cover[temp]
#                 att_prob += 1.0 / ls
#             except:
#                 continue
#     return att_prob


# def check_gen_tran(att_tree, sa_set, value):
#     sa_est = 0.0
#     for tran in value:
#         tran_est = 1.0
#         for t in tran:
#             for item in sa_set:
#                 ls = len(att_tree[item])
#                 if ls == 0:
#                     if t == item:
#                         break
#                 else:
#                     try:
#                         att_tree[item].cover[t]
#                         tran_est *= 1.0 / ls
#                         break
#                     except:
#                         continue
#             else:
#                 tran_est = 0.0
#                 break
#         sa_est += tran_est
#     return sa_est


# def est_query(att_trees, gen_data, att_select, value_select):
#     """estimate aggregate result according to
#     att_select and value_select, return count()
#     """
#     count = 0.0
#     lenquery = len(att_select)
#     for record in gen_data:
#         est_value = 1.0
#         flag = True
#         for i in range(lenquery - 1):
#             # check qid part
#             if flag is False:
#                 break
#             index = att_select[i]
#             att_prob = check_gen_qi(att_trees[index], record[index], value_select[i])
#             if abs(att_prob) <= 0.001:
#                 flag = False
#                 break
#             else:
#                 est_value = est_value * att_prob
#             if flag is False:
#                 continue
#         else:
#             sa_est = check_gen_tran(att_trees[-1], record[-1], value_select[-1])
#             count += (est_value * sa_est)
#     return count


def est_query(gen_data, att_select, value_select):
    """estimate aggregate result according to
    att_select and value_select, return count()
    """
    count = 0.0
    lenquery = len(att_select)
    for record in gen_data:
        est_qi = 1.0
        for i in range(lenquery - 1):
            # check qid part
            att_prob = 0
            index = att_select[i]
            value = value_select[i]
            qi_dict = record[index]
            for temp in value:
                try:
                    att_prob += qi_dict[temp]
                except:
                    pass
            if abs(att_prob) <= 0.0001:
                break
            est_qi = est_qi * att_prob
        else:
            est_sa = 0.0
            value = value_select[-1]
            sa_dict = record[-1]
            for tran in value:
                tran_prob = 1.0
                for t in tran:
                    try:
                        tran_prob *= sa_dict[t]
                    except:
                        break
                else:
                    est_sa += tran_prob
            count += (est_qi * est_sa)
    return count


def average_relative_error(att_trees, data, result, qd=2, s=5):
    """return average relative error of anonmized microdata,
    qd denote the query dimensionality, b denot seleciton of query
    """
    if _DEBUG:
        print "qd=%d s=%d" % (qd, s)
        print "size of raw data %d" % len(data)
        print "size of result data %d" % len(result)
    gen_data = get_result_cover(att_trees, result)
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
    att_cover[-1] = SA_set.values()
    seed = math.pow(s * 1.0 / 100, 1.0 / (qd + 1))
    # transform generalized result to coverage
    # compute b
    for i in range(len_att):
        blist.append(int(math.ceil(len(att_roots[i]) * seed)))
    if _DEBUG:
        print "b %s" % blist
    # query times, normally it's 1000. But query 1000 need more than 10h
    # so we limited query times to 100
    zeroare = 0
    for turn in range(1, QUERY_TIME + 1):
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
            value_select.append(temp)
        # pdb.set_trace()
        act = count_query(data, att_select, value_select)
        if act != 0:
            est = est_query(gen_data, att_select, value_select)
            are += abs(act - est) * 1.0 / act
        else:
            zeroare += 1
        if turn - zeroare == FAST_BREAK:
            break
    if _DEBUG:
        print "Times = %d when Query on microdata is Zero" % zeroare
    if turn == zeroare:
        print "Error: all act ==0"
        return 0
    return are / (turn - zeroare)


def evaluate_one(file_list, k=DEAULT_K, m=DEAULT_M, qd=2, s=5):
    """run are for one time
    """
    match_str = '58568K' + str(k) + 'M' + str(m) + '.txt'
    for t in file_list:
        if match_str in t:
            file_name = t
            break
    else:
        return
    file_result = open('output/' + file_name, 'rb')
    (att_trees, data, result, K, m) = pickle.load(file_result)
    file_result.close()
    print "print FAST_BREAK", FAST_BREAK
    print "K=%d, m=%d" % (K, m)
    are = average_relative_error(att_trees, data, result, qd, s)
    print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_s(file_list, k=DEAULT_K, m=DEAULT_M, qd=2):
    """evaluate s, while fixing qd
    """
    match_str = '58568K' + str(k) + 'M' + str(m) + '.txt'
    for t in file_list:
        if match_str in t:
            file_name = t
            break
    else:
        return
    file_result = open('output/' + file_name, 'rb')
    (att_trees, data, result, K, m) = pickle.load(file_result)
    file_result.close()
    print "print FAST_BREAK", FAST_BREAK
    print "K=%d, m=%d" % (K, m)
    for s in range(1, 10):
        print '-' * 30
        print "s", s
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_qd(file_list, k=DEAULT_K, m=DEAULT_M, s=5):
    """evaluate qd, while fixing s
    """
    match_str = '58568K' + str(k) + 'M' + str(m) + '.txt'
    for t in file_list:
        if '58568K10M2.txt' in t:
            file_name = t
            break
    else:
        return
    file_result = open('output/' + file_name, 'rb')
    (att_trees, data, result, K, m) = pickle.load(file_result)
    file_result.close()
    print "print FAST_BREAK", FAST_BREAK
    print "K=%d, m=%d" % (K, m)
    for qd in range(1, 6):
        print '-' * 30
        print "qd", qd
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)


def evaluate_dataset(file_list, k=DEAULT_K, m=DEAULT_M, qd=2, s=5):
    """evaluate dataset, while fixing qd, s, k, m
    """
    match_str = 'K' + str(k) + 'M' + str(m) + 'N'
    file_list = [t for t in file_list if match_str in t]
    joint = 5000
    dataset_num = 58568 / joint
    if 58568 % joint == 0:
        dataset_num += 1
    print "print FAST_BREAK", FAST_BREAK
    all_are = []
    all_data = []
    for i in range(1, dataset_num + 1):
        print '-' * 30
        pos = i * joint
        all_data.append(pos)
        key_words = 'Size' + str(pos) + 'K' + str(k) + 'M' + str(m) + 'N'
        print "size of dataset %d" % pos
        case_file = [t for t in file_list if key_words in t]
        are = 0.0
        for file_name in case_file:
            if _DEBUG:
                print filename
            file_result = open('output/' + file_name, 'rb')
            (att_trees, data, result, K, m) = pickle.load(file_result)
            file_result.close()
            pre_are = average_relative_error(att_trees, data, result, qd, s)
            are += pre_are
        print "Average Relative Error for %d: %.2f%%" % (pos, are * 10)
        all_are.append(round(are * 100, 2))
    print "Data", all_data
    print "ARE", all_are


def evaluate_k(file_list, m=DEAULT_M, qd=2, s=5):
    """evaluate K, while fixing m, qd, s
    """
    str_list = []
    # we only compute K=5*n <= 50
    # for i in [2, 5, 10, 25, 50, 100]:
    for i in range(5, 55, 5):
        temp = '58568K' + str(i) + 'M' + str(m) + '.txt'
        str_list.append(temp)
    check_list = []
    for filename in file_list:
        for temp in str_list:
            if temp in filename:
                check_list.append(filename)
                break
    all_are = []
    all_k = []
    print "print FAST_BREAK", FAST_BREAK
    for file_name in check_list:
        file_result = open('output/' + file_name, 'rb')
        (att_trees, data, result, K, m) = pickle.load(file_result)
        file_result.close()
        print '-' * 30
        print "K=%d, m=%d" % (K, m)
        all_k.append(K)
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)
        all_are.append(round(are * 100, 2))
    print "K", all_k
    print "ARE", all_are


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
    all_are = []
    all_m = []
    print "print FAST_BREAK", FAST_BREAK
    for file_name in check_list:
        file_result = open('output/' + file_name, 'rb')
        (att_trees, data, result, K, m) = pickle.load(file_result)
        file_result.close()
        print '-' * 30
        print "K=%d, m=%d" % (K, m)
        all_m.append(m)
        are = average_relative_error(att_trees, data, result, qd, s)
        print "Average Relative Error: %.2f%%" % (are * 100)
        all_are.append(round(are * 100, 2))
    print "m", all_m
    print "ARE", all_are


if __name__ == '__main__':
    print "Begin Evaluation"
    flag = ''
    qd = 2
    s = 5
    try:
        flag = sys.argv[1]
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
    elif flag == '':
        cProfile.run('evaluate_one(file_list)')
        # evaluate_one(file_list, qd, s)
    elif flag == 'data':
        evaluate_dataset(file_list)
    elif flag == 'k':
        evaluate_k(file_list)
    elif flag == 'm':
        evaluate_m(file_list)
    else:
        try:
            INPUT_K = int(sys.argv[1])
            evaluate_one(file_list, INPUT_K)
        except:
            print "Usage: python evaluation [qd | s | data | k |m]"
