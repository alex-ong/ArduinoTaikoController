#!/usr/bin/env python3
"""
Arduino Taiko Controller Debug Monitor

This script connects to the Arduino Taiko Controller via serial communication
to monitor debug messages containing the magic symbol ★.

Usage:
    python main.py [COM_PORT]
    
If no COM port is specified, the script will list available ports and let you choose.
"""

import sys
from datetime import datetime
from monitor import select_com_port, SerialMonitor


def monitor_serial_port(port_name: str):
    """Monitor the specified serial port using the background SerialMonitor."""
    print(f"Connecting to {port_name} ...")
    
    try:
        with SerialMonitor(port_name) as monitor:
            if not monitor.is_connected:
                print(f"Failed to connect: {monitor.error_message}")
                return False
            
            print("Connected! Monitoring for messages...")
            print("Press Ctrl+C to stop monitoring\n")
            
            last_timestamp = datetime.now()
            while True:
                # Wait for new data to arrive (blocks until new data or timeout)
                current_data = monitor.wait_for_new_data(timeout=1.0)
                
                # Print any new entries (only those newer than last_timestamp)
                for entry in current_data:
                    if entry.timestamp > last_timestamp:
                        timestamp = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] {entry.parsed_data}")
                last_timestamp = current_data[-1].timestamp
                
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True


def main():
    """Main function to handle command line arguments and start monitoring."""
    print("Arduino Taiko Controller Debug Monitor")
    print("=" * 40)
    
    # Check if COM port was provided as command line argument
    if len(sys.argv) > 1:
        com_port = sys.argv[1]
        print(f"Using COM port from command line: {com_port}")
    else:
        # Let user select a COM port
        com_port = select_com_port()
        if not com_port:
            print("No COM port selected. Exiting...")
            return
    
    # Start monitoring
    success = monitor_serial_port(com_port)
    
    if success:
        print("Monitoring completed successfully")
    else:
        print("Monitoring ended due to error")


if __name__ == "__main__":
    main()