homework#1 
===========================

Code defines Version class to parse and compare semantic version strings following the SemVer 2.0.0 specification.

Features:
- Parses major.minor.patch-prerelease+build
- Supports comparison: <, <=, >, >=, ==, !=
- Pre-release versions sorted correctly
- Build metadata is ignored in comparisons
- Includes test cases in main()

Usage Example:
v1 = Version("1.0.0-alpha")
v2 = Version("1.0.0")
print(v1 < v2)   # True

To run tests:
$ python version_comparator.py

homework#2
===========================
in this homework i provide two scripts for organizing and exploring both json files. one script exports XML format, another JSON as an output. 
both perform the following tasks:
1. load data,
2. combine data,
3. export data.

XML file parameters: 
--students: path to the students.json file. default is 'students.json'.
--rooms: path to the rooms.json file. default is 'rooms.json'.
--output: path to the output XML file. default is 'output.xml'.

JSON file parameters: 
--students: path to the students.json file. default is 'students.json'.
--rooms: path to the rooms.json file. default is 'rooms.json'.
--output: path to the output JSON file. default is 'output.json'.
