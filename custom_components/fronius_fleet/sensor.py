from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FroniusFleetDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fronius Fleet sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            FroniusFleetPowerSensor(coordinator),
            FroniusFleetEnergySensor(coordinator),
            FroniusFleetEnergyTodaySensor(coordinator),
            FroniusFleetOnlineSensor(coordinator),
        ]
    )


class FroniusFleetPowerSensor(CoordinatorEntity, SensorEntity):
    """Sensor for total fleet power."""

    _attr_has_entity_name = True
    _attr_name = "Fleet Total Power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator: FroniusFleetDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_power"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("total_kw")


class FroniusFleetEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor for total fleet energy generated."""

    _attr_has_entity_name = True
    _attr_name = "Fleet Total Energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "GWh"  # Custom unit GWh, HA uses MWh standard but GWh works
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, coordinator: FroniusFleetDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_energy"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("total_gwh")


class FroniusFleetEnergyTodaySensor(CoordinatorEntity, SensorEntity):
    """Sensor for total fleet energy generated today."""

    _attr_has_entity_name = True
    _attr_name = "Fleet Energy Today"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:lightning-bolt-circle"

    def __init__(self, coordinator: FroniusFleetDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_energy_today"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("total_today_kwh")


class FroniusFleetOnlineSensor(CoordinatorEntity, SensorEntity):
    """Sensor for online systems count."""

    _attr_has_entity_name = True
    _attr_name = "Fleet Online Systems"
    _attr_icon = "mdi:solar-panel"

    def __init__(self, coordinator: FroniusFleetDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_online"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("online_count")
        
    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "total_systems": self.coordinator.data.get("total_count"),
            "offline_systems": self.coordinator.data.get("offline_count"),
        }
