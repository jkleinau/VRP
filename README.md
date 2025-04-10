# VRP Scenario Builder

A graphical user interface (UI) application for creating, configuring, visualizing, and solving Vehicle Routing Problems (VRP).

## Features

- Visual 2D canvas for adding and managing nodes
- Configuration of vehicles and their capabilities (skills)
- Node constraints including time windows and required skills
- Save and load scenario presets
- Integration with Google OR-Tools for solving VRP problems
- Visualization of calculated routes

## Requirements

- Python 3.x
- Required packages:
  - tkinter (Python's standard GUI package)
  - customtkinter
  - pillow
  - ortools
  - numpy

## Installation

1. Ensure you have Python 3.x installed

2. Install Tkinter (if not already included with your Python installation):
   - **macOS**: 
     ```bash
     # Using Homebrew
     brew install python-tk@3.12  # Use your Python version number
     # OR
     # Install Python with Tkinter support
     brew reinstall python --with-tcl-tk
     ```
   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install python3-tk
     ```
   - **Windows**:
     Tkinter is normally included with the standard Windows Python installer.
     
   - **Check Tkinter installation**:
     ```bash
     python -m tkinter
     ```
     This should open a small window if Tkinter is properly installed.

3. Install other required packages:
   ```bash
   pip install customtkinter pillow ortools numpy
   ```

## Usage

1. Run the application:

```bash
python vrp_ui.py
```

2. Create a scenario:
   - Left-click on the canvas to add customer nodes
   - Right-click on a node to remove it
   - Click on a node to select it and configure its constraints

3. Configure vehicles:
   - Adjust the number of vehicles using the slider
   - Assign skills to vehicles using the checkboxes

4. Add constraints to nodes:
   - Select a node and set its time window
   - Assign required skills to nodes

5. Solve the VRP:
   - Click "Solve VRP" to find routes
   - Routes will be displayed on the canvas with different colors

6. Save/Load scenarios:
   - Use "Save Preset" to save your scenario
   - Use "Load Preset" to load a previously saved scenario

## Canvas Interaction

- Left-click: Add new node or select existing node
- Right-click: Remove node (cannot remove depot)
- Coordinate system: Depot is at (0,0)

## Implementation Notes

- The depot node is fixed at the center (0,0)
- Customer nodes can be placed anywhere on the canvas
- Time windows are specified as integer values
- The solver uses Euclidean distances between nodes
- Vehicle routes are color-coded for easy identification

## Troubleshooting

### "ModuleNotFoundError: No module named '_tkinter'"
This error indicates that Tkinter is not properly installed. Follow the installation instructions above for your specific operating system.

### "ImportError: No module named 'customtkinter'"
Make sure you've installed CustomTkinter using pip:
```bash
pip install customtkinter
```

### Performance Issues
If the application is slow when solving large problems, try:
- Reducing the number of nodes
- Increasing the solver time limit in the code