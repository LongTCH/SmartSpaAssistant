import json
from datetime import datetime
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from openpyxl import Workbook
from tests.base_excel_test import BaseExcelTest


class CreateSheetExcelTester(BaseExcelTest):
    """Excel tester for create_sheet API"""

    def __init__(self, app_or_client=None):
        """Initialize with app or client"""
        super().__init__("create_sheet_test_data")
        if app_or_client is None:
            from app.main import app

            self.client = TestClient(app)
        elif isinstance(app_or_client, TestClient):
            self.client = app_or_client
        else:
            self.client = TestClient(app_or_client)

    def execute_test_case(self, test_case: dict) -> dict:
        """Execute a single test case for create_sheet API"""
        try:
            # Extract test data
            sheet_name = test_case.get("SheetName", "")
            sheet_description = test_case.get("SheetDescription", "")
            column_name = test_case.get("ColumnName", "")
            column_type = test_case.get("ColumnType", "")
            column_description = test_case.get("ColumnDescription", "")

            # Create column configuration
            column_config = [
                {
                    "column_name": column_name,
                    "column_type": column_type,
                    "description": column_description,
                }
            ]

            # Create test file content
            test_file_content = self._create_test_excel_file()

            # Prepare form data for API call
            form_data = {
                "name": sheet_name,
                "description": sheet_description,
                "column_config": json.dumps(column_config),
                "status": "published",
            }

            # Create file for upload
            files = {
                "file": (
                    "test.xlsx",
                    BytesIO(test_file_content),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }

            # Mock the service call and make API request
            with patch("app.services.sheet_service.insert_sheet") as mock_insert, patch(
                "app.utils.asyncio_utils.run_background"
            ) as mock_background:
                mock_insert.return_value = {"id": "test-sheet-id"}
                response = self.client.post("/sheets", data=form_data, files=files)

                # Determine test result
                logical_test_result = self._determine_test_result(
                    test_case, response.status_code
                )

                # Create result record with standardized format
                result_record = test_case.copy()

                # Standardize ActualResult format
                result_record["ActualResult"] = (
                    "True" if str(logical_test_result).upper() == "TRUE" else "False"
                )

                # Standardize ExpectedResult format
                expected = str(test_case.get("ExpectedResult", "")).strip().lower()
                result_record["ExpectedResult"] = (
                    "True" if expected == "true" else "False"
                )

                # Standardize error logging in 'Log' column
                if response.status_code != 201:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", "Unknown error")
                        if isinstance(error_detail, list):
                            error_detail = json.dumps(error_detail)
                        result_record["Log"] = str(error_detail)
                    except json.JSONDecodeError:
                        result_record["Log"] = (
                            f"HTTP {response.status_code}, Body: {response.text}"
                        )
                    except Exception as e_json:
                        result_record["Log"] = (
                            f"HTTP {response.status_code}, Error parsing JSON: {str(e_json)}, Body: {response.text}"
                        )
                else:
                    result_record["Log"] = None

                result_record["Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return result_record

        except Exception as e:
            # Handle exceptions during test execution
            failed_result = test_case.copy()
            failed_result["ActualResult"] = "Fail"
            failed_result["Log"] = f"Test execution error: {str(e)}"
            failed_result["Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Ensure all expected columns are present
            for key in [
                "SheetName",
                "SheetDescription",
                "ColumnName",
                "ColumnType",
                "ColumnDescription",
                "ExpectedResult",
            ]:
                if key not in failed_result:
                    failed_result[key] = "N/A due to error"
            return failed_result

    def _create_test_excel_file(self) -> bytes:
        """Create a simple Excel file for testing"""
        wb = Workbook()
        ws = wb.active
        ws["A1"] = "Test Data"

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _determine_test_result(self, test_case: dict, status_code: int) -> str:
        """Determine test result based on API response status code"""
        return "True" if status_code == 201 else "False"


def test_create_sheet_from_excel():
    """Test create_sheet API using Excel test data"""
    tester = CreateSheetExcelTester()
    results = tester.run_all_tests()
    summary = tester.get_test_summary(results)

    print(f"\nTest Summary for create_sheet API:")
    print(f"Total tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate']}")
    print(f"Results written to: {tester.test_file_path}")

    assert len(results) > 0, "No test cases found"
    assert (
        summary["failed"] == 0
    ), f"{summary['failed']} tests did not match expected outcomes. Check {tester.test_file_path}"


if __name__ == "__main__":
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    if server_root not in sys.path:
        sys.path.insert(0, server_root)

    def main():
        tester = CreateSheetExcelTester()
        results = tester.run_all_tests()
        summary = tester.get_test_summary(results)

        print(f"\nTest Summary for create_sheet API:")
        print(f"Total tests: {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Pass rate: {summary['pass_rate']}")
        print(f"Results written to: {tester.test_file_path}")

    main()
