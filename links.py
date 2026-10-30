"""Tách link khỏi tin nhắn và kiểm tra theo filter."""
import re
from urllib.parse import urlparse

from telethon.tl.types import MessageEntityTextUrl, MessageEntityUrl

# Dự phòng khi tin không có entity (hiếm, nhưng có thể xảy ra)
URL_RE = re.compile(r"(?:https?://|www\.|t\.me/)\S+", re.I)


def extract_links(msg):
    """Lấy mọi link trong tin: text/caption, link ẩn sau chữ, nút bấm."""
    links = []
    for ent, txt in msg.get_entities_text():
        if isinstance(ent, MessageEntityUrl):
            links.append(txt.strip())
        elif isinstance(ent, MessageEntityTextUrl):
            links.append(ent.url)

    markup = msg.reply_markup
    for row in getattr(markup, "rows", None) or []:
        for btn in row.buttons:
            # tên class nút link khác nhau giữa các bản Telethon -> đọc thẳng .url
            url = getattr(btn, "url", None)
            if isinstance(url, str) and url.startswith(("http://", "https://", "tg://")):
                links.append(url)

    if not links and msg.message:
        links = URL_RE.findall(msg.message)
    return list(dict.fromkeys(links))


def host_of(url):
    """'https://www.Shopee.vn/abc' -> 'shopee.vn'"""
    url = url.strip()
    if "://" not in url:
        url = "http://" + url
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def domain_match(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def passes(links, f):
    """
    - Bỏ các link thuộc exclude_domains.
    - Không cài filter include nào (domains/keywords/regex) -> còn link là qua.
    - Có cài -> ít nhất 1 link khớp 1 trong các filter (OR).
    """
    links = [l for l in links if not domain_match(host_of(l), f["exclude_domains"])]
    if not links:
        return False
    if not (f["domains"] or f["keywords"] or f["regex"]):
        return True
    for link in links:
        low = link.lower()
        if f["domains"] and domain_match(host_of(link), f["domains"]):
            return True
        if any(k in low for k in f["keywords"]):
            return True
        if any(re.search(r, link, re.I) for r in f["regex"]):
            return True
    return False
