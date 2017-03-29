# coding: utf-8


class DictPlus(dict):
    def __add__(self, other):
        self.update(other)
        return self
