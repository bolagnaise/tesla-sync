"""Config flow for Tesla Sync integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_AMBER_API_TOKEN,
    CONF_AMBER_SITE_ID,
    CONF_AMBER_FORECAST_TYPE,
    CONF_SOLAR_CURTAILMENT_ENABLED,
    CONF_TESLEMETRY_API_TOKEN,
    CONF_TESLA_ENERGY_SITE_ID,
    CONF_AUTO_SYNC_ENABLED,
    CONF_DEMAND_CHARGE_ENABLED,
    CONF_DEMAND_CHARGE_RATE,
    CONF_DEMAND_CHARGE_START_TIME,
    CONF_DEMAND_CHARGE_END_TIME,
    CONF_DEMAND_CHARGE_DAYS,
    CONF_DEMAND_CHARGE_BILLING_DAY,
    CONF_DEMAND_CHARGE_APPLY_TO,
    CONF_DAILY_SUPPLY_CHARGE,
    CONF_MONTHLY_SUPPLY_CHARGE,
    CONF_TESLA_API_PROVIDER,
    TESLA_PROVIDER_TESLEMETRY,
    TESLA_PROVIDER_FLEET_API,
    AMBER_API_BASE_URL,
    TESLEMETRY_API_BASE_URL,
    FLEET_API_BASE_URL,
    CONF_AEMO_SPIKE_ENABLED,
    CONF_AEMO_REGION,
    CONF_AEMO_SPIKE_THRESHOLD,
    AEMO_REGIONS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_amber_token(hass: HomeAssistant, api_token: str) -> dict[str, Any]:
    """Validate the Amber API token."""
    session = async_get_clientsession(hass)
    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        async with session.get(
            f"{AMBER_API_BASE_URL}/sites",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == 200:
                sites = await response.json()
                if sites and len(sites) > 0:
                    return {
                        "success": True,
                        "sites": sites,
                    }
                else:
                    return {"success": False, "error": "no_sites"}
            elif response.status == 401:
                return {"success": False, "error": "invalid_auth"}
            else:
                return {"success": False, "error": "cannot_connect"}
    except aiohttp.ClientError:
        return {"success": False, "error": "cannot_connect"}
    except Exception as err:
        _LOGGER.exception("Unexpected error validating Amber token: %s", err)
        return {"success": False, "error": "unknown"}


async def validate_teslemetry_token(
    hass: HomeAssistant, api_token: str
) -> dict[str, Any]:
    """Validate the Teslemetry API token and get sites."""
    session = async_get_clientsession(hass)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    try:
        async with session.get(
            f"{TESLEMETRY_API_BASE_URL}/api/1/products",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get("response", [])

                # Filter for energy sites
                energy_sites = [
                    p for p in products
                    if "energy_site_id" in p
                ]

                if energy_sites:
                    return {
                        "success": True,
                        "sites": energy_sites,
                    }
                else:
                    return {"success": False, "error": "no_energy_sites"}
            elif response.status == 401:
                return {"success": False, "error": "invalid_auth"}
            else:
                error_text = await response.text()
                _LOGGER.error("Teslemetry API error %s: %s", response.status, error_text)
                return {"success": False, "error": "cannot_connect"}
    except aiohttp.ClientError as err:
        _LOGGER.exception("Error connecting to Teslemetry API: %s", err)
        return {"success": False, "error": "cannot_connect"}
    except Exception as err:
        _LOGGER.exception("Unexpected error validating Teslemetry token: %s", err)
        return {"success": False, "error": "unknown"}


async def validate_fleet_api_token(
    hass: HomeAssistant, api_token: str
) -> dict[str, Any]:
    """Validate the Fleet API token and get sites."""
    session = async_get_clientsession(hass)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    try:
        async with session.get(
            f"{FLEET_API_BASE_URL}/api/1/products",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get("response", [])

                # Filter for energy sites
                energy_sites = [
                    p for p in products
                    if "energy_site_id" in p
                ]

                if energy_sites:
                    return {
                        "success": True,
                        "sites": energy_sites,
                    }
                else:
                    return {"success": False, "error": "no_energy_sites"}
            elif response.status == 401:
                return {"success": False, "error": "invalid_auth"}
            else:
                error_text = await response.text()
                _LOGGER.error("Fleet API error %s: %s", response.status, error_text)
                return {"success": False, "error": "cannot_connect"}
    except aiohttp.ClientError as err:
        _LOGGER.exception("Error connecting to Fleet API: %s", err)
        return {"success": False, "error": "cannot_connect"}
    except Exception as err:
        _LOGGER.exception("Unexpected error validating Fleet API token: %s", err)
        return {"success": False, "error": "unknown"}


class TeslaAmberSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesla Sync."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._amber_data: dict[str, Any] = {}
        self._amber_sites: list[dict[str, Any]] = []
        self._teslemetry_data: dict[str, Any] = {}
        self._tesla_sites: list[dict[str, Any]] = []
        self._site_data: dict[str, Any] = {}
        self._tesla_fleet_available: bool = False
        self._tesla_fleet_token: str | None = None
        self._selected_provider: str | None = None
        self._aemo_only_mode: bool = False  # True if using AEMO spike only (no Amber)
        self._aemo_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choose mode."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return await self.async_step_mode_selection()

    async def async_step_mode_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle mode selection - Amber TOU sync or AEMO spike only."""
        if user_input is not None:
            mode = user_input.get("mode", "amber")

            if mode == "aemo_only":
                # AEMO-only mode: skip Amber, go to AEMO config then Tesla
                self._aemo_only_mode = True
                self._amber_data = {}  # No Amber API token needed
                return await self.async_step_aemo_config()
            else:
                # Amber mode: standard flow with optional AEMO
                self._aemo_only_mode = False
                return await self.async_step_amber()

        return self.async_show_form(
            step_id="mode_selection",
            data_schema=vol.Schema({
                vol.Required("mode", default="amber"): vol.In({
                    "amber": "Amber TOU Sync (Real-time prices + optional spike detection)",
                    "aemo_only": "AEMO Spike Detection Only (No Amber subscription needed)",
                }),
            }),
            description_placeholders={
                "amber_desc": "Full price sync with Amber Electric",
                "aemo_desc": "Spike detection using AEMO wholesale prices",
            },
        )

    async def async_step_amber(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Amber API token entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate Amber API token
            validation_result = await validate_amber_token(
                self.hass, user_input[CONF_AMBER_API_TOKEN]
            )

            if validation_result["success"]:
                self._amber_data = user_input
                self._amber_sites = validation_result.get("sites", [])
                # Go to AEMO config (optional for Amber mode)
                return await self.async_step_aemo_config()
            else:
                errors["base"] = validation_result.get("error", "unknown")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_AMBER_API_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="amber",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "amber_url": "https://app.amber.com.au/developers",
            },
        )

    async def async_step_tesla_provider(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let user choose between Tesla Fleet and Teslemetry."""
        # Check if Tesla Fleet integration is configured and loaded
        self._tesla_fleet_available = False
        self._tesla_fleet_token = None

        tesla_fleet_entries = self.hass.config_entries.async_entries("tesla_fleet")
        if tesla_fleet_entries:
            for tesla_entry in tesla_fleet_entries:
                if tesla_entry.state == ConfigEntryState.LOADED:
                    try:
                        if CONF_TOKEN in tesla_entry.data:
                            token_data = tesla_entry.data[CONF_TOKEN]
                            if CONF_ACCESS_TOKEN in token_data:
                                self._tesla_fleet_token = token_data[CONF_ACCESS_TOKEN]
                                self._tesla_fleet_available = True
                                _LOGGER.info("Tesla Fleet integration detected and available")
                                break
                    except Exception as e:
                        _LOGGER.warning("Failed to extract tokens from Tesla Fleet integration: %s", e)

        # If Tesla Fleet is not available, skip provider selection and go to Teslemetry (required)
        if not self._tesla_fleet_available:
            _LOGGER.info("Tesla Fleet not available - Teslemetry required")
            return await self.async_step_teslemetry()

        # Tesla Fleet is available - let user choose
        if user_input is not None:
            self._selected_provider = user_input[CONF_TESLA_API_PROVIDER]

            if self._selected_provider == TESLA_PROVIDER_FLEET_API:
                # User chose Fleet API - validate and get sites
                _LOGGER.info("User selected Tesla Fleet API")
                validation_result = await validate_fleet_api_token(
                    self.hass, self._tesla_fleet_token
                )

                if validation_result["success"]:
                    # Store empty Teslemetry token (we'll use Fleet API in __init__.py)
                    self._teslemetry_data = {CONF_TESLEMETRY_API_TOKEN: ""}
                    self._tesla_sites = validation_result.get("sites", [])
                    return await self.async_step_site_selection()
                else:
                    # Fleet API validation failed - show error
                    errors = {"base": validation_result.get("error", "unknown")}
                    return self.async_show_form(
                        step_id="tesla_provider",
                        data_schema=vol.Schema({
                            vol.Required(CONF_TESLA_API_PROVIDER, default=TESLA_PROVIDER_TESLEMETRY): vol.In({
                                TESLA_PROVIDER_FLEET_API: "Tesla Fleet API (Free - uses existing Tesla Fleet integration)",
                                TESLA_PROVIDER_TESLEMETRY: "Teslemetry (~$3/month - proxy service)",
                            }),
                        }),
                        errors=errors,
                    )
            else:
                # User chose Teslemetry
                _LOGGER.info("User selected Teslemetry")
                return await self.async_step_teslemetry()

        # Show provider selection form
        return self.async_show_form(
            step_id="tesla_provider",
            data_schema=vol.Schema({
                vol.Required(CONF_TESLA_API_PROVIDER, default=TESLA_PROVIDER_FLEET_API): vol.In({
                    TESLA_PROVIDER_FLEET_API: "Tesla Fleet API (Free - uses existing Tesla Fleet integration)",
                    TESLA_PROVIDER_TESLEMETRY: "Teslemetry (~$3/month - proxy service)",
                }),
            }),
            description_placeholders={
                "fleet_detected": "✓ Tesla Fleet integration detected!",
            },
        )

    async def async_step_teslemetry(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Teslemetry API token entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            teslemetry_token = user_input.get(CONF_TESLEMETRY_API_TOKEN, "").strip()

            if teslemetry_token:
                validation_result = await validate_teslemetry_token(
                    self.hass, teslemetry_token
                )

                if validation_result["success"]:
                    self._teslemetry_data = user_input
                    self._tesla_sites = validation_result.get("sites", [])
                    return await self.async_step_site_selection()
                else:
                    errors["base"] = validation_result.get("error", "unknown")
            else:
                errors["base"] = "no_token_provided"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TESLEMETRY_API_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="teslemetry",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "teslemetry_url": "https://teslemetry.com",
            },
        )

    async def async_step_aemo_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle AEMO spike detection configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate AEMO region is selected if enabled
            aemo_enabled = user_input.get(CONF_AEMO_SPIKE_ENABLED, False)

            if aemo_enabled:
                region = user_input.get(CONF_AEMO_REGION)
                if not region:
                    errors["base"] = "aemo_region_required"
                else:
                    # Store AEMO config
                    self._aemo_data = {
                        CONF_AEMO_SPIKE_ENABLED: True,
                        CONF_AEMO_REGION: region,
                        CONF_AEMO_SPIKE_THRESHOLD: user_input.get(
                            CONF_AEMO_SPIKE_THRESHOLD, 300.0
                        ),
                    }

                    if self._aemo_only_mode:
                        # AEMO-only mode: go to Tesla provider selection
                        return await self.async_step_tesla_provider()
                    else:
                        # Amber mode with AEMO: continue to Tesla provider selection
                        return await self.async_step_tesla_provider()
            else:
                # AEMO disabled
                self._aemo_data = {CONF_AEMO_SPIKE_ENABLED: False}

                if self._aemo_only_mode:
                    # Can't be in AEMO-only mode without AEMO enabled
                    errors["base"] = "aemo_required_in_aemo_mode"
                else:
                    # Amber mode without AEMO: continue to Tesla provider
                    return await self.async_step_tesla_provider()

        # Build region choices
        region_choices = {"": "Select Region..."}
        region_choices.update(AEMO_REGIONS)

        # Default to enabled if in AEMO-only mode
        default_enabled = self._aemo_only_mode

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_AEMO_SPIKE_ENABLED, default=default_enabled): bool,
                vol.Optional(CONF_AEMO_REGION, default=""): vol.In(region_choices),
                vol.Optional(CONF_AEMO_SPIKE_THRESHOLD, default=300.0): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0, max=20000.0)
                ),
            }
        )

        return self.async_show_form(
            step_id="aemo_config",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "threshold_hint": "300 = $300/MWh (typical spike level)",
            },
        )

    async def async_step_site_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle site selection for both Amber and Tesla."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Handle Amber site selection (only for Amber mode)
            amber_site_id = None
            if not self._aemo_only_mode:
                amber_site_id = user_input.get(CONF_AMBER_SITE_ID)
                if not amber_site_id:
                    # Auto-select: prefer active site, or fall back to first site
                    active_sites = [s for s in self._amber_sites if s.get("status") == "active"]
                    if len(active_sites) == 1:
                        amber_site_id = active_sites[0]["id"]
                        _LOGGER.info(f"Auto-selected single active Amber site: {amber_site_id}")
                    elif len(self._amber_sites) == 1:
                        amber_site_id = self._amber_sites[0]["id"]
                        _LOGGER.info(f"Auto-selected single Amber site: {amber_site_id}")

            # Store site selection data
            self._site_data = {
                CONF_TESLA_ENERGY_SITE_ID: user_input[CONF_TESLA_ENERGY_SITE_ID],
                CONF_SOLAR_CURTAILMENT_ENABLED: user_input.get(CONF_SOLAR_CURTAILMENT_ENABLED, False),
            }

            # Amber-specific options only in Amber mode
            if not self._aemo_only_mode:
                self._site_data[CONF_AMBER_SITE_ID] = amber_site_id
                self._site_data[CONF_AUTO_SYNC_ENABLED] = user_input.get(CONF_AUTO_SYNC_ENABLED, True)
                self._site_data[CONF_AMBER_FORECAST_TYPE] = user_input.get(CONF_AMBER_FORECAST_TYPE, "predicted")
            else:
                # AEMO-only mode doesn't use Amber sync
                self._site_data[CONF_AUTO_SYNC_ENABLED] = False

            # Go to optional demand charge configuration
            return await self.async_step_demand_charges()

        data_schema_dict: dict[vol.Marker, Any] = {}

        if self._tesla_sites:
            # Build Tesla site options from Teslemetry API response
            tesla_site_options = {}
            for site in self._tesla_sites:
                site_id = str(site.get("energy_site_id"))
                site_name = site.get("site_name", f"Tesla Energy Site {site_id}")
                tesla_site_options[site_id] = f"{site_name} ({site_id})"

            data_schema_dict[vol.Required(CONF_TESLA_ENERGY_SITE_ID)] = vol.In(tesla_site_options)
        else:
            # No sites found - should not happen if validation worked
            _LOGGER.error("No Tesla energy sites found in Teslemetry account")
            return self.async_abort(reason="no_energy_sites")

        # Only add Amber-specific options in Amber mode
        if not self._aemo_only_mode:
            # Build Amber site options with status indicator
            amber_site_options = {}
            default_amber_site = None
            for site in self._amber_sites:
                site_id = site["id"]
                site_nmi = site.get("nmi", site_id)
                site_status = site.get("status", "unknown")

                # Add status indicator to help users identify active vs closed sites
                if site_status == "active":
                    label = f"{site_nmi} (Active)"
                    # Default to active site
                    if default_amber_site is None:
                        default_amber_site = site_id
                elif site_status == "closed":
                    label = f"{site_nmi} (Closed)"
                else:
                    label = f"{site_nmi} ({site_status})"

                amber_site_options[site_id] = label

            # Always show Amber site selection dropdown (so user can see status)
            if amber_site_options:
                data_schema_dict[vol.Required(CONF_AMBER_SITE_ID, default=default_amber_site)] = vol.In(
                    amber_site_options
                )

            data_schema_dict[vol.Optional(CONF_AUTO_SYNC_ENABLED, default=True)] = bool
            data_schema_dict[vol.Optional(CONF_AMBER_FORECAST_TYPE, default="predicted")] = vol.In({
                "predicted": "Predicted (Default)",
                "low": "Low (Conservative)",
                "high": "High (Optimistic)"
            })

        data_schema_dict[vol.Optional(CONF_SOLAR_CURTAILMENT_ENABLED, default=False)] = bool

        data_schema = vol.Schema(data_schema_dict)

        return self.async_show_form(
            step_id="site_selection",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_demand_charges(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle optional demand charge configuration (minimal implementation)."""
        if user_input is not None:
            # Combine all data
            data = {
                **self._amber_data,
                **self._teslemetry_data,
                **self._site_data,
                **self._aemo_data,  # Include AEMO configuration
            }

            # Add demand charge configuration if enabled
            if user_input.get(CONF_DEMAND_CHARGE_ENABLED, False):
                data.update({
                    CONF_DEMAND_CHARGE_ENABLED: True,
                    CONF_DEMAND_CHARGE_RATE: user_input[CONF_DEMAND_CHARGE_RATE],
                    CONF_DEMAND_CHARGE_START_TIME: user_input[CONF_DEMAND_CHARGE_START_TIME],
                    CONF_DEMAND_CHARGE_END_TIME: user_input[CONF_DEMAND_CHARGE_END_TIME],
                    CONF_DEMAND_CHARGE_DAYS: user_input[CONF_DEMAND_CHARGE_DAYS],
                    CONF_DEMAND_CHARGE_BILLING_DAY: user_input[CONF_DEMAND_CHARGE_BILLING_DAY],
                    CONF_DEMAND_CHARGE_APPLY_TO: user_input[CONF_DEMAND_CHARGE_APPLY_TO],
                })
            else:
                data[CONF_DEMAND_CHARGE_ENABLED] = False

            # Add supply charges (always include, even if 0)
            data[CONF_DAILY_SUPPLY_CHARGE] = user_input.get(CONF_DAILY_SUPPLY_CHARGE, 0.0)
            data[CONF_MONTHLY_SUPPLY_CHARGE] = user_input.get(CONF_MONTHLY_SUPPLY_CHARGE, 0.0)

            # Set appropriate title based on mode
            title = "Tesla AEMO Spike" if self._aemo_only_mode else "Tesla Sync"
            return self.async_create_entry(title=title, data=data)

        # Build the form schema
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_DEMAND_CHARGE_ENABLED, default=False): bool,
                vol.Optional(CONF_DEMAND_CHARGE_RATE, default=10.0): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0, max=100.0)
                ),
                vol.Optional(CONF_DEMAND_CHARGE_START_TIME, default="14:00"): str,
                vol.Optional(CONF_DEMAND_CHARGE_END_TIME, default="20:00"): str,
                vol.Optional(CONF_DEMAND_CHARGE_DAYS, default="All Days"): vol.In(
                    ["All Days", "Weekdays Only", "Weekends Only"]
                ),
                vol.Optional(CONF_DEMAND_CHARGE_BILLING_DAY, default=1): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=28)
                ),
                vol.Optional(CONF_DEMAND_CHARGE_APPLY_TO, default="Buy Only"): vol.In(
                    ["Buy Only", "Sell Only", "Both"]
                ),
                vol.Optional(CONF_DAILY_SUPPLY_CHARGE, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_MONTHLY_SUPPLY_CHARGE, default=0.0): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="demand_charges",
            data_schema=data_schema,
            description_placeholders={
                "example_rate": "10.0",
                "example_time": "14:00",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TeslaAmberSyncOptionsFlow:
        """Get the options flow for this handler."""
        return TeslaAmberSyncOptionsFlow()


class TeslaAmberSyncOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Tesla Sync."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from options (fallback to data for backwards compatibility)
        current_auto_sync = self.config_entry.options.get(
            CONF_AUTO_SYNC_ENABLED,
            self.config_entry.data.get(CONF_AUTO_SYNC_ENABLED, True)
        )
        current_forecast_type = self.config_entry.options.get(
            CONF_AMBER_FORECAST_TYPE,
            self.config_entry.data.get(CONF_AMBER_FORECAST_TYPE, "predicted")
        )
        current_demand_enabled = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_ENABLED,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_ENABLED, False)
        )
        current_demand_rate = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_RATE,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_RATE, 10.0)
        )
        current_start_time = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_START_TIME,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_START_TIME, "14:00")
        )
        current_end_time = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_END_TIME,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_END_TIME, "20:00")
        )
        current_days = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_DAYS,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_DAYS, "All Days")
        )
        current_billing_day = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_BILLING_DAY,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_BILLING_DAY, 1)
        )
        current_apply_to = self.config_entry.options.get(
            CONF_DEMAND_CHARGE_APPLY_TO,
            self.config_entry.data.get(CONF_DEMAND_CHARGE_APPLY_TO, "Buy Only")
        )
        current_solar_curtailment = self.config_entry.options.get(
            CONF_SOLAR_CURTAILMENT_ENABLED,
            self.config_entry.data.get(CONF_SOLAR_CURTAILMENT_ENABLED, False)
        )
        current_daily_supply_charge = self.config_entry.options.get(
            CONF_DAILY_SUPPLY_CHARGE,
            self.config_entry.data.get(CONF_DAILY_SUPPLY_CHARGE, 0.0)
        )
        current_monthly_supply_charge = self.config_entry.options.get(
            CONF_MONTHLY_SUPPLY_CHARGE,
            self.config_entry.data.get(CONF_MONTHLY_SUPPLY_CHARGE, 0.0)
        )

        # AEMO Spike Detection settings
        current_aemo_enabled = self.config_entry.options.get(
            CONF_AEMO_SPIKE_ENABLED,
            self.config_entry.data.get(CONF_AEMO_SPIKE_ENABLED, False)
        )
        current_aemo_region = self.config_entry.options.get(
            CONF_AEMO_REGION,
            self.config_entry.data.get(CONF_AEMO_REGION, "")
        )
        current_aemo_threshold = self.config_entry.options.get(
            CONF_AEMO_SPIKE_THRESHOLD,
            self.config_entry.data.get(CONF_AEMO_SPIKE_THRESHOLD, 300.0)
        )

        # Build region choices for AEMO
        region_choices = {"": "Select Region..."}
        region_choices.update(AEMO_REGIONS)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AUTO_SYNC_ENABLED,
                        default=current_auto_sync,
                    ): bool,
                    vol.Optional(
                        CONF_AMBER_FORECAST_TYPE,
                        default=current_forecast_type,
                    ): vol.In({
                        "predicted": "Predicted (Default)",
                        "low": "Low (Conservative)",
                        "high": "High (Optimistic)"
                    }),
                    vol.Optional(
                        CONF_SOLAR_CURTAILMENT_ENABLED,
                        default=current_solar_curtailment,
                    ): bool,
                    vol.Optional(
                        CONF_DEMAND_CHARGE_ENABLED,
                        default=current_demand_enabled,
                    ): bool,
                    vol.Optional(
                        CONF_DEMAND_CHARGE_RATE,
                        default=current_demand_rate,
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=100.0)),
                    vol.Optional(
                        CONF_DEMAND_CHARGE_START_TIME,
                        default=current_start_time,
                    ): str,
                    vol.Optional(
                        CONF_DEMAND_CHARGE_END_TIME,
                        default=current_end_time,
                    ): str,
                    vol.Optional(
                        CONF_DEMAND_CHARGE_DAYS,
                        default=current_days,
                    ): vol.In(["All Days", "Weekdays Only", "Weekends Only"]),
                    vol.Optional(
                        CONF_DEMAND_CHARGE_BILLING_DAY,
                        default=current_billing_day,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=28)),
                    vol.Optional(
                        CONF_DEMAND_CHARGE_APPLY_TO,
                        default=current_apply_to,
                    ): vol.In(["Buy Only", "Sell Only", "Both"]),
                    vol.Optional(
                        CONF_DAILY_SUPPLY_CHARGE,
                        default=current_daily_supply_charge,
                    ): vol.Coerce(float),
                    vol.Optional(
                        CONF_MONTHLY_SUPPLY_CHARGE,
                        default=current_monthly_supply_charge,
                    ): vol.Coerce(float),
                    # AEMO Spike Detection Options
                    vol.Optional(
                        CONF_AEMO_SPIKE_ENABLED,
                        default=current_aemo_enabled,
                    ): bool,
                    vol.Optional(
                        CONF_AEMO_REGION,
                        default=current_aemo_region,
                    ): vol.In(region_choices),
                    vol.Optional(
                        CONF_AEMO_SPIKE_THRESHOLD,
                        default=current_aemo_threshold,
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=20000.0)),
                }
            ),
        )
