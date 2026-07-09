#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recupera gli ultimi video del canale @sicurissimo via YouTube Data API.
La chiave arriva SOLO da variabile d'ambiente (YOUTUBE_API_KEY) — mai hardcoded."""
import os, json, urllib.request, urllib.parse
def fetch_channel_videos(cfg, max_n=6):
    yt=cfg.get("youtube",{}); key=os.environ.get(yt.get("api_env","YOUTUBE_API_KEY"),"").strip()
    if not key: return []
    handle=yt.get("handle","sicurissimo").lstrip("@"); cid=yt.get("channel_id","")
    try:
        if not cid:
            u=f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={urllib.parse.quote(handle)}&key={key}"
            r=json.loads(urllib.request.urlopen(u,timeout=12).read()); it=r.get("items",[])
            if it: cid=it[0]["id"]
        if not cid: return []
        u=(f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={cid}"
           f"&order=date&type=video&maxResults={max_n}&key={key}")
        r=json.loads(urllib.request.urlopen(u,timeout=12).read())
        return [{"id":x["id"]["videoId"],"title":x["snippet"]["title"]}
                for x in r.get("items",[]) if x.get("id",{}).get("videoId")]
    except Exception as e:
        print("[yt]",e); return []
