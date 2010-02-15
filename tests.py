from django.test import TestCase
from check_constraints import *

class CheckConstraintTestCase(TestCase):
    def testNoKwargArgPassed(self):
        self.assertRaises(NoKwargsError, Check())

    def testInvalidSyntaxError(self):
        self.assertRaises(SyntaxError, Check(price_gte=10))

    def testVerifyCheckName(self):
        c = Check(price__gte = 10)
        c.check_name = "check_price"
        gen_sql_stmt = c.generate_sql()
        sql_stmt = """CONSTRAINT "check_price" CHECK ("price" >= 10) """
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testIsCascaded(self):
        c = Check(price__gte=0) & Check(price__gte='discount')
        self.assertEquals(c.is_cascaded, True)

    def testCascadedSQLGen(self):
        c = Check(price__gte=0) & Check(price__gte='discount') | Check(price__lte=100)
        c.check_name = "check_name_price"
        gen_sql_stmt = c.generate_sql()
        sql_stmt = """CONSTRAINT "check_name_price" CHECK ( ("price" >= 0) AND ("price" >= discount) OR ("price" <= 100) )"""
        self.assertEquals(gen_sql_stmt, sql_stmt)

    def testInvalidLookupArg(self):
        self.assertRaises(KeyError, Check(price__gre=10))

    def testInvalidFieldLookup(self):
        self.assertRaises(NonExistentFieldError, Check(tax_percentage__lt=10))


if __name__ == '__main__':
    import unittest
    unittest.main()
