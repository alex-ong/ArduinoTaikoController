"""
Data structures for Arduino Taiko Controller debug messages.

This module defines dataclasses and parsing functions for structured handling
of debug output from the Arduino controller.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TaikoDebugData:
    """
    Structured representation of Arduino Taiko Controller debug data.
    
    Represents a parsed debug message containing raw sensor values,
    processed sensor values, key states, and threshold information.
    """
    raw_values: List[int]           # Raw analog readings from 4 sensors
    sensor_values: List[float]      # Processed sensor values with sensitivity applied
    key_states: List[bool]          # Current state of 4 keys (pressed/released)
    threshold: float                # Current dynamic threshold value
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        keys_str = "".join("X" if pressed else " " for pressed in self.key_states)
        return (f"RAW:[{', '.join(f'{v:3d}' for v in self.raw_values)}] "
                f"SENSOR:[{', '.join(f'{v:6.2f}' for v in self.sensor_values)}] "
                f"KEYS:[{keys_str}] THRESH:{self.threshold:6.2f}")
    
    def __repr__(self) -> str:
        """Developer string representation."""
        return (f"TaikoDebugData(raw={self.raw_values}, "
                f"sensor={self.sensor_values}, keys={self.key_states}, "
                f"threshold={self.threshold})")
    
    @property
    def active_keys(self) -> List[int]:
        """Get indices of currently pressed keys."""
        return [i for i, pressed in enumerate(self.key_states) if pressed]
    
    @property
    def max_sensor_value(self) -> Tuple[int, float]:
        """Get the index and value of the highest sensor reading."""
        max_idx = max(range(len(self.sensor_values)), 
                     key=lambda i: self.sensor_values[i])
        return max_idx, self.sensor_values[max_idx]


def parse_debug_message(message: str) -> Optional[TaikoDebugData]:
    """
    Parse an Arduino debug message into a TaikoDebugData object.
    
    Expected format:
    ★ RAW: 193, 187, 193, 196 | SENSOR: 1.0000, 4.2000, 1.0000, 3.3000 | KEYS: 1, 1, 1, 1 | THRESH: 0.00
    
    Args:
        message: The raw debug message string
        
    Returns:
        TaikoDebugData object if parsing succeeds, None if it fails
    """
    try:
        # Remove the magic symbol and clean up
        clean_message = message.replace("★", "").strip()
        
        # Regular expression to parse the debug message
        pattern = (
            r"RAW:\s*([0-9, ]+)\s*\|\s*"
            r"SENSOR:\s*([0-9., ]+)\s*\|\s*"
            r"KEYS:\s*([01, ]+)\s*\|\s*"
            r"THRESH:\s*([0-9.]+)"
        )
        
        match = re.search(pattern, clean_message)
        if not match:
            return None
        
        # Parse raw values (integers)
        raw_str = match.group(1)
        raw_values = [int(x.strip()) for x in raw_str.split(",")]
        
        # Parse sensor values (floats)
        sensor_str = match.group(2)
        sensor_values = [float(x.strip()) for x in sensor_str.split(",")]
        
        # Parse key states (convert 1/0 to boolean)
        keys_str = match.group(3)
        key_states = [x.strip() == "1" for x in keys_str.split(",")]
        
        # Parse threshold (float)
        threshold = float(match.group(4))
        
        # Validate we got exactly 4 values for each array
        if len(raw_values) != 4 or len(sensor_values) != 4 or len(key_states) != 4:
            return None
        
        return TaikoDebugData(
            raw_values=raw_values,
            sensor_values=sensor_values,
            key_states=key_states,
            threshold=threshold
        )
        
    except (ValueError, AttributeError, IndexError):
        # Return None for any parsing errors
        return None
