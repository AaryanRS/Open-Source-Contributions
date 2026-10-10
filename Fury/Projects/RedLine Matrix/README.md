# FURY Organic 3D Network Visualization

A simple procedural 3D visualization made with **FURY**.

The project creates a dense organic/branching structure similar to a neural or tractography-style network. It uses FURY to render the 3D lines and provides an interactive window for viewing and rotating the structure.

---

## PowerShell Commands

Run these commands from the folder containing `fury_organic_network.py`.

### 1. Run the smoke test

Checks that the project can start its basic setup without opening the full visualization.

```powershell
python fury_organic_network.py --smoke-test
```

### 2. Run the preview

Starts a smaller version of the visualization for quick testing.

```powershell
python fury_organic_network.py --preview
```

### 3. Run the normal visualization

Starts the main version of the project.

```powershell
python fury_organic_network.py
```

### 4. Run with 50 branches

```powershell
python fury_organic_network.py --count 50
```

### 5. Run with 100 branches

```powershell
python fury_organic_network.py --count 100
```

The `--count` option can be changed to test different numbers of branches.

---

## Requirements

- Windows 11
- Python 3.14.7
- FURY
- NumPy
- NVIDIA GPU can be used for the GPU rendering path

FURY should already be installed in the Python environment before running the project.

---

## How the Visualization Is Created

The visualization is generated procedurally, so the branches do not need to be manually created.

### 1. Create the main branches

A set of primary 3D paths is generated around the center.

These paths start from different directions and are designed to come together near the middle. This creates the dense central region seen in the visualization.

In the main configuration there are **48 primary lines**.

### 2. Create secondary branches

Additional smaller paths are generated from the primary structure.

These branches make the visualization look denser and more organic.

The balanced configuration uses around **192 secondary branches**, giving roughly **240 branches in total**.

### 3. Render the primary structure

The primary paths are rendered using FURY's `streamtube` actor.

They use a larger radius so that they appear as the main/bigger branches.

### 4. Render the secondary structure

The secondary paths are rendered using FURY's `streamlines` actor.

They are thinner than the primary branches and are used to create the detailed branching structure.

### 5. Create the dense center

There is no separate sphere or object at the center.

The dense center is created naturally because many of the generated primary paths meet and pass through the same central region.

### 6. Interactive visualization

FURY creates the 3D window and handles the rendering.

The visualization can be rotated and inspected interactively.

---

## Project Structure

```text
fury_organic_network.py
README.md
```

The main Python file contains the procedural generation, FURY actors, visualization setup, and command-line options.

---

## Main Configurations

The project supports different sizes for testing:

| Configuration | Approx. Branches | Purpose |
|---|---:|---|
| Preview | 120 | Quick testing |
| Balanced | 240 | Main visualization |
| High | 300 | Denser visualization |

The balanced version is the main configuration used to demonstrate the intended visual style.

---

## Important Note

The visualization is generated using FURY's existing rendering APIs.

The project is mainly intended as a demonstration of how a dense organic 3D branching structure can be created and rendered using FURY.
