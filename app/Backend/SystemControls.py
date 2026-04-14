from __future__ import annotations

import re
import subprocess
import platform
from dataclasses import dataclass
from typing import Optional, Tuple

# Optional deps
try:
    import keyboard  # type: ignore
except Exception:  # pragma: no cover
    keyboard = None

try:
    import screen_brightness_control as sbc  # type: ignore
except Exception:  # pragma: no cover
    sbc = None


@dataclass
class ControlResult:
    ok: bool
    summary: str


def _clamp(v: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(v)))


# ─────────────────────────────────────────────────────────────────
# BRIGHTNESS
# ─────────────────────────────────────────────────────────────────
def set_brightness_abs(value: int) -> ControlResult:
    if sbc is None:
        return ControlResult(False, 'Brightness control is unavailable (missing dependency).')
    try:
        v = _clamp(value)
        sbc.set_brightness(v)
        return ControlResult(True, f"Brightness set to {v}.")
    except Exception as e:
        return ControlResult(False, f"Failed to set brightness ({e}).")


def change_brightness(delta: int) -> ControlResult:
    if sbc is None:
        return ControlResult(False, 'Brightness control is unavailable (missing dependency).')
    try:
        cur = int(sbc.get_brightness()[0])
        v = _clamp(cur + int(delta))
        sbc.set_brightness(v)
        sign = '+' if delta >= 0 else ''
        return ControlResult(True, f"Brightness changed {sign}{delta} (now {v}).")
    except Exception as e:
        return ControlResult(False, f"Failed to change brightness ({e}).")


# ─────────────────────────────────────────────────────────────────
# VOLUME
# ─────────────────────────────────────────────────────────────────
def _press_volume(key: str, times: int) -> None:
    if keyboard is None:
        raise RuntimeError('Keyboard control is unavailable (missing dependency).')
    for _ in range(max(0, int(times))):
        keyboard.press_and_release(key)


def mute() -> ControlResult:
    if keyboard is None:
        return ControlResult(False, 'Keyboard control is unavailable (missing dependency).')
    try:
        keyboard.press_and_release('volume mute')
        return ControlResult(True, 'Volume muted.')
    except Exception as e:
        return ControlResult(False, f"Failed to mute ({e}).")


def unmute() -> ControlResult:
    try:
        if keyboard is None:
            return ControlResult(False, 'Keyboard control is unavailable (missing dependency).')
        keyboard.press_and_release('volume mute')
        return ControlResult(True, 'Volume unmuted.')
    except Exception as e:
        return ControlResult(False, f"Failed to unmute ({e}).")


def change_volume(delta: int) -> ControlResult:
    try:
        d = int(delta)
        if d == 0:
            return ControlResult(True, 'Volume unchanged.')
        key = 'volume up' if d > 0 else 'volume down'
        _press_volume(key, abs(d))
        sign = '+' if d > 0 else ''
        return ControlResult(True, f"Volume changed {sign}{d}.")
    except Exception as e:
        return ControlResult(False, f"Failed to change volume ({e}).")


def set_volume_extreme(which: str) -> ControlResult:
    which = (which or '').lower().strip()
    try:
        if which in {'max', 'maximum', 'full'}:
            _press_volume('volume up', 60)
            return ControlResult(True, 'Volume set to max.')
        if which in {'min', 'minimum', 'zero', '0'}:
            _press_volume('volume down', 60)
            return ControlResult(True, 'Volume set to 0.')
        return ControlResult(False, 'Unknown volume extreme.')
    except Exception as e:
        return ControlResult(False, f"Failed to set volume ({e}).")


# ─────────────────────────────────────────────────────────────────
# BLUETOOTH
# ─────────────────────────────────────────────────────────────────
def toggle_bluetooth(enable: bool) -> ControlResult:
    """Toggle Bluetooth using the robust BluetoothManager (inspector-verified)."""
    import subprocess
    import sys
    import os

    if platform.system() != 'Windows':
        return ControlResult(False, 'Bluetooth control is only supported on Windows.')

    action = "on" if enable else "off"
    try:
        cmd_path = os.path.join(os.path.dirname(__file__), 'BluetoothManager.py')
        result = subprocess.run(
            [sys.executable, cmd_path, action],
            capture_output=True, text=True, timeout=20
        )
        output = result.stdout + result.stderr
        print(f"[BluetoothManager] {output}")

        if "error" in output.lower() and "no action" not in output.lower():
            return ControlResult(False, f"Bluetooth toggle had an issue: {output[:200]}")

        return ControlResult(True, f"Bluetooth turned {action} successfully.")
    except Exception as e:
        return ControlResult(False, f"Bluetooth manager failed: {e}")


