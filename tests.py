from django.test import TestCase
from check_constraints import *

class CheckConstraintTestCase(TestCase):
    def testNoKwargArgPassed(self):
        self.assertRaises(NoKwargsError, Check)

    def testInvalidSyntaxError(self):
        x = lambda : Check(price_gte=10)
        self.assertRaises(SyntaxError, x)

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
        x = lambda : Check(price__gre=10)
        self.assertRaises(KeyError, x)

    def testInvalidFieldLookup(self):
        x = lambda : Check(tax_percentage__lt=10)
        self.assertRaises(NonExistentFieldError, x)


if __name__ == '__main__':
    import unittest
    unittest.main()
