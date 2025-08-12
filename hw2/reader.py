#!/usr/bin/env python3

import json
import argparse
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


class DataLoader:    
    @staticmethod
    def load_json(filepath: str) -> List[Dict[str, Any]]:
        """Load JSON data from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filepath}: {e}")


class DataCombiner:    
    @staticmethod
    def combine_data(students: List[Dict[str, Any]], rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine students and rooms data into a structured format."""
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


class DataExporter(ABC):    
    @abstractmethod
    def export(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """Export data to specified format."""
        pass


class JSONExporter(DataExporter):    
    def export(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """Export data to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"Data successfully exported to {output_file} in JSON format")


class XMLExporter(DataExporter):    
    def export(self, data: List[Dict[str, Any]], output_file: str) -> None:
        """Export data to XML file."""
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
        
        print(f"Data successfully exported to {output_file} in XML format")


class ExporterFactory:    
    @staticmethod
    def create_exporter(output_format: str) -> DataExporter:
        """Create exporter based on format."""
        if output_format.lower() == 'json':
            return JSONExporter()
        elif output_format.lower() == 'xml':
            return XMLExporter()
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class RoomStudentProcessor:    
    def __init__(self):
        self.loader = DataLoader()
        self.combiner = DataCombiner()
    
    def process(self, students_file: str, rooms_file: str, output_file: str, output_format: str) -> None:
        """Process the data from input files to output file."""
        try:
            students = self.loader.load_json(students_file)
            rooms = self.loader.load_json(rooms_file)
            combined_data = self.combiner.combine_data(students, rooms)
            exporter = ExporterFactory.create_exporter(output_format)
            exporter.export(combined_data, output_file)
            
        except Exception as e:
            print(f"Error processing data: {e}")
            sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Process room-student data and export to JSON or XML format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reader.py --format json
  python3 reader.py --students hw2/students.json --rooms hw2/rooms.json --output result.xml --format xml
  
        """
    )
    
    parser.add_argument(
        '--students', 
        default='students.json',
        help='Path to students JSON file (default: students.json)'
    )
    
    parser.add_argument(
        '--rooms', 
        default='rooms.json',
        help='Path to rooms JSON file (default: rooms.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: output.{format})'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'xml'],
        default='json',
        help='Output format: json or xml (default: json)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point of the script."""
    args = parse_arguments()
    if not args.output:
        args.output = f"output.{args.format}"
    for file_path in [args.students, args.rooms]:
        if not Path(file_path).exists():
            print(f"Error: Input file '{file_path}' does not exist.")
            sys.exit(1)
    
    processor = RoomStudentProcessor()
    processor.process(args.students, args.rooms, args.output, args.format)


if __name__ == '__main__':
    main()