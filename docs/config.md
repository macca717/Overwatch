# Configuration

The application utilizes a combination of config file loading and command line parsing for configuration. The web server requires an environment file (".env") located in the root directory for configuration.

## Command Line Flags
```
usage: overwatch [-h] [--log-level {critical,error,warn,warning,info,debug}] 
[-c CONFIG] [-s] [-t] [--file FILE]

Seizure Detector Server

optional arguments:
  -h, --help            show this help message and exit
  --log-level {critical,error,warn,warning,info,debug,trace}
                        Application log level
  -c CONFIG, --config CONFIG
                        Path to config.toml file
  -s, --silent          Silence all alerts
  -t, --test            Run the application in test mode
  --file FILE           Load video from file path instead of camera

```
Test mode disables:
- Scheduled start and stop times, permanently running the application in the "on" state

## Config File
Further configuration is achieved through the use of a TOML file.

```
[server]
host_name = "localhost"
video_save_dir = "saves"
webserver_port = 8080
websocket_port = 9999

[camera]
url = "http://192.168.1.1/video.mjpeg"

[processing]
avg_weighting = 0.5
dilation_iterations = 0
fixed_lvl_threshold = 5
fps = 2
gauss_ksize = 7
pixel_threshold_hi = 9000
pixel_threshold_lo = 15

[alerting]
alarm_hysteresis_s = 60
alert_time_s = 300
end_time = "18:30"
initial_alarm_duration_m = 30
min_movement_s = 10
start_time = "19:22"

[alerters.siren]
enabled = true
ssh_host = "192.168.1.1"
ssh_key_path = "app/alert_plugins/common/keys/id-rsa"
ssh_user = "user"
test_grp = true

[alerters.telegram]
api_key = "9999999999:XXXXXXXX_XXXXXXXXXXXXXXXXXXXXXXXXXX"
chat_ids = [
  "1111111111", "22222222"
]
enabled = true
test_grp = true
```

## Server Options

#### host_name 
Host name of the websocket/web server.
#### video_save_dir
Directory to store captured alert videos.

#### webserver_port
Websocker server port.

#### websocket_port
Websocket server port.

## Alerting Options

#### alarm_hysteresis_s
Hysteresis of the alarm (Minimum time between alerts) in seconds.

#### alert_time_s
Minimum time of continuous movement in seconds to be considered an alert.

#### end_time
Time of day for detection to stop (24hr).

#### initial_alarm_duration_m
Max duration of time in minutes to display a timer since the first alert. Used to indicate the time since the first alert was raised in a cluster of alerts.


#### min_movement_s
Minimum amount of time in seconds between detected movement. If motion is detected outside this limit then the *alert_time_s* timer is reset (Used to guard against lost frames/missed motion detection).

#### start_time
Time of day for detection to start (24hr).

## Camera Options

#### url
URL of camera

## Processing Options

#### avg_weighting
Used to calculate motion between frames. This value regulates the update speed (how fast the previous frames are forgotten).

#### dilation_iterations
Not used.

#### fixed_lvl_threshold
If the pixel change value is less than the threshold value it is set to 0, else 255 (filtering).

#### fps
The number of camera frames per second to sample for detection.
#### gauss_ksize
Kernal size of the guassian blurring, must be odd. The  higher the value the more filtering is performed.


#### pixel_threshold_hi
High cut off for bandpass filter in pixels (Used to adjust sensitivity).
#### pixel_threshold_lo
Low cut off for bandpass filter in pixels (Used to adjust sensitivity).

## Siren

#### enabled
A boolean flag indicating whether or not the siren is enabled.
#### ssh_host
IP/host name of the host computer

#### ssh_key_path
Relative path to the SSH key file

#### ssh_user
User name of the host account

#### test_grp
A boolean flag indicating whether or not the siren is in the test group (Will sound when a system test is initiated by the user).

## Telegram

#### api_key

API key of Telegram bot, see [here](https://github.com/caronc/apprise/wiki/Notify_telegram) for further information.

#### chat_ids
List of recipient chat IDs

#### enabled
A boolean flag indicating whether or not the Telegram alerter is enabled.

#### test_grp
A boolean flag indicating whether or not the Telegram alerter is in the test group (Will message when a system test is initiated by the user).


## Web Server Env File
A sample .env is provided below:

``` bash
DEBUG=False
SECRET_KEY=<secret>
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///app.db

```

| Key | Description |
| ---- | ---------- |
| DEBUG | Boolean indicating if debug mode is active |
| SECRET_KEY | Secret generated string |
| ALLOWED_HOSTS | List of allowed hosts |
| DATABASE_URL | Path to database |