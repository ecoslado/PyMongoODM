__author__ = 'Enrique Coslado'
__version__ = "0.0.1"


import copy
import pymongo
import fields

from django.conf import settings

client = pymongo.MongoClient(host=settings.MONGODM["HOST"], port=settings.MONGODM["PORT"])
database = client[settings.MONGODM["DATABASE"]]



class ModelMeta(type):
    """
    This class is responsible of PyMongODM Models behaviour.
    """

    def __new__(mcs, name, bases, attrs):
        cls = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)

        parents = [base for base in bases if isinstance(base, ModelMeta)]
        if not parents:
            return cls

        base_fields = dict()

        for base in bases:
            if not isinstance(base, ModelMeta):
                continue

            for field in base._fields:
                if field.field_name not in base_fields:
                    field = copy.copy(field)
                    field.model_class = cls
                    base_fields[field.field_name] = field

        cls_fields = []

        for name, value in attrs.iteritems():
            if isinstance(value, fields.Field):
                base_fields.pop(name, None)
                value.field_name = name
                value.model_class = cls
                cls_fields.append(value)

        cls._fields = base_fields.values() + cls_fields

        cls.objects = database[cls.__name__.lower()]

        return cls


class Model(object):
    """
    Base class for every model you can define.
    Example:

    class Person(pymongodm.Model):
        name = fields.String()
        age = fields.Integer()
    """

    __metaclass__ = ModelMeta
    _fields = []

    def __init__(self, **kwargs):
        for f in self._fields:
            try:
                setattr(self,
                        f.field_name,
                        fields.make_field(kwargs[f.field_name]))
                setattr(self,
                        "get_%s" % f.field_name,
                        self.getattr(f.field_name))
                setattr(self,
                        "set_%s" % f.field_name,
                        self.setattr(f.field_name))

            except KeyError:
                pass

        if "_id" in kwargs:
            self._id = kwargs["_id"]

    def obj_to_doc(self):
        doc = dict()
        doc["type"] = {"class": self.__class__.__name__, "module": self.__module__}
        for field in self._fields:
            attr = getattr(self, field.field_name)
            if attr:
                doc[field.field_name] = attr.render()
        return doc

    def getattr(self, attr):
        field = getattr(self, attr)
        return field.render()

    def setattr(self, attr, value):
        if isinstance(value, Model):
            value = value.obj_to_doc()
        field = fields.make_field(value)
        setattr(self, attr, field)
        return self

    def save(self):
        document = self.obj_to_doc()
        self.__class__.objects.insert(document)
        return self

    def update(self):
        if self._id:
            self.__class__.objects.update({"_id": self._id}, self.obj_to_doc())
        return self

    def delete(self):
        if self._id:
            self.__class__.objects.remove({"_id": self._id})

    @classmethod
    def all_docs(cls, limit=0, skip=0):
        return cls.objects.find().limit(limit).skip(skip)

    @classmethod
    def filter_docs(cls, **kwargs):
        return cls.objects.find(kwargs)

    @classmethod
    def get_doc(cls, **kwargs):
        return cls.objects.find_one(kwargs)

    @classmethod
    def all(cls, limit=0, skip=0):
        return [cls(**doc) for doc in cls.all_docs(limit, skip)]

    @classmethod
    def filter(cls, **kwargs):
        return [cls(**doc) for doc in cls.filter_docs(**kwargs)]

    @classmethod
    def get(cls, **kwargs):
        return cls(**cls.get_doc(**kwargs))
