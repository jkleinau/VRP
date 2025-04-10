Project Requirements Document: VRP Scenario Builder UI

Version: 1.0
Date: 2025-04-10

1. Introduction

Purpose: This document describes the requirements for a graphical user interface (UI) application designed to facilitate the creation, configuration, visualization, and solving of basic Vehicle Routing Problems (VRP). The tool aims to provide an intuitive way to set up test scenarios for experimentation, primarily using Google OR-Tools as the underlying solver engine.
Project Goal: To create a standalone desktop application allowing users to visually define VRP instances, configure parameters, add constraints like time windows and skills, solve the problem, and visualize the resulting routes. The focus is on ease of use for rapid prototyping and testing of VRP scenarios.
Target Audience: Students, researchers, developers, or analysts exploring VRP concepts and solutions who need a simple tool to quickly set up and test different problem configurations without extensive coding for each scenario.
2. Functional Requirements

The application shall provide the following functionalities:

2.1. Scenario Canvas:

2.1.1. Visual Display: Provide a 2D canvas representing the spatial area of the VRP.
2.1.2. Coordinate System: Use a simple Cartesian coordinate system.
2.1.3. Depot Node: Automatically display a fixed depot node at the center (0,0). This node should be visually distinct from customer nodes.
2.1.4. Add Nodes: Allow users to add customer nodes by clicking on the canvas at the desired location.
2.1.5. Remove Nodes: Allow users to select and remove existing customer nodes (e.g., via right-click menu or selection + delete button).
2.1.6. Node Information Display: Optionally display coordinates or node IDs near/on the nodes.
2.2. Parameter Configuration:

2.2.1. Number of Vehicles: Provide a control (e.g., slider, input field) to set the number of vehicles available for routing.
2.2.2. Vehicle Capabilities (Skills):
Allow defining a list of possible skills/requirements (e.g., "electrician", "refrigeration", "heavy_lift").
Allow assigning one or more defined skills to each vehicle (or defining vehicle types with specific skills).
2.3. Node Constraints Configuration:

2.3.1. Node Selection: Allow users to select a specific customer node on the canvas to configure its properties.
2.3.2. Time Windows:
For a selected node, provide an intuitive way to define a time window (start time, end time) during which service must begin or be completed.
Inputs should allow setting numerical time values (e.g., minutes or hours from a start time T=0).
Visually indicate on the canvas which nodes have active time windows.
2.3.3. Node Requirements (Skills):
For a selected node, allow assigning one or more required skills from the predefined list (see 2.2.2).
A node with a requirement (e.g., "electrician") can only be visited by a vehicle possessing that capability/skill.
Visually indicate on the canvas which nodes have specific requirements.
2.4. Scenario Persistence:

2.4.1. Save Preset: Allow the user to save the current scenario configuration (node locations, number of vehicles, vehicle skills, node time windows, node requirements) to a local file.
2.4.2. Load Preset: Allow the user to load a previously saved scenario configuration from a local file, populating the canvas and controls accordingly.
2.4.3. File Format: Define a suitable file format for saving/loading (e.g., JSON, YAML).
2.5. Solving and Visualization:

2.5.1. Initiate Solver: Provide a button or command to trigger the VRP solver (Google OR-Tools) using the current configuration.
2.5.2. Solver Integration: The application will format the current scenario data into the structure required by Google OR-Tools routing library and execute the solver.
2.5.3. Solution Display: Upon successful completion by the solver, visualize the calculated vehicle routes on the canvas.
Draw lines connecting the depot and the sequence of nodes visited by each vehicle.
Use different colors or visual styles to distinguish routes of different vehicles.
2.5.4. Solver Feedback: Provide feedback to the user regarding the solving process (e.g., "Solving...", "Solution Found", "No Solution Found", error messages). Optionally display basic solution metrics (e.g., total distance, completion time).
3. Non-Functional Requirements

3.1. Usability: The UI must be intuitive and easy to learn, requiring minimal instruction for basic operations (adding/removing nodes, setting parameters).
3.2. Performance:
The UI should remain responsive during configuration tasks.
The solver execution time is dependent on Google OR-Tools and problem complexity, but the UI should indicate that solving is in progress.
Canvas updates (drawing nodes, routes) should be reasonably fast for typical scenario sizes (e.g., up to ~50 nodes, ~10 vehicles).
3.3. Reliability: Scenario saving and loading must function correctly. Solver integration should handle potential errors gracefully.
3.4. Platform: The application should run on standard desktop operating systems (Windows, macOS, Linux).
4. User Interface (UI) / User Experience (UX) Requirements

4.1. Layout: A clear layout separating the canvas, configuration controls, and action buttons.
4.2. Controls: Use standard UI elements (buttons, sliders, input fields, lists) appropriately.
4.3. Visual Feedback: Clear visual cues for selected nodes, nodes with constraints (time windows, skills), running processes (solving), and solution routes.
5. Data Requirements

5.1. Input Data Model (Internal): Coordinates for nodes, list of time windows per node, list of required skills per node, number of vehicles, list of skills per vehicle.
5.2. Preset File Format: A structured format (e.g., JSON) containing all elements defined in 5.1 necessary to reconstruct a scenario.
5.3. OR-Tools Input: Data must be translatable into the format required by the Google OR-Tools Python library (e.g., distance matrix, time windows, vehicle definitions, skill constraints).
6. Technical Requirements & Constraints

6.1. Solver Engine: Google OR-Tools (Python library) must be used for solving the VRP.
6.2. Development Language: Python (to easily integrate with OR-Tools).
6.3. UI Framework: A suitable Python GUI framework (e.g., Tkinter, PyQt/PySide, Kivy) should be chosen. Consider ease of development and dependency management.
6.4. Dependencies: The application will depend on Google OR-Tools and the chosen GUI framework library.
7. Future Considerations / Out of Scope (for Version 1.0)

Node demands and vehicle capacities.
Variable start/end locations for vehicles.
Advanced constraints (e.g., pickup and delivery, precedence).
Using real map backgrounds or calculating real road distances.
More sophisticated solution visualization (e.g., animation, detailed stats).
Cloud-based storage for presets.
User accounts or collaboration features.
Advanced configuration of solver parameters.