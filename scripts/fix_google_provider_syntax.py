#!/usr/bin/env python3
"""
Script to fix syntax errors in the google_provider.py file.
"""

import re


def read_file(file_path: str) -> str:
    """Read file content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_google_provider_syntax() -> None:
    """Fix syntax errors in google_provider.py."""
    file_path = (
        "pepperpy/multimodal/audio/providers/transcription/google/google_provider.py"
    )

    try:
        content = read_file(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    # Create a backup of the original file
    backup_path = f"{file_path}.syntax.bak"
    write_file(backup_path, content)
    print(f"Created backup at {backup_path}")

    # Fix the client initialization
    content = re.sub(
        r"try:\s+self\.client = speech\.SpeechClient\(\)\s+credentials=credentials,\s+project=project_id,\s+\)",
        "try:\n            self.client = speech.SpeechClient(\n                credentials=credentials,\n                project=project_id\n            )",
        content,
    )

    # Fix the transcribe method definition
    content = re.sub(
        r"def transcribe\(\)\s+self,\s+audio: Union\[str, Path, bytes\],\s+language: Optional\[str\] = None,\s+\*\*kwargs,\s+\) -> str:",
        "def transcribe(\n        self,\n        audio: Union[str, Path, bytes],\n        language: Optional[str] = None,\n        **kwargs\n    ) -> str:",
        content,
    )

    # Fix the RecognitionConfig initialization
    content = re.sub(
        r"config = speech\.RecognitionConfig\(\)\s+language_code=language or \"en-US\",\s+\*\*self\.kwargs,\s+\*\*kwargs,\s+\)",
        'config = speech.RecognitionConfig(\n                language_code=language or "en-US",\n                **self.kwargs,\n                **kwargs\n            )',
        content,
    )

    # Fix the recognize method call
    content = re.sub(
        r"response = self\.client\.recognize\(\)\s+config=config,\s+audio=audio_input,\s+\)",
        "response = self.client.recognize(\n                config=config,\n                audio=audio_input\n            )",
        content,
    )

    # Fix the join method call
    content = re.sub(
        r"text = \" \"\.join\(\)\s+result\.alternatives\[0\]\.transcript\s+for result in response\.results\s+if result\.alternatives\s+\)",
        'text = " ".join(\n                result.alternatives[0].transcript\n                for result in response.results\n                if result.alternatives\n            )',
        content,
    )

    # Fix the transcribe_with_timestamps method definition
    content = re.sub(
        r"def transcribe_with_timestamps\(\)\s+self,\s+audio: Union\[str, Path, bytes\],\s+language: Optional\[str\] = None,\s+\*\*kwargs,\s+\) -> List\[Dict\[str, Union\[str, float\]\]\]:",
        "def transcribe_with_timestamps(\n        self,\n        audio: Union[str, Path, bytes],\n        language: Optional[str] = None,\n        **kwargs\n    ) -> List[Dict[str, Union[str, float]]]:",
        content,
    )

    # Fix the current_segment initialization
    content = re.sub(
        r"current_segment = \{\}\s+\"text\": \"\",\s+\"start\": words\[0\]\.start_time\.total_seconds\(\),\s+\"end\": words\[-1\]\.end_time\.total_seconds\(\),\s+\}",
        'current_segment = {\n                            "text": "",\n                            "start": words[0].start_time.total_seconds(),\n                            "end": words[-1].end_time.total_seconds()\n                        }',
        content,
    )

    # Fix the return statements in get_supported_languages and get_supported_formats
    content = re.sub(
        r"return \[\]\s+\"af-ZA\",", 'return [\n            "af-ZA",', content
    )

    content = re.sub(
        r"return \[\]\s+\"flac\",", 'return [\n            "flac",', content
    )

    # Write the fixed content
    write_file(file_path, content)
    print(f"Fixed syntax errors in {file_path}")


def main() -> None:
    """Main function."""
    print("Fixing syntax errors in google_provider.py...")
    fix_google_provider_syntax()
    print("Done!")


if __name__ == "__main__":
    main()
