"""
BluetoothManager.py - Absolute Bluetooth Control via pywinauto UI Inspection
Uses exact element names verified by inspector on this machine.
"""
import os
import time
import sys
import site

# Ensure pywinauto is on path (installed with --user)
sys.path.insert(0, site.getusersitepackages())

from pywinauto import Application, Desktop


def _open_bt_settings_and_connect():
    """Opens Bluetooth Settings and returns the connected Settings window."""
    os.system("start ms-settings:bluetooth")
    time.sleep(4)
    app = Application(backend="uia").connect(title_re="Settings", timeout=10)
    return app.window(title_re="Settings")


def toggle_bluetooth(enable: bool):
    """
    Toggle the main Bluetooth radio on/off.
    The inspector confirmed: Title='Bluetooth'  Type='Button'
    - This is a TOGGLE button - clicking it switches state.
    - We check current state text first to avoid toggling the wrong way.
    """
    try:
        dlg = _open_bt_settings_and_connect()

        # Read current state from the status text
        # Inspector shows: Title='Bluetooth is turned off'  Type='Text'  when off
        state_texts = []
        for ctrl in dlg.descendants(control_type="Text"):
            t = ctrl.window_text()
            if "bluetooth is turned" in t.lower():
                state_texts.append(t.lower())
                break

        current_is_on = not any("turned off" in s for s in state_texts)
        print(f"[BT] Current state: {'ON' if current_is_on else 'OFF'}, desired: {'ON' if enable else 'OFF'}")

        if current_is_on == enable:
            print("[BT] Already in desired state. No action needed.")
            return True

        # Click the Bluetooth TOGGLE BUTTON (inspector confirmed Type='Button')
        # There is one Button with title 'Bluetooth' - that is the toggle.
        bt_toggle = dlg.child_window(title="Bluetooth", control_type="Button")
        if bt_toggle.exists(timeout=3):
            print("[BT] Clicking Bluetooth toggle button...")
            bt_toggle.click_input()
            time.sleep(2)
            print("[BT] Toggle clicked successfully.")
            return True
        else:
            print("[BT] Bluetooth toggle button NOT found! Dumping all buttons:")
            for b in dlg.descendants(control_type="Button"):
                print(f"    Button: '{b.window_text()}'")
            return False

    except Exception as e:
        print(f"[BT] Error: {e}")
        return False


def connect_device(device_name: str):
    """
    Connect to an already-paired Bluetooth device by name.
    Inspector shows paired devices as Group elements with 'Connect' Button inside.
    Known devices: Airdopes 131, Boult Audio Airbass, BT SPEAKER, POCO X4 Pro 5G, etc.
    """
    try:
        # First make sure Bluetooth is ON
        print(f"[BT] Ensuring Bluetooth is ON before connecting to '{device_name}'...")
        toggle_bluetooth(True)
        time.sleep(2)

        # Re-connect to the (potentially updated) window
        app = Application(backend="uia").connect(title_re="Settings", timeout=10)
        dlg = app.window(title_re="Settings")

        print(f"[BT] Searching for device: '{device_name}'...")

        # Look for a Group whose title contains the device name
        for group in dlg.descendants(control_type="Group"):
            group_title = group.window_text()
            if device_name.lower() in group_title.lower():
                print(f"[BT] Found device group: '{group_title}'")
                # Find the Connect button inside this group
                try:
                    connect_btn = group.child_window(title="Connect", control_type="Button")
                    if connect_btn.exists(timeout=2):
                        connect_btn.click_input()
                        print(f"[BT] Connect clicked for '{device_name}'!")
                        return True
                except:
                    pass
                # Try clicking the group itself
                try:
                    group.click_input()
                    return True
                except:
                    pass

        print(f"[BT] Device '{device_name}' not found in paired devices.")
        print("[BT] Available paired devices:")
        for group in dlg.descendants(control_type="Group"):
            t = group.window_text()
            if ", Category" in t:
                print(f"    - {t.split(',')[0]}")
        return False

    except Exception as e:
        print(f"[BT] Connect error: {e}")
        return False


def add_new_device(device_name: str):
    """
    Add/pair a NEW Bluetooth device by scanning for it.
    Opens the 'Add a device' wizard and searches for the device.
    """
    try:
        dlg = _open_bt_settings_and_connect()

        # First enable Bluetooth
        toggle_bluetooth(True)
        time.sleep(1)

        # Click 'Add device' button
        add_btn = dlg.child_window(title="Add device", control_type="Button")
        if add_btn.exists(timeout=3):
            add_btn.click_input()
            time.sleep(3)
        else:
            print("[BT] 'Add device' button not found.")
            return False

        # Find the 'Add a device' dialog
        all_wins = Desktop(backend="uia").windows()
        add_dlg = None
        for w in all_wins:
            if "Add a device" in w.window_text():
                add_dlg = w
                break

        if not add_dlg:
            print("[BT] 'Add a device' dialog not found.")
            return False

        print("[BT] Opened 'Add a device' dialog. Selecting Bluetooth...")

        # Click the Bluetooth option (first list item usually)
        for ctrl in add_dlg.descendants(control_type="ListItem"):
            if "Bluetooth" in ctrl.window_text():
                ctrl.click_input()
                break

        print(f"[BT] Scanning for '{device_name}'... (up to 20 seconds)")
        time.sleep(8)  # Wait for scan

        # Search for the device
        for ctrl in add_dlg.descendants(control_type="ListItem"):
            if device_name.lower() in ctrl.window_text().lower():
                print(f"[BT] Found '{device_name}'! Pairing...")
                ctrl.click_input()
                time.sleep(5)
                # Confirm if needed
                from pywinauto.keyboard import send_keys
                send_keys("{ENTER}")
                return True

        print(f"[BT] '{device_name}' not found in scan results.")
        return False

    except Exception as e:
        print(f"[BT] New device error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: BluetoothManager.py [on|off|connect <device>|pair <device>]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "on":
        toggle_bluetooth(True)
    elif cmd == "off":
        toggle_bluetooth(False)
    elif cmd in ("connect", "pair") and len(sys.argv) > 2:
        name = " ".join(sys.argv[2:])
        if cmd == "connect":
            connect_device(name)
        else:
            add_new_device(name)
    else:
        print("Invalid command.")
