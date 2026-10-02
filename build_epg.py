# Erzeugt epg.xml: rumänischer Sendeplan (Quelle: epgshare01) mit Smart-IPTV-Kennungen.
# Dizi bekommt eine eigene Kennung (TimelessDizi.ro), weil Smart IPTV für "Dizi.ro" keine Daten hat.
import datetime as dt
import gzip
import io
import sys
import urllib.request
import xml.etree.ElementTree as ET

SOURCE = "https://epgshare01.online/epgshare01/epg_ripper_RO1.xml.gz"
OUT = "epg.xml"

# Kennung in der Quelle -> Kennung in der Playlist (Smart-IPTV-Codes)
ID_MAP = {
    "AMC.ro": "AMC.ro", "AXN.Black.ro": "AXNBlack.ro", "AXN.White.ro": "AXNWhite.ro", "AXN.ro": "AXN.ro",
    "Acasa.Gold.HD.ro": "AcasaGold.ro", "Acasa.ro": "Acasa.ro", "B1.TV.HD.ro": "B1TV.ro", "BBC.Earth.HD.ro": "BBCEarth.ro",
    "Cartoon.Network.ro": "CartoonNetwork.ro", "Cartoonito.ro": "Cartoonito.ro", "CineMAX.ro": "CineMAX.ro",
    "Cinemax.2.HD.ro": "Cinemax2.ro", "Comedy.Central.ro": "ComedyCentral.ro", "Crime.+.Investigation.ro": "CrimeInvestigation.ro",
    "Digi.24.ro": "Digi24.ro", "Digi.Sport.1.HD.ro": "DigiSport1.ro", "Digi.Sport.2.HD.ro": "DigiSport2.ro",
    "Digi.Sport.3.HD.ro": "DigiSport3.ro", "Digi.Sport.4.HD.ro": "DigiSport4.ro", "Disney.Channel.ro": "DisneyChannel.ro",
    "Disney.Junior.ro": "DisneyJunior.ro", "Diva.ro": "DivaUniversal.ro", "Dizi.ro": "TimelessDizi.ro", "DocuBox.HD.ro": "DocuBox.ro",
    "Duck.TV.ro": "DuckTV.ro", "E!.Entertainment.ro": "E!.ro", "Epic.Drama.ro": "EpicDrama.ro", "Etno.TV.ro": "EtnoTV.ro",
    "Eurosport.1.HD.ro": "Eurosport1.ro", "Eurosport.2.ro": "Eurosport2.ro", "FILM.CAFE.HD.ro": "FilmCafe.ro",
    "Favorit.ro": "Favorit.ro", "Film.Mania.ro": "FilmMania.ro", "FilmBox.Extra.HD.ro": "FilmBoxExtra.ro",
    "FilmBox.Family.ro": "FilmBoxFamily.ro", "Filmbox.Premium.ro": "FilmboxPremium.ro", "Filmbox.Stars.ro": "FilmboxStars.ro",
    "Filmbox.ro": "FilmBox.ro", "HBO.2.ro": "HBO2.ro", "HBO.3.ro": "HBO3.ro", "HBO.ro": "HBO.ro",
    "History.HD.ro": "HistoryChannel.ro", "Jimjam.ro": "Jimjam.ro", "Kanal.D.HD.ro": "KanalD.ro", "Kanal.D2.HD.ro": "KanalD2.ro",
    "Love.Nature.ro": "LoveNature.ro", "Mezzo.ro": "Mezzo.ro", "Minimax.ro": "MiniMax.ro",
    "National.Geographic.Wild.ro": "NatGeoWild.ro", "National.Geographic.ro": "NatGeo.ro", "National.TV.ro": "NationalTV.ro",
    "Nick.Jr.ro": "NickJr.ro", "Nicktoons.ro": "NickToons.ro", "PRO.TV.HD.ro": "PROTV.ro", "Prima.Sport.1.ro": "PrimaSport1.ro",
    "Prima.Sport.2.ro": "PrimaSport2.ro", "Prima.Sport.3.HD.ro": "PrimaSport3.ro", "Prima.Sport.4.HD.ro": "PrimaSport4.ro",
    "Pro.Arena.HD.ro": "PROArena.ro", "Pro.Cinema.ro": "PROCinema.ro", "Realitatea.Plus.ro": "RealitateaPlus.ro",
    "Sport.Extra.ro": "SportExtra.ro", "TV.Paprika.ro": "TVPaprika.ro", "TVR.1.ro": "TVR1.ro", "TVR.2.HD.ro": "TVR2.ro",
    "TVR.Sport.HD.ro": "TVRSport.ro", "Trinitas.TV.HD.ro": "TrinitasTV.ro", "Viasat.Explore.ro": "ViasatExplorer.ro",
    "Viasat.History.ro": "ViasatHistory.ro", "Viasat.Nature.HD.ro": "ViasatNature.ro", "Warner.TV.HD.ro": "WarnerTV.ro",
    "auto.motor.und.sport.channel.ro": "AutoMotorSport.ro",
}


def to_utc(stamp):
    # "20261001074000 -0500" -> "20261001124000 +0000"
    t = dt.datetime.strptime(stamp.strip(), "%Y%m%d%H%M%S %z")
    return t.astimezone(dt.timezone.utc).strftime("%Y%m%d%H%M%S +0000")


def main():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=120).read()
    root = ET.parse(io.BytesIO(gzip.decompress(raw))).getroot()

    tv = ET.Element("tv", {"generator-info-name": "ro-epg"})
    names = {}
    for ch in root.iter("channel"):
        if ch.get("id") in ID_MAP:
            names[ch.get("id")] = (ch.findtext("display-name") or ch.get("id")).strip()
    for src, dst in sorted(ID_MAP.items(), key=lambda x: x[1].lower()):
        if src in names:
            c = ET.SubElement(tv, "channel", {"id": dst})
            ET.SubElement(c, "display-name").text = "Dizi" if dst == "TimelessDizi.ro" else names[src]

    # Nur gestern bis +4 Tage, nur die nötigsten Felder: hält die Datei klein für alte Fernseher
    now = dt.datetime.now(dt.timezone.utc)
    lo = (now - dt.timedelta(hours=12)).strftime("%Y%m%d%H%M%S")
    hi = (now + dt.timedelta(days=4)).strftime("%Y%m%d%H%M%S")
    keep = {"title", "sub-title", "desc", "category", "episode-num"}
    count = {}
    for p in root.iter("programme"):
        src = p.get("channel")
        if src not in ID_MAP:
            continue
        start, stop = to_utc(p.get("start")), to_utc(p.get("stop"))
        if stop[:14] < lo or start[:14] > hi:
            continue
        q = ET.SubElement(tv, "programme", {"start": start, "stop": stop, "channel": ID_MAP[src]})
        for child in p:
            if child.tag in keep:
                q.append(child)
        count[src] = count.get(src, 0) + 1

    # Sicherheitsnetz: ohne Dizi-Daten die alte Datei behalten
    if count.get("Dizi.ro", 0) < 10:
        sys.exit(f"Zu wenig Dizi-Sendungen ({count.get('Dizi.ro', 0)}), epg.xml bleibt unverändert")

    ET.ElementTree(tv).write(OUT, encoding="utf-8", xml_declaration=True)
    print(f"{len(count)} Sender, {sum(count.values())} Sendungen, Dizi: {count['Dizi.ro']}")


if __name__ == "__main__":
    main()
