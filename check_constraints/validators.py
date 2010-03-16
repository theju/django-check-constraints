from django.core import validators
from django.utils.translation import ugettext_lazy as _

__all__ = ['GTValidator', 'LTValidator', 'GTEValidator', 'LTEValidator',
           'NEQValidator', 'EQValidator', 'ListValidator', 'NotInListValidator',
           'RangeValidator', 'LikeValidator', 'NotLikeValidator']

class GTValidator(validators.MinValueValidator):
    message = _(u'Ensure this value is greater than %(limit_value)s.')

class LTValidator(validators.MaxValueValidator):
    message = _(u'Ensure this value is less than %(limit_value)s.')

class GTEValidator(validators.MinValueValidator):
    compare = lambda self, a, b: a >= b
    message = _(u'Ensure this value is less than or equal to %(limit_value)s.')
    
class LTEValidator(validators.MaxValueValidator):
    compare = lambda self, a, b: a <= b
    message = _(u'Ensure this value is greater than or equal to %(limit_value)s.')
    
class NEQValidator(validators.BaseValidator):
    compare = lambda self, a, b: a != b
    message = _(u'Ensure this value is not equal to %(limit_value)s.')

class EQValidator(validators.BaseValidator):
    compare = lambda self, a, b: a == b
    message = _(u'Ensure this value is not equal to %(limit_value)s.')

class ListValidator(validators.BaseValidator):
    compare = lambda self, a, b: a in b
    message = _(u'Ensure this value is in %(limit_value)s')

class NotInListValidator(validators.BaseValidator):
    compare = lambda self, a, b: a not in b
    message = _(u'Ensure this value is not in %(limit_value)s')

class RangeValidator(validators.BaseValidator):
    compare = lambda self, a, b, c: a > b and a < c
    message = _(u'Ensure this value is in range %(limit_value)s')

class LikeValidator(validators.RegexValidator):
    pass

class UnLikeValidator(validators.RegexValidator):
    def __call__(self, value):
        if self.regex.search(smart_unicode(value)):
            raise ValidationError(self.message, code=self.code)
