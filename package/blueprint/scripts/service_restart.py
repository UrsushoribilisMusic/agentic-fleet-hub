#!/usr/bin/env python3
"""
Service Restart Logic: Restart fleet services after project switch.
"""

import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def is_service_running(service_name: str) -> bool:
    """Check if a service is currently running by checking for its process."""
    try:
        # Check if the service process is actually running using ps
        # This is more reliable than launchctl status which can be misleading
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Look for pocketbase or dispatcher processes
        if "pocketbase" in service_name:
            return "pocketbase" in result.stdout and "fleet" in result.stdout
        elif "dispatcher" in service_name:
            # Check for dispatcher.py processes
            return "dispatcher.py" in result.stdout
        else:
            return service_name in result.stdout
    except subprocess.CalledProcessError:
        return False


def get_service_pids(service_name: str) -> list:
    """Get all PIDs for a service process."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )
        
        pids = []
        if "pocketbase" in service_name:
            # Find all pocketbase processes
            for line in result.stdout.split('\n'):
                if "pocketbase" in line and "fleet" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pids.append(parts[1])
        elif "dispatcher" in service_name:
            # Find all dispatcher.py processes
            for line in result.stdout.split('\n'):
                if "dispatcher.py" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pids.append(parts[1])
        
        return pids
    except subprocess.CalledProcessError:
        return []


def stop_service_gracefully(service_name: str, max_retries: int = 3) -> bool:
    """Stop a service gracefully with retries."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to stop {service_name} (attempt {attempt + 1})...")
            
            # First try launchctl stop
            subprocess.run(["launchctl", "stop", service_name], check=False)
            
            # Verify service stopped
            time.sleep(2)
            if not is_service_running(service_name):
                logger.info(f"Successfully stopped {service_name}")
                return True
            else:
                logger.warning(f"{service_name} still running after launchctl stop, trying kill...")
                
                # If launchctl didn't work, find and kill the process directly
                try:
                    # Get all process IDs for this service
                    pids = get_service_pids(service_name)
                    
                    if pids:
                        logger.info(f"Found {len(pids)} processes: {pids}, sending SIGTERM...")
                        # Kill all processes with SIGTERM first
                        for pid in pids:
                            subprocess.run(["kill", pid], check=False)
                        time.sleep(2)
                        
                        # Check if any are still running, if so use SIGKILL
                        remaining_pids = get_service_pids(service_name)
                        if remaining_pids:
                            logger.warning(f"Processes {remaining_pids} still running, sending SIGKILL...")
                            for pid in remaining_pids:
                                subprocess.run(["kill", "-9", pid], check=False)
                            time.sleep(2)
                            
                            # Check again
                            final_pids = get_service_pids(service_name)
                            if not final_pids:
                                logger.info(f"Successfully stopped {service_name}")
                                return True
                except Exception as e:
                    logger.error(f"Error killing process: {e}")
                
                logger.warning(f"{service_name} still running after stop command")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping {service_name}: {e}")
            
    logger.error(f"Failed to stop {service_name} after {max_retries} attempts")
    return False


def start_service(service_name: str, max_retries: int = 3) -> bool:
    """Start a service with retries."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to start {service_name} (attempt {attempt + 1})...")
            subprocess.run(["launchctl", "start", service_name], check=True)
            
            # Verify service started
            time.sleep(2)
            if is_service_running(service_name):
                logger.info(f"Successfully started {service_name}")
                return True
            else:
                logger.warning(f"{service_name} not running after start command")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error starting {service_name}: {e}")
            
    logger.error(f"Failed to start {service_name} after {max_retries} attempts")
    return False


def restart_service(service_name: str) -> bool:
    """Restart a single service with full lifecycle management."""
    logger.info(f"Restarting service: {service_name}")
    
    # Check if service is running
    if not is_service_running(service_name):
        logger.warning(f"{service_name} is not running, attempting to start...")
        return start_service(service_name)
    
    # Stop gracefully
    if not stop_service_gracefully(service_name):
        return False
    
    # Start service
    if not start_service(service_name):
        return False
    
    logger.info(f"Successfully restarted {service_name}")
    return True


def restart_pocketbase() -> bool:
    """Restart PocketBase service."""
    return restart_service("fleet.pocketbase")


def restart_dispatcher() -> bool:
    """Restart dispatcher service."""
    return restart_service("fleet.dispatcher")


def restart_all_services() -> bool:
    """Restart all fleet services."""
    logger.info("Starting full fleet service restart sequence...")
    
    # Restart PocketBase first
    if not restart_pocketbase():
        logger.error("Failed to restart PocketBase, aborting service restart")
        return False
    
    # Restart dispatcher
    if not restart_dispatcher():
        logger.error("Failed to restart dispatcher, PocketBase may be in inconsistent state")
        return False
    
    logger.info("All fleet services restarted successfully")
    return True


if __name__ == "__main__":
    if restart_all_services():
        print("All services restarted successfully")
    else:
        print("Failed to restart services")
