import json
import string
import sys

from pycodestyle import BaseReport, Checker, StyleGuide

import naming_analyzer as naming

# TODO: check trailing whitespace? W291, W292, W293, W391
# TODO: W503, W504? says not enforced by PEP8?
INDENT_ERRORS = ["E111", "E112", "E113", "E121", "E122", "E123", "E124",
                 "E125", "E126", "E127", "E128", "E129", "E131", "E133"]
TABS_SPACES_ERRORS = ["E101", "E223", "E224", "E242", "E273", "E274", "W191"]
LINE_LENGTH_ERRORS = ["E501"]
BLANK_LINE_ERRORS = ["E301", "E302", "E303", "E304", "E305", "E306"]
IMPORT_ERRORS = ["E401", "E402"]

NAMES = "naming"
INDENTS = "indentation"
TABS = "tabs_vs_spaces"
LENGTH = "line_length"
BLANKS = "blank_lines"
IMPORTS = "import"
ENCODING = "file_encoding"

def error_msg(report, prefix):
    msg = report.get_statistics(prefix)[0]
    index = msg.index(prefix)
    fin = msg[index+len(prefix)+1:]
    return fin

# Template function to print information about types of errors found
# Parameters:
# - counters: the counters generated by Pycodestyle
# - report: the file analysis results from Pycodestyle
# - header: the category of errors being outputed
# - macro: the file error codes to consider; a sort of "filter" of the
#   Pycodestyle error codes of interest for this section
# - clean: template message about no errors of this category found
def check_errors(counters, report, header, macro, clean):
    print("{} Errors:".format(header))
    has_errs = False
    for err in macro:
        if err in counters:
            has_errs = True
            print("    {}, {} occurrence{} {}".format(err, counters[err],
                                                      "s:" if counters[err] > 1 else ": ",
                                                      error_msg(report, err)))
    if not has_errs:
        print("    None. {} statements conform to PEP 8.".format(clean))


# Compares the file analysis results from Pycodestyle to the list
# of expected errors passed in through the macro
# Parameters:
# - counters: the error count results from Pycodestyle
# - macro: the file error codes to consider; a sort of "filter" of the
#   Pycodestyle error codes of interest for this section
# Returns a tuple of dictionary of JSON results and number of errors found
# Note: This function assumes PEP 8 and Google style guides are the
# same for the style element being analyzed. If the style guides differ,
# do not use this function
def json_check_errors(counters, macro):
    temp_dict = {"pep": None, "google": None, "errors": None}
    has_errs = False
    count = 0
    for err in macro:
        if err in counters:
            if not has_errs:
                has_errs = True
                temp_dict["pep"] = False
                temp_dict["google"] = False
                temp_dict["errors"] = {err: counters[err]}
            else:
                temp_dict["errors"][err] = counters[err]
            count += counters[err]
    if not has_errs:
        temp_dict["pep"] = True
        temp_dict["google"] = True
    return temp_dict, count


def check_indents(counters, report):
    check_errors(counters, report, "Indentation", INDENT_ERRORS, "Indentations of")

def check_tabs_spaces(counters, report):
    check_errors(counters, report, "Tabs vs. Spaces", TABS_SPACES_ERRORS, "Space-indented")

def check_line_length(counters, report):
    check_errors(counters, report, "Line Length", LINE_LENGTH_ERRORS, "Line length of")

def check_blank_lines(counters, report):
    check_errors(counters, report, "Blank Line", BLANK_LINE_ERRORS, "Blank line")

def check_imports(counters, report):
    check_errors(counters, report, "Import Statement", IMPORT_ERRORS, "Import")

# Create the dictionary of analysis result values to be converted into JSONa
def create_json_dict(counters, file_name):
    obj = {"total_file_errors": None}
    names = naming.naming_results(file_name)
    indents = json_check_errors(counters, INDENT_ERRORS)
    tabs = json_check_errors(counters, TABS_SPACES_ERRORS)
    length = json_check_errors(counters, LINE_LENGTH_ERRORS)
    blanks = json_check_errors(counters, BLANK_LINE_ERRORS)
    imports = json_check_errors(counters, IMPORT_ERRORS)
    obj[NAMES + "_analysis"] = names[0]
    obj[INDENTS + "_analysis"] = indents[0]
    obj[TABS + "_analysis"] = tabs[0]
    obj[LENGTH + "_analysis"] = length[0]
    obj[BLANKS + "_analysis"] = blanks[0]
    obj[IMPORTS + "_analysis"] = imports[0]
    obj[ENCODING + "_analysis"] = None
    obj["total_file_errors"] = names[1] + indents[1] + tabs[1] + length[1] + blanks[1] + imports[1]
    err_counts = {NAMES: names[1], INDENTS: indents[1], TABS: tabs[1],
                  LENGTH: length[1], BLANKS: blanks[1], IMPORTS: imports[1]}
    return obj, err_counts


def collect_file_dict_results(file_name):
    # Collect the PEP8 reported errors according to Pycodestyle.
    sg = StyleGuide()
    # TODO: should be able to "max_line_length=80" in the parens,
    # but not working. add Google line length support
    breport = BaseReport(options=sg.options)
    # TODO: check file actually exists. otherwise falsely outputting that it is compliant
    quiet_checker = Checker(file_name, report=breport)
    quiet_checker.check_all()
    counters = breport.counters
    # TODO: if a runtime error is thrown (E901, E902), still analyze the rest?
    js = create_json_dict(counters, file_name)
    naming.cleanup()
    return js

def check_input(input_str):
    # TODO: double-check this function
    temp = input_str
    msg = "That is not a valid file name. Please double-check your input."
    if " " in temp:
        temp = temp.replace(" ", "")
    for s in string.whitespace:
        if s == " ":
            pass
        else:
            if s in temp:
                raise ValueError(msg)


def main(argv):
    # TODO: pycodestyle always throws EXTRANEOUS_WHITESPACE_REGEX ?
    file_name = argv[0]
    check_input(file_name)
    temp = collect_file_dict_results(file_name)
    res = temp[0]
    print(json.dumps(res))
    return res

if __name__ == '__main__':
    main(sys.argv[1:])
