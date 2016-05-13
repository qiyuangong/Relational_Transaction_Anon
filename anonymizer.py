"""
run DA and AA with given parameters
"""
#!/usr/bin/env python
# coding=utf-8
from RT_ANON import rt_anon
from utils.read_informs_data import read_data as read_informs
from utils.read_informs_data import read_tree as read_informs_tree
from utils.read_youtube_data import read_data as read_youtube
from utils.read_youtube_data import read_tree as read_youtube_tree
from models.gentree import GenTree
from utils.maketree import gen_gh_trees
from utils.save_result import save_to_file
import sys
import copy
import random
import cProfile
import pdb

sys.setrecursionlimit(50000)
TYPE_ALG = 'RMR'
DEFAULT_M = 2
M_MAX = 161
DEFAULT_K = 10
DEFAULT_T = 0.65


def get_result_one(att_tree, data, type_alg, k=DEFAULT_K, m=DEFAULT_M, threshold=DEFAULT_T):
    """
    run RT_ANON for one time, with k=10
    """
    print "K=%d" % k
    print "Size of Data", len(data)
    print "m=%d" % m
    print "Threshold=%.2f" % threshold
    result, eval_result = rt_anon(att_tree, data, type_alg, k, m, threshold)
    save_to_file((att_tree, data, result, k, m))
    print "RNCP %0.2f" % eval_result[0] + "%"
    print "TNCP %0.2f" % eval_result[1] + "%"
    print "Running time %0.2f" % eval_result[2] + " seconds"


def get_result_k(att_tree, data, type_alg, m=DEFAULT_M, threshold=DEFAULT_T):
    """
    change k, whle fixing size of dataset
    """
    data_back = copy.deepcopy(data)
    # for k in range(5, 105, 5):
    print "m=%d" % m
    print "Threshold=%.2f" % threshold
    print "Size of Data", len(data)
    all_rncp = []
    all_tncp = []
    all_rtime = []
    # for k in range(5, 55, 5):
    #     if k in [2, 5, 10, 25, 50, 100]:
    #         continue
    k_range = [2, 5, 10, 25, 50, 100]
    for k in k_range:
        print '#' * 30
        print "K=%d" % k
        result, eval_result = rt_anon(att_tree, data, type_alg, k, m, threshold)
        save_to_file((att_tree, data, result, k, m))
        data = copy.deepcopy(data_back)
        print "RNCP %0.2f" % eval_result[0] + "%"
        all_rncp.append(round(eval_result[0], 2))
        print "TNCP %0.2f" % eval_result[1] + "%"
        all_tncp.append(round(eval_result[1], 2))
        print "Running time %0.2f" % eval_result[2] + " seconds"
        all_rtime.append(round(eval_result[2], 2))
    print "K range", k_range
    print "RNCP", all_rncp
    print "TNCP", all_tncp
    print "Running time", all_rtime


def get_result_m(att_tree, data, type_alg, k=DEFAULT_K, threshold=DEFAULT_T):
    """
    change k, whle fixing size of dataset
    """
    print "K=%d" % k
    print "Threshold=%.2f" % threshold
    print "Size of Data", len(data)
    data_back = copy.deepcopy(data)
    # for m in range(1, 100, 5):
    all_rncp = []
    all_tncp = []
    all_rtime = []
    m_range = [1, 2, 3, 4, 5, M_MAX]
    for m in m_range:
        print '#' * 30
        print "m=%d" % m
        result, eval_result = rt_anon(att_tree, data, type_alg, k, m, threshold)
        save_to_file((att_tree, data, result, k, m))
        data = copy.deepcopy(data_back)
        print "RNCP %0.2f" % eval_result[0] + "%"
        all_rncp.append(round(eval_result[0], 2))
        print "TNCP %0.2f" % eval_result[1] + "%"
        all_tncp.append(round(eval_result[1], 2))
        print "Running time %0.2f" % eval_result[2] + " seconds"
        all_rtime.append(round(eval_result[2], 2))
    print "m range", m_range
    print "RNCP", all_rncp
    print "TNCP", all_tncp
    print "Running time", all_rtime


