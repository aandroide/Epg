#!/usr/bin/env python3
"""
Androide_EPG

Converte l'XML di Open-EPG in un json per Kodi con i programmi in onda adesso.
Gli orari dell'XML sono in UTC e vengono convertiti in Europa/Roma.
"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

CACHE_DIR = 'cache'
OUTPUT_DIR = 'json'

TZ = ZoneInfo('Europe/Rome')
UTC = ZoneInfo('UTC')

# Se True, i canali senza programma in onda compaiono comunque nel json
# con la scritta "Nessun programma disponibile". Utile per accorgersi
# subito se Open-EPG non fornisce i dati di un canale.
SHOW_EMPTY_CHANNELS = True


def parse_xmltv_time(value: str) -> datetime:
    """Converte un orario XMLTV (es. 20261014180000 +0000) in Europa/Roma"""

    value = value.strip()
    if ' ' in value:
        dt = datetime.strptime(value, '%Y%m%d%H%M%S %z')
    else:
        dt = datetime.strptime(value, '%Y%m%d%H%M%S').replace(tzinfo=UTC)
    return dt.astimezone(TZ)


def parse_epg_xml(xml_file: str):
    """Parse EPG XML"""

    print(f" Parsing {xml_file}...")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Estrai canali
    all_channels = {}
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        display_name = channel.find('display-name')

        all_channels[channel_id] = {
            'id': channel_id,
            'name': display_name.text if display_name is not None and display_name.text else channel_id,
            'icon': None
        }

        icon = channel.find('icon')
        if icon is not None:
            all_channels[channel_id]['icon'] = icon.get('src')

    print(f" Trovati {len(all_channels)} canali")

    # Programmi in onda ORA (fuso Europa/Roma)
    now = datetime.now(TZ)
    current_programmes = {}
    next_programmes = {}

    for programme in root.findall('programme'):
        try:
            start_str = programme.get('start')
            stop_str = programme.get('stop')

            if not start_str or not stop_str:
                continue

            start = parse_xmltv_time(start_str)
            stop = parse_xmltv_time(stop_str)

            channel_id = programme.get('channel')

            title_elem = programme.find('title')
            desc_elem = programme.find('desc')

            if start <= now < stop:
                current_programmes[channel_id] = {
                    'start': start,
                    'stop': stop,
                    'start_str': start.strftime('%H:%M'),
                    'stop_str': stop.strftime('%H:%M'),
                    'title': title_elem.text if title_elem is not None and title_elem.text else 'In onda',
                    'desc': desc_elem.text if desc_elem is not None and desc_elem.text else ''
                }

            elif start > now:
                # Tiene il programma che parte per primo, a prescindere dall'ordine nel file
                saved = next_programmes.get(channel_id)
                if saved is None or start < saved['start']:
                    next_programmes[channel_id] = {
                        'start': start,
                        'start_str': start.strftime('%H:%M'),
                        'title': title_elem.text if title_elem is not None and title_elem.text else 'Prossimo'
                    }

        except Exception:
            continue

    print(f" {len(current_programmes)} canali con programmi in onda")

    return {
        'channels': all_channels,
        'current_programmes': current_programmes,
        'next_programmes': next_programmes
    }


def generate_androide_epg(epg_data):
    """Genera JSON semplice - solo EPG"""

    print("\n Generazione Androide_epg...")

    androide = {
        "SetViewMode": "503",
        "RefreshList": "10800",
        "fanart": "https://www.stadiotardini.it/wp-content/uploads/2016/12/mandrakata.jpg",
        "items": []
    }

    # Header semplice
    now = datetime.now(TZ)
    androide['items'].append({
        "title": "Androide - EPG",
        "link": "ignoreme",
        "info": f"Aggiornato: {now.strftime('%d/%m/%Y %H:%M')}"
    })

    # Canali in ordine alfabetico
    channels_list = list(epg_data['channels'].items())
    channels_list.sort(key=lambda x: x[1]['name'].lower())

    empty_count = 0

    for channel_id, channel_info in channels_list:
        current_prog = epg_data['current_programmes'].get(channel_id)
        next_prog = epg_data['next_programmes'].get(channel_id)

        if not current_prog:
            empty_count += 1
            if SHOW_EMPTY_CHANNELS:
                item = {
                    "title": f"{channel_info['name']} - Nessun programma disponibile",
                    "link": "ignoreme",
                    "info": "Open-EPG non fornisce dati per questo canale al momento."
                }
                if channel_info.get('icon'):
                    item["thumbnail"] = channel_info['icon']
                androide['items'].append(item)
            continue

        # Titolo: Nome canale - Orario Programma
        title = f"{channel_info['name']} - {current_prog['start_str']} {current_prog['title']}"

        # Info: orario + descrizione + prossimo
        info_parts = [
            f"In onda: {current_prog['start_str']} - {current_prog['stop_str']}"
        ]

        if current_prog['desc']:
            info_parts.append(f"\n{current_prog['desc']}")

        if next_prog:
            info_parts.append(f"\nA seguire ({next_prog['start_str']}): {next_prog['title']}")

        item = {
            "title": title,
            "link": "ignoreme",
            "info": '\n'.join(info_parts)
        }

        # Aggiungi icona se disponibile
        if channel_info.get('icon'):
            item["thumbnail"] = channel_info['icon']

        androide['items'].append(item)

    print(f" Canali senza programma in onda: {empty_count}")
    print(f" Generati {len(androide['items'])} items")

    return androide


def main():
    """Main"""

    print(" Androide - Solo EPG\n")

    epg_xml = os.path.join(CACHE_DIR, 'epg_raw.xml')

    if not os.path.exists(epg_xml):
        print(" EPG non trovato!")
        raise SystemExit(1)

    epg_data = parse_epg_xml(epg_xml)

    # Genera JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    androide_epg_json = generate_androide_epg(epg_data)

    output_file = os.path.join(OUTPUT_DIR, 'androide_epg.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(androide_epg_json, f, ensure_ascii=False, indent=2)

    print(f"\n Output: {output_file}")
    print(" Completato!\n")


if __name__ == '__main__':
    main()
