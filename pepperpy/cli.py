#!/usr/bin/env python3
"""
PepperPy CLI

Unified command-line interface for the PepperPy framework.
"""

import sys
import asyncio
import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional, Union

from pepperpy import PepperPy
from pepperpy.rag.processor import create_processor, ProcessingOptions


async def process_text(
    text: str,
    processor_type: Optional[str] = None,
    model: Optional[str] = None,
    device: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    output_file: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """Process text using the configured processor.
    
    Args:
        text: Text to process
        processor_type: Type of processor to use
        model: Model name (for model-based processors)
        device: Device to use (cpu/cuda)
        chunk_size: Size of chunks in characters
        chunk_overlap: Overlap between chunks in characters
        output_file: Path to save results
        verbose: Whether to print detailed output
        
    Returns:
        Processing results
    """
    if verbose:
        print(f"Processor: {processor_type or 'default'}")
        if model:
            print(f"Model: {model}")
        if device:
            print(f"Device: {device}")
        print(f"Chunk size: {chunk_size}, Chunk overlap: {chunk_overlap}")
        print("-" * 50)
    
    start_time = time.time()
    
    # Create kwargs with processor-specific options
    kwargs = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }
    
    if model:
        kwargs["model"] = model
        
    if device:
        kwargs["device"] = device
    
    # Create processor
    processor = create_processor(processor_type, **kwargs)
    
    # Initialize processor
    await processor.initialize()
    
    try:
        # Process the text
        options = ProcessingOptions(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            preserve_newlines=True
        )
        
        results = await processor.process_text(text, options)
        
        # Calculate processing time
        elapsed_time = time.time() - start_time
        
        # Prepare results
        response = {
            "status": "success",
            "metadata": {
                "processor": processor_type or "default",
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "processing_time": f"{elapsed_time:.2f}s"
            },
            "result": {
                "chunks": results.chunks,
                "num_chunks": len(results.chunks),
                "num_tokens": sum(len(tokens) for tokens in results.tokens if tokens),
                "embeddings_shape": [emb.shape for emb in results.embeddings] if results.embeddings else None,
                "metadata": results.metadata
            }
        }
        
        # Save to file if requested
        if output_file:
            result_dict = {
                "chunks": results.chunks,
                "tokens": [[str(t) for t in tokens] for tokens in results.tokens],
                "embeddings_shape": [str(emb.shape) for emb in results.embeddings] if results.embeddings else None,
                "metadata": results.metadata
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2)
                
            response["file"] = output_file
            
        return response
    finally:
        # Clean up
        await processor.cleanup()


async def run_workflow(
    workflow_name: str, 
    input_data: Dict[str, Any], 
    output_file: Optional[str] = None, 
    verbose: bool = False
) -> Dict[str, Any]:
    """Run a workflow with the given input data.
    
    Args:
        workflow_name: Name of the workflow to run
        input_data: Input data for the workflow
        output_file: Path to save results
        verbose: Whether to print detailed output
        
    Returns:
        Workflow results
    """
    if verbose:
        print(f"Running workflow: {workflow_name}")
        print(f"Input data: {json.dumps(input_data, indent=2)}")
        print("-" * 50)
    
    start_time = time.time()
    
    # Extract the provider type from the workflow name
    # Workflow names are typically in the format "workflow/provider_name"
    # or just "provider_name"
    provider_name = workflow_name
    if "/" in workflow_name:
        _, provider_name = workflow_name.split("/", 1)
    
    if verbose:
        print(f"Using workflow provider: {provider_name}")
    
    # Create PepperPy instance with the correct workflow provider
    pepper = (
        PepperPy.create()
        .with_workflow(provider_name)
        .build()
    )
    
    # Use async context manager for resource management
    async with pepper:
        try:
            # Execute workflow
            result = await pepper.workflow.execute(input_data)
            
            # Calculate execution time
            elapsed_time = time.time() - start_time
            
            # Prepare response
            response = {
                "status": "success",
                "metadata": {
                    "workflow": workflow_name,
                    "execution_time": f"{elapsed_time:.2f}s"
                },
                "result": result
            }
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                response["file"] = output_file
                
            # Print summary if verbose
            if verbose:
                print(f"Execution time: {elapsed_time:.2f}s")
                print(f"Status: {result.get('status', 'unknown')}")
                
            return response
        except Exception as e:
            print(f"Error executing workflow: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "metadata": {
                    "workflow": workflow_name,
                    "execution_time": f"{time.time() - start_time:.2f}s"
                },
                "error": str(e)
            }


