"""
API Mock Workflow Provider.

This provider creates and manages mock API servers based on OpenAPI specifications
using the Prism CLI tool (https://github.com/stoplightio/prism).
"""

import os
import json
import asyncio
import subprocess
import signal
import time
import tempfile
from enum import Enum
from typing import Dict, List, Any, Optional, TypedDict, Literal, Union, cast
from dataclasses import dataclass
import logging
import shutil
import platform
import uuid
import requests

from pepperpy.core.plugin import ProviderPlugin
from pepperpy.workflow import BaseWorkflowProvider
from pepperpy.utils.logger import get_logger

logger = get_logger(__name__)

class ServerStatus(str, Enum):
    """Status of a mock server."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class MockServer:
    """Mock server information."""
    id: str
    name: str
    port: int
    spec_path: str
    process: Optional[subprocess.Popen] = None
    status: ServerStatus = ServerStatus.STOPPED
    pid: Optional[int] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary without process info."""
        return {
            "id": self.id,
            "name": self.name,
            "port": self.port,
            "spec_path": self.spec_path,
            "status": self.status,
            "pid": self.pid,
            "error": self.error
        }

class ActionType(str, Enum):
    """Available actions for the mock API provider."""
    START_SERVER = "start_server"
    STOP_SERVER = "stop_server"
    LIST_SERVERS = "list_servers"
    GET_SERVER = "get_server"
    GENERATE_CLIENT = "generate_client"

class StartServerInput(TypedDict, total=False):
    """Input for starting a mock server."""
    spec_path: str
    name: Optional[str]
    port: Optional[int]
    validate: Optional[bool]

class StopServerInput(TypedDict, total=False):
    """Input for stopping a mock server."""
    server_id: str

class GetServerInput(TypedDict, total=False):
    """Input for getting server details."""
    server_id: str

class GenerateClientInput(TypedDict, total=False):
    """Input for generating client code."""
    server_id: str
    language: str
    output_dir: str
    package_name: Optional[str]

class ActionInput(TypedDict, total=False):
    """Input for executing a workflow action."""
    action: ActionType
    start_server: Optional[StartServerInput]
    stop_server: Optional[StopServerInput]
    get_server: Optional[GetServerInput]
    generate_client: Optional[GenerateClientInput]

