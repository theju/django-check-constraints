# Dummy models.py file to allow for tests to run
from django.db import models

class CCTestModel(models.Model):
    name = models.CharField(max_length=10)
    age  = models.IntegerField()
    gender = models.CharField(max_length=10)
    price = models.PositiveIntegerField()
    discount = models.PositiveIntegerField()
    mfg_date = models.DateField()

    class Meta:
        constraints = ()