async def rag_processor_command(args: argparse.Namespace) -> int:
    """Handle RAG processor subcommand.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Get text from file or argument
        text = args.text
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        
        if not text:
            print("Error: No text provided")
            return 1
        
        # Process the text
        result = await process_text(
            text=text,
            processor_type=args.processor,
            model=args.model,
            device=args.device,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            output_file=args.output,
            verbose=args.verbose
        )
        
        # Print summary of results
        if args.summary or args.verbose:
            print("\nProcessing Results:")
            print(f"Processor: {result['metadata'].get('processor', 'default')}")
            print(f"Processing time: {result['metadata'].get('processing_time', 'unknown')}")
            print(f"Number of chunks: {result['result'].get('num_chunks', 0)}")
            print(f"Number of tokens: {result['result'].get('num_tokens', 0)}")
            
            if args.output:
                print(f"Results saved to: {args.output}")
                
        return 0
    except Exception as e:
        print(f"Error processing text: {e}")
        return 1


async def workflow_command(args: argparse.Namespace) -> int:
    """Handle workflow subcommand.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse input data
    try:
        if args.input:
            # Check if input is a file
            if os.path.isfile(args.input):
                with open(args.input, 'r', encoding='utf-8') as f:
                    input_data = json.load(f)
            else:
                # Try to parse as JSON
                input_data = json.loads(args.input)
        else:
            # Create input data from command line options
            input_data = {}
            if args.task:
                input_data["task"] = args.task
            if args.text:
                input_data["text"] = args.text
            if args.options:
                options = {}
                for option in args.options:
                    if '=' in option:
                        key, value = option.split('=', 1)
                        # Try to convert value to appropriate type
                        try:
                            if value.lower() == 'true':
                                value = True
                            elif value.lower() == 'false':
                                value = False
                            elif value.isdigit():
                                value = int(value)
                            elif value.replace('.', '', 1).isdigit():
                                value = float(value)
                        except:
                            pass
                        options[key] = value
                input_data["options"] = options
    except json.JSONDecodeError:
        print("Error: Invalid JSON input")
        return 1
    except Exception as e:
        print(f"Error parsing input data: {e}")
        return 1
    
    try:
        # Run the workflow
        result = await run_workflow(
            workflow_name=args.workflow,
            input_data=input_data,
            output_file=args.output,
            verbose=args.verbose
        )
        
        # Print summary of results
        if args.summary:
            print("\nWorkflow Results:")
            print(f"Workflow: {result['metadata'].get('workflow', 'unknown')}")
            print(f"Execution time: {result['metadata'].get('execution_time', 'unknown')}")
            print(f"Status: {result['result'].get('status', 'unknown')}")
            
            if args.output:
                print(f"Results saved to: {args.output}")
                
        # Print full results if verbose and not already printed
        if args.verbose and not args.summary:
            print("\nFull results:")
            print(json.dumps(result['result'], indent=2))
            
        return 0
    except Exception as e:
        print(f"Error executing workflow: {e}")
        return 1


