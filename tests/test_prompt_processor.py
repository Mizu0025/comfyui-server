import unittest
from prompt_processor import PromptProcessor

class TestPromptProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_workflow = {
            'Checkpoint': {'inputs': {'ckpt_name': 'old.safetensors'}},
            'KSampler': {'inputs': {'steps': 20, 'seed': 0, 'cfg': 8, 'sampler_name': 'euler'}},
            'EmptyLatentImage': {'inputs': {'width': 512, 'height': 512, 'batch_size': 1}},
            'PositivePrompt': {'inputs': {'text': ''}},
            'NegativePrompt': {'inputs': {'text': ''}}
        }
        self.model_config = {
            'checkpointName': 'new.safetensors',
            'imageWidth': 1024,
            'imageHeight': 1024,
            'defaultPositivePrompt': 'masterpiece, best quality',
            'defaultNegativePrompt': 'low quality',
            'steps': 30
        }
        self.global_defaults = {'WIDTH': 1024, 'HEIGHT': 1024, 'COUNT': 1, 'STEPS': 20}

    def test_create_prompt_data(self):
        data = PromptProcessor.create_prompt_data(self.mock_workflow)
        self.assertEqual(data['workflow'], self.mock_workflow)
        self.assertEqual(data['metadata']['model'], 'old.safetensors')
        self.assertEqual(data['metadata']['width'], 512)

    def test_update_prompt_with_model_config(self):
        prompt_wrapper = {"workflow": self.mock_workflow}
        filtered_prompt = {'prompt': 'a beautiful cat', 'width': 768, 'seed': 12345}
        
        PromptProcessor.update_prompt_with_model_config(
            prompt_wrapper, self.model_config, filtered_prompt, self.global_defaults
        )
        
        workflow = prompt_wrapper['workflow']
        self.assertEqual(workflow['Checkpoint']['inputs']['ckpt_name'], 'new.safetensors')
        self.assertEqual(workflow['KSampler']['inputs']['steps'], 30)
        self.assertEqual(workflow['KSampler']['inputs']['seed'], 12345)
        self.assertEqual(workflow['EmptyLatentImage']['inputs']['width'], 768) # User priority
        self.assertEqual(workflow['EmptyLatentImage']['inputs']['height'], 1024) # Model priority
        self.assertIn('masterpiece, best quality', workflow['PositivePrompt']['inputs']['text'])
        self.assertIn('a beautiful cat', workflow['PositivePrompt']['inputs']['text'])
        self.assertIn('low quality', workflow['NegativePrompt']['inputs']['text'])

    def test_random_seed(self):
        seed = PromptProcessor.generate_random_seed()
        self.assertTrue(1 <= seed <= 1000000)

if __name__ == "__main__":
    unittest.main()
