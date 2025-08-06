import json
import argparse
import sys
from collections import defaultdict


def load(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def combine(students, rooms):
    students_by_room = defaultdict(list)
    for student in students:
        room_number = student['room']
        students_by_room[room_number].append({
            'id': student['id'],
            'name': student['name']
        })

    combined_data = [] 

    for room_number, assigned_students in students_by_room.items():
        room_data = {
            'room_number': room_number, 
            'students': assigned_students,
            'room_name': f"Room #{room_number}",
            'student_count': len(assigned_students)
        }
        combined_data.append(room_data)

    combined_data.sort(key=lambda x: x['room_number']) 

    return combined_data

def export_to_json(data, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"data is successfully exported to {output_file} JSON format")
    except Exception as e:
        print(f"error! failed writing JSON file '{output_file}' : {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Export room-student data to JSON format')
    
    parser.add_argument('--students', default='students.json', help='C:/Users/Dell/Desktop/hw1/Python-Magic-Semver/students.json')
    parser.add_argument('--rooms', default='rooms.json', help='C:/Users/Dell/Desktop/hw1/Python-Magic-Semver/rooms.json') 
    parser.add_argument('--output', '-o', default='output.json', help='Output JSON file path')

    
    args = parser.parse_args()
    students = load(args.students)
    rooms = load(args.rooms)
    combined_data = combine(students, rooms)
    export_to_json(combined_data, args.output)

if __name__ == '__main__':
    main()