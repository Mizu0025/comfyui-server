import random
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class PromptProcessor:
    """
    Handles the extraction and transformation of workflow data into 
    a structured prompt representation, and applies model-specific configurations.
    """
    @staticmethod
    def create_prompt_data(workflow_data: Dict) -> Dict:
        """
        Extracts and flattens core generation parameters from a raw 
        ComfyUI workflow.
        """
        logger.debug("Creating prompt data from workflow data")
        
        # In the original TS, this returned a PromptData object with flattened fields.
        # But it also kept the original 'data' (workflow).
        # We'll just return a dict that includes the workflow and extracted metadata.
        
        checkpoint = workflow_data.get('Checkpoint', {})
        vae_loader = workflow_data.get('VAELoader', {})
        ksampler = workflow_data.get('KSampler', {})
        latent_image = workflow_data.get('EmptyLatentImage', {})
        positive_prompt = workflow_data.get('PositivePrompt', {})
        negative_prompt = workflow_data.get('NegativePrompt', {})
        
        # Extract metadata for logging/tracking if needed
        metadata = {
            "model": checkpoint.get('inputs', {}).get('ckpt_name', ""),
            "vae": vae_loader.get('inputs', {}).get('vae_name', ""),
            "seed": ksampler.get('inputs', {}).get('seed', 0),
            "steps": ksampler.get('inputs', {}).get('steps', 0),
            "width": latent_image.get('inputs', {}).get('width', 1024),
            "height": latent_image.get('inputs', {}).get('height', 1024),
            "batch_size": latent_image.get('inputs', {}).get('batch_size', 1),
            "cfg": ksampler.get('inputs', {}).get('cfg', 8),
            "sampler": ksampler.get('inputs', {}).get('sampler_name', "euler")
        }
        
        return {
            "workflow": workflow_data,
            "metadata": metadata
        }

    @staticmethod
    def update_prompt_with_model_config(
        prompt_wrapper: Dict,
        model_config: Dict,
        filtered_prompt: Dict,
        global_defaults: Dict
    ) -> None:
        """
        Maps user-provided prompt data and model-specific configurations 
        onto the internal ComfyUI workflow nodes.
        """
        workflow = prompt_wrapper["workflow"]
        
        # Update the workflow data with model configuration
        if 'Checkpoint' in workflow and model_config.get('checkpointName'):
            workflow['Checkpoint']['inputs']['ckpt_name'] = model_config['checkpointName']

        if 'UNETLoader' in workflow and model_config.get('unetName'):
            workflow['UNETLoader']['inputs']['unet_name'] = model_config['unetName']

        if 'CLIPLoader' in workflow and model_config.get('clipName'):
            workflow['CLIPLoader']['inputs']['clip_name'] = model_config['clipName']

        if 'VAELoader' in workflow and model_config.get('vae'):
            workflow['VAELoader']['inputs']['vae_name'] = model_config['vae']

        if 'KSampler' in workflow:
            inputs = workflow['KSampler']['inputs']
            inputs['steps'] = model_config.get('steps') or global_defaults.get('STEPS', 20)
            if model_config.get('cfg'):
                inputs['cfg'] = model_config['cfg']
            if model_config.get('sampler_name'):
                inputs['sampler_name'] = model_config['sampler_name']
            
            requested_seed = filtered_prompt.get('seed', -1)
            inputs['seed'] = PromptProcessor.generate_random_seed() if requested_seed == -1 else requested_seed

        if 'EmptyLatentImage' in workflow or 'EmptySD3LatentImage' in workflow:
            # Handle both node types
            node_key = 'EmptyLatentImage' if 'EmptyLatentImage' in workflow else 'EmptySD3LatentImage'
            inputs = workflow[node_key]['inputs']
            
            # Priority: User > Model > Global
            inputs['width'] = filtered_prompt.get('width') or model_config.get('imageWidth') or global_defaults.get('WIDTH', 1024)
            inputs['height'] = filtered_prompt.get('height') or model_config.get('imageHeight') or global_defaults.get('HEIGHT', 1024)
            inputs['batch_size'] = filtered_prompt.get('count') or model_config.get('COUNT') or global_defaults.get('COUNT', 1)

        # Handle prompt concatenation
        if 'PromptConcatenate' in workflow:
            # If workflow uses PromptConcatenate, update string_a with default prompt and string_b with user prompt
            workflow['PromptConcatenate']['inputs']['string_a'] = model_config['defaultPositivePrompt']
            workflow['PromptConcatenate']['inputs']['string_b'] = filtered_prompt.get('prompt') or ''
        else:
            # Fallback to direct text assignment for workflows without PromptConcatenate
            if 'PositivePrompt' in workflow:
                default_pos = model_config.get('defaultPositivePrompt', '')
                user_pos = filtered_prompt.get('prompt') or ''
                workflow['PositivePrompt']['inputs']['text'] = f"{default_pos}, {user_pos}".strip(", ")

        # Update negative prompt
        if 'NegativePrompt' in workflow:
            default_neg = model_config.get('defaultNegativePrompt', '')
            user_neg = filtered_prompt.get('negative_prompt') or ''
            workflow['NegativePrompt']['inputs']['text'] = f"nsfw, nude, {default_neg}, {user_neg}".strip(", ")

        logger.debug('Workflow updated with model configuration')

    @staticmethod
    def generate_random_seed() -> int:
        """
        Generates a random integer between 1 and 1,000,000 for use as a seed.
        """
        seed = random.randint(1, 1000000)
        logger.debug(f"Generated random seed: {seed}")
        return seed
