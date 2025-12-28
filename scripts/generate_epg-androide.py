#!/usr/bin/env python3
"""
Androide_EPG - Genera 2 JSON separati (Sky e DAZN)

"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime

CACHE_DIR = 'cache'
OUTPUT_DIR = 'json'

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
            'name': display_name.text if display_name is not None else channel_id,
            'icon': None
        }
        
        icon = channel.find('icon')
        if icon is not None:
            all_channels[channel_id]['icon'] = icon.get('src')
    
    print(f" Trovati {len(all_channels)} canali")
    
    # Programmi in onda ORA
    now = datetime.now()
    current_programmes = {}
    next_programmes = {}
    
    for programme in root.findall('programme'):
        try:
            start_str = programme.get('start')
            stop_str = programme.get('stop')
            
            if not start_str or not stop_str:
                continue
            
            start = datetime.strptime(start_str.split()[0], '%Y%m%d%H%M%S')
            stop = datetime.strptime(stop_str.split()[0], '%Y%m%d%H%M%S')
            
            channel_id = programme.get('channel')
            
            if start <= now < stop:
                title_elem = programme.find('title')
                desc_elem = programme.find('desc')
                
                current_programmes[channel_id] = {
                    'start': start,
                    'stop': stop,
                    'start_str': start.strftime('%H:%M'),
                    'stop_str': stop.strftime('%H:%M'),
                    'title': title_elem.text if title_elem is not None else 'In onda',
                    'desc': desc_elem.text if desc_elem is not None else ''
                }
            
            elif start > now and channel_id not in next_programmes:
                title_elem = programme.find('title')
                
                next_programmes[channel_id] = {
                    'start': start,
                    'start_str': start.strftime('%H:%M'),
                    'title': title_elem.text if title_elem is not None else 'Prossimo'
                }
                
        except Exception:
            continue
    
    print(f" {len(current_programmes)} canali con programmi in onda")
    
    return {
        'channels': all_channels,
        'current_programmes': current_programmes,
        'next_programmes': next_programmes
    }

def categorize_channel(channel_name):
    """Categorizza il canale in base al nome"""
    
    name_lower = channel_name.lower()
    
    # SPORT
    if any(keyword in name_lower for keyword in ['sport', 'calcio', 'f1', 'motogp', 'tennis', 'golf']):
        return 'SPORT'
    
    # CINEMA
    if 'cinema' in name_lower:
        return 'CINEMA'
    
    # BAMBINI
    if any(keyword in name_lower for keyword in ['cartoon', 'kids', 'junior', 'bambini', 'boing', 'cartoonito']):
        return 'BAMBINI'
    
    # INTRATTENIMENTO (tutto il resto)
    return 'INTRATTENIMENTO'

def is_dazn_channel(channel_name):
    """Verifica se è un canale DAZN"""
    return 'dazn' in channel_name.lower()

def generate_json(epg_data, include_dazn=True, only_dazn=False):
    """Genera JSON filtrato"""
    
    androide = {
        "SetViewMode": "51",
        "RefreshList": "10800",
        "items": []
    }
    
    # Header
    now = datetime.now()
    if only_dazn:
        androide['items'].append({
            "title": "DAZN - EPG",
            "link": "ignoreme",
            "info": f"Aggiornato: {now.strftime('%d/%m/%Y %H:%M')}"
        })
    else:
        androide['items'].append({
            "title": "Sky - EPG",
            "link": "ignoreme",
            "info": f"Aggiornato: {now.strftime('%d/%m/%Y %H:%M')}"
        })
    
    # Raggruppa canali per categoria
    categories = {
        'CINEMA': [],
        'INTRATTENIMENTO': [],
        'SPORT': [],
        'BAMBINI': []
    }
    
    for channel_id, channel_info in epg_data['channels'].items():
        current_prog = epg_data['current_programmes'].get(channel_id)
        
        if not current_prog:
            continue
        
        # Filtra in base a DAZN
        is_dazn = is_dazn_channel(channel_info['name'])
        
        if only_dazn and not is_dazn:
            continue  # Skip canali non-DAZN se vogliamo solo DAZN
        
        if not include_dazn and is_dazn:
            continue  # Skip DAZN se vogliamo solo Sky
        
        category = categorize_channel(channel_info['name'])
        
        # Titolo
        title = f"{channel_info['name']} - {current_prog['start_str']} {current_prog['title']}"
        
        # Info
        next_prog = epg_data['next_programmes'].get(channel_id)
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
        
        if channel_info.get('icon'):
            item["thumbnail"] = channel_info['icon']
        
        categories[category].append(item)
    
    # Aggiungi le categorie
    category_order = ['CINEMA', 'INTRATTENIMENTO', 'SPORT', 'BAMBINI']
    
    for category in category_order:
        if not categories[category]:
            continue
        
        # Header categoria
        if only_dazn:
            link = "https://raw.githubusercontent.com/aandroide/Epg/main/json/dazn_epg.json"
        else:
            link = "https://raw.githubusercontent.com/aandroide/Epg/main/json/sky_epg.json"
        
        androide['items'].append({
            "title": category,
            "externallink": link,
            "info": f"{len(categories[category])} canali"
        })
        
        # Ordina alfabeticamente
        categories[category].sort(key=lambda x: x['title'])
        
        # Aggiungi i canali
        for item in categories[category]:
            androide['items'].append(item)
    
    return androide

def main():
    """Main"""
    
    print(" Androide - Generazione 2 JSON separati\n")
    
    epg_xml = os.path.join(CACHE_DIR, 'epg_raw.xml')
    
    if not os.path.exists(epg_xml):
        print(" EPG non trovato!")
        return
    
    epg_data = parse_epg_xml(epg_xml)
    
    # Crea directory output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Genera JSON SKY (senza DAZN)
    print("\n Generazione Sky EPG...")
    sky_json = generate_json(epg_data, include_dazn=False, only_dazn=False)
    
    sky_file = os.path.join(OUTPUT_DIR, 'sky_epg.json')
    with open(sky_file, 'w', encoding='utf-8') as f:
        json.dump(sky_json, f, ensure_ascii=False, indent=2)
    
    print(f" Generati {len(sky_json['items'])} items per Sky")
    print(f" Output: {sky_file}")
    
    # 2. Genera JSON DAZN (solo DAZN)
    print("\n Generazione DAZN EPG...")
    dazn_json = generate_json(epg_data, include_dazn=True, only_dazn=True)
    
    dazn_file = os.path.join(OUTPUT_DIR, 'dazn_epg.json')
    with open(dazn_file, 'w', encoding='utf-8') as f:
        json.dump(dazn_json, f, ensure_ascii=False, indent=2)
    
    print(f" Generati {len(dazn_json['items'])} items per DAZN")
    print(f" Output: {dazn_file}")
    
    print("\n Completato! 2 JSON generati\n")

if __name__ == '__main__':
    main()
