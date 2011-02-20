#!/usr/bin/env python

import types
import string
from operator import itemgetter

class Enum(object):
    def __init__(self,cls,*args,**kwargs):
        self.dict_=dict()
        if isinstance(cls,types.StringType):
            name=cls
            bases=args[0]
            dict_=args[1]
            base=args[0][0]
            di=args[1]
            for key,value in di.items():
                if not (key.startswith('__') and key.endswith('__')):
                    self.dict_[key]=EnumLiteral(name,key,value)
        else:
            name=cls.__name__
            bases=cls.__bases__
            di=dict([x for x in cls.__dict__.items() if not (x[0].startswith('__') and x[0].endswith('__'))])
            for key,value in di.items():
                self.dict_[key]=EnumLiteral(name,key,value)
        self.__name__=name
        self.__bases__=bases

    def __repr__(self):
        s=self.__name__
        if self.__bases__:
            s=s + '(' + string.join(map(lambda x: x.__name__,self.__bases__), ", ") + ')'
        if self.__dict__:
            list_=[]
            for key,value in sorted(self.dict_.items(),key=lambda x: x[1]):
                list_.append("%s: %s" % (key,int(value)))
            s="%s: {%s}" % (s,string.join(list_,", "))
        return s

    def __getattr__(self, name):
        if name == '__members__':
            return self.dict_.keys()
        try:
            return self.dict_[name]
        except KeyError:
            for base in self.__bases__:
                try:
                    return getattr(base,name)
                except AttributeError:
                    continue
        raise AttributeError, name

    def __call__(self,value):
        "Factory method for creating 'EnumLiteral's."
        if isinstance(value,types.StringType):
            return self.dict_[value]
        elif isinstance(value,types.IntType):
            lit=filter(lambda x: int(x)==value,self.dict_.values())
            if lit==[]:
                raise AttributeError()
            return lit[0]
        else:
            raise TypeError()


class EnumLiteral(object):
    def __init__(self,cls,name,value):
        self.cls=cls
        self.name=name
        self.value=value

    def __int__(self):
        return self.value

    def __repr__(self):
        return "EnumLiteral(%r, %r, %r)" % (self.cls,self.name,self.value)

    def __str__(self):
        return "%s.%s" % (self.cls,self.name)

    def __cmp__(self, other):
        return cmp(self.value,int(other))
