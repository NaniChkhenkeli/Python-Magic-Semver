import json
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "agvisto",
    "database": "student_rooms_db"
}

STUDENTS_FILE = "students.json"
ROOMS_FILE = "rooms.json"


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

    def create_schema(self):
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
                    ON DELETE SET NULL ON UPDATE CASCADE
            );
        """)

        self.db.execute("CREATE INDEX idx_students_room_id ON students(room_id);")
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
        params = [(s["id"], s["name"], s["birthday"][:10], s["sex"], s["room"]) for s in students]
        self.db.executemany(query, params)
        self.db.commit()


class QueryService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def summary_rooms_and_students(self):
        query = """
            SELECT COUNT(DISTINCT r.id) AS total_rooms,
                   COUNT(s.id) AS total_students
            FROM rooms r
            LEFT JOIN students s ON r.id = s.room_id;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def list_rooms_with_student_counts(self):
        query = """
            SELECT
                r.id AS room_id,
                r.name AS room_name,
                COUNT(s.id) AS student_count
            FROM
                rooms r
            LEFT JOIN
                students s ON r.id = s.room_id
            GROUP BY
                r.id, r.name
            ORDER BY
                r.id;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def top_5_rooms_smallest_avg_age(self):
        query = """
            SELECT
                r.id AS room_id,
                r.name AS room_name,
                AVG(TIMESTAMPDIFF(YEAR, s.birthday, CURDATE())) AS avg_age
            FROM
                rooms r
            JOIN
                students s ON r.id = s.room_id
            GROUP BY
                r.id, r.name
            HAVING
                COUNT(s.id) > 0
            ORDER BY
                avg_age ASC
            LIMIT 5;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def top_5_rooms_largest_age_difference(self):
        query = """
            SELECT
                r.id AS room_id,
                r.name AS room_name,
                MAX(TIMESTAMPDIFF(YEAR, s.birthday, CURDATE())) - MIN(TIMESTAMPDIFF(YEAR, s.birthday, CURDATE())) AS age_difference
            FROM
                rooms r
            JOIN
                students s ON r.id = s.room_id
            GROUP BY
                r.id, r.name
            HAVING
                COUNT(s.id) > 1
            ORDER BY
                age_difference DESC
            LIMIT 5;
        """
        self.db.execute(query)
        return self.db.fetchall()

    def count_rooms_with_mixed_sexes(self):
        query = """
            SELECT COUNT(*) 
            FROM (
                SELECT r.id
                FROM rooms r
                JOIN students s ON r.id = s.room_id
                WHERE s.sex IN ('M', 'F')
                GROUP BY r.id
                HAVING COUNT(DISTINCT s.sex) > 1
            ) AS mixed_rooms;
        """
        self.db.execute(query)
        count = self.db.fetchall()
        return count[0][0] if count else 0

    def list_rooms_with_mixed_sexes(self, limit=10):
        query = f"""
            SELECT r.id, r.name, COUNT(DISTINCT s.sex) AS sex_count
            FROM rooms r
            JOIN students s ON r.id = s.room_id
            WHERE s.sex IN ('M', 'F')
            GROUP BY r.id, r.name
            HAVING sex_count > 1
            LIMIT {limit};
        """
        self.db.execute(query)
        return self.db.fetchall()


def main():
    db = DatabaseManager(DB_CONFIG)
    output_file = "output.txt"

    try:
        schema_service = SchemaService(db)
        schema_service.create_schema()

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
            f.write("\nTop 5 rooms with smallest average student age:\n")
            for row in query_service.top_5_rooms_smallest_avg_age():
                f.write(f"Room ID: {row[0]}, Name: {row[1]}, Avg Age: {row[2]:.2f}\n")

            f.write("\nTop 5 rooms with largest age difference among students:\n")
            for row in query_service.top_5_rooms_largest_age_difference():
                f.write(f"Room ID: {row[0]}, Name: {row[1]}, Age Difference: {row[2]}\n")

            mixed_count = query_service.count_rooms_with_mixed_sexes()
            f.write(f"\nRooms where students of different sexes live together: {mixed_count} rooms found\n")
            f.write("Listing first 10 such rooms:\n")
            for row in query_service.list_rooms_with_mixed_sexes(limit=10):
                f.write(f"Room ID: {row[0]}, Name: {row[1]}, Sex Types: {row[2]}\n")

        print(f"Report written to {output_file}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
