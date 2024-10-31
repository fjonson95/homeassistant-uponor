from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE,
    DEVICE_MANUFACTURER,
    MODEL_R208
)


async def async_setup_entry(hass, entry, async_add_entities):
    state_proxy = hass.data[DOMAIN]["state_proxy"]
    entities = [AwaySwitch(state_proxy, entry.data[CONF_NAME])]

    entities.append(AutoUpdate(state_proxy, entry.data[CONF_NAME]))

    for controller in hass.data[DOMAIN]["controllers"]:
        if controller.lower() in entry.data:
            name = entry.data[controller.lower()]
        else:
            name = state_proxy.get_controller_name(controller)
    if state_proxy.is_cool_available():
        entities.append(CoolSwitch(state_proxy, entry.data[CONF_NAME]))

    for thermostat in hass.data[DOMAIN]["thermostats"]:
        if thermostat.lower() in entry.data:
            name = entry.data[thermostat.lower()]
        else:
            name = state_proxy.get_room_name(thermostat)        
        entities.append(OwerrideThermostat(state_proxy, thermostat, name))
    async_add_entities(entities)


class AwaySwitch(SwitchEntity):
    def __init__(self, state_proxy, name):
        self._state_proxy = state_proxy
        self._name = name

    @property
    def name(self) -> str:
        return self._name + " Away"

    @property
    def icon(self):
        return "mdi:home-export-outline"

    @property
    def should_poll(self):
        return False

    @property
    def is_on(self):
        return self._state_proxy.is_away()

    async def async_turn_on(self, **kwargs):
        await self._state_proxy.async_set_away(True)

    async def async_turn_off(self, **kwargs):
        await self._state_proxy.async_set_away(False)
    
    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        self.async_schedule_update_ha_state(True)

    @property
    def unique_id(self):
        return self.name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "c")},
            "name": self._name,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": MODEL_R208,
        }

class AutoUpdate(SwitchEntity):
    def __init__(self, state_proxy, name):
        self._state_proxy = state_proxy
        self._name = name

    @property
    def name(self) -> str:
        return self._name + " Autoupdate"

    @property
    def icon(self):
        return "mdi:cloud-refresh"

    @property
    def should_poll(self):
        return False

    @property
    def is_on(self):
        return self._state_proxy.is_autoupdate()

    async def async_turn_on(self, **kwargs):
        await self._state_proxy.async_set_autoupdate(True)

    async def async_turn_off(self, **kwargs):
        await self._state_proxy.async_set_autoupdate(False)
    
    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        self.async_schedule_update_ha_state(True)

    @property
    def unique_id(self):
        return self.name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "c")},
            "name": self._name,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": MODEL_R208,
        }

class CoolSwitch(SwitchEntity):
    def __init__(self, state_proxy, name):
        self._state_proxy = state_proxy
        self._name = name

    @property
    def name(self) -> str:
        return self._name + " Cooling Mode"

    @property
    def icon(self):
        return "mdi:snowflake"

    @property
    def should_poll(self):
        return False

    @property
    def is_on(self):
        return self._state_proxy.is_cool_enabled()

    async def async_turn_on(self, **kwargs):
        await self._state_proxy.async_switch_to_cooling()

    async def async_turn_off(self, **kwargs):
        await self._state_proxy.async_switch_to_heating()
    
    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        self.async_schedule_update_ha_state(True)

    @property
    def unique_id(self):
        return self.name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "c")},
            "name": self._name,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": MODEL_R208,
        }
    
class OwerrideThermostat(SwitchEntity):
    def __init__(self, state_proxy, thermostat, name):
        self._state_proxy = state_proxy
        self._thermostat = thermostat
        self._name = name

    @property
    def name(self) -> str:
        return self._name + " Override Local"

    @property
    def icon(self):
        return "mdi:ThermometerCheck"
    
    @property
    def should_poll(self):
        return False
    
    @property
    def is_on(self):
        return self._state_proxy.get_local_override(self._thermostat)

    async def async_turn_on(self, **kwargs):
        await self._state_proxy.async_local_override(self._thermostat,True)

    async def async_turn_off(self, **kwargs):
        await self._state_proxy.async_local_override(self._thermostat,False)
    
    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        self.async_schedule_update_ha_state(True)

    @property
    def unique_id(self):
        return self.name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._state_proxy.get_thermostat_id(self._thermostat))},
            "name": self._name,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": self._state_proxy.get_model(self._thermostat),
            "sw_version": self._state_proxy.get_version(self._thermostat),
            "serial_number": self._state_proxy.get_thermostat_id(self._thermostat),              
            "via_device" : (DOMAIN,self._state_proxy.get_controller_id(self._thermostat[:2]))
        }