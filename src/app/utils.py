"""Utility functions for Streamlit app rendering."""

import importlib.util
import os
import re
import sys
from pathlib import Path

import streamlit as st


def render_markdown(filename: str, base_dir: Path = None) -> None:
    """
    Render a markdown file with support for image embedding.
    
    Images are detected from markdown image syntax ![alt](path) and rendered
    with st.image() for proper path handling and display. Relative paths are
    resolved relative to base_dir.
    
    Args:
        filename: Name of the markdown file to render
        base_dir: Base directory to resolve relative paths from. If None,
                 uses the caller's directory.
    """
    if base_dir is None:
        # Get the caller's directory
        import inspect
        frame = inspect.currentframe().f_back
        base_dir = Path(frame.f_globals.get('__file__', '.')).parent
    else:
        base_dir = Path(base_dir)
    
    md_path = base_dir / filename
    if not md_path.exists():
        st.warning(f"Missing markdown file: {filename}")
        return
    
    with md_path.open("r", encoding="utf-8") as file:
        content = file.read()
    
    # Pattern to match markdown images: ![alt text](path/to/image.ext)
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    # Find all images and their positions
    current_pos = 0
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        image_path_str = match.group(2)
        
        # Render text before image
        text_before = content[current_pos:match.start()].strip()
        if text_before:
            st.markdown(text_before)
        
        # Resolve image path
        if image_path_str.startswith(('http://', 'https://')):
            # Absolute URL
            image_path = image_path_str
        else:
            # Relative path - resolve relative to markdown file location
            image_path = base_dir / image_path_str
            if not image_path.exists():
                st.warning(f"Image not found: {image_path}")
                continue
            image_path = str(image_path)
        
        # Render image
        st.image(image_path, caption=alt_text if alt_text else None)
        
        current_pos = match.end()
    
    # Render remaining text after last image
    remaining_text = content[current_pos:].strip()
    if remaining_text:
        st.markdown(remaining_text)


def run_widget(widget_filename: str, function_name: str, widgets_dir: Path = None) -> None:
    """
    Dynamically load and execute a widget function.
    
    Args:
        widget_filename: Name of the widget file (e.g., "02_01_huygens.py")
        function_name: Name of the function to call in the widget
        widgets_dir: Directory containing widgets. If None, uses {app_dir}/widgets
    """
    if widgets_dir is None:
        # Assume standard structure: {app_dir}/widgets
        import inspect
        frame = inspect.currentframe().f_back
        caller_file = frame.f_globals.get('__file__', '')
        if caller_file:
            app_dir = Path(caller_file).parent
            while app_dir.name != 'app' and app_dir.parent != app_dir:
                app_dir = app_dir.parent
            if app_dir.name == 'app':
                widgets_dir = app_dir / "widgets"
            else:
                widgets_dir = Path(caller_file).parent / "widgets"
    else:
        widgets_dir = Path(widgets_dir)
    
    widget_path = widgets_dir / widget_filename
    if not widget_path.exists():
        st.warning(f"Missing widget file: {widget_filename}")
        return
    
    module_name = f"streamlit_widget_{widget_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, str(widget_path))
    if spec is None or spec.loader is None:
        st.error(f"Could not load widget: {widget_filename}")
        return
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    if not hasattr(module, function_name):
        st.error(f"Function '{function_name}' not found in {widget_filename}")
        return
    
    getattr(module, function_name)()
