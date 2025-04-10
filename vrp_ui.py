import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import math
import threading
import queue
from PIL import Image, ImageTk
import numpy as np
import copy
import os

# Import the VRP solver functionality from main.py
from main import create_data_model as original_create_data_model
from main import pywrapcp, routing_enums_pb2


class VRPNode:
    """Class to represent a node in the VRP (customer or depot)"""
    id_counter = 0
    
    def __init__(self, x, y, is_depot=False):
        if not is_depot:
            self.id = VRPNode.id_counter
            VRPNode.id_counter += 1
        else:
            self.id = 0  # Depot is always ID 0
            
        self.x = x
        self.y = y
        self.is_depot = is_depot
        self.time_window = None  # (start_time, end_time) or None if no time window
        self.required_skills = set()  # Set of required skills
        
    def set_time_window(self, start_time, end_time):
        """Set time window for this node"""
        try:
            self.time_window = (int(start_time), int(end_time))
        except ValueError:
            return False
        return True
        
    def clear_time_window(self):
        """Clear time window for this node"""
        self.time_window = None
        
    def add_required_skill(self, skill):
        """Add a required skill for this node"""
        self.required_skills.add(skill)
        
    def remove_required_skill(self, skill):
        """Remove a required skill from this node"""
        if skill in self.required_skills:
            self.required_skills.remove(skill)
            
    def to_dict(self):
        """Convert node to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "is_depot": self.is_depot,
            "time_window": self.time_window,
            "required_skills": list(self.required_skills)
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create node from dictionary (for JSON deserialization)"""
        node = cls(data["x"], data["y"], data["is_depot"])
        node.id = data["id"]
        node.time_window = data["time_window"]
        node.required_skills = set(data["required_skills"])
        return node


class VRPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.title("VRP Scenario Builder")
        self.geometry("1200x700")
        
        # Set theme
        ctk.set_appearance_mode("System")  # "System", "Dark" or "Light"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Initialize app data
        self.nodes = []  # List of VRPNode objects
        self.selected_node = None  # Currently selected node
        self.num_vehicles = 4  # Default number of vehicles
        self.available_skills = []  # List of defined skills
        self.vehicle_skills = {}  # Dict of vehicle_id -> list of skills
        self.routes = []  # List of routes (each route is a list of node indices)
        self.queue = queue.Queue()  # For safe thread communication
        
        # Initialize the canvas scale factor (canvas coordinates to VRP coordinates)
        self.canvas_width = 800
        self.canvas_height = 600
        self.scale_factor = 10  # 1 VRP coordinate unit = 10 pixels
        
        # Create UI elements
        self.create_widgets()
        
        # Create depot node at center (0, 0)
        canvas_center_x = self.canvas_width // 2
        canvas_center_y = self.canvas_height // 2
        vrp_x, vrp_y = self.canvas_to_vrp_coords(canvas_center_x, canvas_center_y)
        self.depot_node = VRPNode(vrp_x, vrp_y, is_depot=True)
        self.nodes.append(self.depot_node)
        
        # Draw depot node
        self.draw_nodes()
        
    def create_widgets(self):
        """Create all UI widgets"""
        # Create main frame layout
        self.grid_columnconfigure(0, weight=3)  # Canvas area
        self.grid_columnconfigure(1, weight=1)  # Controls area
        self.grid_rowconfigure(0, weight=1)
        
        # Create canvas frame (left side)
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        
        # Draw coordinate system
        self.draw_coordinates()
        
        # Create controls frame (right side)
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Vehicle configuration section
        self.create_vehicle_config_section()
        
        # Node constraints section
        self.create_node_constraints_section()
        
        # Skills configuration section
        self.create_skills_config_section()
        
        # Action buttons section
        self.create_action_buttons_section()
        
        # Status label at bottom
        self.status_label = ctk.CTkLabel(self.controls_frame, text="Ready", anchor="w")
        self.status_label.grid(row=4, column=0, sticky="ew", padx=10, pady=(10, 5))
        
    def create_vehicle_config_section(self):
        """Create vehicle configuration UI section"""
        # Vehicle configuration frame
        vehicle_frame = ctk.CTkFrame(self.controls_frame)
        vehicle_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Title
        vehicle_title = ctk.CTkLabel(vehicle_frame, text="Vehicle Configuration", font=ctk.CTkFont(size=14, weight="bold"))
        vehicle_title.grid(row=0, column=0, sticky="w", padx=10, pady=5, columnspan=2)
        
        # Vehicle count
        vehicle_count_label = ctk.CTkLabel(vehicle_frame, text="Number of Vehicles:")
        vehicle_count_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.vehicle_count_var = tk.IntVar(value=self.num_vehicles)
        self.vehicle_count_slider = ctk.CTkSlider(
            vehicle_frame, from_=1, to=10, number_of_steps=9,
            variable=self.vehicle_count_var, command=self.on_vehicle_count_change
        )
        self.vehicle_count_slider.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        self.vehicle_count_label = ctk.CTkLabel(vehicle_frame, text=str(self.num_vehicles))
        self.vehicle_count_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # Vehicle skills frame (will be populated dynamically)
        self.vehicle_skills_frame = ctk.CTkFrame(vehicle_frame)
        self.vehicle_skills_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        # Initialize vehicle skills
        self.update_vehicle_skills_ui()
    
    def create_node_constraints_section(self):
        """Create node constraints UI section"""
        # Node constraints frame
        node_frame = ctk.CTkFrame(self.controls_frame)
        node_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Title
        node_title = ctk.CTkLabel(node_frame, text="Node Constraints", font=ctk.CTkFont(size=14, weight="bold"))
        node_title.grid(row=0, column=0, sticky="w", padx=10, pady=5, columnspan=2)
        
        # Selected node info
        self.node_info_label = ctk.CTkLabel(node_frame, text="No node selected")
        self.node_info_label.grid(row=1, column=0, sticky="w", padx=10, pady=5, columnspan=2)
        
        # Time window constraints
        time_window_label = ctk.CTkLabel(node_frame, text="Time Window:")
        time_window_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        time_window_frame = ctk.CTkFrame(node_frame)
        time_window_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        start_label = ctk.CTkLabel(time_window_frame, text="Start:")
        start_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.time_window_start = ctk.CTkEntry(time_window_frame, width=60)
        self.time_window_start.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        end_label = ctk.CTkLabel(time_window_frame, text="End:")
        end_label.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        self.time_window_end = ctk.CTkEntry(time_window_frame, width=60)
        self.time_window_end.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        self.set_time_window_btn = ctk.CTkButton(time_window_frame, text="Set", width=50, 
                                                command=self.on_set_time_window)
        self.set_time_window_btn.grid(row=0, column=4, sticky="w", padx=5, pady=5)
        
        self.clear_time_window_btn = ctk.CTkButton(time_window_frame, text="Clear", width=50,
                                                 command=self.on_clear_time_window)
        self.clear_time_window_btn.grid(row=0, column=5, sticky="w", padx=5, pady=5)
        
        # Node required skills
        node_skills_label = ctk.CTkLabel(node_frame, text="Required Skills:")
        node_skills_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Frame for node skills UI elements (will be populated dynamically)
        self.node_skills_frame = ctk.CTkFrame(node_frame)
        self.node_skills_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Disable node constraint controls initially (until a node is selected)
        self.toggle_node_constraint_controls(False)
    
    def create_skills_config_section(self):
        """Create skills configuration UI section"""
        # Skills configuration frame
        skills_frame = ctk.CTkFrame(self.controls_frame)
        skills_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Title
        skills_title = ctk.CTkLabel(skills_frame, text="Skills Configuration", font=ctk.CTkFont(size=14, weight="bold"))
        skills_title.grid(row=0, column=0, sticky="w", padx=10, pady=5, columnspan=2)
        
        # Add skill
        add_skill_label = ctk.CTkLabel(skills_frame, text="New Skill:")
        add_skill_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.new_skill_entry = ctk.CTkEntry(skills_frame, width=120)
        self.new_skill_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        add_skill_btn = ctk.CTkButton(skills_frame, text="Add Skill", command=self.on_add_skill)
        add_skill_btn.grid(row=1, column=2, sticky="w", padx=10, pady=5)
        
        # Skills list
        skills_list_label = ctk.CTkLabel(skills_frame, text="Available Skills:")
        skills_list_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Frame for skills list (will be populated dynamically)
        self.skills_list_frame = ctk.CTkFrame(skills_frame)
        self.skills_list_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        # Add example skills
        default_skills = ["electrician", "refrigeration", "heavy_lift"]
        for skill in default_skills:
            if skill not in self.available_skills:
                self.available_skills.append(skill)
        
        # Update skills UI
        self.update_skills_ui()
    
    def create_action_buttons_section(self):
        """Create action buttons UI section"""
        # Action buttons frame
        actions_frame = ctk.CTkFrame(self.controls_frame)
        actions_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        # Title
        actions_title = ctk.CTkLabel(actions_frame, text="Actions", font=ctk.CTkFont(size=14, weight="bold"))
        actions_title.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Buttons
        solve_btn = ctk.CTkButton(actions_frame, text="Solve VRP", command=self.on_solve_vrp)
        solve_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        clear_routes_btn = ctk.CTkButton(actions_frame, text="Clear Routes", command=self.on_clear_routes)
        clear_routes_btn.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        save_btn = ctk.CTkButton(actions_frame, text="Save Preset", command=self.on_save_preset)
        save_btn.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        load_btn = ctk.CTkButton(actions_frame, text="Load Preset", command=self.on_load_preset)
        load_btn.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        # Clear all button
        clear_all_btn = ctk.CTkButton(actions_frame, text="Clear All Nodes", command=self.on_clear_all)
        clear_all_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
    
    def draw_coordinates(self):
        """Draw coordinate system on canvas"""
        # Center point coordinates (in canvas)
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        
        # Draw axes
        self.canvas.create_line(0, center_y, self.canvas_width, center_y, dash=(4, 2), fill="lightgray")
        self.canvas.create_line(center_x, 0, center_x, self.canvas_height, dash=(4, 2), fill="lightgray")
        
        # Draw origin label
        self.canvas.create_text(center_x + 10, center_y + 10, text="(0,0)", fill="gray")
    
    def canvas_to_vrp_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to VRP coordinate system"""
        # Convert from canvas coordinates to VRP coordinates
        # Canvas center is (0,0) in VRP coordinates
        vrp_x = (canvas_x - self.canvas_width // 2) / self.scale_factor
        vrp_y = (self.canvas_height // 2 - canvas_y) / self.scale_factor  # Y-axis is inverted in canvas
        return vrp_x, vrp_y
    
    def vrp_to_canvas_coords(self, vrp_x, vrp_y):
        """Convert VRP coordinates to canvas coordinate system"""
        # Convert from VRP coordinates to canvas coordinates
        canvas_x = (vrp_x * self.scale_factor) + self.canvas_width // 2
        canvas_y = self.canvas_height // 2 - (vrp_y * self.scale_factor)  # Y-axis is inverted in canvas
        return canvas_x, canvas_y
    
    def draw_nodes(self):
        """Draw all nodes on the canvas"""
        # Clear existing nodes
        self.canvas.delete("node")
        
        # Draw each node
        for node in self.nodes:
            canvas_x, canvas_y = self.vrp_to_canvas_coords(node.x, node.y)
            
            # Different style for depot vs customer nodes
            if node.is_depot:
                # Depot: Larger red square
                size = 8
                self.canvas.create_rectangle(
                    canvas_x - size, canvas_y - size, 
                    canvas_x + size, canvas_y + size,
                    fill="red", outline="darkred", width=2,
                    tags=("node", f"node_{node.id}", "depot")
                )
            else:
                # Customer: Blue circle
                size = 6
                fill_color = "blue"
                outline_color = "darkblue"
                
                # Change appearance if node has constraints
                if node.time_window or node.required_skills:
                    fill_color = "purple"
                    outline_color = "purple"
                    
                # Highlight selected node
                if self.selected_node and self.selected_node.id == node.id:
                    fill_color = "orange"
                    outline_color = "orange"
                
                self.canvas.create_oval(
                    canvas_x - size, canvas_y - size, 
                    canvas_x + size, canvas_y + size,
                    fill=fill_color, outline=outline_color, width=2,
                    tags=("node", f"node_{node.id}", "customer")
                )
            
            # Add node ID label
            self.canvas.create_text(
                canvas_x, canvas_y + size + 10,
                text=str(node.id),
                fill="black",
                tags=("node", f"node_label_{node.id}")
            )
        
        # Make sure routes stay visible if they exist
        if self.routes:
            self.draw_routes()
    
    def draw_routes(self):
        """Draw the solution routes on the canvas"""
        # Clear existing routes
        self.canvas.delete("route")
        
        # Colors for different routes
        route_colors = ["red", "green", "blue", "purple", "orange", "brown", "pink", "cyan", "magenta", "yellow"]
        
        # Draw each route
        for i, route in enumerate(self.routes):
            if not route:
                continue
                
            color = route_colors[i % len(route_colors)]
            
            # Draw lines connecting nodes in the route
            for j in range(len(route) - 1):
                from_node = next((n for n in self.nodes if n.id == route[j]), None)
                to_node = next((n for n in self.nodes if n.id == route[j + 1]), None)
                
                if from_node and to_node:
                    from_x, from_y = self.vrp_to_canvas_coords(from_node.x, from_node.y)
                    to_x, to_y = self.vrp_to_canvas_coords(to_node.x, to_node.y)
                    
                    self.canvas.create_line(
                        from_x, from_y, to_x, to_y,
                        fill=color, width=2,
                        tags=("route", f"route_{i}")
                    )
    
    def on_canvas_click(self, event):
        """Handle left click on canvas"""
        # Get canvas coordinates
        canvas_x = event.x
        canvas_y = event.y
        
        # Check if clicked on existing node
        clicked_node = None
        for node in self.nodes:
            node_x, node_y = self.vrp_to_canvas_coords(node.x, node.y)
            distance = math.sqrt((node_x - canvas_x)**2 + (node_y - canvas_y)**2)
            if distance <= 10:  # Node selection radius
                clicked_node = node
                break
        
        if clicked_node:
            # Select existing node
            self.select_node(clicked_node)
        else:
            # Add new node at click position
            vrp_x, vrp_y = self.canvas_to_vrp_coords(canvas_x, canvas_y)
            new_node = VRPNode(vrp_x, vrp_y)
            self.nodes.append(new_node)
            self.select_node(new_node)
            self.draw_nodes()
            self.status_label.configure(text=f"Added node {new_node.id} at ({vrp_x:.1f}, {vrp_y:.1f})")
    
    def on_canvas_right_click(self, event):
        """Handle right click on canvas"""
        # Get canvas coordinates
        canvas_x = event.x
        canvas_y = event.y
        
        # Check if clicked on existing node
        clicked_node = None
        for node in self.nodes:
            node_x, node_y = self.vrp_to_canvas_coords(node.x, node.y)
            distance = math.sqrt((node_x - canvas_x)**2 + (node_y - canvas_y)**2)
            if distance <= 10:  # Node selection radius
                clicked_node = node
                break
                
        if clicked_node:
            # Don't allow removing depot
            if clicked_node.is_depot:
                messagebox.showinfo("Cannot Remove Depot", "The depot node cannot be removed.")
                return
                
            # Remove the node
            self.nodes.remove(clicked_node)
            if self.selected_node and self.selected_node.id == clicked_node.id:
                self.select_node(None)  # Deselect if removing selected node
            self.draw_nodes()
            self.status_label.configure(text=f"Removed node {clicked_node.id}")
    
    def select_node(self, node):
        """Select a node and update UI"""
        self.selected_node = node
        
        if node is None:
            # Clear node info
            self.node_info_label.configure(text="No node selected")
            self.toggle_node_constraint_controls(False)
        else:
            # Update node info
            node_type = "Depot" if node.is_depot else "Customer"
            self.node_info_label.configure(text=f"Selected: {node_type} Node {node.id} ({node.x:.1f}, {node.y:.1f})")
            
            # Update UI with node's constraints
            if node.time_window:
                self.time_window_start.delete(0, tk.END)
                self.time_window_start.insert(0, str(node.time_window[0]))
                self.time_window_end.delete(0, tk.END)
                self.time_window_end.insert(0, str(node.time_window[1]))
            else:
                self.time_window_start.delete(0, tk.END)
                self.time_window_end.delete(0, tk.END)
            
            # Enable controls
            self.toggle_node_constraint_controls(True)
            
            # Update node skills UI
            self.update_node_skills_ui()
        
        # Redraw to highlight selected node
        self.draw_nodes()
    
    def toggle_node_constraint_controls(self, enabled):
        """Enable or disable node constraint controls"""
        state = "normal" if enabled else "disabled"
        self.time_window_start.configure(state=state)
        self.time_window_end.configure(state=state)
        self.set_time_window_btn.configure(state=state)
        self.clear_time_window_btn.configure(state=state)
    
    def update_skills_ui(self):
        """Update the skills list UI"""
        # Clear existing skills UI
        for widget in self.skills_list_frame.winfo_children():
            widget.destroy()
            
        # No skills message
        if not self.available_skills:
            no_skills_label = ctk.CTkLabel(self.skills_list_frame, text="No skills defined")
            no_skills_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            return
            
        # Add each skill with a delete button
        for i, skill in enumerate(self.available_skills):
            skill_frame = ctk.CTkFrame(self.skills_list_frame)
            skill_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
            skill_label = ctk.CTkLabel(skill_frame, text=skill)
            skill_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            
            delete_btn = ctk.CTkButton(
                skill_frame, text="X", width=30, 
                command=lambda s=skill: self.on_delete_skill(s)
            )
            delete_btn.grid(row=0, column=1, sticky="e", padx=5, pady=5)
        
        # Update other UI elements that depend on skills
        self.update_vehicle_skills_ui()
        if self.selected_node:
            self.update_node_skills_ui()
    
    def update_vehicle_skills_ui(self):
        """Update the vehicle skills UI based on number of vehicles and available skills"""
        # Clear existing vehicle skills UI
        for widget in self.vehicle_skills_frame.winfo_children():
            widget.destroy()
            
        # Initialize vehicle skills if needed
        for i in range(self.num_vehicles):
            if i not in self.vehicle_skills:
                self.vehicle_skills[i] = []
        
        # No skills message
        if not self.available_skills:
            no_skills_label = ctk.CTkLabel(self.vehicle_skills_frame, text="No skills defined")
            no_skills_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            return
        
        # Create a title row
        vehicle_label = ctk.CTkLabel(self.vehicle_skills_frame, text="Vehicle")
        vehicle_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        skills_label = ctk.CTkLabel(self.vehicle_skills_frame, text="Skills")
        skills_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Create a row for each vehicle
        for i in range(self.num_vehicles):
            vehicle_row_label = ctk.CTkLabel(self.vehicle_skills_frame, text=f"Vehicle {i}")
            vehicle_row_label.grid(row=i+1, column=0, sticky="w", padx=5, pady=5)
            
            # Create a frame for the skills checkboxes
            skills_frame = ctk.CTkFrame(self.vehicle_skills_frame)
            skills_frame.grid(row=i+1, column=1, sticky="w", padx=5, pady=2)
            
            # Add checkboxes for each skill
            for j, skill in enumerate(self.available_skills):
                skill_var = tk.BooleanVar(value=skill in self.vehicle_skills.get(i, []))
                skill_checkbox = ctk.CTkCheckBox(
                    skills_frame, text=skill, variable=skill_var,
                    command=lambda v=i, s=skill, var=skill_var: self.on_vehicle_skill_toggle(v, s, var)
                )
                skill_checkbox.grid(row=0, column=j, sticky="w", padx=5, pady=2)
    
    def update_node_skills_ui(self):
        """Update the node skills UI for the selected node"""
        # Clear existing node skills UI
        for widget in self.node_skills_frame.winfo_children():
            widget.destroy()
            
        if not self.selected_node:
            return
            
        # No skills message
        if not self.available_skills:
            no_skills_label = ctk.CTkLabel(self.node_skills_frame, text="No skills defined")
            no_skills_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
            return
            
        # Add checkboxes for each skill
        for i, skill in enumerate(self.available_skills):
            skill_var = tk.BooleanVar(value=skill in self.selected_node.required_skills)
            skill_checkbox = ctk.CTkCheckBox(
                self.node_skills_frame, text=skill, variable=skill_var,
                command=lambda s=skill, var=skill_var: self.on_node_skill_toggle(s, var)
            )
            skill_checkbox.grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=2)
    
    def on_vehicle_count_change(self, value):
        """Handle change in vehicle count"""
        new_count = int(value)
        self.num_vehicles = new_count
        self.vehicle_count_label.configure(text=str(new_count))
        
        # Update vehicle skills
        self.update_vehicle_skills_ui()
    
    def on_set_time_window(self):
        """Handle set time window button click"""
        if not self.selected_node:
            return
            
        start_text = self.time_window_start.get().strip()
        end_text = self.time_window_end.get().strip()
        
        if not start_text or not end_text:
            messagebox.showwarning("Invalid Time Window", "Please enter both start and end times.")
            return
            
        try:
            start_time = int(start_text)
            end_time = int(end_text)
            
            if start_time >= end_time:
                messagebox.showwarning("Invalid Time Window", "End time must be greater than start time.")
                return
                
            if start_time < 0:
                messagebox.showwarning("Invalid Time Window", "Times must be non-negative.")
                return
            
        except ValueError:
            messagebox.showwarning("Invalid Time Window", "Times must be integers.")
            return
        
        # Set the time window
        self.selected_node.set_time_window(start_time, end_time)
        self.draw_nodes()  # Redraw to update node appearance
        self.status_label.configure(text=f"Set time window [{start_time}, {end_time}] for node {self.selected_node.id}")
    
    def on_clear_time_window(self):
        """Handle clear time window button click"""
        if not self.selected_node:
            return
            
        self.selected_node.clear_time_window()
        self.time_window_start.delete(0, tk.END)
        self.time_window_end.delete(0, tk.END)
        self.draw_nodes()  # Redraw to update node appearance
        self.status_label.configure(text=f"Cleared time window for node {self.selected_node.id}")
    
    def on_add_skill(self):
        """Handle add skill button click"""
        new_skill = self.new_skill_entry.get().strip()
        
        if not new_skill:
            messagebox.showwarning("Invalid Skill", "Please enter a skill name.")
            return
            
        if new_skill in self.available_skills:
            messagebox.showwarning("Duplicate Skill", f"Skill '{new_skill}' already exists.")
            return
            
        # Add the skill
        self.available_skills.append(new_skill)
        self.new_skill_entry.delete(0, tk.END)
        self.update_skills_ui()
        self.status_label.configure(text=f"Added skill: {new_skill}")
    
    def on_delete_skill(self, skill):
        """Handle delete skill button click"""
        # Ask for confirmation
        if messagebox.askyesno("Confirm Delete", f"Delete skill '{skill}'? This will remove it from all vehicles and nodes."):
            # Remove skill from the list
            self.available_skills.remove(skill)
            
            # Remove skill from all vehicles
            for vehicle_id, skills in self.vehicle_skills.items():
                if skill in skills:
                    skills.remove(skill)
            
            # Remove skill from all nodes
            for node in self.nodes:
                if skill in node.required_skills:
                    node.required_skills.remove(skill)
            
            # Update UI
            self.update_skills_ui()
            self.draw_nodes()  # Redraw nodes (some might change appearance if they lost their only skill)
            self.status_label.configure(text=f"Deleted skill: {skill}")
    
    def on_vehicle_skill_toggle(self, vehicle_id, skill, var):
        """Handle vehicle skill checkbox toggle"""
        if var.get():
            # Add skill to vehicle
            if vehicle_id not in self.vehicle_skills:
                self.vehicle_skills[vehicle_id] = []
            if skill not in self.vehicle_skills[vehicle_id]:
                self.vehicle_skills[vehicle_id].append(skill)
        else:
            # Remove skill from vehicle
            if vehicle_id in self.vehicle_skills and skill in self.vehicle_skills[vehicle_id]:
                self.vehicle_skills[vehicle_id].remove(skill)
    
    def on_node_skill_toggle(self, skill, var):
        """Handle node skill checkbox toggle"""
        if not self.selected_node:
            return
            
        if var.get():
            # Add skill requirement to node
            self.selected_node.add_required_skill(skill)
        else:
            # Remove skill requirement from node
            self.selected_node.remove_required_skill(skill)
            
        # Redraw nodes to update appearance
        self.draw_nodes()
        
        # Update status
        action = "added to" if var.get() else "removed from"
        self.status_label.configure(text=f"Skill '{skill}' {action} node {self.selected_node.id}")
    
    def on_save_preset(self):
        """Handle save preset button click"""
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save VRP Scenario Preset"
        )
        
        if not file_path:
            return  # User cancelled
            
        try:
            # Prepare data to save
            data = {
                "nodes": [node.to_dict() for node in self.nodes],
                "num_vehicles": self.num_vehicles,
                "available_skills": self.available_skills,
                "vehicle_skills": self.vehicle_skills
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.status_label.configure(text=f"Saved preset to {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving preset: {str(e)}")
    
    def on_load_preset(self):
        """Handle load preset button click"""
        # Ask for file location
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Load VRP Scenario Preset"
        )
        
        if not file_path:
            return  # User cancelled
            
        try:
            # Load from file
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Clear current state
            self.selected_node = None
            self.nodes = []
            self.routes = []
            
            # Load nodes
            VRPNode.id_counter = 0  # Reset node ID counter
            for node_data in data["nodes"]:
                node = VRPNode.from_dict(node_data)
                self.nodes.append(node)
                if not node.is_depot:
                    VRPNode.id_counter = max(VRPNode.id_counter, node.id + 1)
            
            # Find depot node
            self.depot_node = next((node for node in self.nodes if node.is_depot), None)
            
            # Load other settings
            self.num_vehicles = data["num_vehicles"]
            self.vehicle_count_var.set(self.num_vehicles)
            self.vehicle_count_label.configure(text=str(self.num_vehicles))
            
            self.available_skills = data["available_skills"]
            self.vehicle_skills = {int(k): v for k, v in data["vehicle_skills"].items()}
            
            # Update UI
            self.draw_nodes()
            self.update_skills_ui()
            
            self.status_label.configure(text=f"Loaded preset from {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading preset: {str(e)}")
    
    def on_solve_vrp(self):
        """Handle solve VRP button click"""
        # Check if we have enough nodes
        if len(self.nodes) < 2:
            messagebox.showinfo("Not Enough Nodes", "Please add at least one customer node.")
            return
            
        # Update status
        self.status_label.configure(text="Solving VRP...")
        
        # Run solver in a separate thread to keep UI responsive
        solver_thread = threading.Thread(target=self.run_vrp_solver)
        solver_thread.daemon = True
        solver_thread.start()
        
        # Check for results periodically
        self.after(100, self.check_solver_results)
    
    def run_vrp_solver(self):
        """Run the VRP solver in a background thread"""
        try:
            # Debug message for node count
            node_count = len(self.nodes)
            customer_count = sum(1 for node in self.nodes if not node.is_depot)
            debug_msg = f"Solving VRP with {node_count} total nodes ({customer_count} customers) and {self.num_vehicles} vehicles"
            print(debug_msg)
            self.queue.put(("debug", debug_msg))
            
            # Prepare data for the solver
            data = self.prepare_solver_data()
            
            # Debug distance matrix
            print("Distance Matrix:")
            for i, row in enumerate(data["distance_matrix"]):
                node_type = "Depot" if i == 0 else "Customer"
                print(f"Node {i} ({node_type}): {row}")
            
            # Create the routing index manager
            manager = pywrapcp.RoutingIndexManager(
                len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
            )

            # Create Routing Model
            routing = pywrapcp.RoutingModel(manager)

            # Register distance callback
            def distance_callback(from_index, to_index):
                """Returns the distance between the two nodes."""
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return data["distance_matrix"][from_node][to_node]

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            # Add Distance constraint
            dimension_name = "Distance"
            routing.AddDimension(
                transit_callback_index,
                0,  # no slack
                 30000,  # vehicle maximum travel distance - increased this value
                True,  # start cumul to zero
                dimension_name,
            )
            distance_dimension = routing.GetDimensionOrDie(dimension_name)
            distance_dimension.SetGlobalSpanCostCoefficient(100)

            # Check for nodes with skills/time windows
            has_time_windows = any(node.time_window for node in self.nodes)
            has_skills = any(node.required_skills for node in self.nodes)
            print(f"Has time windows: {has_time_windows}, Has skills: {has_skills}")

            # Only add time window constraints if at least one node has time windows
            if has_time_windows:
                # Create time dimension (only if needed)
                time_dimension_name = "Time"
                routing.AddDimension(
                    transit_callback_index,
                    30,  # Allow wait time between locations
                     30000,  # Maximum time allowed for the entire route - increased this value
                    False,  # Don't force start cumul to zero since we have time windows
                    time_dimension_name
                )
                time_dimension = routing.GetDimensionOrDie(time_dimension_name)
                
                # Add time window constraints
                for node_idx, node in enumerate(self.nodes):
                    if node.time_window:
                        index = manager.NodeToIndex(node_idx)
                        time_dimension.CumulVar(index).SetRange(
                            node.time_window[0], node.time_window[1]
                        )
            
            # Only add skills constraints if at least one node has required skills
            if has_skills:
                # First check if any node has skills that no vehicle possesses
                for node in self.nodes:
                    if not node.required_skills:
                        continue
                    
                    valid_vehicles = []
                    for v_id in range(data["num_vehicles"]):
                        if all(skill in self.vehicle_skills.get(v_id, []) for skill in node.required_skills):
                            valid_vehicles.append(v_id)
                    
                    if not valid_vehicles:
                        self.queue.put(("error", f"No vehicle has the skills required for node {node.id} ({', '.join(node.required_skills)})"))
                        return
                
                # Set allowed vehicles for each node based on skills
                for node_idx, node in enumerate(self.nodes):
                    if not node.required_skills or node.is_depot:
                        continue
                    
                    # Find vehicles with all required skills
                    valid_vehicles = []
                    for v_id in range(data["num_vehicles"]):
                        if all(skill in self.vehicle_skills.get(v_id, []) for skill in node.required_skills):
                            valid_vehicles.append(v_id)
                    
                    # Create allowed vehicles list for this node
                    index = manager.NodeToIndex(node_idx)
                    routing.VehicleVar(index).SetValues(valid_vehicles)

            # Set search parameters - use simpler settings for basic scenarios
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            
            # For simple cases without constraints, PATH_CHEAPEST_ARC is fast and reliable
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            
            # Try a different solver strategy if we have many nodes
            if len(self.nodes) > 20:
                search_parameters.first_solution_strategy = (
                    routing_enums_pb2.FirstSolutionStrategy.SAVINGS
                )
            
            # Set a reasonable time limit
            search_parameters.time_limit.seconds = 10
            
            # Only use metaheuristics for complex problems with constraints
            if has_time_windows or has_skills or len(self.nodes) > 15:
                search_parameters.local_search_metaheuristic = (
                    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
                )
                search_parameters.time_limit.seconds = 15
            
            print(f"Using solver strategy: {search_parameters.first_solution_strategy}")
            print(f"Solver time limit: {search_parameters.time_limit.seconds} seconds")
            
            # Solve the problem
            print("Starting solver...")
            solution = routing.SolveWithParameters(search_parameters)
            print(f"Solver completed, solution found: {solution is not None}")

            if solution:
                # Extract routes
                routes = []
                max_route_distance = 0
                for vehicle_id in range(data["num_vehicles"]):
                    route = []
                    index = routing.Start(vehicle_id)
                    route_distance = 0
                    
                    while not routing.IsEnd(index):
                        node_idx = manager.IndexToNode(index)
                        route.append(self.nodes[node_idx].id)
                        
                        previous_index = index
                        index = solution.Value(routing.NextVar(index))
                        route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                    
                    # Add the depot at the end
                    node_idx = manager.IndexToNode(index)
                    route.append(self.nodes[node_idx].id)
                    
                    # Print route for debugging
                    print(f"Vehicle {vehicle_id} route: {route}, distance: {route_distance}")
                    
                    routes.append(route)
                    max_route_distance = max(route_distance, max_route_distance)
                
                # Put results in the queue
                self.queue.put(("success", routes, max_route_distance))
            else:
                # Handle the case where no solution is found
                if len(self.nodes) <= 1:
                    self.queue.put(("error", "Need at least one customer node to create routes."))
                elif data["num_vehicles"] < 1:
                    self.queue.put(("error", "Need at least one vehicle to create routes."))
                elif has_time_windows:
                    self.queue.put(("error", "Could not find a solution. Try relaxing time window constraints."))
                elif has_skills:
                    self.queue.put(("error", "Could not find a solution. Check that vehicles have the necessary skills."))
                else:
                    # Try again with a different strategy as a fallback
                    print("No solution found. Trying again with different solver settings...")
                    self.queue.put(("debug", "First attempt failed. Trying with different solver settings..."))
                    
                    # Create new search parameters with different strategy
                    fallback_parameters = pywrapcp.DefaultRoutingSearchParameters()
                    fallback_parameters.first_solution_strategy = (
                        routing_enums_pb2.FirstSolutionStrategy.SAVINGS
                    )
                    fallback_parameters.local_search_metaheuristic = (
                        routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING
                    )
                    fallback_parameters.time_limit.seconds = 20
                    
                    print(f"Fallback strategy: {fallback_parameters.first_solution_strategy}")
                    print(f"Using metaheuristic: {fallback_parameters.local_search_metaheuristic}")
                    
                    # Try again with fallback parameters
                    solution = routing.SolveWithParameters(fallback_parameters)
                    
                    if solution:
                        # Extract routes with the fallback solution
                        routes = []
                        max_route_distance = 0
                        for vehicle_id in range(data["num_vehicles"]):
                            route = []
                            index = routing.Start(vehicle_id)
                            route_distance = 0
                            
                            while not routing.IsEnd(index):
                                node_idx = manager.IndexToNode(index)
                                route.append(self.nodes[node_idx].id)
                                
                                previous_index = index
                                index = solution.Value(routing.NextVar(index))
                                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                            
                            # Add the depot at the end
                            node_idx = manager.IndexToNode(index)
                            route.append(self.nodes[node_idx].id)
                            
                            # Print route for debugging
                            print(f"Fallback - Vehicle {vehicle_id} route: {route}, distance: {route_distance}")
                            
                            routes.append(route)
                            max_route_distance = max(route_distance, max_route_distance)
                        
                        self.queue.put(("success", routes, max_route_distance))
                    else:
                        # Still no solution
                        self.queue.put(("error", "Could not find a solution. Try using more vehicles or check if constraints are feasible."))
        except Exception as e:
            # Handle unexpected errors
            import traceback
            print(f"Error during solving: {str(e)}")
            print(traceback.format_exc())
            self.queue.put(("error", f"Error during solving: {str(e)}"))
    
    def prepare_solver_data(self):
        """Prepare data for the VRP solver"""
        data = {}
        
        # Create distance matrix
        num_nodes = len(self.nodes)
        distance_matrix = [[0 for _ in range(num_nodes)] for _ in range(num_nodes)]
        
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    distance_matrix[i][j] = 0
                else:
                    # Calculate Euclidean distance between nodes
                    node_i = self.nodes[i]
                    node_j = self.nodes[j]
                    dist = int(math.sqrt((node_i.x - node_j.x)**2 + (node_i.y - node_j.y)**2) * 100)
                    distance_matrix[i][j] = dist
        
        data["distance_matrix"] = distance_matrix
        data["num_vehicles"] = self.num_vehicles
        data["depot"] = 0  # Depot is always the first node
        
        return data
    
    def check_solver_results(self):
        """Check for solver results from the queue"""
        try:
            if not self.queue.empty():
                result = self.queue.get()
                
                if result[0] == "success":
                    routes = result[1]
                    max_distance = result[2]
                    
                    self.routes = routes
                    self.draw_routes()
                    
                    self.status_label.configure(
                        text=f"Solution found! Maximum route distance: {max_distance/100:.1f}"
                    )
                    
                elif result[0] == "debug":
                    debug_msg = result[1]
                    # Update status but continue checking for more results
                    self.status_label.configure(text=f"Debug: {debug_msg}")
                    self.after(100, self.check_solver_results)
                    return
                    
                elif result[0] == "no_solution":
                    messagebox.showinfo("No Solution", "The solver could not find a solution.")
                    self.status_label.configure(text="No solution found")
                    
                elif result[0] == "error":
                    error_msg = result[1]
                    messagebox.showerror("Solver Error", error_msg)
                    self.status_label.configure(text=f"Error: {error_msg}")
            else:
                # Keep checking until we get a result
                self.after(100, self.check_solver_results)
                return
                
        except Exception as e:
            messagebox.showerror("Error", f"Error checking solver results: {str(e)}")
            self.status_label.configure(text="Ready")
    
    def on_clear_routes(self):
        """Handle clear routes button click"""
        self.routes = []
        self.canvas.delete("route")
        self.status_label.configure(text="Routes cleared")
    
    def on_clear_all(self):
        """Handle clear all button click"""
        # Ask for confirmation
        if messagebox.askyesno("Confirm Clear All", "Clear all nodes and routes?"):
            # Keep only the depot node
            self.nodes = [node for node in self.nodes if node.is_depot]
            self.routes = []
            self.selected_node = None
            
            # Redraw
            self.draw_nodes()
            self.canvas.delete("route")
            self.status_label.configure(text="All nodes and routes cleared")


if __name__ == "__main__":
    app = VRPApp()
    app.mainloop()