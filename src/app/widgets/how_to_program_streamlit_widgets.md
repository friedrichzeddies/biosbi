# How to Program Streamlit Widgets

When building complex Streamlit applications with multiple interactive components (widgets), performance and modularity can become major bottlenecks. By default, any interaction in Streamlit—like moving a slider or clicking a button—triggers a top-to-bottom rerun of the entire script.

To circumvent this and build scalable apps, a highly effective design pattern is combining `@st.cache_resource` and `@st.fragment`.

## What does `@st.cache_resource` do?
**Mechanic:** It caches global, unserializable resources—such as deeply nested objects, Machine Learning models (PyTorch tensors/weights), database connections, or large dataset loaders (like `trimesh` geometry or GLB animation data). 

**Impact:** Streamlit normally clears local memory on every script rerun. By wrapping your heavy instantiation logic in `@st.cache_resource`, you guarantee it only computes and loads *once* upon the first execution. Further interactions will completely bypass the loading step, fetching the asset instantly from RAM.

## What does `@st.fragment` do?
**Mechanic:** It isolates a specific rendering function into its own localized execution environment (a "fragment"). 

**Impact:** If a user interacts with an input element (like a slider or a dropdown) that lives *inside* a function decorated with `@st.fragment`, **only that specific function reruns**. The rest of the main Streamlit application, including other widgets, remains completely untouched.

---

## Why this is the Ultimate Setup for Standalone Widgets

If you are building individual complex widgets (like a `cat_projector.py` tool) that will eventually be imported and glued together into one main dashboard file, this setup is perfect for several reasons:

### 1. Perfect Isolation (Zero Cross-Talk)
You can place 10 different widgets on the same page. If a user moves a slider in Widget A to rotate a molecule, only Widget A's `@st.fragment` executes. Widgets B through J don't recalculate, preventing annoying full-page flickering, losing scroll position, and massive computational overhead.

### 2. Self-Contained Modularity
Because each widget can define its own `@st.fragment` for its UI and its own `@st.cache_resource` for its specific underlying data, the widget becomes a pure "plug-and-play" module. 

You can simply `import my_widget` into the main file, and call `my_widget.render()`. The main file doesn't need to be polluted with state management, caching configuration, or complex logic. The widget encapsulates everything it needs to survive on its own.

### 3. Memory Efficiency
If multiple widgets on your dashboard happen to require the same underlying heavy asset (e.g. they all need to access the base physics engine), `@st.cache_resource` acts as a clever singleton. It ensures that regardless of which widget asks for the resource first, it is only loaded into the server's RAM exactly once, and then shared efficiently via reference.

### Summary Example
Here is what a perfect standalone widget looks like:

```python
import streamlit as st

# 1. Self-contained heavy memory management
@st.cache_resource
def load_heavy_data():
    return Engine("heavy_model.pt")

# 2. Self-contained UI and Logic execution
@st.fragment
def render_widget():
    # Grabs the cached data instantly (or loads it if it's the very first time)
    engine = load_heavy_data()
    
    st.write("### Interactive Cat Projector")
    
    # This interaction is trapped inside the fragment!
    angle = st.slider("Rotate", 0, 360, key="widget_a_slider")
    
    # 3. Execution isolated strictly to this widget
    img = engine.calculate_projection(angle)
    st.image(img)
```

When you glue this into `main.py`, the rest of your app has absolutely no idea how heavy this widget is—it just works flawlessly and independently.
