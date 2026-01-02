#!/usr/bin/env python3
"""Test Sungrow power limit registers via Modbus TCP."""

import asyncio
from pymodbus.client import AsyncModbusTcpClient
import pymodbus

# === CONFIGURE THESE ===
HOST = "192.168.1.194"  # Your Sungrow IP
PORT = 502
SLAVE_ID = 1

# Register addresses (sg10rs map)
REG_POWER_LIMIT_TOGGLE = 5006   # 170=enabled, 85=disabled
REG_POWER_LIMIT_PERCENT = 5007  # Value / 10 = percent (1000 = 100%)

# pymodbus 3.9+ changed 'slave' parameter to 'device_id'
_pymodbus_version = tuple(int(x) for x in pymodbus.__version__.split(".")[:2])
SLAVE_PARAM = "device_id" if _pymodbus_version >= (3, 9) else "slave"
print(f"pymodbus version {pymodbus.__version__}, using '{SLAVE_PARAM}' parameter")


async def read_power_limit(client):
    """Read current power limit settings."""
    print("\n=== Reading Power Limit Registers ===")

    # Read toggle (holding register)
    result = await client.read_holding_registers(address=REG_POWER_LIMIT_TOGGLE, count=1, **{SLAVE_PARAM: SLAVE_ID})
    if not result.isError():
        toggle = result.registers[0]
        print(f"Register {REG_POWER_LIMIT_TOGGLE} (toggle): {toggle} ({'ENABLED' if toggle == 170 else 'DISABLED' if toggle == 85 else 'UNKNOWN'})")
    else:
        print(f"Failed to read toggle: {result}")

    # Read percent (holding register)
    result = await client.read_holding_registers(address=REG_POWER_LIMIT_PERCENT, count=1, **{SLAVE_PARAM: SLAVE_ID})
    if not result.isError():
        raw = result.registers[0]
        percent = raw / 10
        print(f"Register {REG_POWER_LIMIT_PERCENT} (percent): {raw} raw = {percent}%")
    else:
        print(f"Failed to read percent: {result}")


async def set_power_limit(client, percent: int):
    """Set power limit percentage (0-100)."""
    value = percent * 10  # Scale for register
    print(f"\n=== Setting Power Limit to {percent}% (writing {value} to {REG_POWER_LIMIT_PERCENT}) ===")

    # First enable power limiting
    result = await client.write_register(address=REG_POWER_LIMIT_TOGGLE, value=170, **{SLAVE_PARAM: SLAVE_ID})
    if result.isError():
        print(f"Failed to enable power limit: {result}")
        return False
    print(f"Enabled power limiting (wrote 170 to {REG_POWER_LIMIT_TOGGLE})")

    # Then set percentage
    result = await client.write_register(address=REG_POWER_LIMIT_PERCENT, value=value, **{SLAVE_PARAM: SLAVE_ID})
    if result.isError():
        print(f"Failed to set power limit: {result}")
        return False
    print(f"Set power limit to {percent}% (wrote {value} to {REG_POWER_LIMIT_PERCENT})")

    return True


async def main():
    print(f"Connecting to Sungrow at {HOST}:{PORT}...")
    client = AsyncModbusTcpClient(HOST, port=PORT, timeout=10)

    if not await client.connect():
        print("Failed to connect!")
        return

    print("Connected!")

    try:
        # Read current state
        await read_power_limit(client)

        # Menu
        while True:
            print("\n=== Options ===")
            print("1. Read power limit")
            print("2. Set power limit to 0% (CURTAIL)")
            print("3. Set power limit to 100% (RESTORE)")
            print("4. Set custom power limit %")
            print("q. Quit")

            choice = input("\nChoice: ").strip().lower()

            if choice == '1':
                await read_power_limit(client)
            elif choice == '2':
                await set_power_limit(client, 0)
                await asyncio.sleep(1)
                await read_power_limit(client)
            elif choice == '3':
                await set_power_limit(client, 100)
                await asyncio.sleep(1)
                await read_power_limit(client)
            elif choice == '4':
                pct = int(input("Enter percentage (0-100): "))
                await set_power_limit(client, pct)
                await asyncio.sleep(1)
                await read_power_limit(client)
            elif choice == 'q':
                break
            else:
                print("Invalid choice")

    finally:
        client.close()
        print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(main())
