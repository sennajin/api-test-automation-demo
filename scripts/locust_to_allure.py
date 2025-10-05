#!/usr/bin/env python3
"""Utilities to convert Locust CSV results into Allure result JSON files.

This module can be used as a library (via ``convert_locust_to_allure``) or executed
as a script to perform the conversion from the command line.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def convert_locust_to_allure(csv_file: str, output_dir: str) -> bool:
    """Convert Locust CSV results to Allure results JSON files.

    This function reads a Locust-generated stats CSV file and produces a set of
    Allure-compatible result JSON files, one per non-aggregated row in the CSV.
    Each Allure result reflects the request name, status (passed/failed based on
    the Failure Rate column), timing information, labels, steps, and parameters.

    Args:
        csv_file (str): Absolute or relative path to the Locust stats CSV file.
        output_dir (str): Directory where the Allure result JSON files will be written.
            The directory will be created if it does not exist.

    Returns:
        bool: True if conversion completes without unrecoverable errors; False otherwise.

    Raises:
        ValueError: If the CSV contains invalid numeric fields that cannot be parsed
            (surfaced only in rare cases where conversion errors aren't caught). Note
            that most runtime issues are handled gracefully and result in a False return.

    Notes:
        - Rows with Name equal to "Aggregated" or empty are skipped.
        - Test status is set to "passed" when Failure Rate == 0, otherwise "failed".
        - A millisecond timestamp is used for start/stop; duration is set to ~1 second.

    Examples:
        >>> convert_locust_to_allure("stats.csv", "reports/allure-results")
        True
    """
    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        results = []
        current_time = int(datetime.now().timestamp() * 1000)

        if not os.path.exists(csv_file):
            print(f"CSV file not found: {csv_file}")
            return False

        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip aggregated and empty rows
                if not row.get("Name") or row["Name"] == "Aggregated":
                    continue

                # Determine test status based on failure rate
                failure_rate = float(row.get("Failure Rate", 0))
                status = "passed" if failure_rate == 0 else "failed"

                # Create Allure result structure
                result = {
                    "name": row["Name"],
                    "status": status,
                    "start": current_time,
                    "stop": current_time + 1000,  # 1 second duration
                    "uuid": f"locust-{row['Name'].replace(' ', '-').replace('/', '-').lower()}",
                    "fullName": f"Locust: {row['Name']}",
                    "labels": [
                        {"name": "suite", "value": "Performance Tests"},
                        {"name": "testClass", "value": "LocustLoadTest"},
                        {"name": "method", "value": row["Name"]},
                        {"name": "package", "value": "performance.locust"},
                    ],
                    "steps": [
                        {
                            "name": f"Load Test: {row['Name']}",
                            "status": status,
                            "start": current_time,
                            "stop": current_time + 1000,
                        }
                    ],
                    "parameters": [
                        {"name": "Request Count", "value": row.get("Request Count", "0")},
                        {"name": "Failure Count", "value": row.get("Failure Count", "0")},
                        {
                            "name": "Average Response Time",
                            "value": f"{row.get('Average Response Time', '0')}ms",
                        },
                        {
                            "name": "Min Response Time",
                            "value": f"{row.get('Min Response Time', '0')}ms",
                        },
                        {
                            "name": "Max Response Time",
                            "value": f"{row.get('Max Response Time', '0')}ms",
                        },
                        {"name": "Requests/sec", "value": row.get("Requests/sec", "0")},
                    ],
                }

                # Add failure details if test failed
                if status == "failed":
                    result["statusDetails"] = {
                        "message": f"Performance test failed with {failure_rate:.2%} failure rate",
                        "trace": f"Request Count: {row.get('Request Count', '0')}, "
                        f"Failure Count: {row.get('Failure Count', '0')}, "
                        f"Average Response Time: {row.get('Average Response Time', '0')}ms",
                    }

                results.append(result)

        # Write Allure results
        for result in results:
            result_path = Path(output_dir) / f"{result['uuid']}-result.json"
            with open(result_path, "w") as f:
                # Type: ignore comment to suppress the specific type error
                json.dump(result, f, indent=2)  # type: ignore


        print(f"Converted {len(results)} Locust results to Allure format")
        print(f"Results written to: {output_dir}")
        return True

    except Exception as e:
        print(f"Error converting Locust results: {e}")
        return False


def main():
    """Command-line interface to convert Locust CSV results into Allure results.

    This entry point parses command-line arguments and calls
    `convert_locust_to_allure` with the provided CSV path and output directory.

    Args:
        None: This function reads from ``sys.argv`` via ``argparse``.

    Side Effects:
        - Prints progress and status messages to stdout.
        - Creates the output directory if it does not exist.
        - Writes Allure JSON result files into the output directory.
        - Exits the interpreter with ``sys.exit(0)`` on success or ``sys.exit(1)`` on failure.

    Example:
        Run from a shell:

            python scripts/locust_to_allure.py --csv-file perf_results.csv --output-dir reports/allure-results
    """
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
