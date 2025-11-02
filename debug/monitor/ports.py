"""
Port management utilities for Arduino Taiko Controller monitoring.

This module provides functions to list and select COM ports for serial communication.
"""

import serial
import serial.tools.list_ports
from typing import Optional, List


def list_available_ports() -> List[serial.tools.list_ports.ListPortInfo]:
    """
    List all available COM ports.
    
    Returns:
        List of available port info objects. Empty list if no ports found.
    """
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No COM ports found!")
        return []
    
    print("\nAvailable COM ports:")
    for i, port in enumerate(ports):
        print(f"{i + 1}. {port.device} - {port.description}")
    
    return ports


def select_com_port() -> Optional[str]:
    """
    Allow user to select a COM port interactively.
    
    Returns:
        Selected COM port device name (e.g., "COM3") or None if cancelled.
    """
    ports = list_available_ports()
    
    if not ports:
        return None
    
    while True:
        try:
            choice = input(f"\nSelect port (1-{len(ports)}): ").strip()
            if choice.lower() in ['q', 'quit', 'exit']:
                return None
            
            port_index = int(choice) - 1
            if 0 <= port_index < len(ports):
                return ports[port_index].device
            else:
                print(f"Invalid choice. Please select 1-{len(ports)}")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            return None