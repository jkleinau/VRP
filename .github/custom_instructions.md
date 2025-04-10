**Project Goal:** Create a Python desktop application UI for configuring, visualizing, and solving a Vehicle Routing Problem (VRP) scenario, based on the previously defined Project Requirements Document (PRD).

**Core Technology Stack:**
1.  **UI Framework:** CustomTkinter (https://github.com/TomSchimansky/CustomTkinter)
2.  **Canvas:** Use the standard `tkinter.Canvas` widget within the CustomTkinter window (CustomTkinter doesn't provide its own canvas widget).
3.  **Language:** Python 3.x
4.  **VRP Solver Integration:** Assume integration with an existing Python function that uses `google.ortools.constraint_solver`.
5.  **Preset Storage:** Use the `json` library for saving/loading scenario presets.
6.  **Image Handling (Optional for Canvas):** `Pillow` (PIL fork) might be needed if using icons or advanced canvas drawing.

**Key UI Components to Implement (Refer to PRD sections):**

1.  **Main Window Layout:** Create a main application window using `customtkinter.CTk`. Divide the layout logically (e.g., Canvas on the left/center, Controls panel on the right).
2.  **Scenario Canvas (PRD 2.1):**
    * Implement using `tkinter.Canvas`.
    * Display the fixed depot at (0,0) (adjust canvas coordinates accordingly).
    * Handle left-clicks (`<Button-1>`) to add customer nodes at the click location. Store node data (ID, coordinates).
    * Implement node selection (e.g., clicking an existing node).
    * Implement node removal (e.g., right-click `<Button-3>` on a node, or selection + delete button).
    * Visually differentiate the depot and customer nodes.
3.  **Parameter Controls (PRD 2.2):**
    * Use `customtkinter.CTkLabel` and `customtkinter.CTkSlider` or `customtkinter.CTkEntry` for setting the number of vehicles.
    * Implement a way to define available skills (e.g., a `CTkEntry` with an "Add Skill" button populating a `CTkOptionMenu` or list).
    * Implement assigning skills to vehicles (e.g., dynamically creating checkboxes or multi-select options for each vehicle based on the number selected).
4.  **Node Constraint Configuration (PRD 2.3):**
    * When a node is selected on the canvas, enable/populate input fields for its constraints.
    * Use `CTkEntry` widgets for Time Window start/end times.
    * Use `CTkOptionMenu` or Checkboxes linked to the defined skills list for setting node requirements.
    * Provide visual feedback on the canvas for nodes with constraints (e.g., small icon, different color).
5.  **Preset Handling (PRD 2.4):**
    * Add "Save Preset" and "Load Preset" buttons (`customtkinter.CTkButton`).
    * Use `customtkinter.filedialog.asksaveasfilename` and `customtkinter.filedialog.askopenfilename`.
    * Implement functions to serialize the current state (node list with coords/constraints, vehicle config) to JSON and deserialize JSON to load the state back into the UI elements.
6.  **Solver Integration & Visualization (PRD 2.5):**
    * Add a "Solve VRP" button (`customtkinter.CTkButton`).
    * This button should trigger a function that:
        * Gathers all current configuration data from the UI widgets.
        * Formats this data appropriately for the existing Python OR-Tools solver function.
        * Calls the solver function. **Crucially:** If the solver function might take time, run it in a separate thread (`threading` module) to avoid freezing the UI. Provide visual feedback (e.g., disable button, show "Solving..." label).
        * Receives the solution (routes).
        * Clears previous routes from the canvas.
        * Draws the new routes on the `tkinter.Canvas` (e.g., using `create_line`, potentially with different colors per route/vehicle). Use tags for easy management/deletion of route lines.
        * Displays solver status/feedback (`CTkLabel`).

**Best Practices & Requirements:**

* **Modularity (Hard Requirement):** Separate UI code (widget creation, layout, event handling) from the data management and solver interaction logic. Use functions or classes appropriately. Avoid putting complex logic directly inside button command lambdas.
* **UI Responsiveness (Hard Requirement):** The UI must remain interactive. Use threading for the potentially long-running VRP solver call. Update the UI safely from the thread (e.g., using `queue` or `after`).
* **Clear Feedback (Hard Requirement):** Provide visual feedback for user actions (node selection), background processes (solving), and outcomes (solution found/not found, errors, saved/loaded preset).
* **Error Handling (Soft Requirement -> Hard for File I/O):** Implement `try...except` blocks for file operations (save/load presets) and around the solver call. Show user-friendly error messages using `tkinter.messagebox` or a status label.
* **Code Clarity (Soft Requirement):** Use meaningful variable and function names. Add comments where necessary.
* **Canvas Coordinate Management:** Be mindful of translating canvas click coordinates to your internal VRP coordinate system (especially with the depot at (0,0)).
* **Styling (Soft Requirement):** Utilize CustomTkinter's appearance modes (`set_appearance_mode`) and color themes (`set_default_color_theme`) for a consistent look.
* **Data Structures:** Use appropriate Python data structures (lists, dictionaries, potentially simple classes) to hold node data, vehicle configurations, and constraints internally.

**Output:**
Provide runnable Python code implementing the UI according to these instructions. Structure the code logically (e.g., imports, helper functions, main App class, main execution block). If the code becomes very large, consider splitting it into multiple logical code blocks or suggesting file separation.