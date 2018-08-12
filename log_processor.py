import argparse
import os
import re


def striplist(l):
    return [x.strip() for x in l]


def remove_celcius_C(match):
    return match.group(1)


def convert_num_with_SI_prefix(match):
    number = float(match.group(1))
    prefix = match.group(2)

    if prefix is "M":
        return str(number * 1000000)
    elif prefix is "K":
        return str(number * 1000)
    elif prefix is "m":
        return str(number / 1000)
    elif prefix is "u":
        return str(number / 1000000)
    elif prefix is "n":
        return str(number / 1000000000)
    elif prefix is "f":
        return str(number / 1000000000000)

    return "_!_"


def remove_SI_prefixes(inLines, testName, isADCTest=False,
                       isHeaderEveryTime=False):
    # array to store desired lines
    lines = []
    isHeaderLine = False

    # find decimal numbers with a SI unit prefix
    numWithSILetter = re.compile(r'(\d+\.\d+)\s+([MKmunf])')

    for line in inLines:
        isTestLine = False

        if testName in line:
            isTestLine = True
        # find start of header section, we'll flag all lines in the header so
        # they're copied over
        elif not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        if isTestLine:
            # get rid of SI Unit prefixes, converting the decimal number
            lineWithNoSILetters = (
                numWithSILetter.sub(convert_num_with_SI_prefix, line))
            lines.append('\t'.join(lineWithNoSILetters.split()))
        elif isHeaderLine:
            # keep header lines as-is
            lines.append(line)

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("    Device#:"):
            isHeaderLine = False

    return lines


def tab_delimit_test_lines(inLines, testName, isADCTest=False,
                        isHeaderEveryTime=False):
    # assumes inLines contains only header lines and test lines; no empty lines
    # or other types of lines accounted for

    # array to store desired lines
    lines = []
    isHeaderLine = False

    for line in inLines:
        # find start of a header section
        if not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        if (isHeaderLine or
           (isADCTest and line.startswith("First 10"))):
            # keep line as-is
            lines.append(line)
        else:
            # assume line is a test line
            # convert whitespace to tabs
            lines.append('\t'.join(line.split()))

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("Device#:"):
            isHeaderLine = False

    return lines


def format_header(oldHeader):
    # convert header into tab-delimited header
    newHeader = []
    newLine = ""
    siteNumLines = []
    siteNumString = ""
    isSiteNumLine = False

    for i, line in enumerate(oldHeader):
        # fine start of multi-line site number list, so we can squash to single
        # line string
        if line.startswith("Site Number"):
            isSiteNumLine = True

        if isSiteNumLine:
            siteNumLines.append(line.replace(":", ""))
        else:
            # add key to date/time string, which is always second line of
            # header
            if i == 1:
                newLine = "Time\t" + line
            # convert delimiters and remove excess whitespace
            else:
                newLine = "\t".join(striplist(line.split(":")))

            newHeader.append(newLine)

        # we've reached end of site number lines, join them as a single line
        if isSiteNumLine and oldHeader[i+1].startswith("Device#"):
            isSiteNumLine = False
            # remove spaces from list of sites and join to label
            siteNumString = ''.join(siteNumLines[1:])
            siteNumString = siteNumString.replace(' ', '')
            newHeader.append('Site Number\t' + siteNumString)

    return newHeader


def format_all_headers(inLines, isHeaderEveryTime=False):
    oldHeader = []
    lines = []
    isHeaderLine = False

    for line in inLines:

        # find start of a header section
        if not isHeaderLine and line.startswith("Datalog report"):
            oldHeader.clear()
            isHeaderLine = True

        if isHeaderLine:
            # store header lines for processing
            # don't copy to output
            oldHeader.append(line)
        else:
            # copy line as-is
            lines.append(line)

        # check if this is last line in header
        if isHeaderLine and line.startswith("Device#:"):
            isHeaderLine = False
            # add the formatted header as list of strings to output
            lines.extend(format_header(oldHeader))

    return lines


