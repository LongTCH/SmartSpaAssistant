from datetime import datetime
from unittest.mock import patch

import pytest
from app.validations.notification_validations import validate_notification_data
from fastapi.testclient import TestClient
from tests.base_excel_test import BaseExcelTest

EXCEL_FILE = "tests/data/excel/insert_notification_test_data.xlsx"


class InsertNotificationExcelTester(BaseExcelTest):
    """Excel tester for insert_notification API (not a pytest test class)"""

    def __init__(self, app_or_client):
        super().__init__("insert_notification_test_data")
        if isinstance(app_or_client, TestClient):
            self.client = app_or_client
        else:
            self.client = TestClient(app_or_client)

    def execute_test_case(self, test_case: dict) -> dict:
        try:
            label = test_case.get("Label", "")
            description = test_case.get("Description", "")
            param_name = test_case.get("ParamName", "")
            param_type = test_case.get("ParamType", "")
            param_description = test_case.get("ParamDescription", "")

            notification = {
                "label": label,
                "description": description,
                "params": [
                    {
                        "param_name": param_name,
                        "param_type": param_type,
                        "description": param_description,
                    }
                ],
            }

            # Validate input
            errors = validate_notification_data(notification)
            expected_result = str(test_case.get("ExpectedResult", "")).strip().lower()
            # Call API only if no validation error
            if not errors:
                with patch(
                    "app.services.notification_service.insert_notification"
                ) as mock_insert:
                    mock_insert.return_value = {"id": "test-notification-id"}
                    response = self.client.post("/notifications", json=notification)
                    status_code = response.status_code
            else:
                status_code = 400

            logical_test_result = self._determine_test_result(test_case, status_code)
            result_record = test_case.copy()
            # ActualResult
            if str(logical_test_result).upper() == "TRUE":
                result_record["ActualResult"] = "True"
            else:
                result_record["ActualResult"] = "False"
            # ExpectedResult
            if expected_result == "true":
                result_record["ExpectedResult"] = "True"
            elif expected_result == "false":
                result_record["ExpectedResult"] = "False"
            # Status
            if status_code != 201:
                result_record["Status"] = (
                    "; ".join(errors) if errors else f"HTTP {status_code}"
                )
            else:
                result_record["Status"] = None
            result_record["Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return result_record
        except Exception as e:
            failed_result = test_case.copy()
            failed_result["ActualResult"] = "Fail"
            failed_result["Status"] = f"Test execution error: {str(e)}"
            failed_result["Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for key in [
                "Label",
                "Description",
                "ParamName",
                "ParamType",
                "ParamDescription",
                "ExpectedResult",
            ]:
                if key not in failed_result:
                    failed_result[key] = "N/A due to error"
            return failed_result

    def _determine_test_result(self, test_case: dict, status_code: int) -> str:
        return "True" if status_code == 201 else "False"


@pytest.mark.asyncio
async def test_insert_notification_from_excel(test_app):
    tester = InsertNotificationExcelTester(test_app)
    results = tester.run_all_tests()
    summary = tester.get_test_summary(results)
    print(f"\nTest Summary for insert_notification API:")
    print(f"Total tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass rate: {summary['pass_rate']}")
    print(f"Results written to: {tester.test_file_path}")
    assert len(results) > 0, "No test cases found"
    assert (
        summary["failed"] == 0
    ), f"{summary['failed']} tests did not match expected outcomes. Check {tester.test_file_path}"
