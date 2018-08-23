import log2csv
import py.test


def test_remove_LSBs():
    test = 'testname'
    lines = [test + '\t' + x + '\t' for x in ['LSB', 'mLSB', 'KLSB']]
    lines_clean = [test + '\t' + x for x in ['', 'm', 'K']]
    assert log2csv.remove_LSBs(lines, test) == lines_clean
# def striplist(l):
# def remove_celcius_C(match):
# def convert_SI_prefix_to_E_notation(match):
# def remove_LSBs(inLines, testName, isADCTest=False,
# def remove_SI_prefixes(inLines, testName, isADCTest=False,
# def tab_delimit_test_lines(inLines, testName, isADCTest=False,
# def format_header(oldHeader):
# def format_all_headers(inLines, isHeaderEveryTime=False):
# def get_test_lines(inLines, testName, isADCTest=False,
# def get_header_and_test_lines(inLines, testName, isADCTest=False,
# def move_MCs_list_to_test_line(inLines):
# def move_header_into_lines(inLines, isADCTest=True, isHeaderEveryTime=False):
# def get_header(isADCTest, isHeaderEveryTime):
# def get_full_header(isADCTest):
# def get_parametric_header(isADCTest):
# def main(filename, testname, isADCTest, isHeaderEveryTime):
