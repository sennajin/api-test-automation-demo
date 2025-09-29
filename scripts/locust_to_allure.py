#!/usr/bin/env python3
"""
Locust to Allure Results Converter

This script converts Locust CSV output to Allure-compatible JSON results.
It reads the Locust statistics CSV file and generates Allure result files.

Usage:
    python scripts/locust_to_allure.py --csv-file locust_results_stats.csv --output-dir allure-results
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def convert_locust_to_allure(csv_file: str, output_dir: str) -> bool:
    """
    Convert Locust CSV results to Allure format.
    
    Args:
        csv_file: Path to Locust stats CSV file
        output_dir: Directory to write Allure results
        
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        current_time = int(datetime.now().timestamp() * 1000)
        
        if not os.path.exists(csv_file):
            print(f"CSV file not found: {csv_file}")
            return False
            
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip aggregated and empty rows
                if not row.get('Name') or row['Name'] == 'Aggregated':
                    continue
                    
                # Determine test status based on failure rate
                failure_rate = float(row.get('Failure Rate', 0))
                status = 'passed' if failure_rate == 0 else 'failed'
                
                # Create Allure result structure
                result = {
                    'name': row['Name'],
                    'status': status,
                    'start': current_time,
                    'stop': current_time + 1000,  # 1 second duration
                    'uuid': f'locust-{row["Name"].replace(" ", "-").replace("/", "-").lower()}',
                    'fullName': f'Locust: {row["Name"]}',
                    'labels': [
                        {'name': 'suite', 'value': 'Performance Tests'},
                        {'name': 'testClass', 'value': 'LocustLoadTest'},
                        {'name': 'method', 'value': row['Name']},
                        {'name': 'package', 'value': 'performance.locust'}
                    ],
                    'steps': [{
                        'name': f'Load Test: {row["Name"]}',
                        'status': status,
                        'start': current_time,
                        'stop': current_time + 1000
                    }],
                    'parameters': [
                        {'name': 'Request Count', 'value': row.get('Request Count', '0')},
                        {'name': 'Failure Count', 'value': row.get('Failure Count', '0')},
                        {'name': 'Average Response Time', 'value': f"{row.get('Average Response Time', '0')}ms"},
                        {'name': 'Min Response Time', 'value': f"{row.get('Min Response Time', '0')}ms"},
                        {'name': 'Max Response Time', 'value': f"{row.get('Max Response Time', '0')}ms"},
                        {'name': 'Requests/sec', 'value': row.get('Requests/sec', '0')}
                    ]
                }
                
                # Add failure details if test failed
                if status == 'failed':
                    result['statusDetails'] = {
                        'message': f"Performance test failed with {failure_rate:.2%} failure rate",
                        'trace': f"Request Count: {row.get('Request Count', '0')}, "
                                f"Failure Count: {row.get('Failure Count', '0')}, "
                                f"Average Response Time: {row.get('Average Response Time', '0')}ms"
                    }
                
                results.append(result)
        
        # Write Allure results
        for result in results:
            result_dir = Path(output_dir) / result['uuid']
            result_dir.mkdir(parents=True, exist_ok=True)
            
            with open(result_dir / 'result.json', 'w') as f:
                json.dump(result, f, indent=2)
        
        print(f"Converted {len(results)} Locust results to Allure format")
        print(f"Results written to: {output_dir}")
        return True
        
    except Exception as e:
        print(f"Error converting Locust results: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert Locust CSV results to Allure format")
    parser.add_argument("--csv-file", required=True, help="Path to Locust stats CSV file")
    parser.add_argument("--output-dir", required=True, help="Directory to write Allure results")
    
    args = parser.parse_args()
    
    print("Converting Locust results to Allure format...")
    print(f"CSV file: {args.csv_file}")
    print(f"Output directory: {args.output_dir}")
    
    success = convert_locust_to_allure(args.csv_file, args.output_dir)
    
    if success:
        print("Conversion completed successfully!")
        sys.exit(0)
    else:
        print("Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
