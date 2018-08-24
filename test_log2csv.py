import log2csv
import py.test


test = 'testname'


def test_remove_LSBs():
    lineIn = [test + '\tLSB\t']
    lineOut = [test + '\t']
    assert log2csv.remove_LSBs(lineIn, test) == lineOut


def test_remove_LSBs_with_prefix():
    prefixes = ['M',
                'K',
                'm',
                'u',
                'n',
                'p',
                'f']
    lines1 = [test + '\t' + x + 'LSB\t' for x in prefixes]
    lines2 = [test + '\t' + x + '\t' for x in prefixes]
    assert log2csv.remove_LSBs(lines1, test) == lines2


def test_get_test_lines():
    inLines = ['line0\t' + test,
               'line1\t',
               'line2\t' + test,
               'line4\t',
               'line5\t' + test]
    outLines = ['line0\t' + test,
                'line2\t' + test,
                'line5\t' + test]
    assert log2csv.get_test_lines(inLines, test) == outLines

def test_log2csv_adc():
    inFile = './test/test_logs_01/test_adc.txt'
    outFile = inFile + '_cleaned'
    referenceFile = inFile + '_cleaned.reference'

    log2csv.main(inFile, 'adclin', isADCTest=True, isHeaderEveryTime=True)

    assert open(outFile, 'r').read() == open(referenceFile , 'r').read()
