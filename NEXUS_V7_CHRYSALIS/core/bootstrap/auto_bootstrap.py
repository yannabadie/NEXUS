"""
AutoBootstrap - Automatic NEXUS.md Generation

When NEXUS is deployed to a new project without NEXUS.md:
1. Analyze project structure (glob, grep, read key files)
2. Detect tech stack and framework
3. Find key commands (package.json, Makefile, pyproject.toml)
4. Generate initial NEXUS.md

The generated NEXUS.md starts generalist and can be refined as NEXUS works.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime


@dataclass
class ProjectAnalysis:
    """Results of project analysis."""

    # Tech stack detection
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # Project structure
    directories: List[str] = field(default_factory=list)
    key_files: List[str] = field(default_factory=list)

    # Commands discovered
    commands: Dict[str, str] = field(default_factory=dict)

    # Conventions observed
    indentation: str = "unknown"
    naming_style: str = "unknown"
    has_tests: bool = False
    has_docs: bool = False
    has_ci: bool = False

    # Metadata
    project_name: str = "Unknown Project"
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())


class AutoBootstrap:
    """
    Automatically analyze a project and generate NEXUS.md.

    Usage:
        bootstrap = AutoBootstrap(project_path)
        analysis = bootstrap.analyze()
        nexus_md = bootstrap.generate_nexus_md(analysis)
        bootstrap.save(nexus_md)
    """

    # Tech stack detection patterns
    LANGUAGE_PATTERNS = {
        "Python": ["*.py", "requirements*.txt", "pyproject.toml", "setup.py", "Pipfile"],
        "JavaScript": ["*.js", "package.json", "*.mjs"],
        "TypeScript": ["*.ts", "*.tsx", "tsconfig.json"],
        "Go": ["*.go", "go.mod", "go.sum"],
        "Rust": ["*.rs", "Cargo.toml"],
        "Java": ["*.java", "pom.xml", "build.gradle"],
        "C#": ["*.cs", "*.csproj", "*.sln"],
        "Ruby": ["*.rb", "Gemfile", "Rakefile"],
        "PHP": ["*.php", "composer.json"],
    }

    FRAMEWORK_PATTERNS = {
        # Python
        "FastAPI": ["from fastapi", "import fastapi"],
        "Django": ["from django", "import django", "DJANGO_SETTINGS"],
        "Flask": ["from flask", "import flask"],
        "PyTorch": ["import torch", "from torch"],
        "TensorFlow": ["import tensorflow", "from tensorflow"],
        # JavaScript/TypeScript
        "React": ["from 'react'", "from \"react\"", "@types/react"],
        "Next.js": ["from 'next'", "next.config"],
        "Vue": ["from 'vue'", "@vue/"],
        "Express": ["from 'express'", "require('express')"],
        "NestJS": ["@nestjs/", "from '@nestjs"],
        # Other
        "Spring": ["org.springframework"],
        "Rails": ["Rails.application", "ActionController"],
    }

    DATABASE_PATTERNS = {
        "PostgreSQL": ["psycopg", "postgresql://", "postgres://", "pg_"],
        "MySQL": ["mysql://", "pymysql", "mysql-connector"],
        "MongoDB": ["mongodb://", "pymongo", "mongoose"],
        "SQLite": ["sqlite://", "sqlite3"],
        "Redis": ["redis://", "import redis", "from redis"],
        "Elasticsearch": ["elasticsearch", "from elasticsearch"],
    }

    TOOL_PATTERNS = {
        "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "Kubernetes": ["*.yaml", "kubectl", "k8s/"],
        "GitHub Actions": [".github/workflows/"],
        "GitLab CI": [".gitlab-ci.yml"],
        "pytest": ["pytest.ini", "conftest.py", "[tool.pytest]"],
        "Jest": ["jest.config*", "@types/jest"],
        "ESLint": [".eslintrc*", "eslint.config*"],
        "Prettier": [".prettierrc*", "prettier.config*"],
        "Black": ["[tool.black]"],
        "Ruff": ["[tool.ruff]", "ruff.toml"],
    }

    def __init__(self, project_path: Path):
        """
        Initialize AutoBootstrap.

        Args:
            project_path: Root path of the project to analyze
        """
        self.project_path = Path(project_path).resolve()
        self.analysis: Optional[ProjectAnalysis] = None

    def analyze(self) -> ProjectAnalysis:
        """
        Perform full project analysis.

        Returns:
            ProjectAnalysis with detected stack, structure, commands
        """
        analysis = ProjectAnalysis()
        analysis.project_name = self.project_path.name

        # Analyze structure
        analysis.directories = self._analyze_directories()
        analysis.key_files = self._find_key_files()

        # Detect tech stack
        analysis.languages = self._detect_languages()
        analysis.frameworks = self._detect_frameworks()
        analysis.databases = self._detect_databases()
        analysis.tools = self._detect_tools()

        # Find commands
        analysis.commands = self._discover_commands()

        # Observe conventions
        analysis.indentation = self._detect_indentation()
        analysis.naming_style = self._detect_naming_style()
        analysis.has_tests = self._has_tests()
        analysis.has_docs = self._has_docs()
        analysis.has_ci = self._has_ci()

        self.analysis = analysis
        return analysis

    def _analyze_directories(self) -> List[str]:
        """Find significant directories."""
        significant_dirs = []
        ignored = {".git", "node_modules", "__pycache__", ".venv", "venv",
                   ".tox", ".pytest_cache", "dist", "build", ".next", "target"}

        try:
            for item in self.project_path.iterdir():
                if item.is_dir() and item.name not in ignored and not item.name.startswith("."):
                    significant_dirs.append(item.name)
        except PermissionError:
            pass

        return sorted(significant_dirs)[:20]  # Limit to 20

    def _find_key_files(self) -> List[str]:
        """Find configuration and key files."""
        key_patterns = [
            "README*", "LICENSE*", "CHANGELOG*",
            "package.json", "pyproject.toml", "setup.py", "setup.cfg",
            "Makefile", "Dockerfile", "docker-compose*",
            "requirements*.txt", "Pipfile", "Cargo.toml", "go.mod",
            "tsconfig.json", ".env.example", "*.config.js", "*.config.ts",
        ]

        found = []
        for pattern in key_patterns:
            for match in self.project_path.glob(pattern):
                if match.is_file():
                    found.append(match.name)

        return sorted(set(found))[:30]  # Limit and dedupe

    def _detect_languages(self) -> List[str]:
        """Detect programming languages used."""
        detected = []

        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern.startswith("*"):
                    # File extension pattern
                    matches = list(self.project_path.rglob(pattern))
                    # Exclude common ignored directories
                    matches = [m for m in matches
                               if not any(p in str(m) for p in ["node_modules", "__pycache__", ".git", "venv"])]
                    if matches:
                        detected.append(lang)
                        break
                else:
                    # Specific file pattern
                    if (self.project_path / pattern).exists():
                        detected.append(lang)
                        break

        return detected

    def _detect_frameworks(self) -> List[str]:
        """Detect frameworks by searching file contents."""
        detected = []

        # Read key files for framework patterns
        files_to_check = []

        # Python files
        for py_file in list(self.project_path.rglob("*.py"))[:50]:
            if not any(p in str(py_file) for p in ["node_modules", "__pycache__", ".git", "venv"]):
                files_to_check.append(py_file)

        # JavaScript/TypeScript files
        for pattern in ["*.js", "*.ts", "*.jsx", "*.tsx"]:
            for js_file in list(self.project_path.rglob(pattern))[:30]:
                if not any(p in str(js_file) for p in ["node_modules", "__pycache__", ".git"]):
                    files_to_check.append(js_file)

        # Package files
        for name in ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml"]:
            pkg_file = self.project_path / name
            if pkg_file.exists():
                files_to_check.append(pkg_file)

        # Check patterns
        content_cache: Dict[Path, str] = {}

        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for file_path in files_to_check:
                try:
                    if file_path not in content_cache:
                        content_cache[file_path] = file_path.read_text(encoding="utf-8", errors="ignore")

                    content = content_cache[file_path]
                    if any(pattern in content for pattern in patterns):
                        if framework not in detected:
                            detected.append(framework)
                        break
                except (PermissionError, OSError):
                    continue

        # Also check package.json dependencies for common frameworks
        pkg_json = self.project_path / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "react" in deps and "React" not in detected:
                    detected.append("React")
                if "vue" in deps and "Vue" not in detected:
                    detected.append("Vue")
                if "express" in deps and "Express" not in detected:
                    detected.append("Express")
                if "@nestjs/core" in deps and "NestJS" not in detected:
                    detected.append("NestJS")
                if "next" in deps and "Next.js" not in detected:
                    detected.append("Next.js")
            except (json.JSONDecodeError, OSError):
                pass

        return detected

    def _detect_databases(self) -> List[str]:
        """Detect databases from connection strings and imports."""
        detected = []

        # Check common config files
        config_files = [
            "*.py", ".env*", "*.json", "*.yaml", "*.yml", "*.toml"
        ]

        files_to_check = []
        for pattern in config_files:
            for f in list(self.project_path.rglob(pattern))[:30]:
                if not any(p in str(f) for p in ["node_modules", "__pycache__", ".git", "venv"]):
                    files_to_check.append(f)

        for db, patterns in self.DATABASE_PATTERNS.items():
            for file_path in files_to_check:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if any(pattern.lower() in content.lower() for pattern in patterns):
                        if db not in detected:
                            detected.append(db)
                        break
                except (PermissionError, OSError):
                    continue

        return detected

    def _detect_tools(self) -> List[str]:
        """Detect development tools."""
        detected = []

        for tool, patterns in self.TOOL_PATTERNS.items():
            found = False
            for pattern in patterns:
                if found:
                    break

                if "/" in pattern:
                    # Directory pattern
                    if (self.project_path / pattern.rstrip("/")).exists():
                        detected.append(tool)
                        found = True
                elif pattern.startswith("["):
                    # TOML section pattern - check pyproject.toml
                    toml_file = self.project_path / "pyproject.toml"
                    if toml_file.exists():
                        try:
                            content = toml_file.read_text(encoding="utf-8")
                            if pattern in content:
                                detected.append(tool)
                                found = True
                        except (PermissionError, OSError):
                            pass
                elif "*" in pattern:
                    # Glob pattern with wildcard
                    matches = list(self.project_path.glob(pattern))
                    if matches:
                        detected.append(tool)
                        found = True
                else:
                    # Exact file pattern
                    if (self.project_path / pattern).exists():
                        detected.append(tool)
                        found = True

        return detected

    def _discover_commands(self) -> Dict[str, str]:
        """Discover available commands from package files."""
        commands = {}

        # package.json scripts
        pkg_json = self.project_path / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                for name, cmd in scripts.items():
                    commands[f"npm run {name}"] = cmd[:100]  # Truncate long commands
            except (json.JSONDecodeError, OSError):
                pass

        # Makefile targets
        makefile = self.project_path / "Makefile"
        if makefile.exists():
            try:
                content = makefile.read_text(encoding="utf-8")
                # Find targets (lines starting with word followed by :)
                for match in re.finditer(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:", content, re.MULTILINE):
                    target = match.group(1)
                    if target not in ["PHONY", "all", "default"]:
                        commands[f"make {target}"] = f"Makefile target: {target}"
            except (OSError, UnicodeDecodeError):
                pass

        # pyproject.toml scripts
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                # Simple TOML parsing for scripts section
                if "[project.scripts]" in content or "[tool.poetry.scripts]" in content:
                    commands["python -m <module>"] = "Entry points defined in pyproject.toml"

                # pytest
                if "pytest" in content.lower():
                    commands["pytest"] = "Run tests with pytest"
            except (OSError, UnicodeDecodeError):
                pass

        # Common commands based on detected files
        if (self.project_path / "requirements.txt").exists():
            commands["pip install -r requirements.txt"] = "Install Python dependencies"

        if (self.project_path / "package.json").exists():
            commands["npm install"] = "Install Node.js dependencies"

        return commands

    def _detect_indentation(self) -> str:
        """Detect common indentation style."""
        # Check a few Python/JS files
        spaces_2 = 0
        spaces_4 = 0
        tabs = 0

        for pattern in ["*.py", "*.js", "*.ts"]:
            for f in list(self.project_path.rglob(pattern))[:10]:
                if any(p in str(f) for p in ["node_modules", "__pycache__", ".git"]):
                    continue
                try:
                    lines = f.read_text(encoding="utf-8").split("\n")[:100]
                    for line in lines:
                        if line.startswith("    ") and not line.startswith("     "):
                            spaces_4 += 1
                        elif line.startswith("  ") and not line.startswith("   "):
                            spaces_2 += 1
                        elif line.startswith("\t"):
                            tabs += 1
                except (OSError, UnicodeDecodeError):
                    continue

        if spaces_4 > spaces_2 and spaces_4 > tabs:
            return "4 spaces"
        elif spaces_2 > spaces_4 and spaces_2 > tabs:
            return "2 spaces"
        elif tabs > 0:
            return "tabs"
        return "unknown"

    def _detect_naming_style(self) -> str:
        """Detect naming conventions."""
        # Check Python files for snake_case vs camelCase
        snake_count = 0
        camel_count = 0

        for f in list(self.project_path.rglob("*.py"))[:20]:
            if any(p in str(f) for p in ["node_modules", "__pycache__", ".git", "venv"]):
                continue
            try:
                content = f.read_text(encoding="utf-8")
                snake_count += len(re.findall(r"\bdef [a-z]+_[a-z]", content))
                camel_count += len(re.findall(r"\bdef [a-z]+[A-Z]", content))
            except (OSError, UnicodeDecodeError):
                continue

        if snake_count > camel_count:
            return "snake_case"
        elif camel_count > snake_count:
            return "camelCase"
        return "mixed"

    def _has_tests(self) -> bool:
        """Check if project has tests."""
        test_indicators = [
            "tests/", "test/", "spec/", "__tests__/",
            "*_test.py", "test_*.py", "*.test.js", "*.spec.ts"
        ]

        for indicator in test_indicators:
            if "/" in indicator:
                if (self.project_path / indicator.rstrip("/")).exists():
                    return True
            else:
                if list(self.project_path.rglob(indicator)):
                    return True
        return False

    def _has_docs(self) -> bool:
        """Check if project has documentation."""
        doc_indicators = ["docs/", "documentation/", "doc/", "README.md", "CONTRIBUTING.md"]
        return any((self.project_path / ind.rstrip("/")).exists() for ind in doc_indicators)

    def _has_ci(self) -> bool:
        """Check if project has CI/CD configuration."""
        ci_paths = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "Jenkinsfile",
            ".circleci/config.yml",
            "azure-pipelines.yml"
        ]
        return any((self.project_path / p).exists() for p in ci_paths)

    def generate_nexus_md(self, analysis: Optional[ProjectAnalysis] = None) -> str:
        """
        Generate NEXUS.md content from analysis.

        Args:
            analysis: ProjectAnalysis (uses self.analysis if not provided)

        Returns:
            NEXUS.md content as string
        """
        if analysis is None:
            analysis = self.analysis
        if analysis is None:
            raise ValueError("No analysis available. Run analyze() first.")

        lines = [
            f"# {analysis.project_name}",
            "",
            "> Auto-generated by NEXUS AutoBootstrap",
            f"> Generated: {analysis.analysis_date[:10]}",
            "",
            "---",
            "",
        ]

        # Tech Stack
        lines.append("## Tech Stack")
        lines.append("")

        if analysis.languages:
            lines.append(f"**Languages:** {', '.join(analysis.languages)}")
        if analysis.frameworks:
            lines.append(f"**Frameworks:** {', '.join(analysis.frameworks)}")
        if analysis.databases:
            lines.append(f"**Databases:** {', '.join(analysis.databases)}")
        if analysis.tools:
            lines.append(f"**Tools:** {', '.join(analysis.tools)}")

        lines.append("")

        # Project Structure
        lines.append("## Project Structure")
        lines.append("")
        lines.append("```")
        lines.append(f"{analysis.project_name}/")
        for dir_name in analysis.directories[:10]:
            lines.append(f"├── {dir_name}/")
        for file_name in analysis.key_files[:5]:
            lines.append(f"├── {file_name}")
        lines.append("```")
        lines.append("")

        # Commands
        if analysis.commands:
            lines.append("## Key Commands")
            lines.append("")
            for cmd, desc in list(analysis.commands.items())[:10]:
                lines.append(f"- `{cmd}` - {desc[:50]}")
            lines.append("")

        # Conventions
        lines.append("## Code Conventions")
        lines.append("")
        lines.append(f"- **Indentation:** {analysis.indentation}")
        lines.append(f"- **Naming:** {analysis.naming_style}")
        lines.append(f"- **Tests:** {'Yes' if analysis.has_tests else 'No tests found'}")
        lines.append(f"- **Documentation:** {'Yes' if analysis.has_docs else 'No docs found'}")
        lines.append(f"- **CI/CD:** {'Yes' if analysis.has_ci else 'Not configured'}")
        lines.append("")

        # DO NOT section (placeholder)
        lines.append("## DO NOT")
        lines.append("")
        lines.append("- DO NOT modify this file without updating the codebase")
        lines.append("- DO NOT commit sensitive data (.env, credentials)")
        lines.append("")

        # Notes
        lines.append("## Notes")
        lines.append("")
        lines.append("This NEXUS.md was auto-generated. Refine as needed:")
        lines.append("- Add project-specific conventions")
        lines.append("- Document architecture decisions")
        lines.append("- Add team coding standards")
        lines.append("")

        return "\n".join(lines)

    def save(self, content: Optional[str] = None, path: Optional[Path] = None) -> Path:
        """
        Save NEXUS.md to project.

        Args:
            content: NEXUS.md content (generates if not provided)
            path: Save path (defaults to project_path/NEXUS.md)

        Returns:
            Path where file was saved
        """
        if content is None:
            content = self.generate_nexus_md()

        save_path = path or (self.project_path / "NEXUS.md")
        save_path.write_text(content, encoding="utf-8")

        return save_path

    def needs_bootstrap(self) -> bool:
        """
        Check if project needs NEXUS.md generation.

        Returns:
            True if no NEXUS.md exists
        """
        nexus_md = self.project_path / "NEXUS.md"
        return not nexus_md.exists()


def bootstrap_project(project_path: Path, force: bool = False) -> Optional[Path]:
    """
    Convenience function to bootstrap a project.

    Args:
        project_path: Project root path
        force: Generate even if NEXUS.md exists

    Returns:
        Path to generated NEXUS.md, or None if skipped
    """
    bootstrap = AutoBootstrap(project_path)

    if not force and not bootstrap.needs_bootstrap():
        return None

    analysis = bootstrap.analyze()
    content = bootstrap.generate_nexus_md(analysis)
    return bootstrap.save(content)
