import os
import re


def striplist(l):
    return [x.strip() for x in l]


def remove_celcius_C(match):
    return match.group(1)


def remove_SI_prefixes(match):
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


def tab_delimit_datalog(inLines, testName, isADCTest=False,
                        isHeaderEveryTime=False):
    # array to store desired lines
    lines = []
    isHeaderLine = False

    numberWithPrefixLetter = re.compile(r'(\d+\.\d+)\s+([MKmunf])')

    for line in inLines:
        isTestLine = False

        if testName in line:
            isTestLine = True
        # find start of header section, we'll flag all lines in the header so
        # they're copied over
        elif not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        if isTestLine:
            fixedMeasureUnitsLine = numberWithPrefixLetter.sub(remove_SI_prefixes, line)
            lines.append('\t'.join(fixedMeasureUnitsLine.split()))
        elif isHeaderLine:
            lines.append(line)
        elif isADCTest and line.startswith("First 10"):
            # lines.append(line.replace(":", "\t"))
            lines.append("test")

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("    Device#:"):
            isHeaderLine = False

    return lines


def format_header(oldHeader):
    newHeader = []
    newLine = ""
    siteNumLines = []
    isSiteNumLine = False

    for i, line in enumerate(oldHeader):
        # fine start of multi-line site number list, so we can squash to single
        # line string
        if line.startswith("Site Number"):
            isSiteNumLine = True

        # ignore empty lines
        if line:
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
        if isSiteNumLine and not line:
            isSiteNumLine = False
            # remove spaces from list of sites and join to label
            newHeader.append('Site Number\t' +
                             ''.join((''.join(siteNumLines[1:])).split()))

    return newHeader


def format_all_headers(inLines, isHeaderEveryTime=False):
    oldHeader = []
    lines = []
    isHeaderLine = False

    for line in inLines:

        # find start of header section, we'll flag all lines in the header so
        # they're copied over
        if not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        if isHeaderLine:
            oldHeader.append(line)
        else:
            lines.append(line)

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("Device#:"):
            isHeaderLine = False
            lines.extend(format_header(oldHeader))
            oldHeader.clear()

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

        # copy only desired lines
        if isTestLine or \
           isHeaderLine or \
           (isADCTest and "First 10" in line):
            lines.append(line)

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("    Device#: "):
            isHeaderLine = False

    return striplist(lines)


def move_missing_code_list_to_result_line(inLines):
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

    for line in inLines:

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


for filename in os.listdir("."):
    if filename.endswith(".txt"):
        # open datalog file and a file to write the results
        datalog = open(filename, "r").readlines()

        # filter down to headers and test result lines
        filteredLines = get_header_and_test_lines(datalog, "adclin",
                                                  isADCTest=True,
                                                  isHeaderEveryTime=True)

        # format the filtered lines
        formattedLines = tab_delimit_datalog(filteredLines, "adclin",
                                             isADCTest=True,
                                             isHeaderEveryTime=True)
        # move missing code list
        newLines = move_missing_code_list_to_result_line(formattedLines)

        # take care of headers
        fixedHeaderLines = format_all_headers(newLines,
                                              isHeaderEveryTime=True)
        # take care of headers
        myLines = move_header_into_lines(fixedHeaderLines,
                                         isADCTest=True,
                                         isHeaderEveryTime=True)

        # write to output file
        # joinedLines = '\n'.join(formattedLines)
        joinedLines = '\n'.join(myLines)
        open(filename + "_cleaned", "w").write(joinedLines)
