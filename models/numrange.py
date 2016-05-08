"""
class from numeric attributes
"""

#!/usr/bin/env python
#coding=utf-8


class NumRange(object):

    """Class for Generalization hierarchies (Taxonomy Tree).
    Store tree node in instances.
    self.value: node value
    self.level: tree level (top is 0)
    self.support: support
    self.parent: ancestor node list
    self.child: direct successor node list
    self.cover: leaves nodes of current node
    """

    def __init__(self, sort_value, support):
        self.sort_value = list(sort_value)
        self.support = support.copy()
        self.range = float(sort_value[-1]) - float(sort_value[0])
        self.dict = {}
        for i, v in enumerate(sort_value):
            self.dict[v] = i
        self.value = sort_value[0] + ',' + sort_value[-1]

    def __len__(self):
        return self.range