class APIBlueprintProvider(BaseWorkflowProvider, ProviderPlugin):
    """API Mock Workflow Provider for creating and managing mock API servers."""
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """Initialize the API Mock Workflow Provider.
        
        Args:
            provider_name: Name of the provider.
            config: Configuration for the provider.
        """
        self.provider_name = provider_name
        self.config = config
        self.servers: Dict[str, MockServer] = {}
        self.initialized = False
        self.prism_path = ""
        self.port_range = self.config.get("default_port_range", [8000, 9000])
        
    async def initialize(self) -> bool:
        """Initialize the provider by checking for required dependencies.
        
        Returns:
            True if initialization was successful, False otherwise.
        """
        try:
            # Check if prism is installed
            try:
                result = subprocess.run(
                    ["prism", "--version"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                logger.info(f"Prism found: {result.stdout.strip()}")
                self.prism_path = "prism"
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Prism CLI not found in PATH. Will check for local installation.")
                
                # Look for prism in common npm binary locations
                possible_paths = [
                    os.path.expanduser("~/.npm-global/bin/prism"),
                    os.path.expanduser("~/node_modules/.bin/prism"),
                    os.path.expanduser("~/.node_modules/.bin/prism"),
                    "/usr/local/bin/prism",
                    "./node_modules/.bin/prism"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        self.prism_path = path
                        logger.info(f"Found Prism at: {path}")
                        break
                
                if not self.prism_path:
                    logger.error("Prism CLI not found. Please install it with 'npm install -g @stoplight/prism-cli'")
                    return False
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize API Mock Provider: {str(e)}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up any running mock servers."""
        for server_id, server in list(self.servers.items()):
            if server.status == ServerStatus.RUNNING:
                await self._stop_server(server_id)
        
        self.servers = {}
        self.initialized = False
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the API Mock workflow based on the specified action.
        
        Args:
            inputs: The input parameters containing the action and its parameters.
            
        Returns:
            A dictionary containing the result of the action.
        """
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return {"error": "Failed to initialize API Mock Provider"}
        
        action_input = cast(ActionInput, inputs)
        action = action_input.get("action")
        
        if not action:
            return {"error": "No action specified"}
        
        try:
            if action == ActionType.START_SERVER:
                if not action_input.get("start_server"):
                    return {"error": "Missing start_server parameters"}
                
                start_params = cast(StartServerInput, action_input["start_server"])
                spec_path = start_params.get("spec_path")
                if not spec_path:
                    return {"error": "Missing spec_path parameter"}
                
                name = start_params.get("name", os.path.basename(spec_path).split(".")[0])
                port = start_params.get("port")
                validate = start_params.get("validate", True)
                
                server = await self._start_server(spec_path, name, port, validate)
                return {"server": server.to_dict()}
                
            elif action == ActionType.STOP_SERVER:
                if not action_input.get("stop_server"):
                    return {"error": "Missing stop_server parameters"}
                
                stop_params = cast(StopServerInput, action_input["stop_server"])
                server_id = stop_params.get("server_id")
                if not server_id:
                    return {"error": "Missing server_id parameter"}
                
                success = await self._stop_server(server_id)
                return {"success": success}
                
            elif action == ActionType.LIST_SERVERS:
                servers = [server.to_dict() for server in self.servers.values()]
                return {"servers": servers}
                
            elif action == ActionType.GET_SERVER:
                if not action_input.get("get_server"):
                    return {"error": "Missing get_server parameters"}
                
                get_params = cast(GetServerInput, action_input["get_server"])
                server_id = get_params.get("server_id")
                if not server_id:
                    return {"error": "Missing server_id parameter"}
                
                server = self.servers.get(server_id)
                if not server:
                    return {"error": f"Server with ID {server_id} not found"}
                
                return {"server": server.to_dict()}
                
            elif action == ActionType.GENERATE_CLIENT:
                if not action_input.get("generate_client"):
                    return {"error": "Missing generate_client parameters"}
                
                gen_params = cast(GenerateClientInput, action_input["generate_client"])
                server_id = gen_params.get("server_id")
                language = gen_params.get("language")
                output_dir = gen_params.get("output_dir")
                
                if not server_id or not language or not output_dir:
                    return {"error": "Missing required parameters (server_id, language, or output_dir)"}
                
                server = self.servers.get(server_id)
                if not server:
                    return {"error": f"Server with ID {server_id} not found"}
                
                package_name = gen_params.get("package_name", server.name)
                client_result = await self._generate_client(server, language, output_dir, package_name)
                return client_result
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Error executing API Mock action: {str(e)}")
            return {"error": f"Error executing action: {str(e)}"}
    
    async def _find_available_port(self) -> int:
        """Find an available port within the configured range.
        
        Returns:
            An available port number.
        """
        min_port, max_port = self.port_range
        
        # Check used ports
        used_ports = {server.port for server in self.servers.values()}
        
        for port in range(min_port, max_port + 1):
            if port not in used_ports:
                # Check if port is actually available
                try:
                    # Try to bind to the port
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.bind(('127.0.0.1', port))
                    sock.close()
                    return port
                except Exception:
                    continue
        
        raise RuntimeError(f"No available ports in range {min_port}-{max_port}")
    
    async def _start_server(
        self, 
        spec_path: str, 
        name: Optional[str] = None, 
        port: Optional[int] = None,
        validate: bool = True
    ) -> MockServer:
        """Start a mock server with the given specification.
        
        Args:
            spec_path: Path to the OpenAPI specification file.
            name: Name for the server.
            port: Port to run the server on. If None, an available port will be chosen.
            validate: Whether to validate requests against the schema.
            
        Returns:
            A MockServer instance with details of the started server.
            
        Raises:
            RuntimeError: If the server fails to start.
        """
        if not os.path.exists(spec_path):
            raise FileNotFoundError(f"Specification file not found: {spec_path}")
        
        server_id = str(uuid.uuid4())
        if not name:
            name = os.path.basename(spec_path).split(".")[0]
        
        if not port:
            port = await self._find_available_port()
        
        logger.info(f"Starting mock server for {spec_path} on port {port}")
        
        # Build prism command
        cmd = [
            self.prism_path, 
            "mock", 
            spec_path,
            "--port", str(port),
        ]
        
        if not validate:
            cmd.append("--errors")
        
        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if platform.system() != "Windows" else None
            )
            
            # Create the server record
            server = MockServer(
                id=server_id,
                name=name,
                port=port,
                spec_path=spec_path,
                process=process,
                status=ServerStatus.RUNNING,
                pid=process.pid
            )
            
            self.servers[server_id] = server
            
            # Give the server a moment to start
            await asyncio.sleep(2)
            
            # Check if the server started successfully
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr else "Unknown error"
                server.status = ServerStatus.ERROR
                server.error = stderr
                logger.error(f"Server failed to start: {stderr}")
                return server
            
            # Check if the server is responsive
            try:
                health_url = f"http://localhost:{port}"
                response = requests.get(health_url)
                if response.status_code >= 500:
                    logger.warning(f"Server may not be fully operational. Status code: {response.status_code}")
            except requests.RequestException as e:
                logger.warning(f"Could not connect to server: {str(e)}")
            
            return server
            
        except Exception as e:
            logger.error(f"Error starting mock server: {str(e)}")
            raise RuntimeError(f"Failed to start mock server: {str(e)}")
    
    async def _stop_server(self, server_id: str) -> bool:
        """Stop a running mock server.
        
        Args:
            server_id: The ID of the server to stop.
            
        Returns:
            True if the server was stopped successfully, False otherwise.
        """
        server = self.servers.get(server_id)
        if not server:
            logger.warning(f"Server with ID {server_id} not found")
            return False
        
        if server.status != ServerStatus.RUNNING or not server.process:
            logger.info(f"Server {server_id} is not running")
            self.servers[server_id].status = ServerStatus.STOPPED
            return True
        
        logger.info(f"Stopping mock server {server_id}")
        
        try:
            if platform.system() == "Windows":
                server.process.terminate()
            else:
                # Use process group ID to kill all child processes
                os.killpg(os.getpgid(server.process.pid), signal.SIGTERM)
            
            # Wait for the process to terminate
            for _ in range(5):
                if server.process.poll() is not None:
                    break
                await asyncio.sleep(0.5)
            else:
                # Force kill if not terminated
                if platform.system() == "Windows":
                    server.process.kill()
                else:
                    os.killpg(os.getpgid(server.process.pid), signal.SIGKILL)
            
            server.status = ServerStatus.STOPPED
            server.process = None
            return True
            
        except Exception as e:
            logger.error(f"Error stopping mock server: {str(e)}")
            server.error = str(e)
            return False
    
    async def _generate_client(
        self, 
        server: MockServer, 
        language: str, 
        output_dir: str,
        package_name: str
    ) -> Dict[str, Any]:
        """Generate client code for the API using OpenAPI Generator.
        
        Args:
            server: The server to generate a client for.
            language: The programming language for the client.
            output_dir: Directory to output the generated code.
            package_name: Name for the client package.
            
        Returns:
            A dictionary with the result of the client generation.
        """
        if not os.path.exists(server.spec_path):
            return {"error": f"Specification file not found: {server.spec_path}"}
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Check if OpenAPI Generator is available
        openapi_generator = self.config.get("client_generators", {}).get("openapi_generator_path")
        
        if not openapi_generator:
            # Check if openapi-generator-cli is in PATH
            try:
                result = subprocess.run(
                    ["openapi-generator-cli", "version"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                openapi_generator = "openapi-generator-cli"
                logger.info(f"OpenAPI Generator found: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                return {
                    "error": "OpenAPI Generator not found. Please install it with npm install @openapitools/openapi-generator-cli -g"
                }
        
        logger.info(f"Generating {language} client for {server.name}")
        
        cmd = [
            openapi_generator, "generate",
            "-i", server.spec_path,
            "-g", language,
            "-o", output_dir,
            "--package-name", package_name
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            logger.info(f"Client generation successful: {output_dir}")
            return {
                "success": True,
                "output_dir": output_dir,
                "language": language,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Error generating client: {e.stderr}")
            return {
                "error": f"Client generation failed: {e.stderr}",
                "stdout": e.stdout,
                "stderr": e.stderr
            } 