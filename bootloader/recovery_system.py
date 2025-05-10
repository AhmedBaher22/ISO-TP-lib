#!/usr/bin/env python3
"""
Recovery System for HMI OTA Updates
This script handles the safe update process between the two system banks.
"""

import os
import sys
import shutil
import json
import time
import signal
import logging
import subprocess
import hashlib
import zipfile
import tempfile
import psutil
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client_data/recovery_logs.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Recovery_System")

class RecoverySystem:
    def __init__(self, source_folder, update_file_path):
        """
        Initialize the recovery system.
        
        Args:
            source_folder: The folder number (1 or 2) that initiated the update
            update_file_path: Path to the update package
        """
        self.source_folder = int(source_folder)
        self.target_folder = 2 if self.source_folder == 1 else 1
        self.update_file_path = update_file_path
        self.source_path = f"folder_{self.source_folder}"
        self.target_path = f"folder_{self.target_folder}"
        self.client_data_path = "client_data"
        self.update_meta_file = os.path.join(self.client_data_path, "update_meta.json")
        self.health_check_timeout = 60  # seconds to wait for health check
        
        # Executables
        self.source_executable = self._find_main_executable(self.source_path)
        self.target_executable = None  # Will be set after update
        
        # Metadata tracking
        self.update_meta = self._load_update_meta()
        
        logger.info(f"Recovery system initialized: source={self.source_folder}, target={self.target_folder}")
        logger.info(f"Source executable: {self.source_executable}")
    
    def _find_main_executable(self, folder_path):
        """Find the main HMI executable in the given folder."""
        # In a real implementation, you would have a specific naming convention
        # For this example, we'll assume it's called main.py, hmi.py, or app.py
        possible_names = ["main.py", "hmi.py", "app.py", "hmi_system.py"]
        
        for name in possible_names:
            path = os.path.join(folder_path, name)
            if os.path.exists(path):
                return path
        
        logger.warning(f"Could not find main executable in {folder_path}")
        return None
    
    def _load_update_meta(self):
        """Load update metadata from client_data."""
        try:
            if os.path.exists(self.update_meta_file):
                with open(self.update_meta_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning("Update metadata file not found, using defaults")
                return {
                    "source_folder": self.source_folder,
                    "target_folder": self.target_folder,
                    "update_file": self.update_file_path,
                    "checksum": None,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.error(f"Error loading update metadata: {str(e)}")
            return None
    
    def _save_system_state(self):
        """Save current system state for potential rollback."""
        try:
            state = {
                "last_working_folder": self.source_folder,
                "last_update_timestamp": time.time(),
                "source_executable": self.source_executable
            }
            
            with open(os.path.join(self.client_data_path, "system_state.json"), "w") as f:
                json.dump(state, f)
                
            logger.info(f"System state saved: {state}")
            return True
        except Exception as e:
            logger.error(f"Error saving system state: {str(e)}")
            return False
    
    def _verify_checksum(self):
        """Verify the checksum of the update package."""
        if not self.update_meta or "checksum" not in self.update_meta:
            logger.error("No checksum found in update metadata")
            return False
            
        expected = self.update_meta["checksum"]
        
        # Calculate actual checksum
        sha256_hash = hashlib.sha256()
        with open(self.update_file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        actual = sha256_hash.hexdigest()
        
        if expected != actual:
            logger.error(f"Checksum mismatch: expected {expected}, got {actual}")
            return False
            
        logger.info("Checksum verification successful")
        return True
    
    def _extract_update(self):
        """Extract the update package to the target folder."""
        try:
            # First, verify the update file exists
            if not os.path.exists(self.update_file_path):
                logger.error(f"Update file not found: {self.update_file_path}")
                return False
                
            # Verify checksum
            if not self._verify_checksum():
                return False
                
            # Create a temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Extracting update to temporary directory: {temp_dir}")
                
                # If it's a zip file, extract it
                if self.update_file_path.endswith('.zip'):
                    with zipfile.ZipFile(self.update_file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                
                # If it's a different format, handle accordingly
                # [Add handling for other formats here]
                
                # Prepare target folder - clear existing contents
                if os.path.exists(self.target_path):
                    # Instead of completely removing, we'll keep a backup
                    backup_path = f"{self.target_path}_backup"
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                    shutil.move(self.target_path, backup_path)
                    logger.info(f"Created backup of target folder at {backup_path}")
                
                # Create fresh target folder
                os.makedirs(self.target_path, exist_ok=True)
                
                # Copy extracted contents to target folder
                for item in os.listdir(temp_dir):
                    s = os.path.join(temp_dir, item)
                    d = os.path.join(self.target_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, symlinks=False)
                    else:
                        shutil.copy2(s, d)
                
                logger.info(f"Update extracted to target folder: {self.target_path}")
                
                # Find the main executable in the updated system
                self.target_executable = self._find_main_executable(self.target_path)
                if not self.target_executable:
                    logger.error("Could not find main executable in updated system")
                    return False
                    
                logger.info(f"Target executable identified: {self.target_executable}")
                return True
                
        except Exception as e:
            logger.error(f"Error extracting update: {str(e)}")
            return False
    
    def _run_health_checks(self):
        """Run health checks on the new system."""
        try:
            logger.info("Running health checks on updated system")
            
            # Check 1: Verify executable exists
            if not os.path.exists(self.target_executable):
                logger.error(f"Target executable not found: {self.target_executable}")
                return False
                
            # Check 2: Verify integrity of key files
            # In a real implementation, you would:
            # - Check integrity of all critical components
            # - Verify dependencies are available
            # - Check system configuration
            
            # Check 3: Run the system in test mode and verify it works
            test_process = subprocess.Popen(
                [sys.executable, self.target_executable, "--test-mode"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for process to complete or timeout
            try:
                stdout, stderr = test_process.communicate(timeout=self.health_check_timeout)
                
                # Check exit code
                if test_process.returncode != 0:
                    logger.error(f"Health check failed with exit code: {test_process.returncode}")
                    logger.error(f"Stderr: {stderr.decode('utf-8')}")
                    return False
                    
                logger.info("Health check passed: Test mode ran successfully")
                
                # In a real implementation, you would:
                # - Parse test results
                # - Verify all critical functionality is working
                # - Check resource usage, stability, etc.
                
            except subprocess.TimeoutExpired:
                test_process.kill()
                logger.error("Health check timed out")
                return False
                
            logger.info("All health checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Error running health checks: {str(e)}")
            return False
    
    def _terminate_source_system(self):
        """Terminate the old system if it's still running."""
        try:
            logger.info("Checking for running instances of source system")
            
            # Find processes that might be the source system
            source_name = os.path.basename(self.source_executable)
            terminated = False
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check if this process is our source system
                    if any(source_name in cmd for cmd in proc.info['cmdline'] if cmd):
                        logger.info(f"Terminating source process: {proc.info}")
                        proc.terminate()
                        terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if terminated:
                # Give processes time to terminate gracefully
                time.sleep(2)
                
                # Force kill any remaining processes
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if any(source_name in cmd for cmd in proc.info['cmdline'] if cmd):
                            logger.warning(f"Force killing source process: {proc.info}")
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            logger.info("Source system terminated")
            return True
            
        except Exception as e:
            logger.error(f"Error terminating source system: {str(e)}")
            return False
    
    def _start_target_system(self):
        """Start the new updated system."""
        try:
            logger.info(f"Starting target system: {self.target_executable}")
            
            # Start the new system
            subprocess.Popen([
                sys.executable, 
                self.target_executable
            ])
            
            # Wait briefly to see if it crashes immediately
            time.sleep(5)
            
            # Check if process is still running
            target_name = os.path.basename(self.target_executable)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if any(target_name in cmd for cmd in proc.info['cmdline'] if cmd):
                        logger.info(f"Target system is running: {proc.info}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            logger.error("Target system failed to start or crashed immediately")
            return False
            
        except Exception as e:
            logger.error(f"Error starting target system: {str(e)}")
            return False
    
    def _rollback(self):
        """Rollback to the previous working system."""
        try:
            logger.warning("Initiating rollback to previous working system")
            
            # Start the source system again
            logger.info(f"Restarting source system: {self.source_executable}")
            subprocess.Popen([
                sys.executable, 
                self.source_executable
            ])
            
            # Update system state to reflect rollback
            state = {
                "last_working_folder": self.source_folder,
                "rollback_timestamp": time.time(),
                "update_failed": True
            }
            
            with open(os.path.join(self.client_data_path, "system_state.json"), "w") as f:
                json.dump(state, f)
                
            logger.info("Rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Critical error during rollback: {str(e)}")
            return False
    
    def run_update_process(self):
        """Main method to run the complete update process."""
        try:
            logger.info("Starting update process")
            
            # Step 1: Save current system state for potential rollback
            if not self._save_system_state():
                logger.error("Failed to save system state, aborting update")
                return self._rollback()
            
            # Step 2: Extract update package to target folder
            logger.info("Extracting update package")
            if not self._extract_update():
                logger.error("Failed to extract update, rolling back")
                return self._rollback()
            
            # Step 3: Run health checks on the new system
            logger.info("Running health checks")
            if not self._run_health_checks():
                logger.error("Health checks failed, rolling back")
                return self._rollback()
            
            # Step 4: Terminate the old system
            logger.info("Terminating old system")
            if not self._terminate_source_system():
                logger.warning("Failed to terminate old system, continuing anyway")
            
            # Step 5: Start the new system
            logger.info("Starting new system")
            if not self._start_target_system():
                logger.error("Failed to start new system, rolling back")
                return self._rollback()
            
            # Step 6: Update system state to reflect successful update
            state = {
                "last_working_folder": self.target_folder,
                "update_timestamp": time.time(),
                "update_successful": True
            }
            
            with open(os.path.join(self.client_data_path, "system_state.json"), "w") as f:
                json.dump(state, f)
                
            logger.info("Update process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unhandled error during update process: {str(e)}")
            return self._rollback()

# Main execution
if __name__ == "__main__":
    try:
        # Validate arguments
        if len(sys.argv) < 3:
            print("Usage: recovery_system.py <source_folder> <update_file_path>")
            sys.exit(1)
            
        source_folder = sys.argv[1]
        update_file_path = sys.argv[2]
        
        # Create client_data directory if it doesn't exist
        os.makedirs("client_data", exist_ok=True)
        
        # Initialize and run the recovery system
        recovery = RecoverySystem(source_folder, update_file_path)
        success = recovery.run_update_process()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        # Log any unhandled exceptions
        logger.critical(f"Critical error in recovery system: {str(e)}")
        sys.exit(1)