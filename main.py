import os
import re


def striplist(l):
    return [x.strip() for x in l]


def tab_delimit_from_spaces(inputStr):
    return '\t'.join(inputStr.split())


def tab_delimit_missing_code_list(inputStr):
    return inputStr.replace(": ", "\t")


def tab_delimit_datalog(inLines, testName, isADCTest=False,
                        isHeaderEveryTime=False):
    # array to store desired lines
    lines = []
    isHeaderLine = False

    for line in inLines:
        isTestLine = False

        if testName in line:
            isTestLine = True
        # find start of header section, we'll flag all lines in the header so
        # they're copied over
        elif not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        if isTestLine:
            cleanedLine = tab_delimit_from_spaces(line)
        elif isHeaderLine:
            cleanedLine = line
        elif isADCTest and line.startswith("First 10"):
            cleanedLine = tab_delimit_missing_code_list(line)

        lines.append(cleanedLine)

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
                siteNumLines.append(line)
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
            newHeader.append('\t'.join(siteNumLines))

    return '\n'.join(newHeader)


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
            lines.append(format_header(oldHeader))
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
            lines.append(line.strip())

        # indicate we've reached the end of the header and don't need to keep
        # copying lines unless they match the desired test name
        if isHeaderLine and line.startswith("    Device#: "):
            isHeaderLine = False

    return lines


for filename in os.listdir("."):
    if filename.endswith(".txt"):
        # open datalog file and a file to write the results
        datalog = open(filename, "r").readlines()

        # filter down to headers and test result lines
        filteredLines = get_header_and_test_lines(datalog, "adclin",
                                                  True, True)

        # format the filtered lines
        formattedLines = tab_delimit_datalog(filteredLines, "adclin", True,
                                             True)

        # take care of headers
        fixedHeaderLines = format_all_headers(formattedLines, True)

        # write to output file
        # joinedLines = '\n'.join(formattedLines)
        joinedLines = '\n'.join(fixedHeaderLines)
        open(filename + "_cleaned", "w").write(joinedLines)
