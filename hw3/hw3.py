import json
import mysql.connector
from datetime import datetime
from pathlib import Path

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "student_rooms_db"
}

BASE_DIR = Path(__file__).resolve().parent
STUDENTS_FILE = BASE_DIR / "students.json"
ROOMS_FILE = BASE_DIR / "rooms.json"


class DatabaseManager:
    def __init__(self, config):
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor()

    def execute(self, query, params=None):
        self.cursor.execute(query, params or ())

    def executemany(self, query, params_list):
        self.cursor.executemany(query, params_list)

    def fetchall(self):
        return self.cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()


class SchemaService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_and_reset_schema(self):
        """Drops existing tables and creates new schema with indexes"""
        self.db.execute("DROP TABLE IF EXISTS students;")
        self.db.execute("DROP TABLE IF EXISTS rooms;")
        self.db.commit()

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                birthday DATE NOT NULL,
                sex ENUM('M', 'F') NOT NULL,
                room_id INT,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
                    ON DELETE SET NULL ON UPDATE CASCADE,
                INDEX idx_room_id (room_id)
            );
        """)

        self.db.execute("CREATE INDEX idx_students_sex ON students(sex);")
        self.db.execute("CREATE INDEX idx_students_birthday ON students(birthday);")
        self.db.commit()


class DataLoader:
    @staticmethod
    def load_json(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)


class DataInserter:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def insert_rooms(self, rooms):
        query = """
            INSERT INTO rooms (id, name) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name)
        """
        params = [(room["id"], room["name"]) for room in rooms]
        self.db.executemany(query, params)
        self.db.commit()

    def insert_students(self, students):
        query = """
            INSERT INTO students (id, name, birthday, sex, room_id)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name=VALUES(name),
                birthday=VALUES(birthday),
                sex=VALUES(sex),
                room_id=VALUES(room_id)
        """
        params = []
        for student in students:
            try:
                birthday_dt = datetime.strptime(student["birthday"], "%Y-%m-%dT%H:%M:%S.%f")
                birthday_str = birthday_dt.strftime("%Y-%m-%d")
                params.append((
                    student["id"],
                    student["name"],
                    birthday_str,
                    student["sex"],
                    student["room"]
                ))
            except (KeyError, ValueError) as e:
                print(f"Error processing student {student.get('id')}: {e}")
                continue

        self.db.executemany(query, params)
        self.db.commit()


class QueryService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def summary_rooms_and_students(self):
        query = """
            SELECT 
                COUNT(DISTINCT r.id) AS total_rooms,
                COUNT(s.id) AS total_students
            FROM rooms r
            LEFT JOIN students s ON r.id = s.room_id;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def top_5_rooms_smallest_avg_age(self):
        query = """
            SELECT
                r.id AS room_id,
                r.name AS room_name,
                AVG(TIMESTAMPDIFF(YEAR, s.birthday, CURDATE())) AS avg_age
            FROM rooms r
            JOIN students s ON r.id = s.room_id
            GROUP BY r.id, r.name
            ORDER BY avg_age ASC
            LIMIT 5;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def top_5_rooms_largest_age_difference(self):
        query = """
            SELECT
                r.id AS room_id,
                r.name AS room_name,
                TIMESTAMPDIFF(YEAR, 
                    MIN(s.birthday), 
                    MAX(s.birthday)
                ) AS age_difference
            FROM rooms r
            JOIN students s ON r.id = s.room_id
            GROUP BY r.id, r.name
            HAVING COUNT(s.id) > 1
            ORDER BY age_difference DESC
            LIMIT 5;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def count_rooms_with_mixed_sexes(self):
        query = """
            SELECT COUNT(DISTINCT r.id)
            FROM rooms r
            WHERE EXISTS (
                SELECT 1 FROM students s 
                WHERE s.room_id = r.id AND s.sex = 'M'
            )
            AND EXISTS (
                SELECT 1 FROM students s 
                WHERE s.room_id = r.id AND s.sex = 'F'
            );
        """
        self.db.execute(query)
        result = self.db.fetchall()
        return result[0][0] if result else 0

    def list_rooms_with_mixed_sexes(self, limit=10):
        query = """
            SELECT 
                r.id, 
                r.name,
                SUM(s.sex = 'M') AS males,
                SUM(s.sex = 'F') AS females,
                COUNT(s.id) AS total_students
            FROM rooms r
            JOIN students s ON r.id = s.room_id
            GROUP BY r.id, r.name
            HAVING males > 0 AND females > 0
            ORDER BY r.id
            LIMIT %s;
        """
        self.db.execute(query, (limit,))
        return self.db.fetchall()


def main():
    db = DatabaseManager(DB_CONFIG)
    output_file = BASE_DIR / "output.txt"

    try:
        schema_service = SchemaService(db)
        schema_service.create_and_reset_schema()

        data_loader = DataLoader()
        rooms = data_loader.load_json(ROOMS_FILE)
        students = data_loader.load_json(STUDENTS_FILE)

        inserter = DataInserter(db)
        inserter.insert_rooms(rooms)
        inserter.insert_students(students)

        query_service = QueryService(db)

        with open(output_file, "w", encoding="utf-8") as f:
            total_rooms, total_students = query_service.summary_rooms_and_students()[0]
            f.write(f"Summary:\nTotal Rooms: {total_rooms}\nTotal Students: {total_students}\n\n")

            f.write("Top 5 rooms with smallest average student age:\n")
            for room_id, room_name, avg_age in query_service.top_5_rooms_smallest_avg_age():
                f.write(f"Room ID: {room_id}, Name: {room_name}, Avg Age: {avg_age:.2f}\n")

            f.write("\nTop 5 rooms with largest age difference among students:\n")
            for room_id, room_name, age_diff in query_service.top_5_rooms_largest_age_difference():
                f.write(f"Room ID: {room_id}, Name: {room_name}, Age Difference: {age_diff}\n")

            mixed_count = query_service.count_rooms_with_mixed_sexes()
            f.write(f"\nRooms where students of different sexes live together: {mixed_count} rooms found\n")
            f.write("Listing first 10 such rooms (males/females/total):\n")
            for room_id, room_name, males, females, total in query_service.list_rooms_with_mixed_sexes(limit=10):
                f.write(f"Room ID: {room_id}, Name: {room_name}, Males: {males}, Females: {females}, Total: {total}\n")

        print(f"Report written to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()