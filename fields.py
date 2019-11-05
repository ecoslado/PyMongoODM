__author__ = 'Enrique Coslado'


def make_field(value):
    if isinstance(value, Field):
        return value

    elif type(value) == list:
        return ListField([make_field(item) for item in value])

    elif type(value) == dict and "type" in value:
        module_name = value["type"]["module"]
        module = __import__(module_name)
        class_name = value["type"]["class"]
        class_ = getattr(module, class_name)
        return ObjectField(class_(**value))

    elif type(value) == float:
        return FloatField(value)

    elif type(value) == int:
        return IntegerField(value)

    else:
        return StringField(value)


class Field(object):
    value = ""
    required = False


    def __init__(self, **kwargs):
        try:
            self.value = kwargs["value"]
            self.required = kwargs["required"]

        except KeyError:
            pass

    def serialize(self):
        return self.value


class IntegerField(Field):
    value = 0
    required = False

    def __init__(self, value=0, **kwargs):
        try:
            self.value = int(value)
            self.required = kwargs["required"]

        except KeyError:
            pass

    def set(self, value):
        self.value = int(value)
        return self


class FloatField(Field):
    value = .0
    required = False

    def __init__(self, value=.0, **kwargs):
        try:
            self.value = float(value)
            self.required = kwargs["required"]

        except KeyError:
            pass

    def set(self, value):
        self.value = float(value)
        return self


class StringField(Field):
    value = ""
    required = False

    def __init__(self, value="", **kwargs):
        try:
            self.value = value
            self.required = kwargs["required"]

        except KeyError:
            pass

    def set(self, value):
        self.value = value
        return self


class ObjectField(Field):
    value = None
    cls = None
    required = False

    def __init__(self, value=None, **kwargs):
        if "required" in kwargs:
            self.required = kwargs["required"]
            del kwargs["required"]
        self.cls = value.__class__
        self.value = value



    def set(self, value):
        if self.cls and isinstance(value, self.cls):
            self.value = value
            return self
        elif not self.cls:
            self.cls = value.__class__
            self.value = value
            return self
        else:
            raise Exception("Object field can't change class.")

    def serialize(self):
        if self.value:
            return self.value.serialize()


class ListField(Field):
    value = []
    required = False

    def __init__(self, value=None, **kwargs):
        value = value or list()
        try:
            if type(value) == list and all(isinstance(obj, Field) for obj in value):
                self.value = value
                self.required = kwargs["required"]

            else:
                raise Exception("ListField instantiation error. List of fields required.")

        except KeyError:
            pass

    def set(self, value):
        if type(value) == list:
            self.value = [make_field(elem) for elem in value]
        else:
            self.value = [make_field(value)]
        return self

    def serialize(self):
        return [field.serialize() for field in self.value]