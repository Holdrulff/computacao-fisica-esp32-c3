#!/usr/bin/env python3
"""
Script de deploy automatizado para ESP32-C3 com MicroPython
Uso: python deploy.py [PORT]
Se PORT não for fornecido, tentará auto-detectar
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple


class ESP32Deployer:
    def __init__(self, port: str = None):
        self.port = port
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.venv_path = self.project_root / "venv"

    def log(self, message: str, level: str = "INFO"):
        """Print formatted log message"""
        colors = {
            "INFO": "\033[94m",  # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "RESET": "\033[0m"
        }
        color = colors.get(level, colors["RESET"])
        print(f"{color}[{level}]{colors['RESET']} {message}")

    def run_command(self, command: List[str], capture_output: bool = False) -> Tuple[int, str]:
        """Execute shell command"""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False
                )
                return result.returncode, result.stdout
            else:
                result = subprocess.run(command, check=False)
                return result.returncode, ""
        except Exception as e:
            self.log(f"Error executing command: {e}", "ERROR")
            return 1, str(e)

    def get_mpremote_path(self) -> str:
        """Get mpremote executable path (venv or global)"""
        # Try venv first
        venv_mpremote = self.venv_path / "Scripts" / "mpremote.exe"
        if venv_mpremote.exists():
            return str(venv_mpremote)

        # Try global installation
        returncode, _ = self.run_command(["mpremote", "--version"], capture_output=True)
        if returncode == 0:
            return "mpremote"

        self.log("mpremote not found! Install it with: pip install mpremote", "ERROR")
        sys.exit(1)

    def detect_port(self) -> str:
        """Auto-detect ESP32 serial port"""
        self.log("Auto-detecting ESP32 port...")
        mpremote = self.get_mpremote_path()

        returncode, output = self.run_command(
            [mpremote, "connect", "list"],
            capture_output=True
        )

        if returncode != 0:
            self.log("Failed to list available ports", "ERROR")
            sys.exit(1)

        # Parse output to find COM ports
        lines = output.strip().split('\n')
        ports = [line.split()[0] for line in lines if line.strip() and 'COM' in line]

        if not ports:
            self.log("No serial ports detected! Is the ESP32 connected?", "ERROR")
            sys.exit(1)

        if len(ports) == 1:
            detected_port = ports[0]
            self.log(f"Detected port: {detected_port}", "SUCCESS")
            return detected_port

        # Multiple ports found, ask user
        self.log(f"Multiple ports found: {', '.join(ports)}", "WARNING")
        print("Available ports:")
        for i, port in enumerate(ports, 1):
            print(f"  {i}. {port}")

        while True:
            try:
                choice = int(input("Select port number: ")) - 1
                if 0 <= choice < len(ports):
                    return ports[choice]
            except (ValueError, KeyboardInterrupt):
                self.log("Invalid selection", "ERROR")
                sys.exit(1)

    def connect(self) -> str:
        """Connect to ESP32 and return connection string"""
        if not self.port:
            self.port = self.detect_port()

        self.log(f"Connecting to {self.port}...", "INFO")
        mpremote = self.get_mpremote_path()

        # Test connection
        returncode, _ = self.run_command(
            [mpremote, "connect", self.port, "exec", "print('OK')"],
            capture_output=True
        )

        if returncode != 0:
            self.log(f"Failed to connect to {self.port}", "ERROR")
            sys.exit(1)

        self.log(f"Connected to {self.port}", "SUCCESS")
        return self.port

    def list_device_files(self) -> List[str]:
        """List all files on the ESP32 device"""
        self.log("Listing files on device...", "INFO")
        mpremote = self.get_mpremote_path()

        # Use mpremote fs ls recursively
        returncode, output = self.run_command(
            [mpremote, "connect", self.port, "fs", "ls"],
            capture_output=True
        )

        if returncode != 0:
            self.log("Failed to list device files", "WARNING")
            return []

        files = [line.strip() for line in output.strip().split('\n') if line.strip()]
        self.log(f"Found {len(files)} items on device", "INFO")
        return files

    def clean_device(self):
        """Remove all files from ESP32 device"""
        self.log("Cleaning device...", "WARNING")
        mpremote = self.get_mpremote_path()

        # Get all files
        files = self.list_device_files()

        if not files:
            self.log("No files to clean", "INFO")
            return

        # Remove each file/directory
        for item in files:
            item = item.strip()
            if not item or item == "." or item == "..":
                continue

            # Try to remove as file first, then as directory
            self.log(f"Removing: {item}", "INFO")

            # Remove file
            returncode, _ = self.run_command(
                [mpremote, "connect", self.port, "fs", "rm", f":{item}"],
                capture_output=True
            )

            if returncode != 0:
                # Try removing as directory
                returncode, _ = self.run_command(
                    [mpremote, "connect", self.port, "fs", "rmdir", f":{item}"],
                    capture_output=True
                )

        self.log("Device cleaned", "SUCCESS")

    def get_all_files(self, directory: Path, base_path: Path) -> List[Tuple[Path, str]]:
        """
        Recursively get all files from directory
        Returns list of (local_path, device_path) tuples
        """
        files = []

        for item in directory.rglob("*"):
            if item.is_file():
                # Calculate relative path from base
                rel_path = item.relative_to(base_path)

                # Convert to device path (Unix-style, forward slashes)
                device_path = "/" + str(rel_path).replace("\\", "/")

                files.append((item, device_path))

        return files

    def create_directory_structure(self, files: List[Tuple[Path, str]]):
        """Create directory structure on device"""
        mpremote = self.get_mpremote_path()
        dirs_created = set()

        for _, device_path in files:
            # Get directory path
            dir_path = str(Path(device_path).parent)

            # Skip if already created or is root
            if dir_path in dirs_created or dir_path in [".", "/"]:
                continue

            # Create directory on device
            self.log(f"Creating directory: {dir_path}", "INFO")
            self.run_command(
                [mpremote, "connect", self.port, "fs", "mkdir", f":{dir_path}"],
                capture_output=True
            )

            dirs_created.add(dir_path)

    def deploy_files(self):
        """Deploy all files from src/ to device"""
        if not self.src_dir.exists():
            self.log(f"Source directory not found: {self.src_dir}", "ERROR")
            sys.exit(1)

        self.log(f"Collecting files from {self.src_dir}...", "INFO")

        # Get all files to deploy
        files = self.get_all_files(self.src_dir, self.src_dir)

        if not files:
            self.log("No files to deploy!", "WARNING")
            return

        self.log(f"Found {len(files)} files to deploy", "INFO")

        # Create directory structure first
        self.create_directory_structure(files)

        # Deploy each file
        mpremote = self.get_mpremote_path()
        success_count = 0
        failed_count = 0

        for local_path, device_path in files:
            self.log(f"Copying: {local_path.name} -> {device_path}", "INFO")

            returncode, _ = self.run_command(
                [mpremote, "connect", self.port, "fs", "cp", str(local_path), f":{device_path}"],
                capture_output=True
            )

            if returncode == 0:
                success_count += 1
            else:
                failed_count += 1
                self.log(f"Failed to copy: {local_path}", "ERROR")

        self.log(f"Deploy complete: {success_count} succeeded, {failed_count} failed",
                "SUCCESS" if failed_count == 0 else "WARNING")

    def verify_deployment(self):
        """Verify files were deployed correctly"""
        self.log("Verifying deployment...", "INFO")
        files = self.list_device_files()

        if files:
            self.log(f"Device now contains {len(files)} items", "SUCCESS")
            print("\nFiles on device:")
            for f in files:
                print(f"  - {f}")
        else:
            self.log("Warning: No files detected on device", "WARNING")

    def run(self):
        """Execute full deployment process"""
        try:
            self.log("Starting ESP32 deployment", "INFO")
            self.log(f"Project root: {self.project_root}", "INFO")
            self.log(f"Source directory: {self.src_dir}", "INFO")

            # Connect to device
            self.connect()

            # Clean device
            response = input("\n⚠️  This will DELETE all files on the device. Continue? (y/N): ")
            if response.lower() != 'y':
                self.log("Deployment cancelled", "WARNING")
                return

            self.clean_device()

            # Deploy files
            self.deploy_files()

            # Verify
            self.verify_deployment()

            self.log("✓ Deployment completed successfully!", "SUCCESS")
            self.log("You can now reset the device or run: mpremote connect " + self.port + " reset", "INFO")

        except KeyboardInterrupt:
            self.log("\nDeployment interrupted by user", "WARNING")
            sys.exit(1)
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy MicroPython code to ESP32-C3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py              # Auto-detect port
  python deploy.py COM3         # Use specific port
  python deploy.py /dev/ttyUSB0 # Linux port
        """
    )
    parser.add_argument(
        "port",
        nargs="?",
        help="Serial port (e.g., COM3, /dev/ttyUSB0). Auto-detect if not provided."
    )

    args = parser.parse_args()

    deployer = ESP32Deployer(port=args.port)
    deployer.run()


if __name__ == "__main__":
    main()
