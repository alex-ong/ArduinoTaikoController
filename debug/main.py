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
import serial
from datetime import datetime
from monitor import select_com_port, parse_debug_message


def monitor_serial_port(port_name: str, baud_rate: int = 115200):
    """Monitor the specified serial port for messages with the magic symbol."""
    magic_symbol = "★"
    
    try:
        print(f"Connecting to {port_name} at {baud_rate} baud...")
        
        with serial.Serial(port_name, baud_rate, timeout=1) as ser:
            print(f"Connected! Monitoring for messages with '{magic_symbol}'")
            print("Press Ctrl+C to stop monitoring\n")
            
            while True:
                try:
                    # Read a line from the serial port
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line and magic_symbol in line:
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        
                        # Try to parse the debug message into structured data
                        debug_data = parse_debug_message(line)
                        if debug_data:
                            # Display structured output using the dataclass __str__ method
                            print(f"[{timestamp}] {debug_data}")
                        else:
                            # Fall back to raw message if parsing fails
                            print(f"[{timestamp}] RAW: {line}")
                        
                except UnicodeDecodeError:
                    # Skip lines that can't be decoded
                    continue
                    
    except serial.SerialException as e:
        print(f"Serial port error: {e}")
        return False
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        return True
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


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