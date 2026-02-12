import unittest
from prompt_parser import PromptParser

class TestPromptParser(unittest.TestCase):
    def test_basic_prompt(self):
        input_str = "a beautiful cat"
        result = PromptParser.parse_input(input_str)
        self.assertEqual(result['prompt'], "a beautiful cat")
        self.assertIsNone(result['width'])
        self.assertIsNone(result['model'])

    def test_modifiers_full(self):
        input_str = "a cat --width 1024 --height 768 --model sdxl --no blurry --count 2 --seed 12345"
        result = PromptParser.parse_input(input_str)
        self.assertEqual(result['prompt'], "a cat")
        self.assertEqual(result['width'], 1024)
        self.assertEqual(result['height'], 768)
        self.assertEqual(result['model'], "sdxl")
        self.assertEqual(result['negative_prompt'], "blurry")
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['seed'], 12345)

    def test_modifiers_short(self):
        input_str = "a dog -w 512 -h 512 -m lumina -n text -c 1 -s 42"
        result = PromptParser.parse_input(input_str)
        self.assertEqual(result['prompt'], "a dog")
        self.assertEqual(result['width'], 512)
        self.assertEqual(result['height'], 512)
        self.assertEqual(result['model'], "lumina")
        self.assertEqual(result['negative_prompt'], "text")
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['seed'], 42)

    def test_modifiers_with_equals(self):
        input_str = "landscape --width=1280 --height=720"
        result = PromptParser.parse_input(input_str)
        self.assertEqual(result['prompt'], "landscape")
        self.assertEqual(result['width'], 1280)
        self.assertEqual(result['height'], 720)

    def test_invalid_int_modifier(self):
        input_str = "cat --width invalid"
        result = PromptParser.parse_input(input_str)
        self.assertIsNone(result['width'])
        self.assertEqual(result['prompt'], "cat")

    def test_multiple_aliases_for_same_key(self):
        input_str = "test --no bad stuff -n more bad"
        result = PromptParser.parse_input(input_str)
        self.assertEqual(result['prompt'], "test")
        # In the current implementation, it will just overwrite.
        self.assertEqual(result['negative_prompt'], "more bad")

if __name__ == "__main__":
    unittest.main()
