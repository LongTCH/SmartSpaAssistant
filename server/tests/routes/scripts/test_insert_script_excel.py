from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from tests.base_excel_test import BaseExcelTest


class InsertScriptExcelTester(BaseExcelTest):
    """Excel tester for insert_script API"""

    def __init__(self, app_or_client=None):
        """Initialize with app or client"""
        super().__init__("insert_script_test_data")
        if app_or_client is None:
            from app.main import app

            self.client = TestClient(app)
        elif isinstance(app_or_client, TestClient):
            self.client = app_or_client
        else:
            self.client = TestClient(app_or_client)

    def execute_test_case(self, test_case):
        """Execute a single test case for insert_script API"""
        try:
            # Extract test data
            test_case.get("TestCaseName", "")
            name = test_case.get("Name")
            description = test_case.get("Description")
            solution = test_case.get("Solution")
            expected_result = str(test_case.get("ExpectedResult", "")).strip()

            # Prepare request payload
            payload = {"name": name, "description": description, "solution": solution}
            # Mock script services functions
            payload = {k: v for k, v in payload.items() if v is not None}
            with patch(
                "app.services.script_service.insert_script"
            ) as mock_insert_script, patch(
                "app.services.script_service.get_script_by_id"
            ) as mock_get_script, patch(
                "app.services.integrations.script_rag_service.insert_script"
            ) as mock_rag_insert_script:
                mock_insert_script.return_value = "test-script-id"
                mock_rag_insert_script.return_value = None

                # Mock the created script response
                mock_script_response = {
                    "id": "test-script-id",
                    "name": name,
                    "description": description,
                    "solution": solution,
                    "status": "published",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
                mock_get_script.return_value = mock_script_response

                response = self.client.post("/scripts", json=payload)

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
            if expected_result.lower() == "true":
                result_record["ExpectedResult"] = "True"
            elif expected_result.lower() == "false":
                result_record["ExpectedResult"] = "False"
            else:
                result_record["ExpectedResult"] = expected_result

            # Standardize error logging in 'Log' column
            if response.status_code != 201:
                try:
                    error_detail = response.json().get("detail", {})
                    if isinstance(error_detail, dict) and "errors" in error_detail:
                        result_record["Log"] = "; ".join(error_detail["errors"])
                    else:
                        result_record["Log"] = str(error_detail)
                except:
                    result_record["Log"] = f"HTTP {response.status_code}"
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
                "TestCaseName",
                "Name",
                "Description",
                "Solution",
                "ExpectedResult",
            ]:
                if key not in failed_result:
                    failed_result[key] = "N/A due to error"
            return failed_result

    def _determine_test_result(self, test_case: dict, status_code: int) -> str:
        """Determine test result based on API response status code"""
        return "True" if status_code == 201 else "False"


def test_insert_script_from_excel():
    """Test insert_script API using Excel test data"""
    tester = InsertScriptExcelTester()
    results = tester.run_all_tests()
    summary = tester.get_test_summary(results)

    print(f"\nTest Summary for insert_script API:")
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
        tester = InsertScriptExcelTester()
        results = tester.run_all_tests()
        summary = tester.get_test_summary(results)

        print(f"\nTest Summary for insert_script API:")
        print(f"Total tests: {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Pass rate: {summary['pass_rate']}")
        print(f"Results written to: {tester.test_file_path}")

    main()
