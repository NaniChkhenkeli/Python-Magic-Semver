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


homework#4
===========================
REST API for managing rooms, students and their assignments, includes CRUD operations and functionality to list students in specific rooms, move students between rooms and search/filter students and rooms. 

no authenticaation needed for this version.

endpoints:
- GET /students (list of all students)
- POST / students (create new student)
- GET /students/{id} (get student details)
- PUT /students/{id} (full student update)
- PATCH /students/{id} (partial student update)
- DELETE /students/{id}
- POST /students/{id}/move (move students to another room)
- GET /rroms (list all rooms)
- POST /rooms (create new room)
- GET /rooms/{roomid} (get room details)
- PUT /rooms/{roomId}
- PATCH /rooms/{roomId}
- DELTE /rooms/{roomId}
- GET /rooms/{roomId}/students (list students in a room)

error handling:
(API returns appropriate HTTP status codes with JSON error responses)
- errorCode (machine-readable code)
- message (human readable code_
- details (additional context)

Documentation:
Full OpenAPI specification available at /docs endpoint.


homework#5
===========================
this project is django REST framework API to manage online courses with teachers/student roles, provides CRUD operations and structures learning environment.

includes:
- user roles and authentication, teachers and students can register and log in.
- teachers can create, update, delete courses, lectures can be added with presentation files.
- teachers can assign homework to lectures, students submit solutions and then teachers grade, add feedback.
- students can't modify courses/lectures, teachers only manage their own courses.

How it works:
  - backend: django + DRF
  - db: SQLite(default)
  - API Docs: swagger/OpenAPI
  - authentication: token-based.

how to run: 
1. install dependencies:
   pip install django djangorestframework drf-yasg
2. apply migrations:
   python manage.py migrate
3. start the server:
   python manage.py runserver
4. access:
   API: http://127.0.0.1:8000/api/v1/
   docs: http://127.0.0.1:8000/swagger/
   admin: http://127.0.0.1:8000/admin/

Key files:
- models: courses/models.py (database structure)
- API views: courses/views.py (business logic)
- permissions: courses/permissions.py (role-based access)
- URLs: courses/urls.py (API endpoints)
