import sys

from junitparser import JUnitXml


def combine_junit_xml(output_file, *input_files):
    combined_xml = JUnitXml()
    for input_file in input_files:
        xml = JUnitXml.fromfile(input_file)
        combined_xml.extend(xml)
    combined_xml.write(output_file)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python combine_junit_xml.py <output_file> <input_file1> <input_file2> ... <input_fileN>"
        )
        sys.exit(1)

    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    combine_junit_xml(output_file, *input_files)