def get_result_dataset(att_tree, data, type_alg='RMR',
                       k=DEFAULT_K, m=DEFAULT_M, threshold=DEFAULT_T, num_test=10):
    """
    fix k, while changing size of dataset
    num_test is the test nubmber.
    """
    print "K=%d" % k
    print "m=%d" % m
    print "Threshold=%.2f" % threshold
    data_back = copy.deepcopy(data)
    length = len(data_back)
    joint = 5000
    datasets = []
    check_time = length / joint
    if length % joint == 0:
        check_time -= 1
    for i in range(check_time):
        datasets.append(joint * (i + 1))
    # datasets.append(length)
    all_rncp = []
    all_tncp = []
    all_rtime = []
    for pos in datasets:
        rncp = tncp = rtime = 0
        if pos > length:
            continue
        print '#' * 30
        print "size of dataset %d" % pos
        for j in range(num_test):
            temp = random.sample(data, pos)
            result, eval_result = rt_anon(att_tree, temp, type_alg, k, m, threshold)
            save_to_file((att_tree, temp, result, k, m), number=j)
            rncp += eval_result[0]
            tncp += eval_result[1]
            rtime += eval_result[2]
            data = copy.deepcopy(data_back)
        rncp /= num_test
        tncp /= num_test
        rtime /= num_test
        print "RNCP %0.2f" % rncp + "%"
        all_rncp.append(round(rncp, 2))
        print "TNCP %0.2f" % tncp + "%"
        all_tncp.append(round(tncp, 2))
        print "Running time %0.2f" % rtime + " seconds"
        all_rtime.append(round(rtime, 2))
    print "Size of datasets", datasets
    print "RNCP", all_rncp
    print "TNCP", all_tncp
    print "Running time", all_rtime


if __name__ == '__main__':
    # set K=10 as default
    FLAG = ''
    DATA_SELECT = 'i'
    # gen_even_BMS_tree(5)
    try:
        DATA_SELECT = sys.argv[1]
        TYPE_ALG = sys.argv[2]
        FLAG = sys.argv[3]
    except IndexError:
        pass
    INPUT_K = 10
    print "*" * 30
    if DATA_SELECT == 'i':
        print "INFORMS data"
        DATA = read_informs()
        # gen_gh_trees(DATA_SELECT)
        ATT_TREES = read_informs_tree()
    elif DATA_SELECT == 'y':
        print "Youtube data"
        DATA = read_youtube()
        # gen_gh_trees(DATA_SELECT)
        ATT_TREES = read_youtube_tree()
    else:
        print "INFORMS data"
        DATA = read_informs()
        # gen_gh_trees(DATA_SELECT)
        ATT_TREES = read_informs_tree()
    # read generalization hierarchy
    # read record
    # remove duplicate items
    # DATA = DATA[:1000]
    # for i in range(len(DATA)):
    #     if len(DATA[i]) <= 40:
    #         DATA[i] = list(set(DATA[i]))
    #     else:
    #         DATA[i] = list(set(DATA[i][:40]))
    for i in range(len(DATA)):
        DATA[i][-1] = list(set(DATA[i][-1]))
    print "Begin to run", TYPE_ALG
    print "*" * 10
    # print "Begin Apriori based Anon"
    if FLAG == 'k':
        get_result_k(ATT_TREES, DATA, TYPE_ALG)
    elif FLAG == 'm':
        get_result_m(ATT_TREES, DATA, TYPE_ALG)
    elif FLAG == 'data':
        k = DEFAULT_K
        try:
            k = int(sys.argv[4])
        except:
            pass
        if k != DEFAULT_K:
            get_result_dataset(ATT_TREES, DATA, TYPE_ALG, k)
        else:
            get_result_dataset(ATT_TREES, DATA, TYPE_ALG)
    elif FLAG == '':
        # cProfile.run('get_result_one(ATT_TREES, DATA, TYPE_ALG)')
        get_result_one(ATT_TREES, DATA, TYPE_ALG)
    else:
        try:
            INPUT_K = int(FLAG)
            get_result_one(ATT_TREES, DATA, TYPE_ALG, INPUT_K)
        except ValueError:
            print "Usage: python anonymizer [k | m | data]"
            print "k: varying k"
            print "m: varying m"
            print "data: varying size of dataset"
            print "example: python anonymizer RMR 10"
            print "example: python anonymizer RMT k"
    # anonymized dataset is stored in result
    print "Finish RT_ANON!!"
