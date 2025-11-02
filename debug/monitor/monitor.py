"""
Background serial monitoring with thread-safe data storage.

This module provides a SerialMonitor class that runs in a background thread
to continuously monitor Arduino debug messages and store them in a thread-safe
data structure with automatic time-based cleanup.
"""

import threading
import time
import serial
from datetime import datetime, timedelta
from typing import List, Optional, NamedTuple
import logging
from .data import parse_debug_message, TaikoDebugData

# Set default logging configuration for this module
def _setup_default_logging():
    """Set up default logging configuration if none exists."""
    root_logger = logging.getLogger()
    
    # Only configure if no handlers exist (hasn't been configured elsewhere)
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

# Apply default logging configuration
_setup_default_logging()

def setup_debug_logging():
    """
    Configure logging to show debug messages to console.
    Call this function in your main script to override default configuration.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override any existing configuration
    )


class SerialDataEntry(NamedTuple):
    """A timestamped entry from the serial monitor."""
    timestamp: datetime
    parsed_data: TaikoDebugData


class SerialMonitor:
    """
    Background serial monitor that collects Arduino debug data in a thread-safe manner.
    
    Features:
    - Runs in background thread
    - Thread-safe data access
    - Automatic cleanup of old data (keeps last 10 seconds)
    - Proper cleanup on shutdown
    """
    
    def __init__(self, port_name: str, baud_rate: int = 115200, 
                 data_retention_seconds: int = 10):
        """
        Initialize the serial monitor.
        
        Args:
            port_name: Serial port to monitor (e.g., "COM3")
            baud_rate: Baud rate for serial communication (default: 115200)
            data_retention_seconds: How long to keep data in memory (default: 10)
        """
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.data_retention = timedelta(seconds=data_retention_seconds)
        
        # Thread-safe data storage
        self._data_lock = threading.RLock()
        self._data: List[SerialDataEntry] = []
        self._data_condition = threading.Condition(self._data_lock)
        
        # Threading control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._serial_connection: Optional[serial.Serial] = None
        
        # Status tracking
        self._connected = False
        self._error_message = ""
        
        # Setup logging
        self._logger = logging.getLogger(__name__)
    
    def start(self) -> bool:
        """
        Start monitoring in a background thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._thread and self._thread.is_alive():
            self._logger.warning("Monitor already running")
            return True
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        # Wait a bit to see if connection succeeds
        time.sleep(0.5)
        return self._connected
    
    def stop(self):
        """Stop monitoring and clean up resources."""
        self._stop_event.set()
        
        if self._serial_connection:
            try:
                self._serial_connection.close()
            except Exception as e:
                self._logger.error(f"Error closing serial connection: {e}")
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.stop()
    
    @property
    def data(self) -> List[SerialDataEntry]:
        """
        Get a thread-safe copy of current data.
        
        Returns:
            List of SerialDataEntry objects from the last 10 seconds
        """
        with self._data_condition:
            return self._data.copy()
    
    def wait_for_new_data(self, timeout: float = 1.0) -> List[SerialDataEntry]:
        """
        Wait for new data to arrive and return current data.
        
        Args:
            timeout: Maximum time to wait for new data
            
        Returns:
            List of current data entries
        """
        with self._data_condition:
            self._data_condition.wait(timeout=timeout)
            return self._data.copy()
    
    @property 
    def latest_entry(self) -> Optional[SerialDataEntry]:
        """Get the most recent data entry."""
        with self._data_condition:
            return self._data[-1] if self._data else None
    
    @property
    def is_connected(self) -> bool:
        """Check if the serial connection is active."""
        return self._connected
    
    @property
    def error_message(self) -> str:
        """Get the last error message, if any."""
        return self._error_message
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in the background thread."""
        try:
            self._serial_connection = serial.Serial(
                self.port_name, 
                self.baud_rate, 
                timeout=1
            )
            self._connected = True
            self._logger.info(f"Connected to {self.port_name} at {self.baud_rate} baud")
            
            while not self._stop_event.is_set():
                try:
                    # Read line from serial
                    line = self._serial_connection.readline().decode('utf-8', errors='ignore').strip()

                    if line:
                        # Parse the debug message
                        parsed_data = parse_debug_message(line)
                        
                        # Only store successfully parsed data
                        if parsed_data:
                            timestamp = datetime.now()
                            entry = SerialDataEntry(
                                timestamp=timestamp,
                                parsed_data=parsed_data
                            )
                            
                            # Add to data store and cleanup old entries
                            with self._data_condition:
                                self._data.append(entry)
                                self._cleanup_old_data()
                                self._data_condition.notify_all()  # Notify waiting threads
                
                except UnicodeDecodeError:
                    # Skip problematic lines
                    continue
                except Exception as e:
                    self._logger.error(f"Error reading serial data: {e}")
                    break
        
        except serial.SerialException as e:
            self._error_message = f"Serial port error: {e}"
            self._logger.error(self._error_message)
        except Exception as e:
            self._error_message = f"Unexpected error: {e}"
            self._logger.error(self._error_message)
        finally:
            self._connected = False
            if self._serial_connection:
                try:
                    self._serial_connection.close()
                except Exception:
                    pass
    
    def _cleanup_old_data(self):
        """Remove data entries older than the retention period."""
        if not self._data:
            return
        
        cutoff_time = datetime.now() - self.data_retention
        
        # Find the first entry to keep (binary search would be more efficient for large datasets)
        keep_from_index = 0
        for i, entry in enumerate(self._data):
            if entry.timestamp >= cutoff_time:
                keep_from_index = i
                break
        
        # Keep only recent entries
        if keep_from_index > 0:
            self._data = self._data[keep_from_index:]
    
    def get_data_since(self, seconds_ago: float) -> List[SerialDataEntry]:
        """
        Get data from the last N seconds.
        
        Args:
            seconds_ago: How many seconds back to retrieve data
            
        Returns:
            List of entries from the specified time window
        """
        cutoff_time = datetime.now() - timedelta(seconds=seconds_ago)
        
        with self._data_condition:
            return [entry for entry in self._data if entry.timestamp >= cutoff_time]
    
    def get_latest_parsed_data(self) -> Optional[TaikoDebugData]:
        """Get the most recent debug data."""
        with self._data_condition:
            if self._data:
                return self._data[-1].parsed_data
            return None