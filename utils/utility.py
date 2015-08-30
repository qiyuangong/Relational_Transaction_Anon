"""
shared functions
"""

#!/usr/bin/env python
#coding=utf-8


def list_to_str(value_list, cmpfun=cmp, sep=';'):
    """covert sorted str list (sorted by cmpfun) to str
    value (splited by sep). This fuction is value safe, which means
    value_list will not be changed.
    """
    temp = value_list[:]
    temp.sort(cmp=cmpfun)
    return sep.join(temp)
