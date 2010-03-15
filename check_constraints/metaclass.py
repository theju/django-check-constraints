from django.db.models.base import ModelBase

class CheckConstraintMetaClass(ModelBase):
    def __new__(cls, name, bases, attrs):
        model = super(CheckConstraintMetaClass, cls).__new__(cls, name, bases, attrs)
        for (constraint_name, constraint_obj) in model._meta.constraints:
            constraint_obj.validate(model._meta)
        return model