async def plugin_command(args: argparse.Namespace) -> int:
    """Handle plugin direct execution subcommand.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse input data
    try:
        if args.input:
            # Check if input is a file
            if os.path.isfile(args.input):
                with open(args.input, 'r', encoding='utf-8') as f:
                    input_data = json.load(f)
            else:
                # Try to parse as JSON
                input_data = json.loads(args.input)
        else:
            input_data = {"task": args.task}
            
            # Add text if provided
            if args.text:
                input_data["text"] = args.text
                
            # Add options if provided
            if args.options:
                options = {}
                for option in args.options:
                    if '=' in option:
                        key, value = option.split('=', 1)
                        # Try to convert value to appropriate type
                        try:
                            if value.lower() == 'true':
                                value = True
                            elif value.lower() == 'false':
                                value = False
                            elif value.isdigit():
                                value = int(value)
                            elif value.replace('.', '', 1).isdigit():
                                value = float(value)
                        except:
                            pass
                        options[key] = value
                
                # Add options to input data or update existing options
                if "options" in input_data and isinstance(input_data["options"], dict):
                    input_data["options"].update(options)
                else:
                    input_data["options"] = options
    except json.JSONDecodeError:
        print("Error: Invalid JSON input")
        return 1
    except Exception as e:
        print(f"Error parsing input data: {e}")
        return 1
    
    try:
        # Import the plugin dynamically
        plugin_path = args.plugin_path.split(".")
        
        if len(plugin_path) < 2:
            print("Error: Invalid plugin path. Format should be: domain.category.provider")
            return 1
            
        # Import the provider module
        if len(plugin_path) == 3:  # domain.category.provider format
            module_path = f"plugins.{plugin_path[0]}.{plugin_path[1]}.{plugin_path[2]}.provider"
            class_name = f"{plugin_path[2].capitalize()}Provider"
        else:  # module.Class format
            module_path = ".".join(plugin_path[:-1])
            class_name = plugin_path[-1]
        
        if args.verbose:
            print(f"Importing: {module_path}.{class_name}")
            
        # Dynamic import
        import importlib
        try:
            module = importlib.import_module(module_path)
            ProviderClass = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(f"Error importing plugin: {e}")
            return 1
            
        # Create provider instance
        provider_kwargs = {}
        if args.config:
            for config_item in args.config:
                if '=' in config_item:
                    key, value = config_item.split('=', 1)
                    # Try to convert value to appropriate type
                    try:
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value)
                    except:
                        pass
                    provider_kwargs[key] = value
        
        # Create the provider instance
        if args.verbose:
            print(f"Creating provider with: {provider_kwargs}")
            
        provider = ProviderClass(**provider_kwargs)
        
        # Initialize the provider
        if args.verbose:
            print("Initializing provider...")
            
        await provider.initialize()
        
        try:
            # Execute the provider
            if args.verbose:
                print(f"Executing provider with input: {json.dumps(input_data, indent=2)}")
                
            start_time = time.time()
            result = await provider.execute(input_data)
            elapsed_time = time.time() - start_time
            
            # Check result
            if not isinstance(result, dict):
                print(f"Error: Provider returned invalid result: {result}")
                return 1
                
            # Add metadata
            result.setdefault("metadata", {})
            result["metadata"]["execution_time"] = f"{elapsed_time:.2f}s"
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                    
                if args.verbose:
                    print(f"Results saved to: {args.output}")
            
            # Print results
            if args.pretty or args.verbose:
                print("\nResults:")
                print(json.dumps(result, indent=2))
            else:
                print(json.dumps(result))
                
            return 0
        finally:
            # Cleanup
            if args.verbose:
                print("Cleaning up...")
                
            await provider.cleanup()
    except Exception as e:
        print(f"Error executing plugin: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="PepperPy Command Line Interface",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    #
    # RAG processor command
    #
    rag_parser = subparsers.add_parser(
        "rag", 
        help="RAG text processor operations",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Processor options
    rag_parser.add_argument("--processor", 
                        choices=["spacy", "nltk", "transformers"], 
                        help="Processor type (default: from config.yaml or spacy)")
    rag_parser.add_argument("--model", type=str,
                        help="Model name (for model-based processors)")
    rag_parser.add_argument("--device", choices=["cpu", "cuda"],
                        help="Device to use (default: from config or cpu)")
    rag_parser.add_argument("--chunk-size", type=int, default=1000,
                        help="Size of chunks in characters")
    rag_parser.add_argument("--chunk-overlap", type=int, default=200,
                        help="Overlap between chunks in characters")
    
    # Input options
    input_group = rag_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", type=str, help="Text to process")
    input_group.add_argument("--file", type=str, help="File containing text to process")
    
    # Output options
    rag_parser.add_argument("--output", "-o", type=str, 
                        help="Output file path for results (JSON format)")
    rag_parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Print detailed processing information")
    rag_parser.add_argument("--summary", "-s", action="store_true",
                        help="Print summary of results")
    
    #
    # Workflow command
    #
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Execute workflows",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Workflow options
    workflow_parser.add_argument("workflow", help="Name of the workflow to run (e.g., workflow/text_processing)")
    
    # Input options for workflow
    input_group = workflow_parser.add_mutually_exclusive_group()
    input_group.add_argument("--input", "-i", help="JSON input data or path to JSON file")
    
    # If no input file is provided, these options can be used instead
    workflow_parser.add_argument("--task", help="Task to execute in the workflow")
    workflow_parser.add_argument("--text", help="Text to process")
    workflow_parser.add_argument("--options", nargs="+", help="Additional options as key=value pairs")
    
    # Output options for workflow
    workflow_parser.add_argument("--output", "-o", help="Output file path for results (JSON format)")
    workflow_parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed execution information")
    workflow_parser.add_argument("--summary", "-s", action="store_true", help="Print summary of results")
    
    #
    # Plugin command (direct execution)
    #
    plugin_parser = subparsers.add_parser(
        "plugin",
        help="Execute plugins directly (development/testing only)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Plugin options
    plugin_parser.add_argument("plugin_path", help="Plugin path in format domain.category.provider or module.Class")
    plugin_parser.add_argument("--config", "-c", nargs="+", help="Configuration options as key=value pairs")
    
    # Input options for plugin
    input_group = plugin_parser.add_mutually_exclusive_group()
    input_group.add_argument("--input", "-i", help="JSON input data or path to JSON file")
    
    # If no input file is provided, these options can be used instead
    plugin_parser.add_argument("--task", default="process", help="Task to execute")
    plugin_parser.add_argument("--text", help="Text to process")
    plugin_parser.add_argument("--options", nargs="+", help="Additional options as key=value pairs")
    
    # Output options for plugin
    plugin_parser.add_argument("--output", "-o", help="Output file path for results (JSON format)")
    plugin_parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed execution information")
    plugin_parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print JSON output")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "rag":
        return asyncio.run(rag_processor_command(args))
    elif args.command == "workflow":
        return asyncio.run(workflow_command(args))
    elif args.command == "plugin":
        return asyncio.run(plugin_command(args))
    elif not args.command:
        parser.print_help()
        return 0
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
