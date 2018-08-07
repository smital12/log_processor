import os
import re


def tab_delimit_from_spaces(inputStr):
    return ('\t').join(inputStr.split())


def tab_delimit_missing_code_list(inputStr):
    return inputStr.replace(":", ":\t")


def get_header_and_test_lines(inLines, testName, isADCTest=False,
                              isHeaderEveryTime=False):
    # array to store desired lines
    lines = []
    isHeaderLine = False

    for line in inLines:
        # find start of header section
        if not isHeaderLine and line.startswith("Datalog report"):
            isHeaderLine = True

        # copy desired lines
        if testName in line:
            # clean and copy desired lines
            cleanedLine = tab_delimit_from_spaces(line.strip())
            lines.append(cleanedLine)
        elif isHeaderLine:
            cleanedLine = line.strip()
            lines.append(cleanedLine)
        elif isADCTest and line.startswith(" First 10"):
            cleanedLine = tab_delimit_missing_code_list(line.strip())
            lines.append(cleanedLine)

        # find end of header section
        if isHeaderLine and line.startswith("    Device#:"):
            isHeaderLine = False

    return lines


for filename in os.listdir("."):
    if filename.endswith(".txt"):
        # open datalog file and a file to write the results
        datalog = open(filename, "r").readlines()

        # filter down to headers and test result lines
        filteredLines = get_header_and_test_lines(datalog, "adclin",
                                                  True, True)

        # write to output file
        joinedLines = '\n'.join(filteredLines)
        open(filename + "_cleaned", "w").write(joinedLines)
