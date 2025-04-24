"""
Utility functions for working with MCP servers.

This module provides helper functions for working with MCP servers,
including running servers in the background.
"""

import os
import signal
import subprocess
import time
from typing import Optional, List, Dict, Any, Union

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


def start_background_server(
    command: Union[str, List[str]],
    env: Optional[Dict[str, str]] = None,
    wait_time: float = 2.0,
) -> subprocess.Popen:
    """Start an MCP server as a background process.
    
    Args:
        command: Command to run the server, either as a string or list of arguments
        env: Environment variables to set for the server process
        wait_time: Time in seconds to wait for the server to start
        
    Returns:
        Process object representing the running server
        
    Example:
        ```python
        # Start an MCP server using the official library
        process = start_background_server(["python", "-m", "mcp.server.stdio", "server.py"])
        
        try:
            # Use the server...
            client.connect()
            # ...
        finally:
            # Stop the server
            stop_background_server(process)
        ```
    """
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    if isinstance(command, str):
        cmd_args = command.split()
    else:
        cmd_args = command
    
    logger.info(f"Starting MCP server with command: {' '.join(cmd_args)}")
    
    # Start the process
    process = subprocess.Popen(
        cmd_args,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
    )
    
    # Wait for the server to start
    if wait_time > 0:
        logger.info(f"Waiting {wait_time} seconds for the server to start...")
        time.sleep(wait_time)
    
    return process


def stop_background_server(process: subprocess.Popen, timeout: float = 5.0) -> None:
    """Stop a background MCP server process.
    
    Args:
        process: Process object returned by start_background_server
        timeout: Time in seconds to wait for the process to terminate
    """
    if process.poll() is None:  # Process is still running
        logger.info("Stopping MCP server process...")
        
        # Send SIGTERM
        process.terminate()
        
        # Wait for process to terminate
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"MCP server did not terminate within {timeout} seconds, sending SIGKILL")
            process.kill()
            process.wait()
    
    # Collect output
    stdout, stderr = process.communicate()
    
    if stdout:
        logger.debug(f"Server stdout: {stdout}")
    
    if stderr:
        logger.debug(f"Server stderr: {stderr}")
    
    logger.info("MCP server process stopped") 