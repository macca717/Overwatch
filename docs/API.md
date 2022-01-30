# API

## Websocket API
The application employs a websocket server to enable communication and data exchange with clients. Some endpoints are implemented as HTTP for ease of use, these require an HTTP *Get* request rather than a websocket connnection.

| Name           | Endpoint      | Data Type | Description                                          |
| -------------- |:-------------:|:---------:| ---------------------------------------------------- |
| Root           | */*           | JSON      | Bi-directional server status and control commands    |
| Metrics        | */metrics*    | JSON      | Server metrics                                       |
| Video Stream   | */raw-video*  | Bytes     | MJPG video stream                                    |
| Health Check   | */health*     | Text      | Health check endpoint(HTTP)                          |
| Image Snapshot | */snapshot*   | Bytes     | Image snapshot, updates every second(HTTP)           |
| Configuration  | */config*     | JSON      | System Configuration(HTTP)                           |

### Status

The server broadcasts a status heartbeat every second, or on a server state change to all clients connected to the root endpoint.
``` json
{
    "timeStamp": 1635802554,
    "state": "on",
    "initialAlarm": 0.0,
    "silencedTill": null,
}

```
| Field              | Description                                             | Unit  |
| ------------------ | ------------------------------------------------------- |:-----:|
| timeStamp          | Unix timestamp since the epoch                          | s     |
| state              | Current system state("on", "off", "alarm", "silenced")  |       |
| initialAlarm       | Unix timestamp since initial alert was raised                  | s     |
| silencedTill       | Unix timestamp till silence lifts, else null            | s     |


### Configuration
The requested current application configuration is returned in the format below.

``` json
{
    "server": {
        "host_name": "localhost",
        "timezone": "Pacific/Auckland",
        "websocket_port": 9876,
        "webserver_port": 9001
    },
    "camera": {
        "url": "http://192.168.1.1/video.mjpeg"
    },
    "flags": {
        "config_path": "test_config.toml",
        "silent": false,
        "log_level": "debug",
        "test": false,
        "file": "null"
    },
    "processing": {
        "fps": 2,
        "avg_weighting": 0.5,
        "dilation_iterations": 0,
        "fixed_lvl_threshold": 5,
        "gauss_ksize": 13,
        "pixel_threshold_hi": 10000,
        "pixel_threshold_lo": 0
    },
    "alerting": {
        "start_time": "16:55",
        "end_time": "16:54",
        "alert_time_s": 360,
        "min_movement_s": 2,
        "initial_alarm_duration_m": 30,
        "alarm_hysteresis_s": 60
    },
    "alerters": {
        "siren": {
            "enabled": true,
            "ssh_host": "198.1.1.2",
            "ssh_key_path": "app/alert_plugins/common/keys/id_rsa",
            "ssh_user": "user",
            "test_grp": true
        },
        "telegram": {
            "api_key": "1234567890:xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "chat_ids": [
                "11111111", "22222222"
            ],
            "enabled": true,
            "test_grp": true
        }
    },
    "monitoring": null
}
```



### Commands

All commands follow the generic JSON template below

``` json
{
    "command": "command name",
    "data": {
        "x": "y"
    }
}
```

Succesful commands are responded with a success message.

``` json
{
    "status": "OK"
}
```

Failed command responses follow the template below.

``` json
{
    "error": "error message"
}
```

#### Silence

Command to request that all alarms are silenced for *n* seconds.

``` json
{
    "command": "silence",
    "data": {
        "silenceFor": 180
    }
}
```

#### Test Alerts

Command to test alert plugins, a list of excluded plugin names can be supplied, these will not be called in the alert test.

``` json
{
    "command": "test",
    "data": {
        "excluded": ["telegram"]
    }
}
```

#### Configuration Update

Command to update the applications running configuration.

``` json
{
    "command": "config_update",
    "data": {
        "config": {
            "server": {
            "host_name": "localhost",
            "timezone": "Pacific/Auckland",
            "websocket_port": 9876,
            "webserver_port": 9001
            },
            "camera": {
                "url": "http://192.168.1.1/video.mjpeg"
            }
            ...
        }
    }
}
```

#### Shutdown

Command to request a server shutdown.

``` json
{
    "command": "shutdown",
    "data": {"shutdownIn": 0}
}
```

### Metrics
Server metrics are broadcast every second to clients connected to the metrics endpoint.

``` json
{
  "timeStamp": 1635298375.525463,
  "sysCpuPercent": 7.7,
  "sysMemPercent": 1.2656211853027344,
  "capCpuPercent": 11.7,
  "capMemPercent": 0.7632732391357422,
  "socketConnections": 4,
  "loopAvgS": 0.004583304933332973,
  "loopMaxS": 0.007386695999997528,
  "loopMinS": 0.0036263889999901266
}
```

| Field              | Description                                             | Unit  |
| ------------------ | ------------------------------------------------------- |:-----:|
| timeStamp          | Unix timestamp since the epoch                          | s     |
| sysCpuPercent      | CPU utilization of the main process                     | %     |
| sysMemPercent      | Memory utilization of the main process                  | %     |
| capCpuPercent      | CPU utilization of the detection process                | %     |
| capMemPercent      | Memory utilization of the detection process             | %     |
| socketConnections  | Current number of TCP connections                       |       |
| loopAvgS           | Average duration of the detection processing            | s     |
| loopMaxS           | Maximum duration of the detection processing            | s     |
| loopMinS           | Minimum duration of the detection processing            | s     |

