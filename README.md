![github](https://github.com/user-attachments/assets/2e1c97c0-6b48-4953-8a32-38f1e9a4d052)

[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub all releases](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Download%20Count&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.esolattakwim.total)
[![Buy](https://img.shields.io/badge/Belanja-Coffee-yellow.svg)](https://zubirco.de/buymecoffee)
[![GitHub Release](https://img.shields.io/github/release/zubir2k/homeassistant-esolattakwim.svg)](https://github.com/zubir2k/homeassistant-esolattakwim/releases/)

Assalamu'alaikum

This is an Islamic calendar and Prayer time integration for Malaysia. \
Instead of creating a sensor for each events and prayer time, I thought of using calendar entity instead.

May this be beneficial to all, InshaAllah

![image](https://github.com/user-attachments/assets/f6f2009b-b187-4d3b-905d-7e4b5dc16b1b)


## Features
- Automatic prayer time retrieval from JAKIM (and stored locally)
- Takwim/Calendar information from JAKIM
- Prayer time information available as attributes in the calendar entity
- Prayer time format in Datetime UTC (e.g. 2023-07-29T22:01:00+00:00)
- `current` and `next` prayer time indicator available as attribute

## Installation
#### With HACS
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=zubir2k&repository=homeassistant-esolattakwim&category=integration)

> [!Tip]
> If you are unable to use the button above, manually search for eSolat Takwim in HACS.

#### Manual
1. Copy the `esolattakwim` directory from `custom_components` in this repository and place inside your Home Assistant's `custom_components` directory.
2. Restart Home Assistant
3. Follow the instructions in the `Setup` section

> [!WARNING]
> If installing manually, in order to be alerted about new releases, you will need to subscribe to releases from this repository.

## Setup
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=esolattakwim)

> [!Tip]
> If you are unable to use the button above, follow the steps below:
> 1. Navigate to the Home Assistant Integrations page (Settings --> Devices & Services)
> 2. Click the `+ ADD INTEGRATION` button in the lower right-hand corner
> 3. Search for `eSolat Takwim Malaysia`
> 4. Select location zone to your preference

![image](https://github.com/user-attachments/assets/7071de5a-1d22-4f89-9162-02fc1b5a782e)

## Prayer Time Markdown Card
I have prepared a markdown card template for this integration.
You may refer to the [Markdown.md](MARKDOWN.md) and copy the markdown codes.

![image](https://github.com/user-attachments/assets/73dd0218-0adb-4ac6-92d3-2226a2072d51)

## Automation Azan
Work-in-progress 🚧 \
InshaAllah, I will share it here after finish running some tests. 

## Disclaimer/Credits
Data provided by JAKIM (Department of Islamic Development Malaysia)
