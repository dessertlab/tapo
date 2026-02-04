#!/usr/bin/env python3

import argparse
import asyncio
import os
from tapo import ApiClient

###############################################################################
# Configuration
###############################################################################
BASHRC_PATHS = ["/home/test/.bashrc", "/root/.bashrc"]


###############################################################################
# 1) Helpers to modify TAPO_P300_IPS in .bashrc files (add/remove)
###############################################################################

def add_ip_to_line(original_line: str, new_ip: str) -> (str, bool):
    """
    Given a line like:
      export TAPO_P300_IPS="192.168.100.120,192.168.100.121"
    parse out the IPs, add 'new_ip' if not present, and return the updated line.
    
    Returns (updated_line, changed_flag).
      updated_line: the new line (possibly the same if no changes)
      changed_flag: True if a change was made, otherwise False.
    """
    line = original_line.strip()

    # e.g., line = export TAPO_P300_IPS="192.168.100.120,192.168.100.121"
    if not line.startswith("export TAPO_P300_IPS="):
        return (original_line, False)

    try:
        # Split on '=', then parse what's inside the quotes
        _, after = line.split("=", 1)  # "export TAPO_P300_IPS", "\"192.168.100.120,192.168.100.121\""
        after = after.strip()
        if after.startswith("\"") and after.endswith("\""):
            ip_string = after[1:-1]  # everything inside quotes
        else:
            ip_string = after

        existing_ips = [ip.strip() for ip in ip_string.split(",") if ip.strip()]

        if new_ip not in existing_ips:
            existing_ips.append(new_ip)
            new_line = f'export TAPO_P300_IPS="{",".join(existing_ips)}"\n'
            return (new_line, True)
        else:
            # No change needed, IP already present
            return (original_line, False)
    except Exception:
        # If something fails in parsing, just return original line
        return (original_line, False)


def remove_ip_from_line(original_line: str, remove_ip: str) -> (str, bool):
    """
    Given a line like:
      export TAPO_P300_IPS="192.168.100.120,192.168.100.231"
    parse out the IPs, remove 'remove_ip' if present, and return the updated line.

    Returns (updated_line, changed_flag).
      updated_line: the new line (possibly empty if no IPs remain)
      changed_flag: True if a change was made, otherwise False
    """
    line = original_line.strip()

    if not line.startswith("export TAPO_P300_IPS="):
        return (original_line, False)

    try:
        _, after = line.split("=", 1)
        after = after.strip()
        if after.startswith("\"") and after.endswith("\""):
            ip_string = after[1:-1]
        else:
            ip_string = after

        existing_ips = [ip.strip() for ip in ip_string.split(",") if ip.strip()]

        if remove_ip in existing_ips:
            existing_ips.remove(remove_ip)
            # If no IPs left, let's keep the line but empty, or we could remove it entirely
            # For clarity, let's keep an empty string
            new_line = f'export TAPO_P300_IPS="{",".join(existing_ips)}"\n'
            return (new_line, True)
        else:
            # IP not in list, no changes
            return (original_line, False)
    except Exception:
        # If parse fails, return original
        return (original_line, False)


def ensure_tapo_line_exists(lines):
    """
    Ensures there's at least one line with 'export TAPO_P300_IPS="' in the lines.
    If none is found, we add a new blank line 'export TAPO_P300_IPS=""' at the end.
    """
    found_line = False
    for line in lines:
        if line.strip().startswith("export TAPO_P300_IPS="):
            found_line = True
            break

    if not found_line:
        lines.append('export TAPO_P300_IPS=""\n')
    return lines


