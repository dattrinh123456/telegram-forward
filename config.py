"""Đọc / ghi config.yaml."""
import copy
import os

import yaml

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

DEFAULT = {
    "targets": [],            # nơi nhận tin (bắt buộc)
    "sources": [],            # trống = nghe tất cả chat
    "exclude_sources": [],    # chat không muốn quét
    "mode": "forward",        # forward (giữ nguồn) | copy (ẩn nguồn)
    "include_outgoing": False,  # có forward tin do chính bạn gửi không
    "delay": 1.0,             # giây nghỉ giữa các lần gửi
    "block_bots": True,       # bỏ qua tin do bot gửi (kể cả gửi "via @bot")
    "link_filters": {
        "domains": [],
        "exclude_domains": [],
        "keywords": [],
        "regex": [],
    },
}


def load():
    cfg = copy.deepcopy(DEFAULT)
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        filters = data.pop("link_filters", None) or {}
        cfg.update({k: v for k, v in data.items() if v is not None})
        cfg["link_filters"].update({k: v or [] for k, v in filters.items()})
    for key in ("targets", "sources", "exclude_sources"):
        cfg[key] = [parse_chat(x) for x in cfg[key] or []]
    return cfg


def save(cfg):
    with open(PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)


def parse_chat(x):
    """'-100123' -> -100123, '@abc' giữ nguyên."""
    s = str(x).strip()
    return int(s) if s.lstrip("-").isdigit() else s
