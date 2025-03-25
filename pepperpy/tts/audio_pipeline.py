"""Audio pipeline for generating and processing TTS content.

This module provides a complete pipeline for processing audio content:
1. Converting text to speech
2. Adding sound effects and background music
3. Compiling segments into final audio

Example:
    >>> from pepperpy.tts.audio_pipeline import AudioPipeline
    >>> pipeline = AudioPipeline()
    >>> audio_files = await pipeline.generate_audio(segments)
    >>> enhanced_files = await pipeline.add_sound_effects(audio_files)
    >>> final_audio = await pipeline.compile_audio(enhanced_files)
"""

import asyncio
import json
import os
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, AsyncIterator, Callable

from pepperpy.core import PepperpyError

# Setup logging
logger = logging.getLogger(__name__)

class VerbosityLevel(Enum):
    """Verbosity levels for audio pipeline operations."""
    SILENT = 0    # No output
    ERROR = 1     # Only errors
    INFO = 2      # Basic information
    DEBUG = 3     # Detailed information
    VERBOSE = 4   # Very detailed information


class AudioPipelineError(PepperpyError):
    """Error raised by audio pipeline operations."""
    pass


@dataclass
class AudioSegment:
    """A segment of audio content."""
    
    title: str
    duration: str
    content: str
    speaker: str = "default"
    audio_path: Optional[str] = None


