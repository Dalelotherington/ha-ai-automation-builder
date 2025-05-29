#!/usr/bin/env python3
"""
AI Automation Builder - Main Application
Automatically handles dependencies and runs the Flask application
"""

import os
import sys
import logging
import json
import yaml  # type: ignore[import]
import requests  # type: ignore[import]
import traceback
from flask import Flask, render_template, request, jsonify  # type: ignore[import]

# Configure logging early with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Debug output for startup troubleshooting
print("=====================================")
print("AI Automation Builder Startup")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print("=====================================")

# Global flag to track LLM status
llm_initialized = False

def check_and_install_dependencies():
    """Check and install dependencies before running the app"""
    try:
        # Try to import dependency manager
        print("Checking for dependency_manager.py...")
        if not os.path.exists('dependency_manager.py'):
            logger.error("dependency_manager.py not found in current directory!")
            print(f"Files in current directory: {os.listdir('.')}")
            return False
            
        from dependency_manager import DependencyManager  # type: ignore[import]
        
        logger.info("Running dependency check...")
        manager = DependencyManager()
        
        if not manager.run_dependency_check():
            logger.error("Dependency check failed. Cannot start application.")
            return False
            
    except ImportError as e:
        logger.error(f"dependency_manager.py import error: {e}")
        print(f"ImportError: {e}")
        print(f"sys.path: {sys.path}")
        return False
    except Exception as e:
        logger.error(f"Error during dependency check: {e}")
        print(f"Exception: {e}")
        print(traceback.format_exc())
        return False
    
    return True

def initialize_llm():
    """Initialize the LLM if dependencies are available"""
    global llm_initialized
    
    try:
        print("Checking for llm_integration.py...")
        if not os.path.exists('llm_integration.py'):
            logger.error("llm_integration.py not found in current directory!")
            print(f"Files in current directory: {os.listdir('.')}")
            return False
            
        from llm_integration import get_llm_manager  # type: ignore[import]
        
        # Get the LLM manager
        llm_manager = get_llm_manager()
        
        # Try to initialize with TinyLlama (small and efficient)
        model_name = os.environ.get('LLM_MODEL', 'tinyllama.gguf')
        llm_initialized = llm_manager.initialize(model_name=model_name)
        
        if llm_initialized:
            logger.info(f"✅ LLM initialized successfully with model: {model_name}")
        else:
            logger.warning("⚠️ LLM initialization failed. Will use template-based generation.")
            
    except ImportError as e:
        logger.warning(f"⚠️ LLM integration module import error: {e}")
        print(f"LLM ImportError: {e}")
        print(f"sys.path: {sys.path}")
    except Exception as e:
        logger.error(f"❌ Error initializing LLM: {e}")
        print(f"LLM Exception: {e}")
        print(traceback.format_exc())
    
    return llm_initialized

def main():
    """Main application entry point"""
    print("=== AI Automation Builder ===")
    print("Starting application...")
    
    # Check for command line arguments
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        print(f"Command line arguments: {sys.argv}")
        print(f"Environment variables: {os.environ}")
    
    # Check and install dependencies first
    print("Checking dependencies...")
    if not check_and_install_dependencies():
        print("❌ Dependency check failed. Exiting.")
        return 1
    
    # Now try to import required modules
    try:
        print("✅ All dependencies loaded successfully!")
        
        # Try to initialize LLM in background
        use_llm = os.environ.get('USE_LLM', 'true').lower() == 'true'
        print(f"LLM enabled in config: {use_llm}")
        
        if use_llm:
            print("Initializing LLM...")
            initialize_llm()
        else:
            logger.info("LLM disabled by configuration.")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        print(traceback.format_exc())
        return 1
    
    # Start the Flask application
    return run_flask_app()

