"""
Context Validation System
Version: 1.4
"""

import yaml
from pathlib import Path

class ContextValidator:
    def __init__(self, docs_root="docs"):
        self.docs_path = Path(docs_root)
        self.requirements = {
            "provider_system": ["registration", "config_schema", "error_handling"],
            "agent_lifecycle": ["initialization", "execution", "cleanup"]
        }

    def validate_structure(self):
        report = {}
        for section, components in self.requirements.items():
            section_file = self.docs_path / "conventions" / f"0_{section}.md"
            if not section_file.exists():
                report[section] = "MISSING_FILE"
                continue
            
            content = section_file.read_text()
            missing = [c for c in components if f"# {c}" not in content]
            if missing:
                report[section] = {"missing_components": missing}
        
        return report

    def check_file_sizes(self):
        oversized = []
        for md_file in self.docs_path.glob("**/*.md"):
            if md_file.stat().st_size > 1024 * 25:  # 25KB
                oversized.append(str(md_file.relative_to(self.docs_path)))
        
        return oversized

if __name__ == "__main__":
    validator = ContextValidator()
    structure_report = validator.validate_structure()
    size_report = validator.check_file_sizes()
    
    print("Validation Report:")
    print(yaml.dump({
        "structure_issues": structure_report,
        "oversized_files": size_report
    }))