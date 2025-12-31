# app/sigenergy_modbus.py
"""Sigenergy Modbus TCP client for Flask.

Provides real-time power data from Sigenergy inverters via Modbus TCP.
Based on the Home Assistant PowerSync integration's Sigenergy controller.
"""

import logging
from typing import Optional
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

logger = logging.getLogger(__name__)


class SigenergyModbusClient:
    """Client for reading Sigenergy inverter data via Modbus TCP."""

    # Modbus register addresses (documentation addresses - 40001 for pymodbus)
    # Holding registers (read/write) - base 40001
    REG_GRID_EXPORT_LIMIT = 37  # 40038 - Grid export limit (U32, gain 1000)

    # Input registers (read-only) - base 30001
    REG_PV_POWER = 34           # 30035 - PV power (S32, gain 1000, kW)
    REG_ACTIVE_POWER = 30       # 30031 - Active power (S32, gain 1000, kW)
    REG_ESS_SOC = 13            # 30014 - Battery SOC (U16, gain 10, %)
    REG_GRID_SENSOR_POWER = 4   # 30005 - Grid sensor active power (S32, gain 1000, kW)
    REG_EMS_WORK_MODE = 2       # 30003 - EMS work mode (U16)

    # Constants
    GAIN_POWER = 1000  # kW → scaled value
    GAIN_SOC = 10      # % → scaled value
    EXPORT_LIMIT_UNLIMITED = 0xFFFFFFFE

    def __init__(self, host: str, port: int = 502, slave_id: int = 1):
        """Initialize Sigenergy Modbus client.

        Args:
            host: IP address of Sigenergy system
            port: Modbus TCP port (default: 502)
            slave_id: Modbus slave ID (default: 1)
        """
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self._client: Optional[ModbusTcpClient] = None

    def connect(self) -> bool:
        """Connect to the Sigenergy system."""
        try:
            if self._client and self._client.connected:
                return True

            self._client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=10,
            )

            connected = self._client.connect()
            if connected:
                logger.info(f"Connected to Sigenergy at {self.host}:{self.port}")
            else:
                logger.error(f"Failed to connect to Sigenergy at {self.host}:{self.port}")

            return connected

        except Exception as e:
            logger.error(f"Error connecting to Sigenergy: {e}")
            return False

    def disconnect(self):
        """Disconnect from the Sigenergy system."""
        if self._client:
            self._client.close()
            self._client = None
        logger.debug(f"Disconnected from Sigenergy at {self.host}")

    def _to_signed32(self, high: int, low: int) -> int:
        """Convert two unsigned 16-bit registers to signed 32-bit."""
        value = (high << 16) | low
        if value >= 0x80000000:
            value -= 0x100000000
        return value

    def _to_unsigned32(self, high: int, low: int) -> int:
        """Convert two unsigned 16-bit registers to unsigned 32-bit."""
        return (high << 16) | low

    def _read_input_registers(self, address: int, count: int = 1) -> Optional[list]:
        """Read values from input registers."""
        if not self._client or not self._client.connected:
            if not self.connect():
                return None

        try:
            result = self._client.read_input_registers(
                address=address,
                count=count,
                slave=self.slave_id,
            )

            if result.isError():
                logger.debug(f"Modbus read error at input register {address}: {result}")
                return None

            return result.registers

        except ModbusException as e:
            logger.debug(f"Modbus exception reading input register {address}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error reading input register {address}: {e}")
            return None

    def _read_holding_registers(self, address: int, count: int = 1) -> Optional[list]:
        """Read values from holding registers."""
        if not self._client or not self._client.connected:
            if not self.connect():
                return None

        try:
            result = self._client.read_holding_registers(
                address=address,
                count=count,
                slave=self.slave_id,
            )

            if result.isError():
                logger.debug(f"Modbus read error at holding register {address}: {result}")
                return None

            return result.registers

        except ModbusException as e:
            logger.debug(f"Modbus exception reading holding register {address}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error reading holding register {address}: {e}")
            return None

    def get_live_status(self) -> dict:
        """Get current power status from Sigenergy system.

        Returns:
            dict with power data matching Tesla status format:
            - solar_power: W (positive = generating)
            - battery_power: W (positive = discharging, negative = charging)
            - grid_power: W (positive = importing, negative = exporting)
            - load_power: W (home consumption)
            - percentage_charged: % (battery SOC)
            - is_curtailed: bool (export limit active)
        """
        try:
            if not self.connect():
                return {"error": "Failed to connect to Sigenergy"}

            result = {}

            # Read PV power (S32, 2 registers) - solar generation
            pv_regs = self._read_input_registers(self.REG_PV_POWER, 2)
            if pv_regs and len(pv_regs) >= 2:
                pv_power_kw = self._to_signed32(pv_regs[0], pv_regs[1]) / self.GAIN_POWER
                result['solar_power'] = pv_power_kw * 1000  # Convert to W
            else:
                result['solar_power'] = 0

            # Read grid sensor power (S32, 2 registers)
            # Positive = importing from grid, negative = exporting to grid
            grid_regs = self._read_input_registers(self.REG_GRID_SENSOR_POWER, 2)
            if grid_regs and len(grid_regs) >= 2:
                grid_power_kw = self._to_signed32(grid_regs[0], grid_regs[1]) / self.GAIN_POWER
                result['grid_power'] = grid_power_kw * 1000  # Convert to W
            else:
                result['grid_power'] = 0

            # Read battery SOC (U16)
            soc_regs = self._read_input_registers(self.REG_ESS_SOC, 1)
            if soc_regs:
                result['percentage_charged'] = soc_regs[0] / self.GAIN_SOC
            else:
                result['percentage_charged'] = 0

            # Read active power (S32, 2 registers) - total system power
            # This can help derive battery power
            active_regs = self._read_input_registers(self.REG_ACTIVE_POWER, 2)
            if active_regs and len(active_regs) >= 2:
                active_power_kw = self._to_signed32(active_regs[0], active_regs[1]) / self.GAIN_POWER
                active_power_w = active_power_kw * 1000
            else:
                active_power_w = 0

            # Calculate battery power from energy balance:
            # Solar + Battery + Grid = Load
            # Battery = Load - Solar - Grid (but we need to derive load)
            # Active power is typically the inverter output which equals load
            # Battery = Active - Solar - Grid (when active is load)
            # Or we can derive: Load = Solar + Grid - Battery

            # For Sigenergy, active_power seems to be inverter AC output
            # Let's calculate battery as: Battery = Grid + Solar - Load
            # where Load ~= Active Power (home consumption through inverter)

            # Simplified: Battery Power = -(Grid + Solar - Active)
            # Positive = discharging, Negative = charging
            solar_w = result.get('solar_power', 0)
            grid_w = result.get('grid_power', 0)

            # Load power is what the home consumes
            # Load = Solar - Grid export + Grid import + Battery discharge
            # Approximation: Load = Active power (inverter output to home)
            result['load_power'] = abs(active_power_w) if active_power_w else abs(solar_w - grid_w)

            # Battery power: positive = discharging, negative = charging
            # Energy balance: Solar + Grid_import + Battery_discharge = Load + Grid_export
            # Battery = Load - Solar + Grid (where grid is positive for import, negative for export)
            result['battery_power'] = result['load_power'] - solar_w + grid_w

            # Check if export is curtailed (export limit set to 0 or very low)
            export_regs = self._read_holding_registers(self.REG_GRID_EXPORT_LIMIT, 2)
            if export_regs and len(export_regs) >= 2:
                export_limit = self._to_unsigned32(export_regs[0], export_regs[1])
                result['is_curtailed'] = export_limit < 100  # Less than 0.1 kW
                if export_limit < self.EXPORT_LIMIT_UNLIMITED:
                    result['export_limit_kw'] = export_limit / self.GAIN_POWER
            else:
                result['is_curtailed'] = False

            # Add metadata
            result['battery_system'] = 'sigenergy'
            result['host'] = self.host

            logger.debug(f"Sigenergy status: Solar={result['solar_power']}W Grid={result['grid_power']}W "
                        f"Battery={result['battery_power']}W Load={result['load_power']}W SOC={result['percentage_charged']}%")

            return result

        except Exception as e:
            logger.error(f"Error getting Sigenergy status: {e}")
            return {"error": str(e)}

        finally:
            self.disconnect()


def get_sigenergy_modbus_client(user) -> Optional[SigenergyModbusClient]:
    """Create a SigenergyModbusClient from a user object.

    Args:
        user: User model instance with Sigenergy Modbus settings

    Returns:
        SigenergyModbusClient instance or None if not configured
    """
    if not user.sigenergy_dc_curtailment_enabled or not user.sigenergy_modbus_host:
        return None

    return SigenergyModbusClient(
        host=user.sigenergy_modbus_host,
        port=user.sigenergy_modbus_port or 502,
        slave_id=user.sigenergy_modbus_slave_id or 1,
    )
