# mqtt-xiaomi-ble-thermostat



# CUSTOM JSON POLL FOR mibletemp
def poll_json(args):
    backend = _get_backend(args)
    poller = MiTempBtPoller(args.mac, backend)
    thisdict = {
      "battery": poller.parameter_value(MI_BATTERY),
      "temp": poller.parameter_value(MI_TEMPERATURE),
      "hum": poller.parameter_value(MI_HUMIDITY)
    }
    print(json.dumps(thisdict))