def get_test_lines(inLines, testName, isADCTest=False,
                              isHeaderEveryTime=False):
    # array to store desired lines
    lines = []

    for line in inLines:
        if (testName in line or
           (isADCTest and "First 10" in line)):
            # copy desired lines
            lines.append(line)

    return striplist(lines)


def get_header_and_test_lines(inLines, testName, isADCTest=False,
                              isHeaderEveryTime=False):
    # array to store desired lines
    lines = []
    isHeaderLine = False

    for line in inLines:
        isTestLine = False

        # check what type of line this is and if we're interested in it
        if testName in line:
            isTestLine = True
        # find start of header section, we'll flag all lines in the header so
        # they're copied over
        elif not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        # copy only desired lines, skip blank header lines
        if (isTestLine or
           (isHeaderLine and line.strip()) or
           (isADCTest and "First 10" in line)):
            lines.append(line)

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("    Device#: "):
            isHeaderLine = False

    return striplist(lines)


def move_MCs_list_to_test_line(inLines):
    # array to store desired lines
    lines = []
    missingCodesList = ""

    for i, line in enumerate(inLines):
        # for line in inLines:

        # check what type of line this is and if we're interested in it
        if "MC" in line and inLines[i+1].startswith("First 10"):
            missingCodesList = inLines[i+1].split(":")[1].strip()
            lines.append(line + '\t' + missingCodesList)
        elif not line.startswith("First 10"):
            lines.append(line)

    return lines


def move_header_into_lines(inLines, isADCTest=True, isHeaderEveryTime=False):
    lines = []
    headerData = []
    headerDataString = ""
    isHeaderLine = False
    tempsWithCelcius = re.compile(r'(\d+)C\b')

    # format headers into tab-delimited lines
    inLinesBetterHeaders = format_all_headers(inLines, isHeaderEveryTime)

    for line in inLinesBetterHeaders:

        # find start of header section, we'll flag all lines in the header so
        # they're copied over
        if not isHeaderLine and line.startswith("Datalog report"):
            headerDataString = ""
            headerData.clear()
            isHeaderLine = True

        if isHeaderLine:
            fixedEnvLine = tempsWithCelcius.sub(r'\1', line)
            try:
                # add values from header key-values
                headerData.append(fixedEnvLine.split('\t', maxsplit=1)[1])
            except IndexError:
                # sometimes there is no value e.g., lot is blank
                pass
        else:
            lines.append(headerDataString + '\t' + line)

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and 'Device#' in line:
            isHeaderLine = False
            headerDataString = '\t'.join(headerData)

    return lines


def get_header(isADCTest, isHeaderEveryTime):
    if isHeaderEveryTime:
        return get_full_header(isADCTest)
    else:
        return get_parametric_header(isADCTest)


def get_full_header(isADCTest):
    headerLabelRow = ("DateTime\t"
                      "Program Name\t"
                      "Job Name\t"
                      "Lot\t"
                      "Operator\t"
                      "Test Mode\t"
                      "Node Name\t"
                      "Part Type\t"
                      "Channel Map\t"
                      "Environment\t"
                      "Site Numbers\t"
                      "Device#\t")

    headerLabelRow += get_parametric_header(isADCTest)

    return headerLabelRow


def get_parametric_header(isADCTest):
    parametricHeader = ("Number\t"
                        "Site\t"
                        "Result\t"
                        "Test Name\t"
                        "Pin\t"
                        "Channel\t"
                        "Low\t"
                        "Measured\t"
                        "High\t"
                        "Force\t"
                        "Loc")
    if isADCTest:
        parametricHeader += "\tFirst 10 Missing Codes"

    return parametricHeader


