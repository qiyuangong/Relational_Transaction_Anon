#!/usr/bin/env python
# coding=utf-8
import string
import math
import pickle
from models.numrange import NumRange
from utils.utility import cmp_str

__DEBUG = False

def gen_gh_trees(data_select):
    """gen all tress from treeseed file or static
    """
    if data_select == 'i':
        gen_informs_even_tree(5)
        gen_informs_ICD9_tree()
        # gen_informs_even_income_tree(5)
        gen_informs_DOBYY_tree()
    else:
        gen_youtube_trees(5)


def gen_youtube_trees(fanout=5):
    qi_names = ['age', 'length',
             'views', 'rate', 'ratings', 'comments', 'related_ID']
    for att_name in qi_names:
        with open('data/youtube_' + att_name + '_static.pickle', 'rb') as static_file:
            gh_tree = open('data/youtube_' + att_name + '.txt', 'w')
            (__, sort_value) = pickle.load(static_file)
            height = int(math.ceil(math.log(len(sort_value), fanout)))
            for i, temp in enumerate(sort_value):
                node = []
                for h in range(height):
                    if h == 0:
                        temp = '%s' % sort_value[i]
                    else:
                        window = fanout ** h
                        times = i / window
                        bottom = times * window
                        top = (times + 1) * window - 1
                        if top >= len(sort_value):
                            top = len(sort_value) - 1
                        temp = '%s,%s' % (sort_value[bottom], sort_value[top])
                    node.append(temp)
                node.append('*')
                gh_tree.write(';'.join(node) + '\n')


def gen_informs_ICD9_tree():
    "disease tree is more complex, so we need treeseed to simplify definition"
    try:
        treefile = open('data/informs_ICD9.txt', 'rU')
        if __DEBUG:
            print "ICD09 full tree exists"
    except:
        if __DEBUG:
            print "generate ICD09 full tree"
        treeseed = open('data/informs_treeseed_ICD9.txt', 'rU')
        treefile = open('data/informs_ICD9.txt', 'w')
        for line in treeseed:
            # get low bound tree leaf
            title = ''
            temp = line.split(';')
            #separate special value
            if temp[0][0] != 'E' and temp[0][0] != 'V':
                now = string.atoi(temp[0])
                bottom = string.atoi(temp[1].split(',')[0])
                top = string.atoi(temp[1].split(',')[1])
                if now > bottom:
                    treefile.write(line)
                    continue
                index = line.find(';')
                while bottom <= top:
                    stemp = str(bottom)
                    if bottom < 100 and bottom >= 0:
                        stemp = '0' + stemp
                    if bottom < 10 and bottom >= 0:
                        stemp = '0' + stemp
                    treefile.write(stemp + line[index:])
                    bottom = bottom + 1
            else:
                title = temp[0][0]
                now = string.atoi(temp[0][1:])
                bottom = string.atoi(temp[1].split(',')[0][1:])
                top = string.atoi(temp[1].split(',')[1][1:])
                if now > bottom:
                    treefile.write(line)
                    continue
                index = line.find(';')
                while bottom <= top:
                    stemp = str(bottom)
                    if bottom < 10:
                        stemp = '0' + stemp
                    treefile.write(title + stemp + line[index:])
                    bottom = bottom + 1
        treeseed.close()
        treefile.close()


# generate tree from treeseed
def gen_informs_even_tree(fanout):
    """This generalization hierarchy is defined according to even fan-out (average distribution).
    For large dataset fanout = 5, for small dataset fanout = 4
    """
    try:
        treefile = open('data/informs_even.txt', 'rU')
        if __DEBUG:
            print "ICD09 even tree exists"
    except:
        if __DEBUG:
            print "generate ICD09 even tree"
        treeseed = open('data/informs_treeseed_even.txt', 'rU')
        treefile = open('data/informs_even.txt', 'w')
        for line in treeseed:
            line = line.strip()
            temp = line.split(',')
            prefix = ''
            str_len = len(temp[0])
            if temp[0][0] == 'E' or temp[0][0] == 'V':
                prefix = temp[0][0]
                temp[0] = temp[0][1:]
                temp[1] = temp[1][1:]
                str_len -= 1
            bottom = string.atoi(temp[0])
            top = string.atoi(temp[1])
            # get height
            temp = top - bottom
            height = 0
            flag = True
            while temp:
                temp /= fanout
                height += 1
            level_len = []
            tree = []
            for i in range(height):
                level_len = pow(fanout, i)
                level_split = []
                temp = bottom
                while temp <= top:
                    stemp = ''
                    if level_len == 1:
                        stemp = prefix + str(temp).rjust(str_len, '0')
                    elif temp + level_len - 1 > top:
                        stemp = prefix + str(temp).rjust(str_len, '0')
                        stemp += ',' + prefix + str(top).rjust(str_len, '0')
                    else:
                        stemp = prefix + str(temp).rjust(str_len, '0')
                        stemp += ',' + prefix + str(temp + level_len - 1).rjust(str_len, '0')
                    level_split.append(stemp)
                    temp += level_len
                tree.append(level_split)
            for i in range(len(tree[0])):
                w_line = ''
                temp = i
                for index in range(height):
                    w_line += tree[index][temp] + ';'
                    temp /= fanout
                w_line += line + ';*\n'
                treefile.write(w_line)
        treeseed.close()
    treefile.close()


