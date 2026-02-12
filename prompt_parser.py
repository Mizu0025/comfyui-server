import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PromptParser:
    """
    Parses user input message into structured image generation parameters.
    Supports various flags (e.g., --width, --height, --model) and their short aliases.
    """
    
    MODIFIER_MAP = {
        'width': ['--width', '-w'],
        'height': ['--height', '-h'],
        'model': ['--model', '-m'],
        'negative_prompt': ['--no', '--negative', '-n'],
        'count': ['--count', '-c'],
        'seed': ['--seed', '-s']
    }

    @staticmethod
    def parse_input(input_str: str) -> Dict[str, Any]:
        """
        Parses the input string with modifiers into a structured dict.
        """
        result = {
            'prompt': "",
            'width': None,
            'height': None,
            'model': None,
            'negative_prompt': None,
            'count': None,
            'seed': -1
        }

        # Flatten all aliases for regex
        all_aliases = [alias for aliases in PromptParser.MODIFIER_MAP.values() for alias in aliases]
        alias_pattern = r'(?:^|\s)(' + '|'.join(re.escape(a) for a in all_aliases) + r')(?=[\s=]|$)'
        
        matches = list(re.finditer(alias_pattern, input_str))
        
        if not matches:
            result['prompt'] = input_str.strip()
            return result

        # Everything before the first modifier is the prompt
        result['prompt'] = input_str[:matches[0].start()].strip()

        # Process each modifier
        for i in range(len(matches)):
            match = matches[i]
            flag = match.group(1)
            start = match.end()
            
            # Determine end of value (start of next flag or end of string)
            end = matches[i+1].start() if i + 1 < len(matches) else len(input_str)
            value = input_str[start:end].strip()
            
            if value.startswith('='):
                value = value[1:].strip()
            
            PromptParser._apply_modifier(result, flag, value)

        return result

    @staticmethod
    def _apply_modifier(result: Dict, flag: str, value: str):
        for key, aliases in PromptParser.MODIFIER_MAP.items():
            if flag in aliases:
                if key in ['width', 'height', 'count', 'seed']:
                    try:
                        result[key] = int(value)
                    except ValueError:
                        pass
                else:
                    result[key] = value
                break
