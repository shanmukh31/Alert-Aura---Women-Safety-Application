from tkinter import ttk

def configure_styles():
    """Configure all custom styles for the application"""
    style = ttk.Style()
    
    # Button styles
    button_styles = {
        "Start.TButton": {"padding": 15, "font": ('Helvetica', 11, 'bold'), "background": "#4CAF50"},
        "Stop.TButton": {"padding": 15, "font": ('Helvetica', 11, 'bold'), "background": "#f44336"},
        "Emergency.TButton": {"padding": 15, "font": ('Helvetica', 13, 'bold'), "background": "#ff1744"},
        "Contacts.TButton": {"padding": 15, "font": ('Helvetica', 11, 'bold'), "background": "#2196F3"},
        "Custom.TButton": {"padding": 15, "font": ('Helvetica', 11, 'bold'), "background": "#9C27B0"}
    }
    
    # Label styles
    label_styles = {
        "Status.TLabel": {"font": ('Helvetica', 11), "background": "#ffffff", "padding": 8},
        "Header.TLabel": {"font": ('Helvetica', 18, 'bold'), "background": "#f0f2f5", "foreground": "#1a237e"},
        "Parameter.TLabel": {"font": ('Helvetica', 12, 'bold'), "background": "#ffffff", "padding": 5},
        "Value.TLabel": {"font": ('Helvetica', 12), "background": "#ffffff", "padding": 5}
    }
    
    # Configure all styles
    for style_name, style_config in button_styles.items():
        style.configure(style_name, **style_config)
    
    for style_name, style_config in label_styles.items():
        style.configure(style_name, **style_config) 