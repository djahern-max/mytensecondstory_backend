#!/usr/bin/env python3
"""
MyTenSecondStory Backend Application Documentation Generator

This script analyzes the FastAPI application structure and generates 
comprehensive documentation about the current capabilities.
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class AppDocumentationGenerator:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.doc_data = {
            "generated_at": datetime.now().isoformat(),
            "application_name": "MyTenSecondStory Backend",
            "structure": {},
            "models": {},
            "routes": {},
            "services": {},
            "schemas": {},
            "dependencies": [],
            "configuration": {},
            "database_tables": []
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file and extract relevant information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to parse as AST for structured analysis
            try:
                tree = ast.parse(content)
                return {
                    "content": content,
                    "classes": [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)],
                    "functions": [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)],
                    "imports": self.extract_imports(tree),
                    "lines": len(content.split('\n'))
                }
            except:
                # If AST parsing fails, just return content
                return {
                    "content": content,
                    "lines": len(content.split('\n')),
                    "error": "Could not parse AST"
                }
        except Exception as e:
            return {"error": str(e)}
    
    def extract_imports(self, tree) -> List[str]:
        """Extract import statements from AST"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports
    
    def analyze_models(self):
        """Analyze SQLAlchemy models"""
        models_dir = self.app_root / "models"
        if models_dir.exists():
            for file_path in models_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    analysis = self.analyze_file(file_path)
                    self.doc_data["models"][file_path.stem] = analysis
    
    def analyze_routes(self):
        """Analyze API routes"""
        routes_dir = self.app_root / "api" / "routes"
        if routes_dir.exists():
            for file_path in routes_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    analysis = self.analyze_file(file_path)
                    self.doc_data["routes"][file_path.stem] = analysis
    
    def analyze_services(self):
        """Analyze service layer"""
        services_dir = self.app_root / "services"
        if services_dir.exists():
            for file_path in services_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    analysis = self.analyze_file(file_path)
                    self.doc_data["services"][file_path.stem] = analysis
    
    def analyze_schemas(self):
        """Analyze Pydantic schemas"""
        schemas_dir = self.app_root / "schemas"
        if schemas_dir.exists():
            for file_path in schemas_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    analysis = self.analyze_file(file_path)
                    self.doc_data["schemas"][file_path.stem] = analysis
    
    def analyze_config(self):
        """Analyze configuration files"""
        config_dir = self.app_root / "core"
        if config_dir.exists():
            for file_path in config_dir.glob("*.py"):
                analysis = self.analyze_file(file_path)
                self.doc_data["configuration"][file_path.stem] = analysis
    
    def analyze_requirements(self):
        """Analyze requirements.txt for dependencies"""
        req_file = self.app_root.parent / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                self.doc_data["dependencies"] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    def analyze_main(self):
        """Analyze main.py for app structure"""
        main_file = self.app_root / "main.py"
        if main_file.exists():
            analysis = self.analyze_file(main_file)
            self.doc_data["main_application"] = analysis
    
    def generate_structure_tree(self):
        """Generate directory structure"""
        def build_tree(path: Path, prefix: str = "") -> Dict:
            tree = {"name": path.name, "type": "directory" if path.is_dir() else "file", "children": []}
            if path.is_dir():
                try:
                    for item in sorted(path.iterdir()):
                        if not item.name.startswith('.') and item.name != '__pycache__':
                            tree["children"].append(build_tree(item, prefix + "  "))
                except PermissionError:
                    pass
            return tree
        
        self.doc_data["structure"] = build_tree(self.app_root)
    
    def generate_markdown_report(self) -> str:
        """Generate a comprehensive markdown report"""
        md = f"""# MyTenSecondStory Backend Application Documentation

Generated on: {self.doc_data['generated_at']}

## Overview
This is a FastAPI-based backend application for MyTenSecondStory, a platform for creating and sharing 10-second personal video stories with AI-generated backgrounds.

## Application Structure

```
{self.format_structure_tree(self.doc_data['structure'])}
```

## Dependencies
The application uses the following main dependencies:
"""
        
        for dep in self.doc_data["dependencies"][:20]:  # Show first 20 deps
            md += f"- {dep}\n"
        
        if len(self.doc_data["dependencies"]) > 20:
            md += f"... and {len(self.doc_data['dependencies']) - 20} more dependencies\n"
        
        md += "\n## Database Models\n"
        for model_name, model_info in self.doc_data["models"].items():
            md += f"\n### {model_name.title()} Model\n"
            md += f"- **Classes**: {', '.join(model_info.get('classes', []))}\n"
            md += f"- **Functions**: {', '.join(model_info.get('functions', []))}\n"
            md += f"- **Lines of code**: {model_info.get('lines', 'Unknown')}\n"
        
        md += "\n## API Routes\n"
        for route_name, route_info in self.doc_data["routes"].items():
            md += f"\n### {route_name.title()} Routes\n"
            md += f"- **Functions**: {', '.join(route_info.get('functions', []))}\n"
            md += f"- **Lines of code**: {route_info.get('lines', 'Unknown')}\n"
        
        md += "\n## Services\n"
        for service_name, service_info in self.doc_data["services"].items():
            md += f"\n### {service_name.title()} Service\n"
            md += f"- **Classes**: {', '.join(service_info.get('classes', []))}\n"
            md += f"- **Functions**: {', '.join(service_info.get('functions', []))}\n"
            md += f"- **Lines of code**: {service_info.get('lines', 'Unknown')}\n"
        
        md += "\n## Data Schemas\n"
        for schema_name, schema_info in self.doc_data["schemas"].items():
            md += f"\n### {schema_name.title()} Schema\n"
            md += f"- **Classes**: {', '.join(schema_info.get('classes', []))}\n"
            md += f"- **Lines of code**: {schema_info.get('lines', 'Unknown')}\n"
        
        md += "\n## Configuration\n"
        for config_name, config_info in self.doc_data["configuration"].items():
            md += f"\n### {config_name.title()}\n"
            md += f"- **Classes**: {', '.join(config_info.get('classes', []))}\n"
            md += f"- **Functions**: {', '.join(config_info.get('functions', []))}\n"
            md += f"- **Lines of code**: {config_info.get('lines', 'Unknown')}\n"
        
        # Add main application analysis
        if "main_application" in self.doc_data:
            md += "\n## Main Application\n"
            main_info = self.doc_data["main_application"]
            md += f"- **Functions**: {', '.join(main_info.get('functions', []))}\n"
            md += f"- **Lines of code**: {main_info.get('lines', 'Unknown')}\n"
        
        return md
    
    def format_structure_tree(self, tree: Dict, indent: str = "") -> str:
        """Format structure tree as text"""
        result = f"{indent}{tree['name']}/\n" if tree['type'] == 'directory' else f"{indent}{tree['name']}\n"
        for child in tree.get('children', []):
            result += self.format_structure_tree(child, indent + "  ")
        return result
    
    def generate_detailed_code_analysis(self) -> str:
        """Generate detailed code analysis with actual code snippets"""
        md = "\n\n# Detailed Code Analysis\n\n"
        
        # Analyze each major component
        sections = [
            ("Models", self.doc_data["models"]),
            ("Routes", self.doc_data["routes"]), 
            ("Services", self.doc_data["services"]),
            ("Schemas", self.doc_data["schemas"])
        ]
        
        for section_name, section_data in sections:
            md += f"## {section_name} Code Analysis\n\n"
            
            for file_name, file_info in section_data.items():
                md += f"### {file_name}.py\n\n"
                
                if 'content' in file_info:
                    # Show first 50 lines of each file
                    lines = file_info['content'].split('\n')
                    preview_lines = lines[:50]
                    
                    md += "```python\n"
                    md += '\n'.join(preview_lines)
                    if len(lines) > 50:
                        md += f"\n... ({len(lines) - 50} more lines)\n"
                    md += "```\n\n"
                
                if file_info.get('classes'):
                    md += f"**Classes found**: {', '.join(file_info['classes'])}\n\n"
                
                if file_info.get('functions'):
                    md += f"**Functions found**: {', '.join(file_info['functions'])}\n\n"
        
        return md
    
    def run_analysis(self, include_code: bool = True):
        """Run complete analysis"""
        print("Analyzing application structure...")
        self.generate_structure_tree()
        
        print("Analyzing models...")
        self.analyze_models()
        
        print("Analyzing routes...")
        self.analyze_routes()
        
        print("Analyzing services...")
        self.analyze_services()
        
        print("Analyzing schemas...")
        self.analyze_schemas()
        
        print("Analyzing configuration...")
        self.analyze_config()
        
        print("Analyzing requirements...")
        self.analyze_requirements()
        
        print("Analyzing main application...")
        self.analyze_main()
        
        # Generate reports
        markdown_report = self.generate_markdown_report()
        
        if include_code:
            markdown_report += self.generate_detailed_code_analysis()
        
        # Save to file
        output_file = self.app_root.parent / "application_documentation.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"Documentation generated: {output_file}")
        
        # Also save JSON for structured data
        json_file = self.app_root.parent / "application_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # Remove content to avoid huge JSON file
            clean_data = self.doc_data.copy()
            for section in ['models', 'routes', 'services', 'schemas', 'configuration']:
                for item in clean_data.get(section, {}):
                    if 'content' in clean_data[section][item]:
                        clean_data[section][item]['content'] = f"[{clean_data[section][item]['lines']} lines of code]"
            
            json.dump(clean_data, f, indent=2)
        
        print(f"Structured data saved: {json_file}")
        
        return output_file

if __name__ == "__main__":
    import sys
    
    # Get app directory from command line or use default
    app_dir = sys.argv[1] if len(sys.argv) > 1 else "./app"
    include_code = "--code" in sys.argv
    
    if not os.path.exists(app_dir):
        print(f"Error: Directory {app_dir} does not exist")
        sys.exit(1)
    
    generator = AppDocumentationGenerator(app_dir)
    output_file = generator.run_analysis(include_code=include_code)
    
    print(f"\n✅ Analysis complete!")
    print(f"📄 Documentation: {output_file}")
    print(f"📊 JSON data: {output_file.parent}/application_analysis.json")
    print(f"\nYou can now share the generated documentation file with Claude!")
