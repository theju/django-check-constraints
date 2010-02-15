"""
=========================
Django Check Constraints
=========================

:Info: See <http://code.google.com/p/django-check-constraints/>.
:Author: Thejaswi Puthraya <thejaswi.puthraya@gmail.com>
:Date: $Date: 2007-09-01 $
:Revision: $Revision: 51 $
:Description: Implementing Range and Value based constraints for Django.
This is the Django Check Constraint Module written by Thejaswi Puthraya
for the Google Summer of Code 2007 mentored by Simon Blanchard.

>>> c = Check()
Traceback (most recent call last):
...
NoKwargsError: No Keyword arguments present.
>>> c = Check(price_gte = 100)
Traceback (most recent call last):
...
SyntaxError: Invalid Syntax.Keyword Arguments must contain "__"
>>>
>>>
>>> c = Check(price__gte = 10)
>>> c.check_name = u"check_price"
>>> unicode(c)
u'CONSTRAINT "check_price" CHECK ("price" >= 10)'
>>>
>>>
>>> c = Check(price__gte = 0) & Check(price__gte = 'discount')
>>> c.is_cascaded
True
>>> c.sql_data
[(u'price', u'>=', 0, u' AND'), (u'price', u'>=', 'discount', u'')]
>>> c.sql_tuple
(u'price', u'>=', 0, u' AND')
>>> c.check_name = "check_name_price"
>>> unicode(c)
u'CONSTRAINT "check_name_price" CHECK ( ("price" >= 0) AND \
("price" >= discount) )'
>>>
>>>
>>> c = Check(tax_percent__gte = 10) & Check(vat_percent__lte = 20) \
| Check(price__gte=0)
>>> c.check_name = "check_tax"
>>> c.sql_data
[(u'tax_percent', u'>=', 10, u' AND'), (u'vat_percent', u'<=', 20, u' OR'), \
(u'price', u'>=', 0, u'')]
>>> unicode(c)
u'CONSTRAINT "check_tax" CHECK ( ("tax_percent" >= 10) AND \
("vat_percent" <= 20) OR ("price" >= 0) )'
>>> c.is_check_field()
True
>>>
>>>
>>> c = Check(tax_percent__gte = 10) & \
Check(vat_percent__lte = 20) | Check(price__gte=0,price__lte=100)
>>> c.check_name = "check_price"
>>> c.sql_data
[(u'tax_percent', u'>=', 10, u' AND'), (u'vat_percent', u'<=', 20, u' OR'), \
(u'price', u'<=', 100, u' AND'), (u'price', u'>=', 0, u'')]
>>> unicode(c)
u'CONSTRAINT "check_price" CHECK ( ("tax_percent" >= 10) AND \
("vat_percent" <= 20) OR ("price" <= 100) AND ("price" >= 0) )'
"""

__version__ = "$Revision: 51$"
# $Source$

from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext
from django.core.management import color


class NonExistentFieldError(Exception):
    """
    Error raised when field does not exist.
    """
    pass

class NotSupportedError(Exception):
    """
    Error raised when features are not supported
    by database.
    """
    pass

class NoKwargsError(Exception):
    """
    Error raised when no keyword arguments are passed
    to Check Object.
    """
    pass