# ─────────────────────────────────────────────────────────────────
# WIFI
# ─────────────────────────────────────────────────────────────────
def toggle_wifi(enable: bool) -> ControlResult:
    """Toggle Wi-Fi adapter on Windows using netsh."""
    if platform.system() != 'Windows':
        return ControlResult(False, 'Wi-Fi control is only supported on Windows.')

    action_cmd = 'enable' if enable else 'disable'
    action_word = 'enabled' if enable else 'disabled'

    try:
        # First, find the Wi-Fi adapter name
        result = subprocess.run(
            ['netsh', 'interface', 'show', 'interface'],
            capture_output=True, text=True, timeout=10
        )
        wifi_name = 'Wi-Fi'  # default
        for line in result.stdout.splitlines():
            if 'wi-fi' in line.lower() or 'wireless' in line.lower() or 'wlan' in line.lower():
                parts = line.split()
                if len(parts) >= 4:
                    wifi_name = ' '.join(parts[3:])
                    break

        cmd = ['netsh', 'interface', 'set', 'interface', wifi_name, action_cmd]
        result2 = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if result2.returncode == 0:
            return ControlResult(True, f"Wi-Fi {action_word} successfully.")

        # Try PowerShell fallback
        ps_cmd = (
            f"$radio = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]; "
            f"$r = [Windows.Devices.Radios.Radio]::GetRadiosAsync().GetAwaiter().GetResult() | "
            f"Where-Object Kind -eq ([Windows.Devices.Radios.RadioKind]::WiFi); "
            f"if($r) {{ $r.SetStateAsync([Windows.Devices.Radios.RadioState]::{'On' if enable else 'Off'}).GetAwaiter().GetResult() }}"
        )
        subprocess.run(['powershell', '-Command', ps_cmd], timeout=15)
        return ControlResult(True, f"Wi-Fi {action_word}.")

    except Exception as e:
        return ControlResult(False, f"Failed to toggle Wi-Fi: {e}")


# ─────────────────────────────────────────────────────────────────
# MOBILE HOTSPOT
# ─────────────────────────────────────────────────────────────────
def toggle_hotspot(enable: bool) -> ControlResult:
    """Toggle Mobile Hotspot on Windows 10/11 via PowerShell."""
    if platform.system() != 'Windows':
        return ControlResult(False, 'Hotspot control is only supported on Windows.')

    action_word = 'started' if enable else 'stopped'

    try:
        if enable:
            # Windows 10/11 Mobile Hotspot via PowerShell
            ps_cmd = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
$tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
$tetheringManager.StartTetheringAsync().GetAwaiter().GetResult()
"""
        else:
            ps_cmd = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
$tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
$tetheringManager.StopTetheringAsync().GetAwaiter().GetResult()
"""

        result = subprocess.run(
            ['powershell', '-Command', ps_cmd],
            capture_output=True, text=True, timeout=20
        )

        if result.returncode == 0:
            return ControlResult(True, f"Mobile hotspot {action_word}.")

        # If it failed but there's an error about admin privileges, attempt elevation
        if "administrator" in result.stderr.lower() or "administrator" in result.stdout.lower():
            safe_ps_cmd = ps_cmd.replace('"', '`"').replace('$', '`$').replace('\n', '; ')
            elevated_ps_cmd = (
                f"Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy Bypass', "
                f"'-Command', \"{safe_ps_cmd}\" "
                f"-Verb RunAs -WindowStyle Hidden"
            )
            subprocess.run(['powershell', '-Command', elevated_ps_cmd], timeout=15)
            return ControlResult(True, f"Elevated request to {action_word} mobile hotspot.")

        # Fallback: try hosted network (older method)
        if enable:
            subprocess.run(['netsh', 'wlan', 'set', 'hostednetwork', 'mode=allow'], timeout=10)
            r2 = subprocess.run(['netsh', 'wlan', 'start', 'hostednetwork'], capture_output=True, text=True, timeout=10)
            if 'started' in r2.stdout.lower():
                return ControlResult(True, "Mobile hotspot started.")
        else:
            r2 = subprocess.run(['netsh', 'wlan', 'stop', 'hostednetwork'], capture_output=True, text=True, timeout=10)
            if 'stopped' in r2.stdout.lower():
                return ControlResult(True, "Mobile hotspot stopped.")

        return ControlResult(True, f"Hotspot command sent - {action_word}.")

    except Exception as e:
        return ControlResult(False, f"Failed to toggle hotspot: {e}")


# ─────────────────────────────────────────────────────────────────
# POWER CONTROLS
# ─────────────────────────────────────────────────────────────────
def lock_screen() -> ControlResult:
    """Lock the Windows screen."""
    try:
        subprocess.Popen(['rundll32.exe', 'user32.dll,LockWorkStation'])
        return ControlResult(True, 'Screen locked.')
    except Exception as e:
        return ControlResult(False, f"Failed to lock screen: {e}")


