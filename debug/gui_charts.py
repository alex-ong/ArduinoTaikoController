#!/usr/bin/env python3
"""
Arduino Taiko Controller Live Charts

Real-time visualization of Arduino Taiko Controller debug data using DearPyGui.
Shows live charts for raw sensor values, processed sensor values, key states, and threshold.
"""

import dearpygui.dearpygui as dpg
import time
from datetime import datetime
from typing import Optional
from threading import Thread, Event
import logging

from monitor import SerialMonitor


class TaikoChartApp:
    """
    Real-time chart application for Arduino Taiko Controller data.
    
    Features:
    - Live charts for all sensor data (13 lines total)
    - 60fps smooth updates
    - COM port selection
    - Time-based data window (configurable seconds)
    - Automatic scaling and scrolling
    """
    
    def __init__(self, com_port: str, time_window_seconds: float = 4.0):
        """Initialize the chart application."""
        self.com_port = com_port
        self.time_window_seconds = time_window_seconds
        self.monitor: Optional[SerialMonitor] = None
        self.is_running = False
        self.update_thread: Optional[Thread] = None
        self.stop_event = Event()
        
        # Chart series IDs for updating
        self.chart_series = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def setup_gui(self):
        """Setup the DearPyGui interface."""
        dpg.create_context()
        
        # Create main window
        with dpg.window(label=f"Arduino Taiko Controller Live Charts - {self.com_port}", 
                       width=1200, height=800, tag="main_window"):
            
            # Simple control panel
            with dpg.group(horizontal=True):
                dpg.add_text(f"Port: {self.com_port}")
                dpg.add_button(label="Disconnect", tag="disconnect_btn", 
                              callback=self._on_disconnect, enabled=False)
            
            # Status display
            dpg.add_text("Status: Connecting...", tag="status_text")
            dpg.add_separator()
            
            # Charts arranged in a grid
            with dpg.group():
                # Raw sensor values chart
                with dpg.plot(label="Raw Sensor Values", height=200, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (seconds ago)", tag="raw_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Raw Value", tag="raw_y_axis")
                    
                    # Add 4 raw sensor series
                    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # Red, Green, Blue, Yellow
                    for i in range(4):
                        series_id = f"raw_series_{i}"
                        dpg.add_line_series([], [], label=f"Raw {i}", 
                                          parent="raw_y_axis", tag=series_id)
                        dpg.bind_item_theme(series_id, self._create_line_theme(colors[i]))
                        self.chart_series[f"raw_{i}"] = series_id
                
                # Processed sensor values chart  
                with dpg.plot(label="Processed Sensor Values", height=200, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (seconds ago)", tag="sensor_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Sensor Value", tag="sensor_y_axis")
                    
                    # Add 4 sensor series
                    for i in range(4):
                        series_id = f"sensor_series_{i}"
                        dpg.add_line_series([], [], label=f"Sensor {i}", 
                                          parent="sensor_y_axis", tag=series_id)
                        dpg.bind_item_theme(series_id, self._create_line_theme(colors[i]))
                        self.chart_series[f"sensor_{i}"] = series_id
                
                # Key states chart
                with dpg.plot(label="Key States", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (seconds ago)", tag="keys_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Key State", tag="keys_y_axis")
                    dpg.set_axis_limits("keys_y_axis", -0.5, 4.5)  # Fixed range for key states
                    
                    # Add 4 key series (offset vertically for visibility)
                    for i in range(4):
                        series_id = f"key_series_{i}"
                        dpg.add_line_series([], [], label=f"Key {i}", 
                                          parent="keys_y_axis", tag=series_id)
                        dpg.bind_item_theme(series_id, self._create_line_theme(colors[i]))
                        self.chart_series[f"key_{i}"] = series_id
                
                # Threshold chart
                with dpg.plot(label="Threshold", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time (seconds ago)", tag="thresh_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Threshold Value", tag="thresh_y_axis")
                    
                    series_id = "threshold_series"
                    dpg.add_line_series([], [], label="Threshold", 
                                      parent="thresh_y_axis", tag=series_id)
                    dpg.bind_item_theme(series_id, self._create_line_theme((255, 0, 255)))  # Magenta
                    self.chart_series["threshold"] = series_id
        
        # Setup viewport and themes
        dpg.create_viewport(title="Arduino Taiko Controller Charts", width=1250, height=850)
        dpg.setup_dearpygui()
        
        # Set main window as primary
        dpg.set_primary_window("main_window", True)
    
    def _create_line_theme(self, color):
        """Create a theme for line series with specified color."""
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots)
        return theme
    
    def _auto_connect(self):
        """Automatically connect to the specified COM port on startup."""
        try:
            self.monitor = SerialMonitor(self.com_port)
            if self.monitor.start():
                self.is_running = True
                self.stop_event.clear()
                
                # Start update thread
                self.update_thread = Thread(target=self._update_loop, daemon=True)
                self.update_thread.start()
                
                # Update UI
                dpg.set_value("status_text", f"Status: Connected to {self.com_port}")
                dpg.configure_item("disconnect_btn", enabled=True)
                
                self.logger.info(f"Connected to {self.com_port}")
            else:
                dpg.set_value("status_text", f"Status: Failed to connect - {self.monitor.error_message}")
        
        except Exception as e:
            dpg.set_value("status_text", f"Status: Connection error - {str(e)}")
            self.logger.error(f"Connection error: {e}")
    
    def _on_disconnect(self):
        """Disconnect from COM port and stop monitoring."""
        self.is_running = False
        self.stop_event.set()
        
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        
        if self.update_thread:
            self.update_thread.join(timeout=2.0)
        
        # Update UI
        dpg.set_value("status_text", "Status: Disconnected")
        dpg.configure_item("disconnect_btn", enabled=False)
        
        self.logger.info("Disconnected")
    
    def _update_loop(self):
        """Main update loop running at ~60fps."""
        target_fps = 60
        frame_time = 1.0 / target_fps
        
        while self.is_running and not self.stop_event.is_set():
            frame_start = time.time()
            
            try:
                self._update_charts()
            except Exception as e:
                self.logger.error(f"Chart update error: {e}")
            
            # Maintain target FPS
            elapsed = time.time() - frame_start
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _update_charts(self):
        """Update all chart data from the monitor."""
        if not self.monitor or not self.monitor.is_connected:
            return
        
        # Get recent data based on time window
        current_data = self.monitor.get_data_since(self.time_window_seconds)
        
        if not current_data:
            return
        
        # Calculate time offsets (seconds ago)
        now = datetime.now()
        time_offsets = [(now - entry.timestamp).total_seconds() for entry in current_data]
        
        # Update raw sensor data
        for i in range(4):
            raw_values = [entry.parsed_data.raw_values[i] for entry in current_data]
            dpg.set_value(self.chart_series[f"raw_{i}"], [time_offsets, raw_values])
        
        # Update processed sensor data
        for i in range(4):
            sensor_values = [entry.parsed_data.sensor_values[i] for entry in current_data]
            dpg.set_value(self.chart_series[f"sensor_{i}"], [time_offsets, sensor_values])
        
        # Update key states (offset vertically for visibility: key 0 at y=0, key 1 at y=1, etc.)
        for i in range(4):
            key_values = [i + (1 if entry.parsed_data.key_states[i] else 0) for entry in current_data]
            dpg.set_value(self.chart_series[f"key_{i}"], [time_offsets, key_values])
        
        # Update threshold
        threshold_values = [entry.parsed_data.threshold for entry in current_data]
        dpg.set_value(self.chart_series["threshold"], [time_offsets, threshold_values])
        
        # Auto-scale axes (except keys and raw which are fixed)
        dpg.fit_axis_data("raw_x_axis")
        dpg.set_axis_limits("raw_y_axis", 0, 1024)  # Fixed scale for raw values
        dpg.fit_axis_data("sensor_x_axis") 
        dpg.fit_axis_data("sensor_y_axis")
        dpg.fit_axis_data("keys_x_axis")
        dpg.fit_axis_data("thresh_x_axis")
        dpg.fit_axis_data("thresh_y_axis")
    
    def run(self):
        """Start the GUI application."""
        self.setup_gui()
        dpg.show_viewport()
        
        # Auto-connect after GUI is ready
        self._auto_connect()
        
        try:
            # Main GUI loop
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
        finally:
            # Cleanup
            if self.is_running:
                self._on_disconnect()
            dpg.destroy_context()


def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Arduino Taiko Controller Live Charts")
    print("=" * 40)
    
    # Import here to avoid circular dependency
    from monitor import select_com_port
    
    # Let user select a COM port
    com_port = select_com_port()
    if not com_port:
        print("No COM port selected. Exiting...")
        return
    
    print(f"Selected: {com_port}")
    print("Starting GUI...")
    
    # Create and run the application
    app = TaikoChartApp(com_port)
    app.run()


if __name__ == "__main__":
    main()