def main(filename, testname, isADCTest, isHeaderEveryTime):

    print('Processing "' + filename + '" for "' + testname + '"')

    # open datalog file and a file to write the results
    datalog = open(filename, "r").readlines()

    # get the desired lines
    if isHeaderEveryTime:
        filteredLines = get_header_and_test_lines(datalog, testname, isADCTest,
                                                  isHeaderEveryTime)
    else:
        filteredLines = get_test_lines(datalog, testname, isADCTest,
                                       isHeaderEveryTime)

    # format the filtered lines
    formattedLines = tab_delimit_test_lines(filteredLines, testname, isADCTest,
                                            isHeaderEveryTime)

    # move missing code list
    if isADCTest:
        formattedLines = move_MCs_list_to_test_line(formattedLines)

    # move info from header blocks to columns instead
    if isHeaderEveryTime:
        formattedLines = move_header_into_lines(formattedLines, isADCTest,
                                                isHeaderEveryTime)

    # if we didn't find anything
    if not formattedLines:
        print('No lines matching testname found: ' + filename)
    else:
        # add the appropriate header
        formattedLines.insert(0, get_header(isADCTest, isHeaderEveryTime))

        # write to output file
        joinedLines = '\n'.join(formattedLines)
        outputFile = filename + "_cleaned"
        open(outputFile, "w").write(joinedLines)
        print('Finished ' + outputFile)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=(
        'Process Teradyne IG-XL data logs into tab-delimited files for '
        'easy import into data analysis tools. Logs should have header '
        'before very flow'))

    # filter args
    parser.add_argument('--filter-name', dest='nameFilter', type=str,
                        help=
                            ('file name filter string, ignore files without '
                             'this string in the filename or file ending'))
    parser.add_argument('--filter-type', dest='typeFilter', type=str,
                        help=
                            ('filetype filter string, ignore files not ending '
                             'in this string'))

    # ADC args
    parser.add_argument('--ADC', dest='isADCTest',
                        action='store_true',
                        help=(
                            'ADC test results desired, include First 10 '
                            'missing codes list at end of MC results line '
                            '(default: test is not an ADC test)'))
    parser.set_defaults(isADCTest=False)

    # header args
    parser.add_argument('--header-every-time',
                        dest='isHeaderEveryTime', action='store_true',
                        help='datalog has a header before every flow (default)')
    parser.add_argument('--no-header-every-time',
                        dest='isHeaderEveryTime', action='store_false',
                        help='header is/may be missing before flow(s)')
    parser.set_defaults(isHeaderEveryTime=True)

    # testname arg
    parser.add_argument('-n', dest='testname', type=str, required=True,
                        help=(
                            'string to ID desired lines e.g., some/all of'
                            ' the test name'))

    # input files or directory
    inputFilesGroup = parser.add_mutually_exclusive_group(required=True)
    # filenames 
    inputFilesGroup.add_argument('-f', dest='file', nargs='+', type=str,
                        help='input file or files')
    # directory args
    inputFilesGroup.add_argument('-d', dest='dir', type=str,
                        help='directory of input files')
    parser.add_argument('-r', dest='recurse', action='store_true',
                        help='resursively search DIR')

    args = parser.parse_args()

    # get list of files, either from args, single directory, or recursevely
    # searching a directory
    files = []
    if args.filenames:
        files.extend(args.file)
    if args.dir:
        if args.recurse:
            for dirName, subdirList, fileList in os.walk(args.dir):
                for fName in fileList:
                    fNameWithPath = os.path.join(dirName,fName)
                    files.append(fNameWithPath)
        else:
            for fName in os.listdir(args.dir):
                fNameWithPath = os.path.join(args.dir, fName)
                if os.path.isfile(fNameWithPath):
                    files.append(fNameWithPath)
                
    if args.nameFilter:
        files = [f for f in files if args.nameFilter in f]
    if args.typeFilter:
        files = [f for f in files if f.endswith(args.typeFilter)]

    if not files:
        print('no filenames given')

    else:
        for filename in files:
            main(filename, args.testname, args.isADCTest, args.isHeaderEveryTime)
