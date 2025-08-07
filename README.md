homework#1 
Semantic Version Comparator
===========================

Code defines Version class to parse and compare semantic version strings following the SemVer 2.0.0 specification.

Features:
- Parses major.minor.patch-prerelease+build
- Supports comparison: <, <=, >, >=, ==, !=
- Pre-release versions sorted correctly
- Build metadata is ignored in comparisons
- Includes test cases in main()

Usage Example:
--------------
v1 = Version("1.0.0-alpha")
v2 = Version("1.0.0")
print(v1 < v2)   # True

To run tests:
-------------
$ python version_comparator.py
