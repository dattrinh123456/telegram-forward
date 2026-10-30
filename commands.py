"""Lệnh quản lý, gõ trong Saved Messages (Tin nhắn đã lưu) của bạn."""
import re

import config
from links import URL_RE, host_of, passes

HELP = """📋 Lệnh (gõ trong Saved Messages):

/status – xem cấu hình hiện tại
/test <nội dung> – thử xem tin này có bị forward không

Chat (id hoặc @username):
/addtarget, /deltarget – nơi nhận tin
/addsource, /delsource – nguồn (trống = nghe tất cả)
/addexclude, /delexclude – chat bỏ qua

Filter link (trống hết = có link là forward):
/adddomain, /deldomain – chỉ lấy domain này
/addexdomain, /delexdomain – bỏ link domain này
/addkw, /delkw – link chứa chữ này
/addregex, /delregex – link khớp regex

/clear <targets|sources|exclude|domains|exdomains|kw|regex>
/mode forward|copy
/delay <giây>
/blockbots on|off – chặn / cho phép tin từ bot

Thêm nhiều giá trị một lần: /adddomain shopee.vn t.me"""

# tên lệnh -> (khóa trong config, khóa con hoặc None)
LISTS = {
    "target": ("targets", None),
    "source": ("sources", None),
    "exclude": ("exclude_sources", None),
    "domain": ("link_filters", "domains"),
    "exdomain": ("link_filters", "exclude_domains"),
    "kw": ("link_filters", "keywords"),
    "regex": ("link_filters", "regex"),
}
CLEAR_ALIASES = {"targets": "target", "sources": "source", "domains": "domain",
                 "exdomains": "exdomain", "keywords": "kw"}


def _list(cfg, name):
    key, sub = LISTS[name]
    return cfg[key][sub] if sub else cfg[key]


def _normalize(name, value):
    if name in ("target", "source", "exclude"):
        return config.parse_chat(value)
    if name in ("domain", "exdomain"):
        return host_of(value)
    if name == "kw":
        return value.lower()
    return value


def status(cfg):
    f = cfg["link_filters"]
    show = lambda xs: ", ".join(map(str, xs)) or "(trống)"
    return (
        "⚙️ Cấu hình\n"
        f"Đích: {show(cfg['targets'])}\n"
        f"Nguồn: {show(cfg['sources']) if cfg['sources'] else 'TẤT CẢ chat'}\n"
        f"Bỏ qua: {show(cfg['exclude_sources'])}\n"
        f"Mode: {cfg['mode']} | Delay: {cfg['delay']}s\n"
        f"Chặn bot: {'bật' if cfg['block_bots'] else 'tắt'}\n\n"
        "🔗 Filter link\n"
        f"Domain: {show(f['domains'])}\n"
        f"Bỏ domain: {show(f['exclude_domains'])}\n"
        f"Từ khóa: {show(f['keywords'])}\n"
        f"Regex: {show(f['regex'])}"
    )


async def handle(event, cfg, on_change):
    """Trả về True nếu đã xử lý lệnh."""
    text = event.raw_text.strip()
    cmd, _, rest = text.partition(" ")
    cmd, rest = cmd.lower().lstrip("/"), rest.strip()
    reply = None

    if cmd in ("help", "start"):
        reply = HELP
    elif cmd == "status":
        reply = status(cfg)
    elif cmd == "test":
        links = URL_RE.findall(rest)
        if not links:
            reply = "❌ Không tìm thấy link → KHÔNG forward"
        else:
            ok = passes(links, cfg["link_filters"])
            reply = f"Link: {', '.join(links)}\n" + ("✅ SẼ forward" if ok else "❌ KHÔNG forward (không khớp filter)")
    elif cmd == "mode":
        if rest not in ("forward", "copy"):
            reply = "Dùng: /mode forward hoặc /mode copy"
        else:
            cfg["mode"] = rest
            reply = f"✅ Mode = {rest}"
    elif cmd == "delay":
        try:
            cfg["delay"] = max(0.0, float(rest))
            reply = f"✅ Delay = {cfg['delay']}s"
        except ValueError:
            reply = "Dùng: /delay 1.5"
    elif cmd == "blockbots":
        if rest not in ("on", "off"):
            reply = "Dùng: /blockbots on hoặc /blockbots off"
        else:
            cfg["block_bots"] = rest == "on"
            reply = "✅ Đang chặn tin từ bot" if cfg["block_bots"] else "✅ Cho phép tin từ bot"
    elif cmd == "clear":
        name = CLEAR_ALIASES.get(rest, rest)
        if name not in LISTS:
            reply = "Dùng: /clear targets|sources|exclude|domains|exdomains|kw|regex"
        else:
            _list(cfg, name).clear()
            reply = f"✅ Đã xóa hết {rest}"
    elif cmd[:3] in ("add", "del") and cmd[3:] in LISTS:
        action, name = cmd[:3], cmd[3:]
        if not rest:
            reply = f"Thiếu giá trị. VD: /{cmd} ..."
        else:
            # regex có thể chứa dấu cách nên giữ nguyên cả chuỗi
            values = [rest] if name == "regex" else re.split(r"[\s,]+", rest)
            values = [_normalize(name, v) for v in values if v]
            if name == "regex" and action == "add":
                try:
                    re.compile(values[0])
                except re.error as e:
                    values, reply = [], f"❌ Regex lỗi: {e}"
            target = _list(cfg, name)
            for v in values:
                if action == "add" and v not in target:
                    target.append(v)
                elif action == "del":
                    target[:] = [x for x in target if str(x) != str(v)]
            if values:
                reply = f"✅ {'Đã thêm' if action == 'add' else 'Đã xóa'}: {', '.join(map(str, values))}"
    else:
        return False

    if cmd not in ("help", "start", "status", "test"):
        config.save(cfg)
        await on_change()
    await event.reply(reply)
    return True