class Check(object):
    """
    Class Definition of a Check Object.
    """

    def __init__(self,**kwargs):
        """
        The constructor for the Check Field.
        Called whenever the object is initialized.
        """
        # First check if the databases support check constraints.
        # Currently supporting Postgresql, Sqlite and Oracle.
        # Untested on Firebird.
        if not settings.DATABASE_ENGINE in (u'postgresql_psycopg2',
                                            u'postgresql',\
                                            u'sqlite3', u'oracle'):
            raise NotSupportedError(color.color_style().ERROR(ugettext(\
                u"%s does not support Check Constraints natively."\
                %settings.DATABASE_ENGINE)))
        # A name to identify every Check object.
        # Initially it is '' (empty string).
        # The name is set in management.py.
        self.check_name = u''
        # Cascade Condition by default is '' (empty string)
        self.cascade_condition = u''
        # Initially the check object is not cascaded.
        self.is_cascaded = False
        # The container (list) for storing all the check conditions.
        self.sql_data = []
        # Supported Check Conditions.
        LOOKUP_TABLE = {u'gte':u'>=', u'lte':u'<=', u'gt':u'>', \
                        u'lt':u'<', u'neq':u'<>', u'eq':u'=', \
                        u'in':u'in', u'not_in': u'not in',u'like': u'like', \
                        u'unlike':u'not like', u'between':u'between',}
        # Checking if there are keywords present.
        if not len(kwargs) >= 1:
            raise NoKwargsError(color.color_style().ERROR(ugettext(\
                u"No Keyword arguments present.")))
        for keywords in kwargs.items():
            # Checking for "__" in the Keyword Arguments.
            if keywords[0].__contains__(u"__"):
                # The left-side argument must be the field and the
                # right-side the condition.
                # Example: price__gte. price is the checked_field and
                # gte is the check condition.
                try:
                    self.checked_field,self.check_condition_ul,\
                           self.upper_or_lower = keywords[0].split(u"__")
                    if not self.upper_or_lower in ("upper","lower"):
                        raise SyntaxError(color.color_style().\
                                          ERROR(\
                            ugettext(\
                            u'Was expecting upper or lower keyword argument')))
                except ValueError:
                    self.checked_field,self.check_condition_ul = keywords[0]\
                                                                 .split(u"__")
                try:
                    # Get the equivalent symbol from the lookup table.
                    # Example: gte is converted to >=
                    self.check_condition = LOOKUP_TABLE[\
                        self.check_condition_ul]
                except KeyError,e:
                    # If check condition not in LOOKUP_TABLE, then raise Error.
                    raise KeyError(color.color_style().ERROR(ugettext(\
                        u'%s not found in Lookup Table' %(e.message))))
                # Data to be validated. This is the Keyword Argument Value.
                self.validate_data = keywords[1]
                # Bind each check condition in a tuple.
                # [(checked_field,check_condition,validate_data,\
                # cascade_condition),]
                self.sql_tuple = tuple((self.checked_field, \
                                        self.check_condition, \
                                        self.validate_data, \
                                        self.cascade_condition))
                self.sql_data.append(self.sql_tuple)
                # If more than one keyword argument is found in the
                # Check Object, then cascade the arguments.
                # Example: Check(price__gte = 100,discount__lte = 10)
                if len(self.sql_data) > 1:
                    self.is_cascaded = True
                    self.cascade_condition = u' AND'
                    for i in range(len(self.sql_data)-1):
                        self.sql_tuple = tuple((self.sql_data[i][0], \
                                                self.sql_data[i][1], \
                                                self.sql_data[i][2], \
                                                self.cascade_condition))
                        self.sql_data[i] = self.sql_tuple
                # Once the keyword argument is processed.
                # It is removed from the Keyword Argument Dictionary.
                kwargs.pop(keywords[0])
            else:
                # If __ (two underscores) are not found,
                # the syntax is wrong, an error is raised.
                raise SyntaxError(color.color_style().ERROR(ugettext(\
                u'Invalid Syntax.Keyword Arguments must contain \"__\"')))

    def __and__(self,other):
        """
        Used to handle cascaded AND Check Objects.
        """
        self.is_cascaded = True
        self.cascade_condition = u' AND'
        self.sql_tuple = tuple((self.sql_data[len(self.sql_data)-1][0], \
                                self.sql_data[len(self.sql_data)-1][1], \
                                self.sql_data[len(self.sql_data)-1][2], \
                                self.cascade_condition))
        self.sql_data[len(self.sql_data)-1] = self.sql_tuple
        self.sql_data += other.sql_data
        return self

    def __or__(self,other):
        """
        Used to handle cascaded OR Check Objects.
        """
        self.is_cascaded = True
        self.cascade_condition = u' OR'
        self.sql_tuple = tuple((self.sql_data[len(self.sql_data)-1][0], \
                                self.sql_data[len(self.sql_data)-1][1], \
                                self.sql_data[len(self.sql_data)-1][2], \
                                self.cascade_condition))
        self.sql_data[len(self.sql_data)-1] = self.sql_tuple
        self.sql_data += other.sql_data
        return self

    def is_check_field(self):
        """
        Method used to identify Check Fields.
        This method might not be required.
        """
        return True

    def validate(self,opts):
        """
        Validates the Check Object.
        """
        from datetime import date,datetime,time

        # Contains all the field attribute names defined in the models.
        all_fields = []

        for num_of_fields in range(len(opts.fields)):
            # Fetch all attribute names of fields.
            all_fields.append(opts.fields[num_of_fields].get_attname())

        for check_arg in range(len(self.sql_data)):
            if_field_exists = self.sql_data[check_arg][0]
            if_data_is_valid = self.sql_data[check_arg][2]
            if not all_fields.__contains__(if_field_exists):
                # Check if checked_field exists among fields.
                raise NonExistentFieldError(color.color_style().ERROR(\
                    ugettext(u"%s Field not found" %(if_field_exists))))
            if isinstance(if_data_is_valid,str):
                # There are two cases. One if the check condition is 'like'.
                # Two if the string is a field as given below:
                # If data is a string then check if it exists in the fields.
                # Example: Check(price__lte = 'discount')
                if self.sql_data[check_arg][1] in (u'like',u'not like'):
                    temp_var = list(self.sql_data[check_arg])
                    replaced_text = self.sql_data[check_arg][2]
                    replaced_text = replaced_text.replace("*","%%")
                    replaced_text = replaced_text.replace(".","_")
                    temp_var[2] = smart_unicode(replaced_text.__repr__())
                    self.sql_data[check_arg] = tuple(temp_var)
                else:
                    if not all_fields.__contains__(if_data_is_valid):
                        raise NonExistentFieldError(\
                            color.color_style().ERROR(ugettext(\
                            u"%s Field not found" %(if_data_is_valid))))
            # If data is an instance of Integer then convert to string.
            elif isinstance(if_data_is_valid,int):
                pass
            # If data is an instance of tuple then has
            # to be part of 'in' check condition.
            elif isinstance(if_data_is_valid,tuple):
                if not self.sql_data[check_arg][1] in (u'in',u'not in'):
                    raise SyntaxError(color.color_style().ERROR(ugettext(\
                        u"Was expecting the 'in'/'not in' Check Condition.")))
                temp_var = list(self.sql_data[check_arg])
                temp_data_list = list(self.sql_data[check_arg][2])
                for i in range(len(temp_var[2])):
                    if isinstance(temp_data_list[i],(date,datetime)):
                        if not hasattr(temp_data_list[i],"time"):
                            temp_data_list[i] = self.adjust_date(\
                                temp_data_list[i])
                        else:
                            temp_data_list[i] = self.adjust_datetime(\
                                temp_data_list[i])
                    elif isinstance(temp_data_list[i],time):
                        temp_data_list[i] = self.adjust_time(\
                            temp_data_list[i])
                    else:
                        temp_data_list[i] = temp_data_list[i].__repr__()
                temp_var[2] = u"("+smart_unicode(",".join(temp_data_list))+u")"
                self.sql_data[check_arg] = tuple(temp_var)
            # If data is an instance of list then has to be
            # part of 'between' check condition.
            elif isinstance(if_data_is_valid,list):
                if not self.sql_data[check_arg][1] == u'between':
                    raise SyntaxError(color.color_style().ERROR(ugettext(\
                        u"Was expecting the 'between' Check Condition.")))
                else:
                    # If length of list is not two then raise exception.
                    if not len(self.sql_data[check_arg][2]) == 2:
                        raise SyntaxError(color.color_style().ERROR(ugettext(\
                            u"'Between' data must have a length two.")))
                    # If everything is fine....
                    else:
                        temp_var = list(self.sql_data[check_arg])
                        between_check_sql_data = u""
                        for i in range(2):
                            if isinstance(temp_var[2][i],date):
                                between_check_sql_data += \
                                self.adjust_date(self.sql_data[check_arg]\
                                                 [2][i])
                            elif isinstance(temp_var[2][i],str):
                                if not all_fields.__contains__(temp_var[2][i]):
                                    raise NonExistentFieldError(\
                                        color.color_style().ERROR(\
                                        ugettext(\
                                        u"%s Field not found."
                                        %(temp_var[2][i]))))
                                else:
                                    between_check_sql_data += \
                                    self.sql_data[check_arg][2][i]
                            elif isinstance(temp_var[2][i],int):
                                between_check_sql_data += \
                                smart_unicode(self.sql_data[check_arg]\
                                              [2][i].__repr__())
                            else:
                                raise SyntaxError(\
                                    color.color_style().ERROR(ugettext(\
                                    u"Does not support the datatype.")))
                            if i == 0:
                                between_check_sql_data += u" AND "
                        temp_var[2] = between_check_sql_data
                        self.sql_data[check_arg] = tuple(temp_var)
            # If data is an instance of date then get its
            # actual representation.
            elif isinstance(if_data_is_valid,(date,datetime)):
                # If the data is a date field then convert to
                # a list to make use of list properties.
                # Because tuple does not support assignment.
                temp_var = list(self.sql_data[check_arg])
                # Since datetime is derived from date,
                # isinstance(if_data_is_valid,date) will return
                # True for a datetime also. So we have to check
                # up whether the if_data_is_valid is a date
                # or a datetime object.
                # Hint: Only Datetime objects have the time method.
                if not hasattr(if_data_is_valid,"time"):
                    temp_var[2] = self.adjust_date(if_data_is_valid)
                else:
                    # Now for datetime field SQL representation.
                    temp_var[2] = self.adjust_datetime(if_data_is_valid)
                self.sql_data[check_arg] = tuple(temp_var)
            # If data is an instance of time then convert
            # to equivalent SQL representation.
            elif isinstance(if_data_is_valid,time):
                temp_var = list(self.sql_data[check_arg])
                temp_var[2] = self.adjust_time(if_data_is_valid)
                self.sql_data[check_arg] = tuple(temp_var)

        return 0

    def adjust_date(self,date_field):
        """
        Method to adjust date field according to database specs.
        """
        if settings.DATABASE_ENGINE in (u'postgresql_psycopg2',u'postgresql'):
            temp_date = smart_unicode(date_field.strftime("date '%Y-%m-%d'"))
        elif settings.DATABASE_ENGINE == u'sqlite3':
            temp_date = smart_unicode(date_field.strftime("%Y-%m-%d"))
        elif settings.DATABASE_ENGINE == u'oracle':
            temp_date =smart_unicode(date_field.strftime("'%d-%b-%Y'").upper())
        else:
            raise NotSupportedError(color.color_style().ERROR(ugettext(\
                u"Your database is currently not supported.")))

        return temp_date

    def adjust_datetime(self,datetime_field):
        """
        Method to adjust datetime field according to database specs.
        """
        if settings.DATABASE_ENGINE in (u'postgresql_psycopg2', u'postgresql'):
            temp_datetime = smart_unicode(datetime_field.\
                                          strftime(\
                "timestamp '%Y-%m-%d %H:%M:%S'"))
        elif settings.DATABASE_ENGINE == u'sqlite3':
            temp_datetime = smart_unicode(datetime_field.\
                                          strftime("%Y-%m-%d %H:%M:%S"))
        elif settings.DATABASE_ENGINE == u'oracle':
            temp_datetime = smart_unicode(datetime_field.strftime(\
                "'%d-%b-%Y %H:%M:%S'").upper())
        else:
            raise NotSupportedError(color.color_style().ERROR(ugettext(\
                u"Your database is currently not supported.")))

        return temp_datetime

    def adjust_time(self,time_field):
        """
        Method to adjust time field according to database specs.
        """
        if settings.DATABASE_ENGINE in (u'postgresql_psycopg2',u'postgresql'):
            temp_time = smart_unicode(time_field.strftime("time '%H:%M:%S'"))
        elif settings.DATABASE_ENGINE == u'sqlite3':
            temp_time = smart_unicode(time_field.strftime("%H:%M:%S"))
        elif settings.DATABASE_ENGINE == u'oracle':
            temp_time = smart_unicode(time_field.strftime("'%H:%M:%S'"))
        else:
            raise NotSupportedError(color.color_style().ERROR(ugettext(\
                u"Your database is currently not supported.")))

        return temp_time

    def __unicode__(self):
        """
        All SQL statements are generated by this method.
        """
        from django.db import connection

        if connection.features.uses_case_insensitive_names:
            # If the database uses upper case like Oracle then
            # convert the data to uppercase.
            for check_arg in range(len(self.sql_data)):
                self.check_name = self.check_name.upper()
                temp_var = list(self.sql_data[check_arg])
                temp_var[0] = self.sql_data[check_arg][0].upper()
                temp_var[1] = self.sql_data[check_arg][1].upper()
                if isinstance(self.sql_data[check_arg][2],str):
                    # Make the check_data uppercase only if is a string.
                    temp_var[2] = self.sql_data[check_arg][2].upper()
                self.sql_data[check_arg] = tuple(temp_var)

        constraints_output = []
        constraints_output.append(u'CONSTRAINT' + \
                                  u" \"" + smart_unicode(self.check_name) + \
                                  u"\" " + u'CHECK')

        try:
            if not self.is_cascaded:
                if not hasattr(self,"upper_or_lower"):
                    # If only one argument is present or is not cascaded.
                    constraints_output.append(u"(" + u"\"" + smart_unicode(\
                        self.sql_data[0][0]) + u"\" " + \
                        smart_unicode(self.sql_data[0][1]) + u" " + \
                        smart_unicode(self.sql_data[0][2]) + u")")
                else:
                    constraints_output.append(u"(" + self.upper_or_lower +
                        u"(" + smart_unicode(self.sql_data[0][0]) + u") "+ \
                        smart_unicode(self.sql_data[0][1]) + u" " + \
                        smart_unicode(self.sql_data[0][2]) + u")")
            else:
                # When Cascaded ie '&' or '|'
                constraints_output.append(u"(")
                for check_arg in range(len(self.sql_data)):
                    if not hasattr(self,"upper_or_lower"):
                        constraints_output.append(u"(" + u"\"" + \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][0]) \
                                                  + u"\" "+ \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][1])
                                                  + u" " + \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][2]) \
                                                  + u")" + \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][3]))
                    else:
                        constraints_output.append(u"(" + self.upper_or_lower \
                                                  + u"(" + \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][0]) \
                                                  + u") "+ \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][1])
                                                  + u" " + \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][2]) \
                                                  + u")" + \
                                                  smart_unicode(self.sql_data[\
                                                  check_arg][3]))
                constraints_output.append(u")")
        except IndexError,e:
            # A worst case scenario exception.
            raise IndexError(color.color_style().ERROR(ugettext(\
                u"An Error Occured: %s" %(e.message))))

        return ' '.join(constraints_output)


def _test():
    """
    Django-Check-Constraints Doctest Suite.
    """
    import doctest
    doctest.testmod()
    doctest.testfile("tests.txt")

if __name__ == "__main__":
    _test()
