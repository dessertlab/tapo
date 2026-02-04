# Tapo Control Script

A Python utility to control **Tapo P300 Smart Wi-Fi Power Strips** via the terminal. This script allows you to manage multiple P300 strips, control individual child sockets by nickname, and manage your device IP configuration dynamically. Please note that the actual smart power strip and the devices must be previously set via the Tapo app.

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/dessertlab/tapo.git](https://github.com/dessertlab/tapo.git)
cd tapo
```

### 2. Install Dependencies
This script requires the `tapo` Python library and `asyncio`.
```bash
pip install tapo
```

### 3. Configure Environment Variables
The script relies on environment variables for authentication and device discovery. You can set these manually or add them to your shell profile (e.g., `~/.bashrc`).

Run the following commands to set up your environment permanently:

```bash
# Set the path to this repository
echo 'export TAPO_PATH="'$PWD'"' >> ~/.bashrc

# Set your Tapo credentials
echo 'export TAPO_USERNAME="your_email@example.com"' >> ~/.bashrc
echo 'export TAPO_PASSWORD="your_password"' >> ~/.bashrc

# Set initial P300 IPs (comma-separated)
echo 'export TAPO_P300_IPS="192.168.1.50,192.168.1.51"' >> ~/.bashrc

# Create a convenient alias
echo 'alias tapo="python3 $TAPO_PATH/tapo_control.py"' >> ~/.bashrc

# Apply changes
source ~/.bashrc
```

---

## 🚀 Usage

Once the alias is set, you can use the `tapo` command directly.

### 1. Listing Devices
To see all connected P300 power strips and their child devices (sockets), use the list flag. This displays the **Nickname** you will use to control them.

```bash
tapo -l
```
*Output example:*
```text
=== P300 at 192.168.100.120 ===
  - Nickname: desk_lamp
    Device ID: 8012...
    State: ON

  - Nickname: monitor
    Device ID: 8013...
    State: OFF
```

### 2. Controlling Devices
You can turn devices **on**, **off**, or **reset** them (power cycle) using their nickname.

**Syntax:**
```bash
tapo <nickname> <action>
```

**Examples:**

* **Turn ON a device:**
    ```bash
    tapo desk_lamp on
    ```

* **Turn OFF a device:**
    ```bash
    tapo monitor off
    ```

* **Reset (Power Cycle) a device:**
    *Useful for rebooting stuck hardware. This turns the device OFF, waits 2 seconds, and turns it back ON.*
    ```bash
    tapo router reset
    ```

### 3. Managing Device IPs
You can add or remove P300 IP addresses from your configuration directly via the CLI.
*Note: This modifies your `~/.bashrc` and `/root/.bashrc` files.*

* **Add a new P300 IP:**
    ```bash
    tapo -a 192.168.1.55
    ```

* **Remove an old P300 IP:**
    ```bash
    tapo -r 192.168.1.55
    ```

---

## ❓ Help
To view the built-in help message and arguments:
```bash
tapo -h
```

---

### ⚠️ Troubleshooting
* **"No device with nickname found":** Ensure the nickname matches exactly what is shown in the `tapo -l` output or your Tapo mobile app.
* **Connection Errors:** Ensure the IP address in `TAPO_P300_IPS` is correct and the device is online.