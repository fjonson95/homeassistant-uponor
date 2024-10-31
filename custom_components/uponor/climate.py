import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature
)

from homeassistant.components.climate.const import (
    HVACMode,
    HVACAction,
    PRESET_AWAY,
    PRESET_ECO,
    ClimateEntityFeature
)

from .const import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE,
    DEVICE_MANUFACTURER
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    state_proxy = hass.data[DOMAIN]["state_proxy"]

    entities = []
    for thermostat in hass.data[DOMAIN]["thermostats"]:
        if thermostat.lower() in entry.data:
            name = entry.data[thermostat.lower()]
        else:
            name = state_proxy.get_room_name(thermostat)
        match state_proxy.get_model(thermostat):
            case "T144", "T145":
                entities.append(UponorClimate(state_proxy, thermostat, name))
            case _:
                if state_proxy.has_humidity_sensor(thermostat):
                    entities.append(UponorClimate_hum(state_proxy, thermostat, name))
                else:
                    entities.append(UponorClimate(state_proxy, thermostat, name))
    if entities:
        async_add_entities(entities, update_before_add=False)


class UponorClimate(ClimateEntity):

    _enable_turn_on_off_backwards_compatibility = False
    
    def __init__(self, state_proxy, thermostat, name):
        self._state_proxy = state_proxy
        self._thermostat = thermostat
        self._name = name
        temp = self._state_proxy.get_setpoint(self._thermostat)
        is_cool = self._state_proxy.is_cool_enabled()
        self._is_on = not ((is_cool and temp >= self.max_temp) or (not is_cool and temp <= self.min_temp))

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

    @property
    def name(self):
        return self._name
    
    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        async_dispatcher_connect(
            self.hass, SIGNAL_UPONOR_STATE_UPDATE, self._update_callback
        )

    @callback
    def _update_callback(self):
        temp = self._state_proxy.get_setpoint(self._thermostat)
        is_cool = self._state_proxy.is_cool_enabled()
        self._is_on = not ((is_cool and temp >= self.max_temp) or (not is_cool and temp <= self.min_temp))
        self.async_schedule_update_ha_state(True)

    @property
    def unique_id(self):
        return self._state_proxy.get_thermostat_id(self._thermostat)
    
    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE

    @property
    def hvac_modes(self):
        if self._state_proxy.is_cool_enabled():
            return [HVACMode.COOL, HVACMode.OFF]
        return [HVACMode.HEAT]

    @property
    def hvac_mode(self):
        if not self._is_on:
            return HVACMode.OFF
        if self._state_proxy.is_cool_enabled():
            return HVACMode.COOL
        return HVACMode.HEAT

    @property
    def hvac_action(self):
        if not self._is_on:
            return HVACAction.OFF
        if self._state_proxy.is_active(self._thermostat):
            return HVACAction.COOLING if self._state_proxy.is_cool_enabled() else HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def preset_modes(self):
        return [self.preset_mode] if self.preset_mode is not None else []
       
    @property
    def current_temperature(self):
        return self._state_proxy.get_temperature(self._thermostat)
    
    @property
    def target_temperature(self):
        return self._state_proxy.get_setpoint(self._thermostat)

    @property
    def target_temperature_low(self):
        return self._state_proxy.get_min_limit(self._thermostat)

    @property
    def target_temperature_high(self):
        return self._state_proxy.get_max_limit(self._thermostat)
    
    @property
    def extra_state_attributes(self):
        return {
            'id': self._thermostat,
            'status': self._state_proxy.get_status(self._thermostat),
            'pulse_width_modulation': self._state_proxy.get_pwm(self._thermostat),
            'last_update': self._state_proxy.get_last_update(),
            'eco_setback': self._state_proxy.get_eco_setback(self._thermostat),
        }

    @property
    def preset_mode(self):
        if self._state_proxy.is_eco(self._thermostat):
            return PRESET_ECO
        if self._state_proxy.is_away():
            return PRESET_AWAY
        return None
    

class UponorClimate_hum(UponorClimate):

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TARGET_HUMIDITY

    @property
    def current_humidity(self):
        return self._state_proxy.get_humidity(self._thermostat)




