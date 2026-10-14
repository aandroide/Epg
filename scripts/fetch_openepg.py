#!/usr/bin/env python3
"""
Scarica EPG da Open-EPG
URL: https://www.open-epg.com/generate/EDanRWx8Pp.xml

"""

import os
import re
import sys
import requests

# CONFIGURAZIONE - Il tuo EPG xml
OPENEPG_URL = "https://www.open-epg.com/generate/EDanRWx8Pp.xml"

CACHE_DIR = 'cache'
OUTPUT_FILE = os.path.join(CACHE_DIR, 'epg_raw.xml')

# Se True, quando l'EPG risulta incompleto il file in cache NON viene
# sovrascritto e lo script termina con errore (il json precedente resta com'e').
# Se False, mostra solo un avviso e salva comunque il file.
BLOCK_IF_INCOMPLETE = False

# Soglia: percentuale minima di canali che devono avere programmi
MIN_CHANNELS_WITH_DATA = 0.5

# User-Agent Mozilla Firefox
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'


def check_completeness(content: bytes):
    """Conta canali dichiarati e canali con almeno un programma"""

    declared = set(re.findall(rb'<channel id="([^"]+)"', content))
    with_data = set(re.findall(rb'<programme [^>]*channel="([^"]+)"', content))

    print(f" Canali dichiarati: {len(declared)}")
    print(f" Canali con programmi: {len(with_data)}")

    missing = sorted(c.decode('utf-8', 'replace') for c in declared - with_data)
    if missing:
        print(f" Canali SENZA programmi ({len(missing)}):")
        for name in missing:
            print(f"   {name}")

    complete = True
    if declared and len(with_data) < len(declared) * MIN_CHANNELS_WITH_DATA:
        complete = False
        print(" ATTENZIONE: meno della meta dei canali ha programmi, EPG probabilmente incompleto")
        # Avviso giallo visibile nella pagina del run di GitHub Actions
        print("::warning::EPG Open-EPG incompleto, controlla la configurazione su open-epg.com")

    return complete


def download_epg():
    """Scarica EPG XML da Open-EPG"""

    print(" Downloading EPG...")
    print(f"   URL: {OPENEPG_URL}")
    print("   User-Agent: Mozilla Firefox")
    print("   Format: XML (non-compressed)\n")

    try:
        # Headers browser reale (senza br: requests non lo decomprime senza brotli)
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(OPENEPG_URL, headers=headers, timeout=30)
        response.raise_for_status()

        content = response.content

        # Verifica che sia XML valido
        if content.lstrip().startswith(b'<?xml'):
            print(" Valid XML file")
        else:
            print(" Errore: il file non inizia con un header XML, non lo salvo")
            return False

        # Controllo completezza PRIMA di scrivere il file
        complete = check_completeness(content)
        if not complete and BLOCK_IF_INCOMPLETE:
            print(" EPG incompleto: cache precedente mantenuta")
            return False

        # Salva XML diretto
        os.makedirs(CACHE_DIR, exist_ok=True)

        with open(OUTPUT_FILE, 'wb') as f:
            f.write(content)

        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f" Downloaded: {size_mb:.2f} MB")

        return True

    except requests.RequestException as e:
        print(f" Errore download: {e}")
        return False
    except Exception as e:
        print(f" Errore: {e}")
        return False


if __name__ == '__main__':
    success = download_epg()
    sys.exit(0 if success else 1)