def gen_informs_DOBYY_tree():
    "We define a birth year tree with min = 1900 and max = 2010, and coverage splited by 5, 10, 50 year"
    try:
        treefile = open('data/informs_DOBYY.txt', 'rU')
        if __DEBUG:
            print "DOBYY tree exists"
    except:
        if __DEBUG:
            print "generate DOBYY tree"
        treefile = open('data/informs_DOBYY.txt', 'w')
        for i in range(1900, 2011):
            i1 = i / 5
            i2 = i / 10
            i3 = i / 50
            i4 = i / 100
            temp = '%d;%d,%d;%d,%d;%d,%d;%d,%d;*\n' % (i, i1 * 5, i1 * 5 + 4, i2 * 10,
                                                       i2 * 10 + 9, i3 * 50, i3 * 50 + 49, i4 * 100, i4 * 100 + 99)
            treefile.write(temp)
    treefile.close()


# def gen_income_tree():
#     "We split this tree by i,100,1000,10000,*(5 layers) min = -40 000, max = 200 000"
#     treefile = open('data/informs_income.txt','w')
#     for i in range(-40000, 220001):
#         i0 = i / 10
#         i1 = i / 100
#         i2 = i / 1000
#         i3 = i / 10000
#         temp = '%d;%d,%d;%d,%d;%d,%d;%d,%d;*\n' % (i, i0*10, i0*10 +9, i1 * 100, i1 * 100 + 99, i2*1000,\
#          i2*1000 + 999, i3*10000, i3*10000 + 9999)
#         treefile.write(temp)
#     treefile.close()
#     return
# even fan out create a tree with less node. making the algorithm more effective
# meanwhile, generalization tree create by 10*n maybe more semantic
def gen_informs_even_income_tree(fanout):
    """This generalization hierarchy for BMS-WebView-2.dat is defined according to even fan-out (average distribution).
    For large dataset fanout = 5, for small dataset fanout = 4
    """
    need_static = False
    static_value = []
    try:
        income_tree = open('data/informs_income.txt', 'rU')
        if __DEBUG:
            print "even income tree exists"
    except:
        if __DEBUG:
            print "generate income tree"
        income_tree = open('data/informs_income.txt', 'w')
        try:
            static_file = open('data/informs_income_Static_value.pickle', 'rb')
            pickled = pickle.load(static_file)
            static_file.close()
        except:
            # index of income is 16
            pickled = pickle_static_income(16)
        static_value = pickled.sort_value
        height = int(math.ceil(math.log(len(static_value), fanout)))
        for i, temp in enumerate(static_value):
            node = []
            for h in range(height):
                if h == 0:
                    temp = '%s' % static_value[i]
                else:
                    window = fanout ** h
                    times = i / window
                    bottom = times * window
                    top = (times + 1) * window - 1
                    if top >= len(static_value):
                        top = len(static_value) - 1
                    temp = '%s,%s' % (static_value[bottom], static_value[top])
                node.append(temp)
            node.append('*')
            income_tree.write(';'.join(node) + '\n')
    income_tree.close()


def pickle_static_income(index):
    """pickle sorted values of datasets
    """
    userfile = open('data/demographics.csv', 'rU')
    need_static = False
    support = {}
    try:
        static_file = open('data/informs_income_Static_value.pickle', 'rb')
        # print "Income pickle Data exist..."
        result = pickle.load(static_file)
    except:
        need_static = True
        static_file = open('data/informs_income_Static_value.pickle', 'wb')
        print "Pickle Data..."
        for i, line in enumerate(userfile):
            line = line.strip()
            if i == 0:
                continue
            # ignore first line of csv
            row = line.split(',')
            try:
                support[row[index]] += 1
            except:
                support[row[index]] = 1
        sort_value = support.keys()
        sort_value.sort(cmp=cmp_str)
        result = NumRange(sort_value, support)
        pickle.dump(result, static_file)
    static_file.close()
    userfile.close()
    return result
