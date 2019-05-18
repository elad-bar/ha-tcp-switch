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
        momentary_delay: 0 # 0-65356 - Number of seconds before doing the opposite action 
        channels: # List of numbers of channels you would like to control (up to 255)
          - 1
```
