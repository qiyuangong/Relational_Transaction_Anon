"""
shared functions
"""

#!/usr/bin/env python
#coding=utf-8


def cmp_str(element1, element2):
    """
    compare number in str format correctley
    """
    try:
        return cmp(float(element1), float(element2))
    except ValueError:
        return cmp(element1, element2)


def list_to_str(value_list, cmpfun=cmp, sep=';'):
    """covert sorted str list (sorted by cmpfun) to str
    value (splited by sep). This fuction is value safe, which means
    value_list will not be changed.
    """
    temp = value_list[:]
    temp.sort(cmp=cmpfun)
    return sep.join(temp)
