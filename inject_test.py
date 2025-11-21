import hid
import struct
import time
import zlib

# Constants
REPORT_ID_CONFIG = 100
CONFIG_VERSION = 18
CONFIG_COMMAND_INJECT_INPUT = 26
CONFIG_SIZE = 32
USAGE_PAGE_VENDOR = 0xFF00

# Usage IDs (from our_descriptor.cc / standard HID)
# Generic Desktop Page (0x01)
USAGE_X = 0x00010030
USAGE_Y = 0x00010031
USAGE_WHEEL = 0x00010038
# Button Page (0x09)
USAGE_BUTTON_1 = 0x00090001 # Left Click
USAGE_BUTTON_2 = 0x00090002 # Right Click

def find_device():
    for d in hid.enumerate():
        if d['usage_page'] == USAGE_PAGE_VENDOR:
            return hid.device()
            try:
                dev = hid.device()
                dev.open_path(d['path'])
                return dev
            except Exception as e:
                print(f"Failed to open device: {e}")
    return None

def create_inject_packet(usage, value):
    # Structure: Version (1), Command (1), Data (26), CRC (4)
    # Data for INJECT_INPUT: Usage (4), Value (4), Padding (18)
    
    data = struct.pack("<BBIi", CONFIG_VERSION, CONFIG_COMMAND_INJECT_INPUT, usage, value)
    data += b'\x00' * (CONFIG_SIZE - 4 - len(data)) # Pad to 28 bytes
    
    # Calculate CRC32 over the first 28 bytes
    crc = zlib.crc32(data) & 0xFFFFFFFF
    
    packet = data + struct.pack("<I", crc)
    return packet

def send_inject(dev, usage, value):
    packet = create_inject_packet(usage, value)
    # Prepend Report ID
    report = bytes([REPORT_ID_CONFIG]) + packet
    dev.write(report)

def main():
    print("Looking for device...")
    dev = find_device()
    if not dev:
        # Try to find by VID/PID if usage_page fails (some platforms don't report it)
        # Assuming VID/PID from RP2040_host.py
        try:
            dev = hid.device()
            dev.open(0x046D, 0xC08B)
        except:
            print("Device not found!")
            return

    print("Device found!")

    try:
        print("Moving mouse right...")
        for _ in range(50):
            send_inject(dev, USAGE_X, 10)
            time.sleep(0.01)
        
        print("Moving mouse left...")
        for _ in range(50):
            send_inject(dev, USAGE_X, -10)
            time.sleep(0.01)

        print("Clicking left button...")
        send_inject(dev, USAGE_BUTTON_1, 1) # Press
        time.sleep(0.1)
        send_inject(dev, USAGE_BUTTON_1, 0) # Release
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        dev.close()

if __name__ == "__main__":
    main()
