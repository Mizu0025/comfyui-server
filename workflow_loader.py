import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WorkflowLoader:
    """
    Handles the loading of ComfyUI workflow definitions from JSON files stored on disk.
    """
    @staticmethod
    def load_workflow_data(workflow_path: str) -> Optional[Dict]:
        """
        Loads and parses a raw ComfyUI workflow JSON file from a specific absolute path.
        """
        try:
            logger.debug(f"Loading workflow data from {workflow_path}")
            if not os.path.exists(workflow_path):
                logger.error(f"Error: {workflow_path} not found.")
                raise Exception(f"{workflow_path} not found.")
            
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            logger.info(f"Workflow loaded successfully from {workflow_path}")
            return workflow_data
        except json.JSONDecodeError as e:
            logger.error(f"Error: Invalid JSON format in {workflow_path}: {e}")
            raise Exception(f"Invalid JSON format in {workflow_path}.")
        except Exception as e:
            logger.error(f"Error loading workflow data: {e}")
            raise e

    @staticmethod
    def load_workflow_by_name(workflow_name: str) -> Optional[Dict]:
        """
        Loads a named workflow from the 'workflows' directory.
        """
        # Assuming we are in image-service/ and workflows are in image-service/workflows/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(current_dir, "workflows", f"{workflow_name}.json")
        logger.info(f"Loading workflow: {workflow_name}")
        return WorkflowLoader.load_workflow_data(workflow_path)