def sleep_pc() -> ControlResult:
    """Put the PC to sleep."""
    try:
        subprocess.Popen(
            ['powershell', '-Command', 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)']
        )
        return ControlResult(True, 'System is going to sleep.')
    except Exception as e:
        return ControlResult(False, f"Failed to sleep: {e}")


def shutdown_pc(delay: int = 0) -> ControlResult:
    """Shutdown the PC."""
    try:
        subprocess.Popen(['shutdown', '/s', '/t', str(delay)])
        msg = f"System will shut down in {delay} seconds." if delay > 0 else "System is shutting down."
        return ControlResult(True, msg)
    except Exception as e:
        return ControlResult(False, f"Failed to shutdown: {e}")


def restart_pc(delay: int = 0) -> ControlResult:
    """Restart the PC."""
    try:
        subprocess.Popen(['shutdown', '/r', '/t', str(delay)])
        msg = f"System will restart in {delay} seconds." if delay > 0 else "System is restarting."
        return ControlResult(True, msg)
    except Exception as e:
        return ControlResult(False, f"Failed to restart: {e}")


def cancel_shutdown() -> ControlResult:
    """Cancel a pending shutdown or restart."""
    try:
        subprocess.run(['shutdown', '/a'], capture_output=True)
        return ControlResult(True, 'Shutdown cancelled.')
    except Exception as e:
        return ControlResult(False, f"Failed to cancel shutdown: {e}")


# ─────────────────────────────────────────────────────────────────
# NATURAL LANGUAGE PARSING
# ─────────────────────────────────────────────────────────────────
def parse_brightness_volume_query(query: str) -> Optional[Tuple[str, int | str]]:
    """Parse natural-language brightness/volume intents."""
    q = (query or '').lower()

    # brightness extremes
    if re.search(r'\b(brightness)\b', q):
        if re.search(r'\b(max|maximum|full)\b', q):
            return ('brightness_extreme', 'max')
        if re.search(r'\b(min|minimum|zero|0)\b', q) and re.search(r'\b(to|set)\b', q):
            return ('brightness_extreme', 'min')

        m = re.search(r'\b(set|to)\s+(?:brightness\s+)?(\d{1,3})\b', q)
        if m:
            return ('brightness_abs', int(m.group(2)))

        m = re.search(r'\b(increase|raise|up)\s+(?:the\s+)?brightness\s+(?:by\s+)?(\d{1,3})\b', q)
        if m:
            return ('brightness_delta', int(m.group(2)))

        m = re.search(r'\b(decrease|lower|down|reduce)\s+(?:the\s+)?brightness\s+(?:by\s+)?(\d{1,3})\b', q)
        if m:
            return ('brightness_delta', -int(m.group(2)))

    # volume
    if re.search(r'\b(volume)\b', q):
        if re.search(r'\b(mute|silent)\b', q):
            return ('volume_mute', 1)
        if re.search(r'\b(unmute)\b', q):
            return ('volume_unmute', 1)
        if re.search(r'\b(max|maximum|full)\b', q):
            return ('volume_extreme', 'max')
        if re.search(r'\b(min|minimum|zero|0)\b', q) and re.search(r'\b(to|set)\b', q):
            return ('volume_extreme', 'min')

        m = re.search(r'\b(increase|raise|up)\s+(?:the\s+)?volume\s+(?:by\s+)?(\d{1,3})\b', q)
        if m:
            return ('volume_delta', int(m.group(2)))

        m = re.search(r'\b(decrease|lower|down|reduce)\s+(?:the\s+)?volume\s+(?:by\s+)?(\d{1,3})\b', q)
        if m:
            return ('volume_delta', -int(m.group(2)))

        # "reduce volume to 0" etc
        if re.search(r'\b(to|set)\s+0\b', q):
            return ('volume_extreme', 'min')

    return None


def execute_parsed_control(parsed: Tuple[str, int | str]) -> ControlResult:
    kind, val = parsed
    if kind == 'brightness_abs':
        return set_brightness_abs(int(val))
    if kind == 'brightness_delta':
        return change_brightness(int(val))
    if kind == 'brightness_extreme':
        return set_brightness_abs(100 if val == 'max' else 0)
    if kind == 'volume_delta':
        return change_volume(int(val))
    if kind == 'volume_mute':
        return mute()
    if kind == 'volume_unmute':
        return unmute()
    if kind == 'volume_extreme':
        return set_volume_extreme(str(val))
    return ControlResult(False, 'Unknown control command.')
