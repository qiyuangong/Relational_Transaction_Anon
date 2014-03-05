#!/usr/bin/env python
#coding=utf-8

# logic tree
class GenTree(object):

    """Class for Generalization hierarchies (Taxonomy Tree). 
    Store tree node in instances.
    self.value: node value
    self.level: tree level (top is 0)
    self.parent: ancestor node list
    self.child: successor node list
    self.cover: support 
    """

    def __init__(self, value = None, parent = None):
        self.value = ''
        self.level = 0
        self.support = 0
        self.parent = []
        self.child = []
        # range is for ARE, all possible values are in range
        self.cover = []
        if value != None:
            self.value = value
        if parent != None:
            self.parent = parent.parent[:]
            self.parent.insert(0, parent)
            parent.child.append(self)
            self.level = parent.level + 1

    def node(self, value):
        """Search tree with value, return GenTree node.
        If value == node value, return node. 
        If value != node value, recurse search.
        """
        if self.value == value:
            return self
        else:
            for tn in child:
                return child.node(value)

    def getsupport(self):
        """compute the tree's support, and store in their var support
        """
        if len(self.child) != 0:
            for t in self.child:
                self.support = self.support + t.getsupport()
                self.cover.extend(t.cover)
        else:
            self.support = 1
            self.cover.append(self.value)
        return self.support


class Cluster(object):

    """Cluster is for cluster based k-anonymity
    middle denote generlized value for one cluster
    self.member: record list in cluster
    self.middle: middle node in cluster
    """
    
    def __init__(self, member, middle = ['*']):
        self.iloss = 0.0
        self.member = member
        self.middle = middle[:]

    def merge_group(self, group, middle):
        """merge group into self_gourp and delete group elements.
        update self.middle with middle
        """
        while group.member:
            temp = group.member.pop()
            self.member.append(temp)
        self.middle = middle[:]

    def merge_record(self, record, middle):
        """merge record into hostgourp. update self.middle with middle
        """
        self.member.append(record)
        self.middle = middle[:]


if __name__ == '__main__':

    print 'OK'
