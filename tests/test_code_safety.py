import pytest
from prismix.core.iterative_programmer import IterativeProgrammer, setup_agent


@pytest.fixture
def agent():
    return setup_agent()


def test_safe_code(agent):
    """Test that safe code passes the safety check"""
    safe_code = """
def greet(name):
    return f"Hello, {name}!"
"""
    is_safe, message = agent.is_code_safe(safe_code)
    assert is_safe is True
    assert isinstance(message, str)
    assert len(message) > 0


def test_unsafe_code(agent):
    """Test that unsafe code fails the safety check"""
    unsafe_code = """
import os
def delete_files():
    os.system("rm -rf /")
"""
    is_safe, message = agent.is_code_safe(unsafe_code)
    assert is_safe is False
    assert isinstance(message, str)
    assert len(message) > 0


def test_code_with_imports(agent):
    """Test that code with suspicious imports fails safety check"""
    code_with_imports = """
import subprocess
import socket
import os
import sys
from scapy.all import *  # Network attack toolkit
import paramiko  # SSH attacks
import requests  # Web scraping/attacks

def network_attack():
    # Port scanning
    scan_result = subprocess.check_output(['nmap', '-sS', 'localhost'])
    # Try SSH brute force
    ssh = paramiko.SSHClient()
    # System manipulation
    os.system('chmod 777 /etc/passwd')
    return scan_result
"""
    is_safe, message = agent.is_code_safe(code_with_imports)
    assert is_safe is False
    assert isinstance(message, str)
    assert len(message) > 0


def test_empty_code(agent):
    """Test handling of empty code"""
    is_safe, message = agent.is_code_safe("")
    assert isinstance(is_safe, bool)
    assert isinstance(message, str)
    assert len(message) > 0


def test_malformed_code(agent):
    """Test handling of syntactically incorrect code"""
    malformed_code = """
def broken_function(
    print("This is broken"
"""
    is_safe, message = agent.is_code_safe(malformed_code)
    assert isinstance(is_safe, bool)
    assert isinstance(message, str)
    assert len(message) > 0
