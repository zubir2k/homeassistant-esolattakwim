## Automation Blueprint 
The automation blueprint allow you to easily configure and maintain the azan automation.
Press below button to begin.

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzubir2k%2Fhomeassistant-esolattakwim%2Fblob%2Fmain%2Fblueprints%2Fesolat_automation.yaml)

> [!CAUTION]
> Some reported that blueprint is not working. You may use the alternative below.

## Automation Alternatives
You can also use this template automation for azan. Just follow the instruction below.
What it does:
- Remind via HA Persistent Notification 15min before prayer time
- Alert Prayer Time via HA Persistent Notification
- Play Azan audio using `play_media` action to the selected `media_player`

Follow the steps below to begin.

### 1. Enable HAMY path in your `configuration.yaml`
- Add the following line into the config file

```yaml
homeassistant:
  packages: !include_dir_named HAMY/
```

### 2. Placing the template file
- Create a path/folder name `HAMY` inside /config
- Create a file name `esolattakwim.yaml`
- Copy and Paste below into this file
- Restart Home Assistant
- Once restarted, look for `select.esolat_media_player` entity and choose your media_player.

> [!NOTE]  
> This template does not support Alexa Integration.
> Will include it soon. Insha`Allah

```yaml
## Select Entity ##
template:
  - select:
    - name: "eSolat Media Player"
      state: "{{ states('input_text.esolat_media_player') }}"
      options: >
        {{ states.media_player
        | rejectattr('state', 'in', ['unavailable', 'unknown'])
        | map(attribute ='entity_id') | list }}
      select_option:
        - action: input_text.set_value
          target:
            entity_id: input_text.esolat_media_player
          data:
            value: "{{ option }}"

## Input Text ##
input_text:
  esolat_media_player:
    name: "eSolat Media Player"
    
## Automation ##
automation:
  - alias: 🕋 eSolat Automation
    description: ""
    triggers:
      - trigger: template
        value_template: >-
          {{ now().strftime('%H:%M') ==
          as_timestamp(state_attr('calendar.esolat_takwim',(state_attr('calendar.esolat_takwim','current')
          | lower))) | timestamp_custom('%H:%M') }}
        id: esolat_prayer
        alias: esolat_prayer
      - alias: esolat_reminder (15min)
        trigger: template
        value_template: >-
          {{ (as_local(now()).strftime("%s") | int + (15*60)) |
          timestamp_custom("%H:%M", false) ==
          as_timestamp(state_attr('calendar.esolat_takwim',(state_attr('calendar.esolat_takwim','next')
          | lower))) | timestamp_custom('%H:%M') }}
        id: esolat_reminder
    conditions: []
    actions:
      - variables:
          prayer: >-
            {% set prayer_map = {'Imsak':'Imsak', 'Fajr':'Subuh', 'Syuruk':'Syuruk',
            'Dhuhr':'Zohor', 'Asr':'Asar', 'Maghrib':'Maghrib', 'Isha':'Isyak'} %}{{
            prayer_map[state_attr('calendar.esolat_takwim','current')] }}
          prayer_next: >-
            {% set prayer_map = {'Imsak':'Imsak', 'Fajr':'Subuh', 'Syuruk':'Syuruk',
            'Dhuhr':'Zohor', 'Asr':'Asar', 'Maghrib':'Maghrib', 'Isha':'Isyak'} %}{{
            prayer_map[state_attr('calendar.esolat_takwim','next')] }}
          prayer_audio: >-
            {% if prayer == 'Subuh'
            %}https://github.com/zubir2k/HomeAssistantAdzan/raw/refs/heads/main/audio/azansubuh_alexa.mp3
            {% else
            %}https://github.com/zubir2k/HomeAssistantAdzan/raw/refs/heads/main/audio/azan_alexa.mp3{%
            endif %}
        alias: Variables
      - choose:
          - conditions:
              - condition: and
                conditions:
                  - condition: trigger
                    id:
                      - esolat_prayer
                  - condition: template
                    value_template: >-
                      {{ state_attr('calendar.esolat_takwim','current') in
                      ['Fajr','Dhuhr','Asr','Maghrib','Isha'] }}
                    alias: Waktu Solat
            sequence:
              - action: persistent_notification.create
                metadata: {}
                data:
                  notification_id: esolat_notify_manual
                  title: 🕋 eSolat - Waktu {{ prayer }}
                  message: >-
                    {{ now().strftime('%-I:%M %p') }} - Sekarang telah masuk waktu
                    {{ prayer }} bagi kawasan ini dan kawasan yang sama waktu
                    dengannya.
                alias: Notify
              - action: media_player.play_media
                target:
                  entity_id: "{{ states('select.esolat_media_player') }}"
                data:
                  media_content_id: "{{ prayer_audio }}"
                  media_content_type: audio/mp3
                  extra:
                    title: Azan {{ prayer }}
                    thumb: https://i.imgur.com/1U9Ehvr.png
            alias: Waktu Solat
          - conditions:
              - condition: and
                conditions:
                  - condition: trigger
                    id:
                      - esolat_reminder
                  - condition: template
                    value_template: >-
                      {{ state_attr('calendar.esolat_takwim','next') in
                      ['Fajr','Dhuhr','Asr','Maghrib','Isha'] }}
                    alias: Waktu Solat
            sequence:
              - action: persistent_notification.create
                metadata: {}
                data:
                  notification_id: esolat_remind_manual
                  title: 🕋 eSolat - Waktu {{ prayer_next }} ⏰ 
                  message: >-
                    {{ now().strftime('%-I:%M %p') }} - Azan {{ prayer_next }} akan
                    berkumandang sebentar nanti.
                alias: Notify
            alias: Reminder Solat
    mode: single

```
