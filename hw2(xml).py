import json
import argparse
import sys
from collections import defaultdict
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


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

def export_to_xml(data, output_file):
    try:
        root = Element('rooms')
        
        for room in data:
            room_elem = SubElement(root, 'room')
            room_elem.set('number', str(room['room_number']))
            
            name_elem = SubElement(room_elem, 'room_name')
            name_elem.text = room['room_name']
            
            count_elem = SubElement(room_elem, 'student_count')
            count_elem.text = str(room['student_count'])
            
            students_elem = SubElement(room_elem, 'students')
            for student in room['students']:
                student_elem = SubElement(students_elem, 'student')
                student_elem.set('id', str(student['id']))
                student_elem.text = student['name']
        
        xml_str = tostring(root, encoding='unicode')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent='  ')
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
        
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(pretty_xml)
        
        print(f"data is successfully exported to {output_file} XML format")
    except Exception as e:
        print(f"error! failed writing XML file '{output_file}' : {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Export room-student data to XML format')
    
    parser.add_argument('--students', default='students.json', help='C:/Users/Dell/Desktop/hw1/Python-Magic-Semver/students.json')
    parser.add_argument('--rooms', default='rooms.json', help='C:/Users/Dell/Desktop/hw1/Python-Magic-Semver/rooms.json') 
    parser.add_argument('--output', '-o', default='output.xml', help='Output XML file path')

    
    args = parser.parse_args()
    students = load(args.students)
    rooms = load(args.rooms)
    combined_data = combine(students, rooms)
    export_to_xml(combined_data, args.output)

if __name__ == '__main__':
    main()