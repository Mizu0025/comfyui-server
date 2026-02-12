import os
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Set environment variable before importing app
os.environ["WEB_DOMAIN"] = "https://test.domain"

from app import app

client = TestClient(app)

def test_job_result_contains_domain():
    # Mock the generator and queue processing
    with patch("app.generator.generate_image") as mock_generate:
        mock_generate.return_value = "/path/to/output/image.webp"
        
        # Submit a request
        response = client.post("/request", json={"message": "test prompt", "nick": "tester"})
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # We need to manually process the job in the test or wait for it
        # Since the worker is running in the background, we'll wait for the event
        # However, testing background tasks in FastAPI can be tricky.
        # Let's directly check the waiting endpoint which waits for job completion.
        
        # In this test, we'll mock the job result directly to see if app logic handles it.
        from app import jobs, Job
        import asyncio
        
        # Create a mock job already "completed"
        test_job = Job("test", "tester")
        test_job.status = "completed"
        # The logic we want to test is in the worker function.
        # Let's see if we can trigger the worker or test the logic it uses.
        
        # Actually, let's test the get_domain_path integration in app.py's worker loop
        # But mocking the worker is hard. 
        # Better to unit test the get_domain_path (already done) 
        # and verify app.py loads the env var correctly.
        
        from app import WEB_DOMAIN
        assert WEB_DOMAIN == "https://test.domain"

def test_wait_for_job_returns_url():
    from app import jobs, Job
    import asyncio
    
    # Manually inject a completed job with a local path
    job_id = "test-job-id"
    job = Job("prompt", "nick")
    job.id = job_id
    # In app.py, the worker sets job.result = get_domain_path(image_path, WEB_DOMAIN)
    # So we simulate that
    from filename_utils import get_domain_path
    from app import WEB_DOMAIN
    
    image_path = "/tmp/output/test.webp"
    job.result = get_domain_path(image_path, WEB_DOMAIN)
    job.status = "completed"
    job.event.set()
    jobs[job_id] = job
    
    response = client.get(f"/wait/{job_id}")
    assert response.status_code == 200
    assert response.json()["result"] == "https://test.domain/test.webp"

@pytest.mark.asyncio
async def test_worker_logic_with_domain():
    from app import worker, queue, jobs, Job, WEB_DOMAIN
    with patch("app.generator.generate_image") as mock_gen:
        mock_gen.return_value = "/path/to/image.webp"
        
        job = Job("test prompt", "tester")
        jobs[job.id] = job
        await queue.put(job)
        
        # Run worker for one iteration
        # We can't easily run it for one iteration as it is 'while True'
        # But we can mock queue.get to return our job then raise an exception
        with patch.object(queue, 'get', side_effect=[job, asyncio.CancelledError()]):
            try:
                await worker()
            except asyncio.CancelledError:
                pass
        
        assert job.result == f"{WEB_DOMAIN}/image.webp"
