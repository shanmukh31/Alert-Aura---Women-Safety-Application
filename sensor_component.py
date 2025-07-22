import tkinter as tk
from tkinter import ttk

class SensorComponent:
    def __init__(self, parent_frame):
        self.frame = tk.Frame(parent_frame, bg="#ffffff", relief=tk.FLAT,
                            highlightthickness=1, highlightbackground="#e0e0e0")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        self.title_label = ttk.Label(self.frame, text="Sensor Status",
                                   style="Header.TLabel")
        self.title_label.pack(pady=(10, 20))
        
        # Sensor status grid
        self._create_sensor_grid()
    
    def _create_sensor_grid(self):
        """Create the sensor status grid"""
        # Create a frame for the grid
        grid_frame = tk.Frame(self.frame, bg="#ffffff")
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Configure grid columns
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        
        # Sensor status fields
        sensor_fields = [
            ("Motion Sensor", "Inactive"),
            ("Proximity Sensor", "Inactive"),
            ("Temperature Sensor", "Inactive"),
            ("Humidity Sensor", "Inactive"),
            ("Light Sensor", "Inactive"),
            ("Pressure Sensor", "Inactive")
        ]
        
        self.sensor_labels = {}
        for i, (sensor, status) in enumerate(sensor_fields):
            # Sensor name label
            name_label = ttk.Label(grid_frame, text=sensor,
                                 style="Parameter.TLabel")
            name_label.grid(row=i, column=0, sticky="e", padx=(0, 10), pady=5)
            
            # Status label
            status_label = ttk.Label(grid_frame, text=status,
                                   style="Value.TLabel")
            status_label.grid(row=i, column=1, sticky="w", pady=5)
            
            self.sensor_labels[sensor] = status_label
    
    def update_sensor_status(self, sensor_name, status):
        """Update the status of a specific sensor"""
        if sensor_name in self.sensor_labels:
            self.sensor_labels[sensor_name].config(text=status) 