# TCP Switch


## Description

Integration with TCP Switch (SR-201)

## Configuration
Basic configuration of the Component follows:

```yaml

configuration:
  switch:
      - platform: tcp_switch
        name: Name for component
        host: hostname # or IP
        port: port # Optional - default 6722
        momentary_delay: 0 # Optional (0-65356) - default 0 - Number of seconds before doing the opposite action 
        channels: # Optional - default none - List of channels to control (up to 255)
          - 1
```

## Track Updates

This custom card can be tracked with the help of custom-updater.

In your configuration.yaml

```yaml
configuration:
    custom_updater:
      track:
        - components
      component_urls:
        - https://raw.githubusercontent.com/elad-bar/ha-tcp-switch/master/tcp_switch.json
```

