"""Telegram auto-forward: tin có link (khớp filter) -> forward sang đích."""
import asyncio
import logging
import os

from dotenv import load_dotenv
from telethon import TelegramClient, events, utils
from telethon.errors import FloodWaitError

import commands
import config
from links import extract_links, passes

os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/forward.log", encoding="utf-8")],
)
logging.getLogger("telethon").setLevel(logging.WARNING)
log = logging.getLogger("forward")

client = TelegramClient(os.getenv("SESSION", "forwarder"), int(os.environ["API_ID"]), os.environ["API_HASH"])
cfg = config.load()
# id đã resolve từ config (username -> id)
resolved = {"targets": [], "sources": set(), "exclude": set()}
me_id = None


async def resolve(ref):
    try:
        return utils.get_peer_id(await client.get_input_entity(ref))
    except Exception as e:
        log.warning("Không tìm thấy chat %r: %s", ref, e)
        return None


async def refresh():
    async def ids(refs):
        return [i for i in [await resolve(r) for r in refs] if i is not None]

    resolved["targets"] = await ids(cfg["targets"])
    resolved["sources"] = set(await ids(cfg["sources"]))
    resolved["exclude"] = set(await ids(cfg["exclude_sources"]))
    if cfg["sources"] and not resolved["sources"]:
        log.warning("Đã cài nguồn nhưng không resolve được nguồn nào -> sẽ không forward gì")


def should_check(chat_id, out):
    if chat_id == me_id or chat_id in resolved["targets"]:
        return False  # tránh vòng lặp forward
    if out and not cfg["include_outgoing"]:
        return False
    if chat_id in resolved["exclude"]:
        return False
    if cfg["sources"] and chat_id not in resolved["sources"]:
        return False
    return True


async def from_bot(msg):
    if msg.via_bot_id:
        return True
    try:
        sender = await msg.get_sender()
    except Exception:
        return False
    return bool(getattr(sender, "bot", False))


async def send(target, msgs):
    for attempt in range(3):
        try:
            if cfg["mode"] == "copy":
                if len(msgs) == 1:
                    await client.send_message(target, msgs[0])
                else:
                    await client.send_file(target, [m.media for m in msgs], caption=[m.text or "" for m in msgs])
            else:
                await client.forward_messages(target, msgs)
            return
        except FloodWaitError as e:
            log.warning("FloodWait %ss, chờ rồi thử lại...", e.seconds)
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            log.error("Gửi tới %s lỗi: %s", target, e)
            return


async def process(msgs, chat_id, out):
    if not should_check(chat_id, out):
        return
    links = [l for m in msgs for l in extract_links(m)]
    if not links:
        return
    if cfg["block_bots"] and await from_bot(msgs[0]):
        log.info("Bỏ qua (tin từ bot) chat=%s msg=%s", chat_id, msgs[0].id)
        return
    if not passes(links, cfg["link_filters"]):
        log.info("Bỏ qua (không khớp filter) chat=%s links=%s", chat_id, links)
        return
    if not resolved["targets"]:
        log.warning("Chưa có đích (/addtarget) -> không forward được")
        return
    log.info("Forward chat=%s msg=%s links=%s", chat_id, msgs[0].id, links)
    for target in resolved["targets"]:
        await send(target, msgs)
        await asyncio.sleep(cfg["delay"])


@client.on(events.NewMessage)
async def on_message(event):
    if event.chat_id == me_id and event.raw_text.startswith("/"):
        if await commands.handle(event, cfg, refresh):
            return
    if event.message.grouped_id:
        return  # album được xử lý ở on_album
    await process([event.message], event.chat_id, event.out)


@client.on(events.Album)
async def on_album(event):
    await process(event.messages, event.chat_id, event.messages[0].out)


async def main():
    global me_id
    await client.start()
    me = await client.get_me()
    me_id = me.id
    await client.get_dialogs()  # nạp cache để resolve được id dạng số
    await refresh()
    log.info("Đăng nhập: %s (@%s)", me.first_name, me.username)
    log.info("Nguồn: %s | Đích: %s", cfg["sources"] or "TẤT CẢ", cfg["targets"] or "(chưa có)")
    log.info("Gõ /help trong Saved Messages để xem lệnh. Ctrl+C để dừng.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        log.info("Đã dừng.")