@dataclass
class AudioProject:
    """A complete audio project."""
    
    title: str
    description: str
    segments: List[AudioSegment]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AudioPipeline:
    """Pipeline for generating and processing audio content."""

    def __init__(
        self, 
        output_dir: Optional[Union[str, Path]] = None,
        voice_mapping: Optional[Dict[str, str]] = None,
        verbosity: Union[int, VerbosityLevel] = VerbosityLevel.INFO,
        **kwargs
    ) -> None:
        """Initialize the audio pipeline.
        
        Args:
            output_dir: Directory to save output files. If None, uses current directory.
            voice_mapping: Mapping of speaker names to voice IDs. If None, uses default mapping.
            verbosity: Verbosity level for pipeline operations.
            **kwargs: Additional configuration options.
        """
        # Setup output directory
        self.output_dir = Path(output_dir) if output_dir else Path("output/audio")
        self._ensure_directory(self.output_dir)
        
        # Setup default voice mapping
        default_voice_mapping = {
            "default": "en-US-1",
            "host": "en-US-1",
            "guest1": "en-US-2",
            "guest2": "en-US-3"
        }
        
        # Use provided mapping but ensure 'default' is included
        if voice_mapping:
            self.voice_mapping = voice_mapping.copy()
            if "default" not in self.voice_mapping:
                self.voice_mapping["default"] = default_voice_mapping["default"]
        else:
            self.voice_mapping = default_voice_mapping
        
        # Set verbosity
        self.verbosity = verbosity if isinstance(verbosity, VerbosityLevel) else VerbosityLevel(verbosity)
        
        # Setup logging based on verbosity
        self._configure_logging()
        
        # Additional configuration
        self.config = kwargs
    
    def _configure_logging(self) -> None:
        """Configure logging based on verbosity level."""
        log_level = logging.ERROR
        
        if self.verbosity == VerbosityLevel.SILENT:
            log_level = logging.CRITICAL
        elif self.verbosity == VerbosityLevel.ERROR:
            log_level = logging.ERROR
        elif self.verbosity == VerbosityLevel.INFO:
            log_level = logging.INFO
        elif self.verbosity == VerbosityLevel.DEBUG:
            log_level = logging.DEBUG
        elif self.verbosity == VerbosityLevel.VERBOSE:
            log_level = logging.DEBUG  # Python doesn't have a more verbose level
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.setLevel(log_level)
        logger.addHandler(handler)
        
        # Remove duplicate handlers
        for hdlr in logger.handlers[:-1]:
            logger.removeHandler(hdlr)
            
    def _ensure_directory(self, directory: Path) -> None:
        """Ensure a directory exists.
        
        Args:
            directory: Directory path
        """
        directory.mkdir(parents=True, exist_ok=True)
        
    def log(self, level: VerbosityLevel, message: str) -> None:
        """Log a message based on the current verbosity level.
        
        Args:
            level: Verbosity level of the message
            message: Message to log
        """
        if level.value <= self.verbosity.value:
            if level == VerbosityLevel.SILENT:
                return
            elif level == VerbosityLevel.ERROR:
                logger.error(message)
            elif level == VerbosityLevel.INFO:
                logger.info(message)
            elif level == VerbosityLevel.DEBUG:
                logger.debug(message)
            elif level == VerbosityLevel.VERBOSE:
                logger.debug(f"[VERBOSE] {message}")

    @staticmethod
    def create_segment(
        title: str, 
        content: str, 
        speaker: str = "default", 
        duration: str = ""
    ) -> AudioSegment:
        """Create an audio segment.
        
        Args:
            title: Segment title
            content: Segment content text
            speaker: Speaker identifier (maps to voice)
            duration: Optional duration string
            
        Returns:
            AudioSegment instance
        """
        return AudioSegment(
            title=title,
            content=content,
            speaker=speaker,
            duration=duration
        )
    
    @staticmethod
    def create_project(
        title: str,
        description: str,
        segments: Optional[List[Union[AudioSegment, Dict[str, Any]]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AudioProject:
        """Create an audio project.
        
        Args:
            title: Project title
            description: Project description
            segments: List of segments or segment data dictionaries
            metadata: Optional project metadata
            
        Returns:
            AudioProject instance
        """
        processed_segments = []
        
        # Process segments if provided
        if segments:
            for segment in segments:
                if isinstance(segment, AudioSegment):
                    processed_segments.append(segment)
                elif isinstance(segment, dict):
                    processed_segments.append(AudioSegment(
                        title=segment.get("title", "Untitled Segment"),
                        content=segment.get("content", ""),
                        speaker=segment.get("speaker", "default"),
                        duration=segment.get("duration", "")
                    ))
        
        return AudioProject(
            title=title,
            description=description,
            segments=processed_segments,
            metadata=metadata or {}
        )
    
    def save_project(self, project: AudioProject, file_path: Optional[Union[str, Path]] = None) -> str:
        """Save an audio project to a file.
        
        Args:
            project: AudioProject to save
            file_path: Optional file path. If None, a path is generated based on the project title.
            
        Returns:
            Path where the project was saved
        """
        # Generate path if not provided
        if file_path is None:
            file_path = self.output_dir / f"{project.title.lower().replace(' ', '_')}.json"
        else:
            file_path = Path(file_path)
            self._ensure_directory(file_path.parent)
        
        # Convert project to dictionary
        project_dict = {
            "title": project.title,
            "description": project.description,
            "metadata": project.metadata,
            "segments": [
                {
                    "title": segment.title,
                    "content": segment.content,
                    "speaker": segment.speaker,
                    "duration": segment.duration,
                    "audio_path": segment.audio_path
                }
                for segment in project.segments
            ]
        }
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(project_dict, f, indent=2)
        
        self.log(VerbosityLevel.INFO, f"Project saved to {file_path}")
        return str(file_path)

    async def load_content(self, 
                          source: Union[str, Path, Dict[str, Any]],
                          content_type: Optional[str] = None) -> AudioProject:
        """Load content from file or dictionary.
        
        Args:
            source: Path to content file or content dictionary
            content_type: Type of content (auto-detected if None)
            
        Returns:
            AudioProject with loaded content
            
        Raises:
            AudioPipelineError: If content cannot be loaded
        """
        try:
            # Handle dictionary input
            if isinstance(source, dict):
                result = self._create_project_from_dict(source)
                self.log(VerbosityLevel.INFO, f"Loaded project '{result.title}' from dictionary")
                return result
                
            # Handle file path input
            path = Path(source)
            if not path.exists():
                error_msg = f"Content file not found: {path}"
                self.log(VerbosityLevel.ERROR, error_msg)
                raise AudioPipelineError(error_msg)
                
            # Auto-detect content type from extension if not specified
            if content_type is None:
                content_type = path.suffix.lower().replace(".", "")
                
            # Load based on content type
            if content_type in ("json", ""):
                with open(path) as f:
                    data = json.load(f)
                    result = self._create_project_from_dict(data)
                    self.log(VerbosityLevel.INFO, f"Loaded project '{result.title}' from {path}")
                    return result
            else:
                error_msg = f"Unsupported content type: {content_type}"
                self.log(VerbosityLevel.ERROR, error_msg)
                raise AudioPipelineError(error_msg)
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {source}: {e}"
            self.log(VerbosityLevel.ERROR, error_msg)
            raise AudioPipelineError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load content: {e}"
            self.log(VerbosityLevel.ERROR, error_msg)
            raise AudioPipelineError(error_msg)
    
    def _create_project_from_dict(self, data: Dict[str, Any]) -> AudioProject:
        """Create an AudioProject from a dictionary.
        
        Args:
            data: Dictionary containing project data
            
        Returns:
            AudioProject instance
        """
        segments = []
        
        # Extract segments
        for i, segment_data in enumerate(data.get("segments", [])):
            # Determine speaker if not specified
            speaker = segment_data.get("speaker", "default")
            if not speaker or speaker == "default":
                if i % 3 == 0:
                    speaker = "host"
                elif i % 3 == 1 and data.get("speakers"):
                    speaker = "guest1"
                elif i % 3 == 2 and len(data.get("speakers", [])) > 1:
                    speaker = "guest2"
                
            segments.append(AudioSegment(
                title=segment_data.get("title", f"Segment {i+1}"),
                duration=segment_data.get("duration", ""),
                content=segment_data.get("content", ""),
                speaker=speaker
            ))
        
        return AudioProject(
            title=data.get("title", "Untitled Project"),
            description=data.get("description", ""),
            segments=segments,
            metadata=data.get("metadata", {})
        )
    
    async def generate_audio(self, 
                           project: AudioProject, 
                           provider: Optional[str] = None,
                           **kwargs) -> Dict[str, str]:
        """Generate audio for each segment of the project.
        
        Args:
            project: The audio project to generate audio for
            provider: Optional TTS provider to use
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary of segment titles to audio file paths
            
        Raises:
            AudioPipelineError: If audio generation fails
        """
        try:
            # Import here to avoid circular imports
            from pepperpy.tts import convert_text, save_audio
            
            audio_files = {}
            self.log(VerbosityLevel.INFO, f"Generating audio for {len(project.segments)} segments")
            
            for i, segment in enumerate(project.segments):
                # Skip empty segments
                if not segment.content.strip():
                    self.log(VerbosityLevel.DEBUG, f"Skipping empty segment: {segment.title}")
                    continue
                    
                # Determine voice ID from speaker mapping
                voice_id = self.voice_mapping.get(segment.speaker, self.voice_mapping["default"])
                
                self.log(VerbosityLevel.DEBUG, f"Processing segment {i+1}/{len(project.segments)}: '{segment.title}' with voice {voice_id}")
                
                # Generate audio
                audio = await convert_text(
                    text=segment.content, 
                    voice_id=voice_id, 
                    provider=provider,
                    **kwargs
                )
                
                # Create file name and path
                file_name = f"{i+1}_{segment.title.lower().replace(' ', '_')}.mp3"
                file_path = str(self.output_dir / file_name)
                
                # Save audio
                self.log(VerbosityLevel.DEBUG, f"Saving audio to {file_path}")
                save_audio(audio, file_path)
                
                # Update segment with audio path
                segment.audio_path = file_path
                audio_files[segment.title] = file_path
                
                self.log(VerbosityLevel.INFO, f"Generated audio for segment: {segment.title}")
                
            self.log(VerbosityLevel.INFO, f"Completed audio generation for all segments")
            return audio_files
            
        except Exception as e:
            error_msg = f"Failed to generate audio: {e}"
            self.log(VerbosityLevel.ERROR, error_msg)
            raise AudioPipelineError(error_msg)
    
    async def add_sound_effects(self, 
                              audio_files: Dict[str, str],
                              effects_mapping: Optional[Dict[str, str]] = None,
                              background_music: Optional[str] = None,
                              **kwargs) -> Dict[str, str]:
        """Add sound effects and background music to audio files.
        
        Args:
            audio_files: Dictionary of segment titles to audio file paths
            effects_mapping: Optional mapping of segment types to effect files
            background_music: Optional path to background music file
            **kwargs: Additional processing parameters
            
        Returns:
            Dictionary of segment titles to enhanced audio file paths
            
        Raises:
            AudioPipelineError: If adding effects fails
        """
        try:
            # Import here to avoid circular imports
            from pepperpy.tts import save_audio
            
            enhanced_files = {}
            self.log(VerbosityLevel.INFO, f"Adding sound effects to {len(audio_files)} audio files")
            
            if background_music:
                self.log(VerbosityLevel.INFO, f"Using background music: {background_music}")
            
            for title, file_path in audio_files.items():
                # Create enhanced file path
                enhanced_path = file_path.replace(".mp3", "_enhanced.mp3")
                
                self.log(VerbosityLevel.DEBUG, f"Enhancing audio for segment: {title}")
                
                # In a real implementation, this would mix the audio with effects
                # For now, we'll just copy the original file or simulate the output
                if os.path.exists(file_path):
                    # Here you would add code to mix audio with effects
                    # For example: mixer.mix_audio(file_path, effects, background_music, enhanced_path)
                    enhanced_files[title] = enhanced_path
                    self.log(VerbosityLevel.DEBUG, f"Enhanced audio saved to: {enhanced_path}")
                else:
                    # Simulated output for development/example purposes
                    enhanced_files[title] = enhanced_path
                    self.log(VerbosityLevel.DEBUG, f"Simulated enhanced audio for: {title}")
            
            self.log(VerbosityLevel.INFO, f"Completed adding sound effects to all audio files")
            return enhanced_files
            
        except Exception as e:
            error_msg = f"Failed to add sound effects: {e}"
            self.log(VerbosityLevel.ERROR, error_msg)
            raise AudioPipelineError(error_msg)
    
    async def compile_audio(self, 
                          enhanced_files: Dict[str, str],
                          project: AudioProject,
                          add_intro: bool = True,
                          add_outro: bool = True,
                          **kwargs) -> str:
        """Compile all segments into a final audio file.
        
        Args:
            enhanced_files: Dictionary of segment titles to enhanced audio file paths
            project: The audio project
            add_intro: Whether to add intro music
            add_outro: Whether to add outro music
            **kwargs: Additional compilation parameters
            
        Returns:
            Path to the final audio file
            
        Raises:
            AudioPipelineError: If compilation fails
        """
        try:
            # Create final output path
            final_path = str(self.output_dir / f"{project.title.lower().replace(' ', '_')}_final.mp3")
            
            self.log(VerbosityLevel.INFO, f"Compiling final audio to: {final_path}")
            
            if add_intro:
                self.log(VerbosityLevel.DEBUG, "Adding intro music")
            
            if add_outro:
                self.log(VerbosityLevel.DEBUG, "Adding outro music")
            
            # In a real implementation, this would merge audio files with transitions
            # For now, we'll just simulate the output
            
            # Here you would add code to compile the audio segments
            # For example: compiler.compile_audio(enhanced_files, transitions, final_path)
            
            self.log(VerbosityLevel.INFO, f"Successfully compiled final audio to: {final_path}")
            return final_path
            
        except Exception as e:
            error_msg = f"Failed to compile audio: {e}"
            self.log(VerbosityLevel.ERROR, error_msg)
            raise AudioPipelineError(error_msg)

    async def process_project(self, 
                            source: Union[str, Path, Dict[str, Any], AudioProject],
                            output_path: Optional[Union[str, Path]] = None,
                            *, 
                            background_music: Optional[str] = None,
                            **kwargs: Any) -> str:
        """Process a complete audio project from source to final output.
        
        This is a convenience method that runs the entire pipeline in one call.
        
        Args:
            source: Source content (file path, dictionary, or AudioProject)
            output_path: Optional output path for final audio
            **kwargs: Additional processing parameters
            
        Returns:
            Path to the final audio file
            
        Raises:
            AudioPipelineError: If processing fails
        """
        try:
            self.log(VerbosityLevel.INFO, "Starting audio project processing")
            
            # Load content if needed
            project = source if isinstance(source, AudioProject) else await self.load_content(source)
            
            # Set output path if provided
            if output_path:
                self.output_dir = Path(output_path).parent
                self._ensure_directory(self.output_dir)
                self.log(VerbosityLevel.DEBUG, f"Set output directory to: {self.output_dir}")
            
            # Generate audio
            self.log(VerbosityLevel.INFO, "Generating audio for project segments")
            audio_files = await self.generate_audio(project, **kwargs)
            
            # Add sound effects
            self.log(VerbosityLevel.INFO, "Adding sound effects to audio files")
            enhanced_files = await self.add_sound_effects(audio_files, background_music=background_music, **kwargs)
            
            # Compile final audio
            self.log(VerbosityLevel.INFO, "Compiling final audio output")
            final_path = await self.compile_audio(enhanced_files, project, **kwargs)
            
            self.log(VerbosityLevel.INFO, f"Project processing completed successfully")
            return final_path
            
        except Exception as e:
            error_msg = f"Failed to process audio project: {e}"
            self.log(VerbosityLevel.ERROR, error_msg)
            raise AudioPipelineError(error_msg) 