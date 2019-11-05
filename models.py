__author__ = 'Enrique Coslado'
__version__ = "0.0.1"

import copy
import pymongo
import fields

import settings

client = pymongo.MongoClient(host=settings.MONGODM["HOST"], port=settings.MONGODM["PORT"])
database = client[settings.MONGODM["NAME"]]


def import_module(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


class ModelMeta(type):
    """
    This class is responsible of PyMongODM Models behaviour.
    """

    def __init__(cls, name, bases, attrs):

        super(ModelMeta, cls).__init__(name, bases, attrs)

        parents = [base for base in bases if isinstance(base, ModelMeta)]
        if not parents:
            return

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

        for name, value in attrs.items():
            if isinstance(value, fields.Field):
                base_fields.pop(name, None)
                value.field_name = name
                value.model_class = cls
                cls_fields.append(value)

        cls._fields = list(base_fields.values()) + cls_fields
        cls.objects = database[cls.__name__.lower()]


class Model(object, metaclass=ModelMeta):
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
                        self.setattr(f.field_name, kwargs[f.field_name]))

            except KeyError:
                pass

        if "_id" in kwargs:
            self._id = kwargs["_id"]

    def serialize(self):
        doc = dict()
        doc["__type__"] = {"class": self.__class__.__name__, "module": self.__module__}
        for field in self._fields:
            attr = getattr(self, field.field_name)
            if attr:
                doc[field.field_name] = attr.serialize()
        return doc

    def deserialize(self, dictionary):
        return self.__deserialize(dictionary).value

    def __deserialize(self, dictionary):
        cls = None
        if '__type__' in dictionary:
            mod_name = dictionary['__type__']['module']
            cls_name = dictionary['__type__']['class']
            mod = import_module(mod_name)
            cls = getattr(mod, cls_name)
            del dictionary['__type__']

        deserialized = dict()
        for key, value in dictionary.items():
            if type(value) == dict:
                deserialized[key] = fields.ObjectField(self.deserialize(value))
            elif type(value) == list:
                deserialized[key] = fields.ListField([self.deserialize(v) for v in value])
            elif type(value) == int:
                deserialized[key] = fields.IntegerField(value)
            elif type(value) == float:
                deserialized[key] = fields.FloatField(value)
            else:
                deserialized[key] = fields.StringField(value)
        if cls:
            return fields.ObjectField(cls(**deserialized))
        else:
            return deserialized

    def getattr(self, attr):
        field = getattr(self, attr)
        #return field.serialize()
        return field.value

    def setattr(self, attr, value):
        if isinstance(value, Model):
            value = value.serialize()
        field = fields.make_field(value)
        setattr(self, attr, field)
        return self

    def save(self):
        document = self.serialize()
        self.__class__.objects.insert(document)
        return self

    def update(self):
        if self._id:
            self.__class__.objects.update({"_id": self._id}, self.serialize())
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
