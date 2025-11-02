# Arduino Taiko Controller Debug Monitor

This Python project monitors debug messages from the Arduino Taiko Controller via serial communication.

## Requirements

- Python 3.14
- Pipenv

## Setup

1. Install Pipenv (if not already installed):
   ```bash
   pip install pipenv
   ```

2. Install project dependencies:
   ```bash
   pipenv install
   ```

3. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

## Usage

### Interactive Mode
Run the script without arguments to see available COM ports:
```bash
python main.py
```

### Direct COM Port
Specify the COM port directly:
```bash
python main.py COM3
```

## Features

- **Automatic COM Port Detection**: Lists all available COM ports for easy selection
- **Magic Symbol Filtering**: Only displays messages containing the ★ symbol
- **Structured Data Parsing**: Converts debug messages into structured dataclasses
- **115200 Baud Rate**: Configured to match Arduino's serial output
- **Error Handling**: Gracefully handles connection issues and Unicode errors
- **Keyboard Interrupt**: Stop monitoring with Ctrl+C

## Data Structure

The Arduino sends debug messages in this format:
```
★ RAW: 193, 187, 193, 196 | SENSOR: 1.0000, 4.2000, 1.0000, 3.3000 | KEYS: 1, 1, 1, 1 | THRESH: 0.00
```

This gets parsed into a `TaikoDebugData` object with:
- **raw_values**: Raw analog readings from 4 piezo sensors
- **sensor_values**: Processed values with sensitivity applied  
- **key_states**: Current pressed/released state of 4 keys
- **threshold**: Dynamic threshold for hit detection

## Testing

Test the parser with sample data:
```bash
python test_parser.py
```

This will verify that the debug message parsing works correctly with sample Arduino output.

## Troubleshooting

- **No COM ports found**: Make sure the Arduino is connected and drivers are installed
- **Permission denied**: Run as administrator or check port permissions
- **Connection timeout**: Verify the Arduino is running and the correct port is selected
- **Garbled text**: Check that the Arduino is using 115200 baud rate
- **Parser errors**: Raw messages will be displayed if structured parsing fails