def update_bashrc_file(bashrc_path: str, ip_value: str, mode: str) -> bool:
    """
    Updates a single bashrc file for adding or removing an IP address.
    mode: 'add' or 'remove'
    Returns True if changes were written, otherwise False.
    """
    changed = False
    lines = []

    # Read the file if it exists
    try:
        with open(bashrc_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    # Ensure we have at least one line with "export TAPO_P300_IPS=",
    # so we can add/remove from that line
    lines = ensure_tapo_line_exists(lines)

    new_lines = []
    for line in lines:
        if mode == 'add':
            updated_line, was_changed = add_ip_to_line(line, ip_value)
        else:  # mode == 'remove'
            updated_line, was_changed = remove_ip_from_line(line, ip_value)

        if was_changed:
            changed = True
            new_lines.append(updated_line)
        else:
            new_lines.append(line)

    if changed:
        try:
            with open(bashrc_path, "w") as f:
                f.writelines(new_lines)
            print(f"[{mode.upper()}] Updated TAPO_P300_IPS in {bashrc_path}")
        except Exception as e:
            print(f"[{mode.upper()}] Error writing to {bashrc_path}: {e}")
            return False
    else:
        print(f"[{mode.upper()}] No changes made to {bashrc_path} (IP '{ip_value}' might already be in desired state).")

    return changed


def update_bashrc_files(ip_value: str, mode: str):
    """
    Calls update_bashrc_file(...) for each file in BASHRC_PATHS with the given mode.
    mode can be 'add' or 'remove'.
    """
    for path in BASHRC_PATHS:
        update_bashrc_file(path, ip_value, mode)


###############################################################################
# 2) Tapo listing & control functionality
###############################################################################

async def list_all_devices(client, p300_ips):
    """Lists all child devices across all given P300 IPs."""
    for ip_address in p300_ips:
        print(f"\n=== P300 at {ip_address} ===")
        try:
            power_strip = await client.p300(ip_address)
            child_device_list = await power_strip.get_child_device_list()
            if not child_device_list:
                print("  No child devices found.")
                continue

            for child in child_device_list:
                state_str = "ON" if child.device_on else "OFF"
                print(f"  - Nickname: {child.nickname}")
                print(f"    Device ID: {child.device_id}")
                print(f"    State: {state_str}\n")
        except Exception as e:
            print(f"  Warning: Could not connect to P300 at {ip_address} - {e}")


async def control_device(client, p300_ips, child_nickname, action):
    """
    Search all P300s for a matching child nickname; turn it on/off/reset if found.
    If action is 'reset', forcibly power-cycle the device (off -> wait -> on).
    """
    found_device = False

    for ip_address in p300_ips:
        try:
            power_strip = await client.p300(ip_address)
            child_device_list = await power_strip.get_child_device_list()

            for child in child_device_list:
                if child.nickname == child_nickname:
                    # Found a match
                    found_device = True
                    print(f"Found device '{child.nickname}' on P300 at {ip_address}.")

                    plug = await power_strip.plug(device_id=child.device_id)
                    is_on = child.device_on

                    if action == "reset":
                        # Force power-cycle: off -> wait -> on
                        print(f"Resetting '{child.nickname}' (off -> on)...")
                        await plug.off()
                        await asyncio.sleep(2)  # wait 2s
                        await plug.on()
                        await asyncio.sleep(1)  # optional second wait
                    else:
                        # 'on' or 'off'
                        if action == "on" and is_on:
                            print(f"'{child.nickname}' is already ON.")
                            return
                        elif action == "off" and not is_on:
                            print(f"'{child.nickname}' is already OFF.")
                            return

                        if action == "on":
                            print(f"Turning '{child.nickname}' ON...")
                            await plug.on()
                        else:  # action == "off"
                            print(f"Turning '{child.nickname}' OFF...")
                            await plug.off()

                        await asyncio.sleep(1)  # short wait before final check

                    # Print final state
                    new_info = await plug.get_device_info()
                    new_state = "ON" if new_info.device_on else "OFF"
                    print(f"New state for '{child.nickname}': {new_state}")

                    # Exit after controlling the first matching device
                    return
        except Exception as e:
            print(f"Warning: Could not connect to P300 at {ip_address} - {e}")

    if not found_device:
        print(f"No device with nickname '{child_nickname}' found on any known P300 IP.")
        print("Check your nickname spelling or rename it in the Tapo app.")


###############################################################################
# 3) Main entrypoint / argument parsing
###############################################################################

async def main():
    parser = argparse.ArgumentParser(
        description="Control multiple Tapo P300 strips by nickname, list them, add IPs, or remove IPs from .bashrc."
    )
    parser.add_argument(
        "-l", 
        "--list", 
        action="store_true",
        help="List all child devices across all configured Tapo P300 IPs and exit."
    )
    parser.add_argument(
        "-a",
        "--add",
        metavar="NEW_IP",
        help="Add a new IP to the TAPO_P300_IPS in /home/test/.bashrc and /root/.bashrc, then exit."
    )
    parser.add_argument(
        "-r",
        "--remove",
        metavar="OLD_IP",
        help="Remove an IP from TAPO_P300_IPS in /home/test/.bashrc and /root/.bashrc, then exit."
    )
    parser.add_argument(
        "child_nickname", 
        nargs="?",
        help="Nickname of the child device (e.g. 'kriakv260')."
    )
    parser.add_argument(
        "action", 
        nargs="?", 
        choices=["on", "off", "reset"],
        help="Desired action: 'on', 'off', or 'reset' (force off->on)."
    )
    args = parser.parse_args()

    # Handle the --add case
    if args.add:
        new_ip = args.add.strip()
        print(f"Adding IP '{new_ip}' to environment in {', '.join(BASHRC_PATHS)}...")
        update_bashrc_files(new_ip, 'add')
        return  # Exit after adding

    # Handle the --remove case
    if args.remove:
        rm_ip = args.remove.strip()
        print(f"Removing IP '{rm_ip}' from environment in {', '.join(BASHRC_PATHS)}...")
        update_bashrc_files(rm_ip, 'remove')
        return  # Exit after removing

    # 1) Read Tapo credentials from environment
    tapo_username = os.getenv("TAPO_USERNAME")
    tapo_password = os.getenv("TAPO_PASSWORD")
    if not tapo_username or not tapo_password:
        print("Error: Please set TAPO_USERNAME and TAPO_PASSWORD in your environment.")
        return

    # 2) Read list of P300 IPs from environment
    p300_ips_str = os.getenv("TAPO_P300_IPS")
    if not p300_ips_str:
        print("Error: Please set TAPO_P300_IPS in your environment, e.g. '192.168.100.120,192.168.100.121'")
        return
    p300_ips = [ip.strip() for ip in p300_ips_str.split(",") if ip.strip()]
    if not p300_ips:
        print("Error: No valid IPs found in TAPO_P300_IPS environment variable.")
        return

    # 3) Create a Tapo API client (same account for all P300s)
    client = ApiClient(tapo_username, tapo_password)

    # 4) If --list is used, just list everything and exit
    if args.list:
        print("Listing all devices across configured P300 IPs...")
        await list_all_devices(client, p300_ips)
        return

    # 5) Otherwise, we need child_nickname + action
    if not args.child_nickname or not args.action:
        parser.print_help()
        return

    # 6) Perform the desired on/off/reset action
    await control_device(client, p300_ips, args.child_nickname, args.action)


if __name__ == "__main__":
    asyncio.run(main())
