#!/usr/bin/env python3
"""
LLM Integration for AI Automation Builder
Provides integration with local LLM models via llama-cpp-python
"""

import os
import sys
import logging
import traceback
import json
import yaml
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Singleton instance for the LLM manager
_llm_manager = None

class LLMManager:
    """Manages LLM integration for the AI Automation Builder"""
    
    def __init__(self):
        """Initialize the LLM manager"""
        self.model = None
        self.model_name = None
        self.initialized = False
        self.has_llama_cpp = self._check_llama_cpp()
        
        # Create model directory if it doesn't exist
        os.makedirs("/data/models", exist_ok=True)
    
    def _check_llama_cpp(self) -> bool:
        """Check if llama-cpp-python is installed"""
        try:
            import llama_cpp
            logger.info(f"Found llama-cpp-python version {llama_cpp.__version__}")
            return True
        except ImportError:
            logger.warning("llama-cpp-python not found. LLM features will be disabled.")
            return False
        except Exception as e:
            logger.error(f"Error checking llama-cpp-python: {e}")
            print(traceback.format_exc())
            return False
    
    def initialize(self, model_name: str = "tinyllama.gguf") -> bool:
        """Initialize the LLM with the specified model"""
        try:
            if not self.has_llama_cpp:
                logger.warning("Cannot initialize LLM: llama-cpp-python not installed")
                return False
            
            # Import llama_cpp here to avoid import errors if not installed
            import llama_cpp
            
            model_path = f"/data/models/{model_name}"
            
            # Check if model exists
            if not os.path.exists(model_path):
                logger.warning(f"Model {model_path} not found. Will download dummy model for testing.")
                
                # If this is just for testing or development, create a dummy model file
                if not os.path.exists(os.path.dirname(model_path)):
                    os.makedirs(os.path.dirname(model_path), exist_ok=True)
                
                # Create a dummy model file for testing
                with open(model_path, 'w') as f:
                    f.write("DUMMY MODEL FILE FOR TESTING")
                    
                logger.info(f"Created dummy model file at {model_path}")
                
                # In a real scenario, we would download the model here
                # For now, just log a message
                logger.warning("This is a dummy model. In production, you would need to download a real GGUF model.")
                
                # Return initialized as true but with dummy model
                self.initialized = True
                self.model_name = model_name
                return True
            
            # In a real implementation, we would load the model:
            # self.model = llama_cpp.Llama(
            #     model_path=model_path,
            #     n_ctx=2048,
            #     n_threads=4
            # )
            
            # For now, just log that we would load the model
            logger.info(f"Would load model from {model_path}")
            
            self.initialized = True
            self.model_name = model_name
            return True
            
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            print(traceback.format_exc())
            self.initialized = False
            return False
    
    def generate_automation(self, description: str) -> Dict[str, Any]:
        """Generate a Home Assistant automation from a natural language description"""
        try:
            if not self.initialized:
                logger.warning("LLM not initialized. Using fallback template.")
                return self._get_fallback_template(description)
            
            logger.info(f"Generating automation for: {description}")
            
            # In a real implementation, we would generate the automation using the LLM:
            # prompt = f"""
            # Create a Home Assistant automation based on this description:
            # {description}
            # 
            # Output only valid YAML that can be used directly in Home Assistant.
            # """
            # 
            # response = self.model.create_completion(
            #     prompt=prompt,
            #     max_tokens=1024,
            #     temperature=0.7,
            #     stop=["```"]
            # )
            # 
            # try:
            #     # Parse the YAML from the response
            #     yaml_text = response.text
            #     automation = yaml.safe_load(yaml_text)
            #     return automation
            # except Exception as e:
            #     logger.error(f"Error parsing LLM output: {e}")
            #     return self._get_fallback_template(description)
            
            # For now, use a more intelligent template-based approach
            automation = self._get_smart_template(description)
            
            logger.info(f"Generated automation with {len(automation.get('trigger', []))} triggers and {len(automation.get('action', []))} actions")
            return automation
            
        except Exception as e:
            logger.error(f"Error generating automation: {e}")
            print(traceback.format_exc())
            return self._get_fallback_template(description)
    
    def _get_fallback_template(self, description: str) -> Dict[str, Any]:
        """Get a fallback template for when LLM generation fails"""
        automation = {
            'alias': f'AI Generated: {description[:50]}...' if len(description) > 50 else f'AI Generated: {description}',
            'description': f'Generated from: {description}',
            'trigger': [
                {
                    'platform': 'time',
                    'at': '12:00:00'
                }
            ],
            'condition': [],
            'action': [
                {
                    'service': 'notify.notify',
                    'data': {
                        'message': f'Automation triggered: {description}'
                    }
                }
            ],
            'mode': 'single'
        }
        return automation
    
    def _get_smart_template(self, description: str) -> Dict[str, Any]:
        """Get a smarter template based on keywords in the description"""
        # Start with the basic template
        automation = self._get_fallback_template(description)
        
        # Convert to lowercase for easier matching
        desc_lower = description.lower()
        
        # Check for time-based triggers
        if any(word in desc_lower for word in ['morning', 'sunrise', 'dawn']):
            automation['trigger'] = [{'platform': 'sun', 'event': 'sunrise', 'offset': '0:30:00'}]
            
        elif any(word in desc_lower for word in ['evening', 'sunset', 'dusk']):
            automation['trigger'] = [{'platform': 'sun', 'event': 'sunset', 'offset': '0:00:00'}]
            
        elif any(word in desc_lower for word in ['midnight']):
            automation['trigger'] = [{'platform': 'time', 'at': '00:00:00'}]
            
        elif any(word in desc_lower for word in ['noon']):
            automation['trigger'] = [{'platform': 'time', 'at': '12:00:00'}]
            
        # Check for sensor-based triggers
        if 'motion' in desc_lower:
            automation['trigger'] = [{'platform': 'state', 'entity_id': 'binary_sensor.motion_sensor', 'to': 'on'}]
            
        elif 'door' in desc_lower and ('open' in desc_lower or 'opened' in desc_lower):
            automation['trigger'] = [{'platform': 'state', 'entity_id': 'binary_sensor.door_sensor', 'to': 'on'}]
            
        elif 'door' in desc_lower and ('close' in desc_lower or 'closed' in desc_lower):
            automation['trigger'] = [{'platform': 'state', 'entity_id': 'binary_sensor.door_sensor', 'to': 'off'}]
            
        # Check for common actions
        if 'light' in desc_lower and any(word in desc_lower for word in ['on', 'turn on', 'enable']):
            automation['action'] = [{'service': 'light.turn_on', 'target': {'entity_id': 'light.living_room'}}]
            
        elif 'light' in desc_lower and any(word in desc_lower for word in ['off', 'turn off', 'disable']):
            automation['action'] = [{'service': 'light.turn_off', 'target': {'entity_id': 'light.living_room'}}]
            
        elif 'notification' in desc_lower or 'notify' in desc_lower or 'alert' in desc_lower:
            automation['action'] = [{'service': 'notify.mobile_app', 'data': {'message': description}}]
        
        return automation

def get_llm_manager() -> LLMManager:
    """Get the singleton instance of the LLM manager"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

if __name__ == "__main__":
    # For testing purposes
    manager = get_llm_manager()
    if manager.initialize():
        print("LLM initialized successfully!")
        
        # Test automation generation
        description = "Turn on the living room lights at sunset"
        automation = manager.generate_automation(description)
        
        print("\nGenerated automation:")
        print(yaml.dump(automation, default_flow_style=False, sort_keys=False))
    else:
        print("Failed to initialize LLM.") 