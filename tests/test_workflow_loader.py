import unittest
import os
import json
from unittest.mock import patch, mock_open
from workflow_loader import WorkflowLoader

class TestWorkflowLoader(unittest.TestCase):
    def test_load_workflow_data_success(self):
        mock_data = {"test": "data"}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            with patch("os.path.exists", return_value=True):
                result = WorkflowLoader.load_workflow_data("/path/to/workflow.json")
                self.assertEqual(result, mock_data)

    def test_load_workflow_data_not_found(self):
        with patch("os.path.exists", return_value=False):
            with self.assertRaises(Exception) as cm:
                WorkflowLoader.load_workflow_data("/path/to/missing.json")
            self.assertIn("not found", str(cm.exception))

    def test_load_workflow_data_invalid_json(self):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists", return_value=True):
                with self.assertRaises(Exception) as cm:
                    WorkflowLoader.load_workflow_data("/path/to/invalid.json")
                self.assertIn("Invalid JSON format", str(cm.exception))

    def test_load_workflow_by_name(self):
        mock_data = {"name": "test_workflow"}
        with patch("workflow_loader.WorkflowLoader.load_workflow_data", return_value=mock_data) as mock_load:
            result = WorkflowLoader.load_workflow_by_name("test")
            self.assertEqual(result, mock_data)
            mock_load.assert_called_once()
            # Verify it constructs the right path
            call_args = mock_load.call_args[0][0]
            self.assertTrue(call_args.endswith("workflows/test.json"))

if __name__ == "__main__":
    unittest.main()
