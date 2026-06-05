import os

def capture_card_screenshot(element_handle, output_path: str) -> bool:
    if element_handle is None:
        return False
        
    try:
        # Ensure output directory exists
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # Take element screenshot
        element_handle.screenshot(path=output_path)
        print(f"[SUCCESS] Captured screenshot to: {output_path}")
        return True
    except Exception as e:
        print(f"[WARNING] Screenshot capture failed: {e}")
        save_error_placeholder(output_path, f"Playwright screenshot exception: {e}")
        return False

def save_error_placeholder(output_path: str, reason: str):
    try:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        placeholder_path = output_path.replace(".png", ".txt")
        with open(placeholder_path, "w", encoding="utf-8") as f:
            f.write(f"Screenshot placeholder. Reason: {reason}")
        print(f"[INFO] Created error placeholder file: {placeholder_path}")
    except Exception as e:
        print(f"[WARNING] Failed to write placeholder: {e}")
