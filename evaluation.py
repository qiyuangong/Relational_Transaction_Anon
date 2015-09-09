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
QUERY_TIME = 1000


def get_tran_range(att_tree, tran):
    cover_dict = dict()
    for item in tran:
        prob = 1.0
        leaf_num = len(att_tree[item])
        if leaf_num > 0:
            cover = att_tree[item].leaf.keys()
            prob = prob / leaf_num
            for t in cover:
                cover_dict[t] = prob
        else:
            cover_dict[item] = prob
    return cover_dict


def get_qi_range(att_trees, record, qi_len):
    prob = 1.0
    cover_set = []
    for i in range(qi_len):
        qi_value = record[i]
        cover_dict = dict()
        node = att_trees[i][qi_value]
        prob = 1.0
        if len(node) > 0:
            cover = node.leaf.keys()
            prob /= len(node)
            for t in cover:
                cover_dict[t] = prob
        else:
            cover_dict[qi_value] = prob
        cover_set.append(cover_dict)
    return cover_set


def get_result_cover(att_trees, result):
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


# def gen_to_cover(att_tree, result):
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
        est_value = 1.0
        flag = True
        for i in range(lenquery):
            # check qid part
            if flag is False:
                break
            att_prob = 0
            index = att_select[i]
            value = value_select[i]
            value_dict = record[index]
            for temp in value:
                try:
                    att_prob += value_dict[temp]
                except:
                    continue
            if abs(att_prob) <= 0.001:
                flag = False
                break
            else:
                est_value = est_value * att_prob
        if flag is False:
            continue
        count += est_value
    return count


def average_relative_error(att_trees, data, result, qd=2, s=5):
    """return average relative error of anonmized microdata,
    qd denote the query dimensionality, b denot seleciton of query
    """
    print "qd=%d s=%d" % (qd, s)
    print "size of raw data %d" % len(data)
    print "size of result data %d" % len(result)
    gen_data = get_result_cover(att_trees, result[:100])
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
        blist.append(int(math.ceil(len(att_roots[i]) * seed)))
    if _DEBUG:
        print "b %s" % blist
    # query times, normally it's 1000. But query 1000 need more than 10h
    # so we limited query times to 100
    zeroare = 0
    for turn in range(QUERY_TIME):
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
    if QUERY_TIME == zeroare:
        return 0
    return are / (QUERY_TIME - zeroare)


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
    file_list = [t for t in file_list if 'K10M2N' in t]
    joint = 5000
    dataset_num = 58568 / joint
    if 58568 % joint == 0:
        dataset_num += 1
    for i in range(1, dataset_num + 1):
        print '-' * 30
        pos = i * joint
        key_words = 'Size' + str(pos) + 'K10M2N'
        case_file = [t for t in file_list if key_words in t]
        are = 0.0
        for file_name in file_list:
            file_result = open('output/' + file_name, 'rb')
            (att_trees, data, result, K, m) = pickle.load(file_result)
            file_result.close()
            pre_are = average_relative_error(att_trees, data, result, qd, s)
            are += pre_are
        print "Average Relative Error for %d: %.2f%%" % (pos, are * 10)


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