def run_flask_app():
    """Run the main Flask application"""
    try:
        print("Starting AI Automation Builder app...")
        
        app = Flask(__name__)
        
        # Configuration
        API_KEY = os.environ.get('API_KEY', '')
        MODEL = os.environ.get('MODEL', 'gpt-3.5-turbo')
        PORT = int(os.environ.get('PORT', 5001))
        HA_URL = os.environ.get('HA_URL', 'http://supervisor/core')
        HA_TOKEN = os.environ.get('HA_TOKEN', '')
        
        # If HA_TOKEN is empty or whitespace, set to None for cleaner handling
        if not HA_TOKEN or HA_TOKEN.strip() == '':
            HA_TOKEN = None
            logger.warning("Home Assistant token is not available. Running in limited mode.")
        else:
            logger.info("Home Assistant token is available.")
        
        print(f"Web server will start on port {PORT}")
        print(f"Home Assistant API URL: {HA_URL}")
        print(f"Home Assistant token available: {HA_TOKEN is not None}")
        
        # Fix for Home Assistant ingress
        app.config['APPLICATION_ROOT'] = '/'
        app.config['PREFERRED_URL_SCHEME'] = 'http'
        
        @app.route('/')
        def index():
            """Main page for the AI Automation Builder"""
            print(f"Serving index page request from {request.remote_addr}")
            return render_template('index.html')
        
        @app.route('/api/entities', methods=['GET'])
        def get_entities():
            """Get entities from Home Assistant"""
            try:
                if not HA_TOKEN:
                    return jsonify({
                        'error': 'Home Assistant token not available',
                        'domains': {},
                        'entities': []
                    }), 200  # Return empty result but OK status to avoid UI errors
                    
                headers = {
                    "Authorization": f"Bearer {HA_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                print(f"Fetching entities from Home Assistant at {HA_URL}/api/states")
                response = requests.get(
                    f"{HA_URL}/api/states",
                    headers=headers,
                    timeout=10  # Add a timeout
                )
                
                if response.status_code != 200:
                    print(f"Error fetching entities: {response.status_code} - {response.text}")
                    return jsonify({'error': f'Failed to fetch entities: {response.text}'}), response.status_code
                
                entities = response.json()
                
                # Organize entities by domain
                domains = {}
                for entity in entities:
                    entity_id = entity['entity_id']
                    domain = entity_id.split('.')[0]
                    
                    if domain not in domains:
                        domains[domain] = []
                    
                    domains[domain].append({
                        'entity_id': entity_id,
                        'name': entity.get('attributes', {}).get('friendly_name', entity_id),
                        'state': entity['state'],
                        'attributes': entity['attributes']
                    })
                
                print(f"Found {len(entities)} entities across {len(domains)} domains")
                return jsonify({
                    'entities': entities,
                    'domains': domains
                })
                
            except requests.exceptions.RequestException as e:
                print(f"Request error fetching entities: {e}")
                print(traceback.format_exc())
                return jsonify({
                    'error': f'Connection error: {str(e)}',
                    'domains': {},
                    'entities': []
                }), 200  # Return empty result but OK status
            except Exception as e:
                print(f"Error fetching entities: {e}")
                print(traceback.format_exc())
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/entity/test', methods=['POST'])
        def test_entity():
            """Test an entity by turning it on or off"""
            try:
                if not HA_TOKEN:
                    return jsonify({'error': 'Home Assistant token not available', 'success': False}), 200
                
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                entity_id = data.get('entity_id')
                action = data.get('action', 'toggle')
                
                if not entity_id:
                    return jsonify({'error': 'No entity_id provided'}), 400
                
                domain = entity_id.split('.')[0]
                service = action  # 'toggle', 'turn_on', 'turn_off'
                
                headers = {
                    "Authorization": f"Bearer {HA_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                print(f"Testing entity {entity_id} with action {action}")
                response = requests.post(
                    f"{HA_URL}/api/services/{domain}/{service}",
                    headers=headers,
                    json={"entity_id": entity_id},
                    timeout=10  # Add a timeout
                )
                
                if response.status_code not in (200, 201):
                    print(f"Error testing entity: {response.status_code} - {response.text}")
                    return jsonify({'error': f'Failed to test entity: {response.text}'}), response.status_code
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully tested {entity_id} with {action}'
                })
                
            except requests.exceptions.RequestException as e:
                print(f"Request error testing entity: {e}")
                print(traceback.format_exc())
                return jsonify({'error': f'Connection error: {str(e)}', 'success': False}), 200
            except Exception as e:
                print(f"Error testing entity: {e}")
                print(traceback.format_exc())
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/generate', methods=['POST'])
        def generate_automation():
            """Generate automation from natural language description"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
        
                description = data.get('description', '')
        
                if not description:
                    return jsonify({'error': 'No description provided'}), 400
        
                print(f"Generating automation for: {description}")
                
                # Create automation YAML based on description
                automation = create_automation_from_description(description)
        
                return jsonify({
                    'automation': automation,
                    'yaml': yaml.dump(automation, default_flow_style=False, sort_keys=False)
                })
        
            except Exception as e:
                logger.error(f"Error generating automation: {str(e)}")
                print(traceback.format_exc())
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/save', methods=['POST'])
        def save_automation():
            """Save automation to Home Assistant"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
        
                automation = data.get('automation')
        
                if not automation:
                    return jsonify({'error': 'No automation data provided'}), 400
        
                # If HA_TOKEN is provided, attempt to save to Home Assistant
                if HA_TOKEN:
                    try:
                        return save_to_home_assistant(automation)
                    except Exception as e:
                        logger.error(f"Error saving to Home Assistant: {str(e)}")
                        print(traceback.format_exc())
                        return jsonify({'error': f"Error saving to Home Assistant: {str(e)}"}), 500
                else:
                    # Return mock success for demo mode
                    return jsonify({
                        'success': True,
                        'message': 'Automation created successfully (demo mode - no HA token provided)'
                    })
        
            except Exception as e:
                logger.error(f"Error saving automation: {str(e)}")
                print(traceback.format_exc())
                return jsonify({'error': str(e)}), 500
        
        def save_to_home_assistant(automation):
            """Save automation to Home Assistant via API"""
            # Generate a filename from the alias
            filename = automation.get('alias', 'ai_generated').lower().replace(' ', '_')[:40]
            if not filename.endswith('.yaml'):
                filename += '.yaml'
            
            headers = {
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # First check if the file exists
            config_path = f"{HA_URL}/api/config/automation/config/{filename}"
            try:
                print(f"Saving automation to Home Assistant: {filename}")
                response = requests.post(
                    f"{HA_URL}/api/services/automation/reload",
                    headers=headers,
                    timeout=10  # Add a timeout
                )
                
                if response.status_code not in (200, 201):
                    logger.warning(f"Failed to reload automations: {response.text}")
                    
                # Convert to YAML and save
                yaml_content = yaml.dump(automation, default_flow_style=False, sort_keys=False)
                
                # Save to Home Assistant's config directory
                print(f"Posting to {config_path}")
                response = requests.post(
                    config_path,
                    headers=headers,
                    json={"content": yaml_content},
                    timeout=10  # Add a timeout
                )
                
                if response.status_code in (200, 201):
                    print(f"Successfully saved automation to {filename}")
                    return jsonify({
                        'success': True,
                        'message': f'Automation saved successfully to {filename}',
                        'filename': filename
                    })
                else:
                    print(f"Error saving to Home Assistant: {response.status_code} - {response.text}")
                    return jsonify({
                        'success': False,
                        'message': f'Error saving to Home Assistant: {response.text}'
                    }), response.status_code
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                print(traceback.format_exc())
                return jsonify({
                    'success': False,
                    'message': f'Connection error: {str(e)}'
                }), 500
        
        def create_automation_from_description(description):
            """Create a basic automation structure from description"""
            # Try to use LLM if available
            if llm_initialized:
                try:
                    from llm_integration import get_llm_manager  # type: ignore[import]
                    llm_manager = get_llm_manager()
                    return llm_manager.generate_automation(description)
                except Exception as e:
                    logger.error(f"Error using LLM for generation: {e}")
                    print(traceback.format_exc())
                    # Fall back to template-based approach
            
            # Template-based approach (fallback)
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
            
            # Simple rule-based enhancements
            if "sunset" in description.lower() or "dusk" in description.lower():
                automation["trigger"] = [{"platform": "sun", "event": "sunset", "offset": "0:00:00"}]
                
            if "sunrise" in description.lower() or "dawn" in description.lower():
                automation["trigger"] = [{"platform": "sun", "event": "sunrise", "offset": "0:00:00"}]
                
            if "motion" in description.lower() and "detected" in description.lower():
                automation["trigger"] = [{"platform": "state", "entity_id": "binary_sensor.motion_sensor", "to": "on"}]
                
            if "light" in description.lower() and "on" in description.lower():
                automation["action"] = [{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}]
                
            if "light" in description.lower() and "off" in description.lower():
                automation["action"] = [{"service": "light.turn_off", "target": {"entity_id": "light.living_room"}}]
        
            return automation
        
        @app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy', 
                'service': 'AI Automation Builder',
                'ha_connected': bool(HA_TOKEN and HA_URL),
                'llm_enabled': llm_initialized,
                'dependencies_ok': True
            })
        
        @app.route('/api/dependencies')
        def check_dependencies_endpoint():
            """Endpoint to check dependency status"""
            try:
                from dependency_manager import DependencyManager
                manager = DependencyManager()
                status = manager.check_all_dependencies()
                
                return jsonify({
                    'status': 'success',
                    'dependencies': status,
                    'all_installed': all(info['installed'] for info in status.values())
                })
                
            except Exception as e:
                print(f"Error checking dependencies: {e}")
                print(traceback.format_exc())
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        # Start the Flask application
        logger.info(f"Starting AI Automation Builder on port {PORT}")
        logger.info("✅ All systems ready!")
        print(f"✅ Web server started on port {PORT}")
        print("✅ AI Automation Builder is now ready to use!")
        
        # Run with host set to 0.0.0.0 to make it accessible outside container
        app.run(host='0.0.0.0', port=PORT, debug=(os.environ.get('DEBUG', 'false').lower() == 'true'))
        return 0
        
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        print(f"CRITICAL ERROR: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == '__main__':
    try:
        print("Entering main() function")
        exit_code = main()
        print(f"Exiting with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Unhandled exception in main application: {e}")
        print(traceback.format_exc())
        sys.exit(1)