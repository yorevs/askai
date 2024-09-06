import pyautogui


def take_screenshot(file_path):
    # Take a screenshot using pyautogui
    screenshot = pyautogui.screenshot()

    # Check if saving as JPEG and convert to RGB if necessary
    if file_path.lower().endswith(".jpg") or file_path.lower().endswith(".jpeg"):
        screenshot = screenshot.convert("RGB")

    # Save the screenshot to the specified file path
    screenshot.save(file_path)
    print(f"Screenshot saved at {file_path}")


if __name__ == "__main__":
    take_screenshot("gabiroba.jpeg")
