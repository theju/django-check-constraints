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
"""

__version__ = "$Revision: 51$"

from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _
from datetime import date, datetime, time


def quote_obj(obj):
    return "'%s'" %(smart_unicode(obj))

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

    def __init__(self, **kwargs):
        """
        The constructor for the Check Field.
        Called whenever the object is initialized.
        """
        # Checking if there are keywords present.
        if not kwargs:
            raise NoKwargsError(_(u"No keyword arguments present."))
        # A name to identify every Check object.
        # Initially it is '' (empty string).
        # The name is set by the sql_create_model method.
        self.check_name = u''
        # Cascade Condition by default is '' (empty string)
        self.cascade_condition = u''
        # Initially the check object is not cascaded.
        self.is_cascaded = False
        # The container (list) for storing all the check conditions.
        self.sql_data = []
        # Supported Check Conditions.
        LOOKUP_TABLE = {u'gte':u'>=', u'lte':u'<=', u'gt':u'>', u'lt':u'<', 
                        u'neq':u'<>', u'eq':u'=', u'in':u'in', u'not_in': u'not in', 
                        u'like': u'like', u'unlike':u'not like', u'between':u'between'}
        for (key,val) in kwargs.items():
            # Checking for "__" in the Keyword Arguments.
            if not u"__" in key:
                raise SyntaxError(_(u'Invalid Syntax. Keyword Arguments must contain \"__\"'))
            # The left-side argument must be the field and the
            # right-side the condition.
            # Example: price__gte. price is the checked_field and
            # gte is the check condition.
            tokens = key.split(u"__")
            self.upper_or_lower = u""
            try:
                self.checked_field, self.check_condition_ul = key.split(u"__")
            except ValueError:
                self.checked_field, self.check_condition_ul, self.upper_or_lower = key.split(u"__")
            if self.upper_or_lower:
                if not self.upper_or_lower.lower() in (u"upper", u"lower"):
                    raise SyntaxError(_(u"Expecting an upper or lower keyword argument"))
                self.upper_or_lower = tokens[-1].upper()
            # Get the equivalent symbol from the lookup table.
            # Example: gte is converted to >=
            self.check_condition = LOOKUP_TABLE.get(self.check_condition_ul, None)
            if not self.check_condition:
                # If check condition not in LOOKUP_TABLE, then raise Error.
                raise KeyError(_(u'%s not found in Lookup Table' %self.check_condition_ul))
            # Data to be validated. This is the Keyword Argument Value.
            # Bind each check condition in a tuple.
            # [(checked_field,check_condition,validate_data, cascade_condition),]
            sql_tuple = tuple((self.checked_field, 
                               self.check_condition, 
                               val, 
                               self.cascade_condition))
            self.sql_data.append(sql_tuple)
            # If more than one keyword argument is found in the
            # Check Object, then cascade the arguments.
            # Example: Check(price__gte = 100,discount__lte = 10)
            if len(self.sql_data) > 1:
                self.is_cascaded = True
                self.cascade_condition = u'AND'
                for i in range(len(self.sql_data)-1):
                    sql_tuple = tuple((self.sql_data[i][0], 
                                       self.sql_data[i][1], 
                                       self.sql_data[i][2], 
                                       self.cascade_condition))
                    self.sql_data[i] = sql_tuple
            # Once the keyword argument is processed.
            # It is removed from the Keyword Argument Dictionary.
            kwargs.pop(key)

    def _cascade(self, cascade_condition, sql_data, other):
        sql_tuple = tuple((sql_data[len(sql_data)-1][0], 
                           sql_data[len(sql_data)-1][1], 
                           sql_data[len(sql_data)-1][2], 
                           cascade_condition))
        sql_data[len(sql_data)-1] = sql_tuple
        sql_data += other.sql_data
        return self.sql_data

    def __and__(self, other):
        """
        Used to handle cascaded AND Check Objects.
        """
        self.is_cascaded = True
        self.cascade_condition = u'AND'
        self.sql_data = self._cascade(self.cascade_condition, self.sql_data, other)
        return self

    def __or__(self,other):
        """
        Used to handle cascaded OR Check Objects.
        """
        self.is_cascaded = True
        self.cascade_condition = u'OR'
        self.sql_data = self._cascade(self.cascade_condition, self.sql_data, other)
        return self

    def validate(self, opts):
        """
        Validates the Check Object. Is called when sql is generated.
        """
        # Contains all the field attribute names defined in the models.
        all_fields = []

        for num_of_fields in range(len(opts.fields)):
            # Fetch all attribute names of fields.
            all_fields.append(opts.fields[num_of_fields].get_attname())

        for check_arg in range(len(self.sql_data)):
            field_name = self.sql_data[check_arg][0]
            field_val  = self.sql_data[check_arg][2]
            if not field_name in all_fields:
                # Check if checked_field exists among fields.
#                raise NonExistentFieldError(_(u"'%s' field not found" %field_val))
                raise NonExistentFieldError()
            if isinstance(field_val, str):
                # There are two cases. One if the check condition is 'like'.
                # Two if the string is a field as given below:
                # If data is a string then check if it exists in the fields.
                # Example: Check(price__lte = 'discount')
                if self.sql_data[check_arg][1] in (u'like', u'not like'):
                    temp_var = list(self.sql_data[check_arg])
                    replaced_text = self.sql_data[check_arg][2]
                    replaced_text = replaced_text.replace("*","%%")
                    replaced_text = replaced_text.replace(".","_")
                    temp_var[2] = quote_obj(replaced_text)
                    self.sql_data[check_arg] = tuple(temp_var)
                else:
                    if not field_val in all_fields:
                        raise NonExistentFieldError(_(u"%s field not found" %field_val))
            # If data is an instance of tuple then has
            # to be part of the 'in' check condition.
            elif isinstance(field_val, (tuple, list)):
                if not (self.sql_data[check_arg][1] in (u'in', u'not in') or self.sql_data[check_arg][1] == u"between"):
                    raise SyntaxError(_(u"Was expecting the 'in'/'not in' or 'between' Check Condition."))
                temp_var = list(self.sql_data[check_arg])
                temp_data_list = list(self.sql_data[check_arg][2])
                if self.sql_data[check_arg][1] in (u'in', u'not in'):
                    for i in range(len(temp_data_list)):
                        temp_data_list[i] = quote_obj(temp_data_list[i])
                if self.sql_data[check_arg][1] == u"between":
                    between_check_sql_data = u""
                    for i in range(len(temp_data_list)):
                        if isinstance(temp_data_list[i], (date, datetime, time)):
                            between_check_sql_data += quote_obj(temp_data_list[i])
                        elif isinstance(temp_var[2][i], str):
                            if not temp_data_list[i] in all_fields:
                                raise NonExistentFieldError(_(u"%s field not found." %temp_var[2][i]))
                            else:
                                between_check_sql_data += quote_obj(self.sql_data[check_arg][2][i])
                        elif isinstance(temp_var[2][i],int):
                            between_check_sql_data += quote_obj(self.sql_data[check_arg][2][i])
                        else:
                            raise SyntaxError(_(u"Does not support the datatype."))
                        if i == 0:
                            between_check_sql_data += u"AND"
                temp_var[2] = u"( %s )" %",".join(map(smart_unicode, temp_data_list))
                self.sql_data[check_arg] = tuple(temp_var)
            # If data is an instance of date then get it's actual representation
            elif isinstance(field_val,(date,datetime,time)):
                # If the data is a date field then convert to
                # a list to make use of list properties.
                # Because tuple does not support assignment.
                temp_var = list(self.sql_data[check_arg])
                temp_var[2] = quote_obj(field_val)
                # If data is an instance of time then convert
                # to equivalent SQL representation.
                self.sql_data[check_arg] = tuple(temp_var)

    def generate_sql(self, connection, style):
        """
        All SQL statements are generated by this method.
        """
        # First check if the databases support check constraints.
        # Currently supporting Postgresql, Sqlite and Oracle.
        # Untested on Firebird.
        db_alias = connection.alias
        db_engine = settings.DATABASES[db_alias]["ENGINE"]
        if not db_engine in (u'django.db.backends.postgresql_psycopg2',
                             u'django.db.backends.postgresql',
                             u'django.db.backends.sqlite3', 
                             u'django.db.backends.oracle'):
            raise NotSupportedError(style.ERROR(_(u"%s does not support check constraints natively." %connection["ENGINE"])))
        constraints_output = [u'CONSTRAINT' + u" \"" + smart_unicode(self.check_name) + u"\" " + u'CHECK',]

        if len(self.sql_data) > 1:
            constraints_output.append("(")
        for check_arg in range(len(self.sql_data)):
            check_name = "\"%s\"" %self.sql_data[check_arg][0]
            if self.upper_or_lower:
                check_name = u"%s(\"%s\")" %(self.upper_or_lower, self.sql_data[check_arg][0])
            constraints_output.append(u"( %s %s %s )" %(check_name, self.sql_data[check_arg][1], 
                                                        self.sql_data[check_arg][2]))
            if self.sql_data[check_arg][3]:
                constraints_output.append(u"%s" %self.sql_data[check_arg][3])
        if len(self.sql_data) > 1:
            constraints_output.append(")")

        return ' '.join(constraints_output)
