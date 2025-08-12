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
in this homework script reads data from json files, groups students by room, counts the number of students per room and then outputs data in json or xml formats.

Usage:
JSON output - python reader.py --students hw2/students.json --rooms hw2/rooms.json --output result.json --format json. 
XML output - python reader.py --students hw2/students.json --rooms hw2/rooms.json --output result.xml --format xml.


Usage Example: python reader.py --students hw2/students.json --rooms hw2/rooms.json --output report.xml --format xml
 - this will create xml containing all rooms with their assigned students.


homework#3
===========================
this script loads student and room data from JSON files into a MySQL database, runs queries to analyze data,
and generates a summary report in 'output.txt'.

Requirements:
- Python 3.6+
- MySQL Server
- mysql-connector-python package
- 'students.json' and 'rooms.json' in script folder

Setup: 
1. Install dependencies:
   pip install mysql-connector-python
2. Ensure MySQL server is running and database 'student_rooms_db' exists.
3. Update DB_CONFIG in the script if needed.
4. Place JSON files in the script directory.


Output:
Generates 'output.txt' with:
- Total rooms and students
- Top 5 rooms with smallest avg student age
- Top 5 rooms with largest age difference
- Rooms housing both male and female students


