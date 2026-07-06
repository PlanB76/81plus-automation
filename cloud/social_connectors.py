# -*- coding: utf-8 -*-
"""SOCIAL81+ CONNETTORI — pubblicazione automatica su FB / IG / TikTok / LinkedIn (TG gia' attivo altrove).
Ogni funzione legge i token SOLO da env (mai nel codice) e pubblica testo+immagine. Se il token manca -> skip pulito.
Token richiesti (in 81plus_secrets.env, li metti tu una volta):
  FB_PAGE_ID, FB_PAGE_TOKEN            (Facebook Page)
  IG_USER_ID, FB_PAGE_TOKEN            (Instagram business, stesso token FB/Meta)
  TIKTOK_TOKEN                         (TikTok Content Posting API, app approvata)
  LINKEDIN_URN, LINKEDIN_TOKEN         (LinkedIn, es. urn:li:person:xxxx o urn:li:organization:xxxx)"""
import os,json,urllib.request,urllib.parse
def _post(url,data=None,headers=None,method="POST"):
    body=json.dumps(data).encode() if isinstance(data,(dict,list)) else (urllib.parse.urlencode(data).encode() if data else None)
    r=urllib.request.Request(url,data=body,method=method,headers=headers or {})
    with urllib.request.urlopen(r,timeout=30) as resp: return json.loads(resp.read().decode() or "{}")
def facebook(caption,image_url=""):
    pid=os.environ.get("FB_PAGE_ID"); tok=os.environ.get("FB_PAGE_TOKEN")
    if not pid or not tok: return "skip(no FB token)"
    try:
        if image_url:
            return "fb:"+str(_post(f"https://graph.facebook.com/{pid}/photos",{"url":image_url,"caption":caption,"access_token":tok}).get("id","ok"))
        return "fb:"+str(_post(f"https://graph.facebook.com/{pid}/feed",{"message":caption,"access_token":tok}).get("id","ok"))
    except Exception as e: return f"fb-err:{e}"
def instagram(caption,image_url=""):
    uid=os.environ.get("IG_USER_ID"); tok=os.environ.get("FB_PAGE_TOKEN")
    if not uid or not tok or not image_url: return "skip(no IG token/img)"
    try:
        cid=_post(f"https://graph.facebook.com/v20.0/{uid}/media",{"image_url":image_url,"caption":caption,"access_token":tok}).get("id")
        if not cid: return "ig-err:no-container"
        return "ig:"+str(_post(f"https://graph.facebook.com/v20.0/{uid}/media_publish",{"creation_id":cid,"access_token":tok}).get("id","ok"))
    except Exception as e: return f"ig-err:{e}"
def tiktok(caption,video_url=""):
    tok=os.environ.get("TIKTOK_TOKEN")
    if not tok or not video_url: return "skip(no TikTok token/video)"
    try:
        h={"Authorization":f"Bearer {tok}","Content-Type":"application/json"}
        body={"post_info":{"title":caption[:150],"privacy_level":"SELF_ONLY"},"source_info":{"source":"PULL_FROM_URL","video_url":video_url}}
        return "tt:"+str(_post("https://open.tiktokapis.com/v2/post/publish/video/init/",body,h).get("data",{}).get("publish_id","ok"))
    except Exception as e: return f"tt-err:{e}"
def linkedin(caption,image_url=""):
    urn=os.environ.get("LINKEDIN_URN"); tok=os.environ.get("LINKEDIN_TOKEN")
    if not urn or not tok: return "skip(no LinkedIn token)"
    try:
        h={"Authorization":f"Bearer {tok}","Content-Type":"application/json","X-Restli-Protocol-Version":"2.0.0"}
        body={"author":urn,"lifecycleState":"PUBLISHED","specificContent":{"com.linkedin.ugc.ShareContent":{"shareCommentary":{"text":caption[:2900]},"shareMediaCategory":"NONE"}},"visibility":{"com.linkedin.ugc.MemberNetworkVisibility":"PUBLIC"}}
        return "li:"+str(_post("https://api.linkedin.com/v2/ugcPosts",body,h).get("id","ok"))
    except Exception as e: return f"li-err:{e}"
def post_all(caption,image_url="",video_url=""):
    return {"facebook":facebook(caption,image_url),"instagram":instagram(caption,image_url),
            "tiktok":tiktok(caption,video_url),"linkedin":linkedin(caption,image_url)}
if __name__=="__main__":
    print(json.dumps(post_all("Test SICURIX — Sicurezza semplice. 81plus.net","",""),ensure_ascii=False,indent=1))
