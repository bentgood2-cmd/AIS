"""
Automated setup script for AIS v3.2.1. Creates directory structure, generates files with initial content,
installs dependencies, and configures the system.
Usage: python setup_ais.py
"""
from pathlib import Path
from subprocess import run, CalledProcessError, PIPE
from shutil import rmtree
from sys import executable, exit
import logging
from logging import basicConfig, getLogger, DEBUG, INFO
from typing import Dict, List
from dataclasses import dataclass, field
import os

# Import configuration
from setup_config import (
    AIS_VERSION, DIRECTORIES, FILE_TEMPLATES, 
    LOGGING_CONFIG, DEFAULT_CONFIG
)

# Configure logging
try:
    log_level = getattr(logging, LOGGING_CONFIG["level"], INFO)
except (AttributeError, KeyError):
    log_level = INFO

basicConfig(
    level=log_level,
    format=LOGGING_CONFIG["format"],
    filename=LOGGING_CONFIG["filename"]
)
logger = getLogger(__name__)

@dataclass
class SetupConfig:
    """Configuration for the AIS setup process."""
    version: str = AIS_VERSION
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.resolve())
    cleanup_existing: bool = DEFAULT_CONFIG["cleanup_existing"]
    install_dependencies: bool = DEFAULT_CONFIG["install_dependencies"]
    create_files: bool = DEFAULT_CONFIG["create_files"]
    verbose: bool = DEFAULT_CONFIG["verbose"]
    
    def __post_init__(self):
        """Validate and sanitize base_dir to prevent path traversal."""
        if self.base_dir:
            # Resolve to absolute path and check for traversal attempts
            resolved_path = Path(self.base_dir).resolve()
            current_dir = Path(__file__).parent.resolve()
            
            # Ensure the path is within reasonable bounds (not going up too many levels)
            try:
                resolved_path.relative_to(current_dir.parent.parent)
            except ValueError:
                # Path is outside allowed area, use default
                logger.warning(f"Invalid base_dir path detected: {self.base_dir}. Using default.")
                self.base_dir = current_dir
            else:
                self.base_dir = resolved_path

class DirectoryManager:
    """Manages directory creation and cleanup operations."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.directories = DIRECTORIES
    
    def create_directories(self) -> None:
        """Create all required directories."""
        for dir_path in self.directories:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
    
    def cleanup_existing(self) -> None:
        """Clean up any existing AIS installation."""
        ais_path = self.base_dir / "ais"
        if ais_path.exists():
            try:
                rmtree(ais_path)
                logger.info("Cleaned up previous AIS installation")
            except Exception as e:
                logger.warning(f"Failed to clean up previous installation: {str(e)}")

class FileGenerator:
    """Generates files with initial content."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.files = FILE_TEMPLATES
    
    def generate_files(self) -> None:
        """Generate all files with initial content."""
        created_files = []
        try:
            for file_name, content in self.files.items():
                file_path = self.base_dir / file_name
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    created_files.append(file_path)
                    logger.info(f"Created file: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to create file {file_path}: {str(e)}")
                    # Cleanup partially created files
                    for created_file in created_files:
                        try:
                            created_file.unlink(missing_ok=True)
                        except Exception:
                            pass
                    raise
        except Exception as e:
            logger.error(f"File generation failed: {str(e)}")
            raise

class DependencyManager:
    """Manages dependency installation."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.requirements_path = base_dir / "requirements.txt"
    
    def install_dependencies(self) -> None:
        """Install required dependencies."""
        try:
            if not self.requirements_path.exists():
                raise FileNotFoundError("Requirements.txt not found")
                
            logger.info("Installing dependencies...")
            result = run(
                [executable, "-m", "pip", "install", "-r", str(self.requirements_path)], 
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            logger.info("Dependencies installed successfully")
            if result.stdout:
                logger.debug(f"Installation output: {result.stdout}")
        except CalledProcessError as e:
            logger.error(f"Dependency installation failed: {str(e)}")
            if e.stdout:
                logger.error(f"STDOUT: {e.stdout}")
            if e.stderr:
                logger.error(f"STDERR: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Dependency installation error: {str(e)}")
            raise

class AISSetup:
    """Main setup orchestrator for AIS."""
    
    def __init__(self, config: SetupConfig):
        self.config = config
        self.dir_manager = DirectoryManager(self.config.base_dir)
        self.file_generator = FileGenerator(self.config.base_dir)
        self.dep_manager = DependencyManager(self.config.base_dir)
    
    def setup(self) -> None:
        """Execute the complete setup process."""
        logger.info(f"Starting AIS v{self.config.version} setup in {self.config.base_dir}")
        
        try:
            # Clean up previous installation if requested
            if self.config.cleanup_existing:
                try:
                    self.dir_manager.cleanup_existing()
                except Exception as e:
                    logger.error(f"Cleanup failed: {str(e)}")
                    raise
            
            # Create directory structure
            try:
                self.dir_manager.create_directories()
            except Exception as e:
                logger.error(f"Directory creation failed: {str(e)}")
                raise
            
            # Generate files if requested
            if self.config.create_files:
                try:
                    self.file_generator.generate_files()
                except Exception as e:
                    logger.error(f"File generation failed: {str(e)}")
                    raise
            
            # Install dependencies if requested
            if self.config.install_dependencies:
                try:
                    self.dep_manager.install_dependencies()
                except Exception as e:
                    logger.error(f"Dependency installation failed: {str(e)}")
                    raise
            
            logger.info(f"AIS v{self.config.version} setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            raise

def create_cli_parser():
    """Create command line argument parser."""
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description=f"AIS v{AIS_VERSION} Setup Script")
    parser.add_argument(
        "--no-cleanup", 
        action="store_true", 
        help="Skip cleanup of existing installation"
    )
    parser.add_argument(
        "--no-deps", 
        action="store_true", 
        help="Skip dependency installation"
    )
    parser.add_argument(
        "--no-files", 
        action="store_true", 
        help="Skip file generation"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--base-dir", 
        type=Path, 
        help="Base directory for installation"
    )
    
    return parser

def main() -> None:
    """Main function to execute the setup process."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Configure setup based on CLI arguments
    config = SetupConfig(
        cleanup_existing=not args.no_cleanup,
        install_dependencies=not args.no_deps,
        create_files=not args.no_files,
        verbose=args.verbose,
        base_dir=args.base_dir or Path(__file__).parent.resolve()
    )
    
    # Set logging level based on verbosity
    if config.verbose:
        getLogger().setLevel(DEBUG)
        logger.debug("Verbose logging enabled")
    
    try:
        setup = AISSetup(config)
        setup.setup()
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        if config.verbose:
            logger.exception("Full traceback:")
        exit(1)

if __name__ == "__main__":
    main()
