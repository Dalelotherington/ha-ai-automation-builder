#!/usr/bin/env python3
"""
Dependency Manager for AI Automation Builder
Checks and manages dependencies for the application
"""

import os
import sys
import logging
import importlib.util
import subprocess
import traceback
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DependencyManager:
    """Manages dependencies for the AI Automation Builder"""
    
    def __init__(self):
        """Initialize the dependency manager"""
        self.dependencies = {
            'flask': {
                'package': 'flask',
                'import_name': 'flask',
                'version': '>=2.0.0',
                'installed': False
            },
            'pyyaml': {
                'package': 'pyyaml',
                'import_name': 'yaml',
                'version': '>=6.0',
                'installed': False
            },
            'requests': {
                'package': 'requests',
                'import_name': 'requests',
                'version': '>=2.25.0',
                'installed': False
            }
        }
        
        # Optional LLM dependencies
        self.optional_dependencies = {
            'llama-cpp-python': {
                'package': 'llama-cpp-python',
                'import_name': 'llama_cpp',
                'version': '>=0.1.75',
                'installed': False
            }
        }
    
    def check_dependency(self, package_info: Dict[str, Any]) -> bool:
        """Check if a dependency is installed"""
        try:
            module_name = package_info['import_name']
            spec = importlib.util.find_spec(module_name)
            
            if spec is not None:
                # Try to import the module to be sure
                module = importlib.import_module(module_name)
                logger.info(f"✅ Found {module_name}")
                
                # Try to get version if possible
                if hasattr(module, '__version__'):
                    version = getattr(module, '__version__')
                    logger.info(f"   Version: {version}")
                
                return True
            else:
                logger.warning(f"⚠️ Module {module_name} not found")
                return False
                
        except ImportError:
            logger.warning(f"⚠️ Unable to import {package_info['import_name']}")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking {package_info['import_name']}: {e}")
            print(traceback.format_exc())
            return False
    
    def install_dependency(self, package_info: Dict[str, Any]) -> bool:
        """Install a dependency using pip"""
        try:
            package = f"{package_info['package']}{package_info['version']}"
            logger.info(f"📦 Installing {package}...")
            
            # Use subprocess to install the package
            command = [sys.executable, "-m", "pip", "install", "--no-cache-dir", package]
            logger.info(f"Running command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully installed {package}")
                return True
            else:
                logger.error(f"❌ Failed to install {package}")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error installing {package_info['package']}: {e}")
            print(traceback.format_exc())
            return False
    
    def check_all_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Check the status of all dependencies"""
        status = {}
        
        # Check required dependencies
        for name, info in self.dependencies.items():
            info['installed'] = self.check_dependency(info)
            status[name] = info.copy()
        
        # Check optional dependencies
        for name, info in self.optional_dependencies.items():
            info['installed'] = self.check_dependency(info)
            status[name] = info.copy()
            status[name]['optional'] = True
            
        return status
    
    def install_missing_dependencies(self) -> bool:
        """Install all missing dependencies"""
        all_installed = True
        
        # Install required dependencies
        for name, info in self.dependencies.items():
            if not self.check_dependency(info):
                success = self.install_dependency(info)
                if success:
                    info['installed'] = True
                else:
                    all_installed = False
        
        # Install optional dependencies only if USE_LLM is true
        use_llm = os.environ.get('USE_LLM', 'true').lower() == 'true'
        if use_llm:
            logger.info("LLM is enabled, installing optional dependencies...")
            for name, info in self.optional_dependencies.items():
                if not self.check_dependency(info):
                    success = self.install_dependency(info)
                    if success:
                        info['installed'] = True
                    # Don't set all_installed to False for optional dependencies
        
        return all_installed
    
    def run_dependency_check(self) -> bool:
        """Run a full dependency check and install missing dependencies"""
        try:
            logger.info("🔍 Checking required dependencies...")
            missing_deps = False
            
            # Check all required dependencies
            for name, info in self.dependencies.items():
                if not self.check_dependency(info):
                    logger.warning(f"⚠️ Missing required dependency: {name}")
                    missing_deps = True
                else:
                    info['installed'] = True
            
            # Check if we should install LLM dependencies
            use_llm = os.environ.get('USE_LLM', 'true').lower() == 'true'
            if use_llm:
                logger.info("🔍 Checking optional LLM dependencies...")
                for name, info in self.optional_dependencies.items():
                    if not self.check_dependency(info):
                        logger.warning(f"⚠️ Missing optional dependency: {name}")
                    else:
                        info['installed'] = True
            
            # Install missing dependencies if needed
            if missing_deps:
                logger.info("📦 Installing missing dependencies...")
                if not self.install_missing_dependencies():
                    logger.error("❌ Failed to install all required dependencies")
                    return False
            
            # Verify required dependencies are now installed
            for name, info in self.dependencies.items():
                if not self.check_dependency(info):
                    logger.error(f"❌ Required dependency {name} still missing after installation attempt")
                    return False
            
            logger.info("✅ All required dependencies are available!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during dependency check: {e}")
            print(traceback.format_exc())
            return False

if __name__ == "__main__":
    # Run a standalone dependency check
    manager = DependencyManager()
    success = manager.run_dependency_check()
    
    if success:
        print("✅ All dependencies are installed and ready to use!")
        sys.exit(0)
    else:
        print("❌ Dependency check failed. Please check the logs.")
        sys.exit(1)