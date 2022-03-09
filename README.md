# mqtt-xiaomi-ble-thermostat



## CUSTOM JSON POLL FOR mibletemp
```
# add this in the demo.py file of the MiTemp project
def poll_json(args):
    backend = _get_backend(args)
    poller = MiTempBtPoller(args.mac, backend)
    thermo_dict = {
      "fw": poller.firmware_version(),
      "name": poller.name(),
      "battery": poller.parameter_value(MI_BATTERY),
      "temperature": poller.parameter_value(MI_TEMPERATURE),
      "humidity": poller.parameter_value(MI_HUMIDITY)
    }
    print(json.dumps(thermo_dict))
```
