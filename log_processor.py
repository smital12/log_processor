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
                          "Device#\t"
                          "Number\t"
                          "Site\t"
                          "Result\t"
                          "Test Name\t"
                          "Pin\t"
                          "Channel\t"
                          "Low\t"
                          "Measured\t"
                          "High\t"
                          "Force\t"
                          "Loc\t")
        if isADCTest:
            headerLabelRow += "First 10 Missing Codes"

    lines.insert(0, headerLabelRow)
    return lines


def main(filename, testname, isADCTest, isHeaderEveryTime):

    print('Processing "' + filename + '" for "' + testname + '"')

    # open datalog file and a file to write the results
    datalog = open(filename, "r").readlines()

    # filter down to headers and test result lines
    filteredLines = get_header_and_test_lines(datalog, testname, isADCTest,
                                              isHeaderEveryTime)

    # format the filtered lines
    formattedLines = tab_delimit_test_lines(filteredLines, testname, isADCTest,
                                            isHeaderEveryTime)

    if isADCTest:
        # move missing code list
        formattedLines = move_MCs_list_to_test_line(formattedLines)

    # take care of headers
    formattedLines = move_header_into_lines(formattedLines, isADCTest,
                                            isHeaderEveryTime)

    # write to output file
    joinedLines = '\n'.join(formattedLines)
    outputFile = filename + "_cleaned"
    open(outputFile, "w").write(joinedLines)
    print('Finished, see: ' + outputFile)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=(
        'Process Teradyne IG-XL data logs into tab-delimited files for '
        'easy import into data analysis tools. Logs should have header '
        'before very flow'))
    parser.add_argument('testname', type=str,
                        help=(
                            'string to ID desired lines e.g., some/all of'
                            ' the test name'))
    parser.add_argument('filenames', nargs='+', type=str,
                        help='name of input file')

    parser.add_argument('--ADC', dest='isADCTest',
                        action='store_true',
                        help=(
                            'ADC test results desired, include First 10 '
                            'missing codes list at end of MC results line '
                            '(default: test is not an ADC test)'))
    parser.set_defaults(isADCTest=False)

    # parser.add_argument('--header-every-time',
    #                     dest='isHeaderEveryTime', action='store_true',
    #                     help='datalog has a header before every flow')
    # parser.add_argument('--no-header-every-time',
    #                     dest='isHeaderEveryTime', action='store_false',
    #                     help='header is/may be missing before flow(s)')
    parser.set_defaults(isHeaderEveryTime=True)

    args = parser.parse_args()

    for filename in args.filenames:
        main(filename, args.testname, args.isADCTest, args.isHeaderEveryTime)
