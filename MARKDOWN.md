## 🕋 Prayer Time Markdown Card

![image](https://github.com/user-attachments/assets/73dd0218-0adb-4ac6-92d3-2226a2072d51)

1. Edit your current dashboard.
2. Add a new Markdown card. [What is Markdown card?](https://www.home-assistant.io/dashboards/markdown)
3. Copy below markdown.
4. Save

```markdown
> Today is</b><br /><font size=7>{{ now().strftime('%I:%M %p') }}<br />{{ now().strftime('%A') }}</font>
<font size=2>{{ now().strftime('%d %B %Y') }} | {{ state_attr('calendar.esolat_takwim','hijri_full') }}h</font>
<table align=center width=100%>
<tr align=center>
<td>Subuh</td>
<td>Zohor</td>
<td>Asar</td>
<td>Maghrib</td>
<td>Isyak</td>
</tr>
<tr align=center>
<td><ha-icon icon="mdi:star-crescent"></ha-icon></td>
<td><ha-icon icon="mdi:star-crescent"></ha-icon></td>
<td><ha-icon icon="mdi:star-crescent"></ha-icon></td>
<td><ha-icon icon="mdi:star-crescent"></ha-icon></td>
<td><ha-icon icon="mdi:star-crescent"></ha-icon></td>
</tr>
<tr align=center>
<td>{{ as_timestamp(state_attr('calendar.esolat_takwim','fajr')) | timestamp_custom('%I:%M %p') }}</td>
<td>{{ as_timestamp(state_attr('calendar.esolat_takwim','dhuhr')) | timestamp_custom('%I:%M %p') }}</td>
<td>{{ as_timestamp(state_attr('calendar.esolat_takwim','asr')) | timestamp_custom('%I:%M %p') }}</td>
<td>{{ as_timestamp(state_attr('calendar.esolat_takwim','maghrib')) | timestamp_custom('%I:%M %p') }}</td>
<td>{{ as_timestamp(state_attr('calendar.esolat_takwim','isha')) | timestamp_custom('%I:%M %p') }}</td>
</tr>
<tr><ha-alert alert-type="info"><b>Waktu Sekarang: </b>{% set prayer_map = {'Fajr':'Subuh', 'Dhuhr':'Zohor', 'Asr':'Asar', 'Maghrib':'Maghrib', 'Isha':'Isyak'} %}{{ prayer_map[state_attr('calendar.esolat_takwim','current')] }} - {{ as_timestamp(state_attr('calendar.esolat_takwim',(state_attr('calendar.esolat_takwim','current') | lower))) | timestamp_custom('%I:%M %p') }}<br /><b>Waktu Berikutnya: </b>{{ prayer_map[state_attr('calendar.esolat_takwim','next')] }}</ha-alert>

<ha-alert alert-type="info">Location: <b>{{ state_attr('calendar.esolat_takwim','zone') | upper }}</b></ha-alert></tr>
</table>

```
