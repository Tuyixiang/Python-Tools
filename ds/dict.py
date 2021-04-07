"""字典类"""


class Merge(dict):
    """将同样键的值用某种 collection 来保存"""

    def __init__(self, key_iter, value_iter=None, ctype=list):
        """
        构建方法：
            Merge({1: [2, 3]}) => {1: [2, 3]}

            Merge([(1, 2), (1, 3)]) => {1: [2, 3]}

            Merge([1, 1], [2, 3]) => {1: [2, 3]}

            Merge([1, 1], [2, 3], ctype=set) => {1: {2, 3}}
        """
        data = {}

        if value_iter is None and isinstance(key_iter, dict):
            data = key_iter
        else:
            if value_iter is None:
                kv_iter = key_iter
            else:
                kv_iter = zip(key_iter, value_iter)

            for k, v in kv_iter:
                if k in data:
                    data[k].append(v)
                else:
                    data[k] = [v]

        data = {k: ctype(v) for k, v in data.items()}

        super().__init__(data)
        self.ctype = ctype

    def __add__(self, other):
        if not hasattr(self.ctype, '__add__') and not issubclass(self.ctype, set):
            raise TypeError(
                "collection type '%s' does not support +" % self.ctype)
        if isinstance(other, dict):
            self_keys = set(self)
            other_keys = set(other)
            result = {}

            for key in self_keys - other_keys:
                a = result[key] = self[key]
                assert isinstance(a, self.ctype)
            for key in other_keys - self_keys:
                a = result[key] = other[key]
                assert isinstance(a, self.ctype)
            for key in self_keys & other_keys:
                assert isinstance(self[key], self.ctype) and isinstance(
                    other[key], self.ctype)
                if issubclass(self.ctype, set):
                    result[key] = self[key] | other[key]
                else:
                    result[key] = self[key] + other[key]
            return Merge(result, ctype=self.ctype)
        else:
            raise TypeError(
                "unsupported operand type(s) for +: '%s' and '%s'" % (type(self), type(other)))

    def __sub__(self, other):
        if not hasattr(self.ctype, '__sub__'):
            raise TypeError(
                "collection type '%s' does not support -" % self.ctype)
        if isinstance(other, dict):
            self_keys = set(self)
            other_keys = set(other)
            result = {}

            for key in self_keys - other_keys:
                a = result[key] = self[key]
                assert isinstance(a, self.ctype)
            for key in self_keys & other_keys:
                assert isinstance(self[key], self.ctype) and isinstance(
                    other[key], self.ctype)
                result[key] = self[key] - other[key]
            return Merge(result, ctype=self.ctype)
        else:
            raise TypeError(
                "unsupported operand type(s) for -: '%s' and '%s'" % (type(self), type(other)))
