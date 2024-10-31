import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass, SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    SIGNAL_UPONOR_STATE_UPDATE,
    DEVICE_MANUFACTURER
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    state_proxy = hass.data[DOMAIN]["state_proxy"]

    entities = []
    for controller in hass.data[DOMAIN]["controllers"]:
        if controller.lower() in entry.data:
            name = entry.data[controller.lower()]
        else:
            name = state_proxy.get_controller_name(controller)
        entities.append(UponorRoomAvg(state_proxy, controller, name))

    if entities:
        async_add_entities(entities, update_before_add=False) 

class UponorRoomAvg(SensorEntity):
    "Sensors data"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_suggested_display_precision = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = '°C'
    
    def __init__(self, state_proxy, controller,name):
        self._state_proxy = state_proxy
        self._controller = controller
        self._name = name
    
    @property
    def name(self):
        return self._name + " Room avg temp"

    @property
    def should_poll(self):
        return False

    @property
    def icon(self) -> str:
        return "mdi:thermometer"

    @property
    def native_value(self):
        val = self._state_proxy.get_controller_room_avgtemp(self._controller)
        return val
        
    @property
    def unique_id(self):
        return self._name + "_average_room_temperature"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._state_proxy.get_controller_id(self._controller))},
            "name": self._name,
            "model": self._state_proxy.get_controller_hardware(self._controller),
            "manufacturer": DEVICE_MANUFACTURER,
            "sw_version": self._state_proxy.get_controller_version(self._controller),
            "serial_number": self._state_proxy.get_controller_id(self._controller),
            "via_device" : (DOMAIN,self._state_proxy.get_controller_via_id(self._controller))
        }
