#!/usr/bin/env python
# coding=utf-8

import pickle
import os.path
from utils.utility import cmp_str
from models.gentree import GenTree
from models.numrange import NumRange
import pdb

__DEBUG = False
ATT_NAMES = ['video_ID', 'uploader', 'age', 'category', 'length',
             'views', 'rate', 'ratings', 'comments', '']
QI_INDEX = [2, 3, 4, 5, 6, 7, 8]
IS_CAT = [True, True, True, True, True, True, True, True]
SA_INDEX = 9

def read_data():
    """
    read youtube dataset
    """
    QI_num = len(QI_INDEX)
    data = []
    numeric_dict = []
    sa_index = 0
    sa_dict = {}
    for i in range(QI_num):
        numeric_dict.append(dict())
    # oder categorical attributes in intuitive order
    # here, we use the appear number
    data_file = open('data/youtube.txt', 'rU')
    for line in data_file:
        line = line.strip()
        # remove empty and incomplete lines
        # only 30162 records will be kept
        if len(line) == 0:
            continue
        line = line.replace(' ', '')
        temp = line.split('\t')
        ltemp = []
        if len(temp) < 9:
            # remove line only have single id
            continue
        sa_dict[temp[0]] = str(sa_index)
        sa_index += 1
        for i in range(QI_num):
            index = QI_INDEX[i]
            if IS_CAT[i] is False:
                try:
                    numeric_dict[i][temp[index]] += 1
                except KeyError:
                    numeric_dict[i][temp[index]] = 1
            ltemp.append(temp[index])
        # add first 10 related id as a list
        ltemp.append(temp[9:][:10])
        data.append(ltemp)
    # pickle numeric attributes
    for i in range(QI_num):
        if IS_CAT[i] is False:
            static_file = open('data/youtube_' + ATT_NAMES[QI_INDEX[i]] + '_static.pickle', 'wb')
            sort_value = list(numeric_dict[i].keys())
            sort_value.sort(cmp=cmp_str)
            pickle.dump((numeric_dict[i], sort_value), static_file)
            static_file.close()
    final_data = []
    for record in data:
        related_id = record[7]
        temp = []
        for v_id in related_id:
            try:
                temp.append(sa_dict[v_id])
            except KeyError:
                # ignore videos that are not in datasets
                # temp.append(sa_index)
                # sa_dict[v_id] = str(sa_index)
                # sa_index += 1
                pass
        if len(temp) > 0:
            # remove records with empty related id
            record[7] = temp
            final_data.append(record)
    # pickle sa
    if os.path.isfile('youtube_related_ID_static.pickle') is True:
        with open('data/youtube_related_ID_static.pickle', 'wb') as static_file:
            sort_value = list(sa_dict.values())
            sort_value.sort(cmp=cmp_str)
            pickle.dump((sa_dict, sort_value), static_file)
            static_file.close()
            with open('data/youtube_related_ID_to_num.txt', 'w') as related_num:
                temp = sa_dict.items()
                temp.sort(key=lambda x: x[1], cmp=cmp_str)
                for t in temp:
                    related_num.write(t[0] + '\t' + t[1] + '\n')
    return final_data


def read_tree():
    """read tree from data/tree_*.txt, store them in att_tree
    """
    att_names = []
    att_trees = []
    for t in QI_INDEX:
        att_names.append(ATT_NAMES[t])
    att_names.append('related_ID')
    for i in range(len(att_names)):
        if IS_CAT[i]:
            att_trees.append(read_tree_file(att_names[i]))
        else:
            att_trees.append(read_pickle_file(att_names[i]))
    return att_trees


def read_tree_file(treename):
    """read tree data from treename
    """
    leaf_to_path = {}
    att_tree = {}
    prefix = 'data/youtube_'
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


def read_pickle_file(att_name):
    """
    read pickle file for numeric attributes
    return numrange object
    """
    with open('data/youtube_' + att_name + '_static.pickle', 'rb') as static_file:
        (numeric_dict, sort_value) = pickle.load(static_file)
        result = NumRange(sort_value, numeric_dict)
        return result