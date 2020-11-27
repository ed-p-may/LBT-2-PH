import unittest
import to_excel

class Test_to_excel(unittest.TestCase):
    def test_conversion(self):
        worksheet = 'worksheet name'
        range = 'A1'
        value = '12'
        unitsSI = 'M'
        unitIP = 'SI'

        new_excel_obj = to_excel.PHPP_XL_Obj(worksheet, range, value, unitsSI, unitIP)

        self.assertEqual(new_excel_obj.getWorksheet, worksheet)

if __name__ == '__main__':
    unittest.main()