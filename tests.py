from django.test import TestCase
from django.core.management.color import no_style
from django.db import connection
from datetime import datetime
from check_constraints_app.models import CCTestModel
from django.db.models.fields import FieldDoesNotExist
from check_constraints import *

opts = CCTestModel._meta

class CheckConstraintTestCase(TestCase):
    def testNoKwargArgPassed(self):
        self.assertRaises(NoKwargsError, Check)

    def testInvalidSyntaxError(self):
        x = lambda : Check(price_gte=10)
        self.assertRaises(SyntaxError, x)

    def testIsCascaded(self):
        c = Check(price__gte=0) & Check(price__gte='discount')
        self.assertEquals(c.is_cascaded, True)

    def testSQLGen1(self):
        c = Check(price__gte = 10)
        c.check_name = "check_price"
        c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_price" CHECK ( "price" >= 10 )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testSQLGen2(self):
        c = Check(name__like__upper = 'THEJ%')
        c.check_name = "check_name"
        c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_name" CHECK ( UPPER("name") like 'THEJ%' )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testSQLGen3(self):
        c = Check(discount__between = [10, 20])
        c.check_name = "check_discount"
        c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_discount" CHECK ( "discount" between 10 AND 20 )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testSQLGen4(self):
        c = Check(gender__in = ("Male", "Female"))
        c.check_name = "check_gender"
        c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_gender" CHECK ( "gender" in ( 'Male', 'Female' ) )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testSQLGen5(self):
        c = Check(mfg_date__gt = datetime(2010,1,1))
        c.check_name = "check_mfg_date"
        c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_mfg_date" CHECK ( "mfg_date" > '2010-01-01 00:00:00' )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testSQLGen6(self):
        c = Check(name__between = ['john', 'george'])
        c.check_name = "check_name"
        x = lambda : c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_name" CHECK ( "name" between ( 'john', 'george' ) )"""
        self.assertRaises(FieldDoesNotExist, x)

    def testCascadedSQLGen(self):
        c = Check(price__gte=0) & Check(price__gte='discount') | Check(price__lte=100)
        c.check_name = "check_name_price"
        c.validate(opts)
        gen_sql_stmt = c.generate_sql(connection, no_style)
        sql_stmt = """CONSTRAINT "check_name_price" CHECK ( ( "price" >= 0 ) AND ( "price" >= discount ) OR ( "price" <= 100 ) )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testInvalidLookupArg(self):
        x = lambda : Check(price__gre=10)
        self.assertRaises(KeyError, x)

    def testInvalidFieldLookup(self):
        c = Check(tax_percentage__lt=10)
        x = lambda : c.validate(opts)
        self.assertRaises(FieldDoesNotExist, x)


class CheckConstraintValidatorTests(TestCase):
    def testSQLGen1(self):
        c = Check(price__gte = 10)
        c.check_name = "check_price"
        c.validate(opts)
        validators = opts.get_fields_by_name('price').validators
        self.assertTrue(isinstance(validators[0], GTEValidator))

    def testSQLGen2(self):
        c = Check(name__like__upper = 'THEJ%')
        c.check_name = "check_name"
        c.validate(opts)
        validators = opts.get_fields_by_name('name').validators
        self.assertTrue(isinstance(validators[0], LikeValidator))

    def testSQLGen3(self):
        c = Check(discount__between = [10, 20])
        c.check_name = "check_discount"
        c.validate(opts)
        validators = opts.get_fields_by_name('discount').validators
        self.assertTrue(isinstance(validators[0], RangeValidator))

    def testSQLGen4(self):
        c = Check(gender__in = ("Male", "Female"))
        c.check_name = "check_gender"
        c.validate(opts)
        validators = opts.get_fields_by_name('gender').validators
        self.assertTrue(isinstance(validators[0], ListValidator))

    def testSQLGen5(self):
        c = Check(mfg_date__gt = datetime(2010,1,1))
        c.check_name = "check_mfg_date"
        c.validate(opts)
        validators = opts.get_fields_by_name('mfg_date').validators
        self.assertTrue(isinstance(validators[0], GTValidator))

    def testSQLGen6(self):
        c = Check(name__between = ['john', 'george'])
        c.check_name = "check_name"
        x = lambda : c.validate(opts)
        validators = opts.get_fields_by_name('name').validators
        self.assertTrue(isinstance(validators[0], RangeValidator))

    def testCascadedSQLGen(self):
        c = Check(price__gte=0) & Check(price__gte='discount') | Check(price__lte=100)
        c.check_name = "check_name_price"
        c.validate(opts)
        validators = opts.get_fields_by_name('price').validators
        self.assertTrue(isinstance(validators[0], GTEValidator))
        self.assertTrue(isinstance(validators[1], GTEValidator))
        self.assertTrue(isinstance(validators[2], LTEValidator))
            

if __name__ == '__main__':
    import unittest
    unittest.main()
