# Deployment

Docker is the prefered option to deploy the application. The image must be built prior to starting the container.

```bash
docker build -t overwatch .
```

To deploy the application in a docker container:
- The timezone of the container must be set for the correct functioning of the scheduler.
- The config file and video save directory must be mounted.
- The common alerter plugin directory must be mounted.
- The application ports must be forwarded to the host.
- The log level may be specified (error is the default).


```bash
docker run \
    -e TZ=Pacific/Auckland \
    -v "$(pwd)"/config.toml:/config.toml \
    -v "$(pwd)"/saves/:/saves \
    -v "$(pwd)"/.env/:/.env \
    -v "$(pwd)"/common:/app/alert_plugins/common/ \
    -p 9001:9001 \
    -p 9876:9876 \
    -e LOG_LEVEL=debug \
    --restart=always \
    overwatch:latest
```

If the included siren alerter is implemented via docker the following steps must be performed:
1. Generate a SSH key pair
2. Add the generated public key to the host computer/user *authorized_keys* file
3. Ensure the path to the generated SSH private key is correct in the configuration file. Further imformation regarding SSH keys can be found [Here](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server)
4. The host must have [aplay](https://linux.die.net/man/1/aplay) installed and the sound file *app/alert_plugins/common/siren.wav* must be copied to the host users home directory.

The application can also be run via docker-compose, a sample "docker-compose.yaml" is shown below.


```yaml
version: '3'

services:
  app:
    container_name: overwatch
    image: overwatch:latest
    restart: always
    ports:
      - "9001:9001"
      - "9876:9876"
    volumes:
      - ./test.db:/test.db
      - ./saves:/saves/
      - ./config.toml:/config.toml
      - ./.env:/.env
      - ./common:/app/alert_plugins/common/
    environment:
      - TZ=Pacific/Auckland
      - LOG_LEVEL=debug

```
