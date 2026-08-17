import os
import uuid
import asyncio
import time
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

DEVELOPER_URL = "https://www.instagram.com/prashant.07z"

FILE_EXPIRY_SECONDS = 15 * 60

# download_id -> {"path": "...", "created": timestamp}
files = {}

# chat_id -> processing message
processing_messages = {}


# =========================================================
# KEYBOARDS
# =========================================================

def main_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📖 How to Use",
                callback_data="help"
            ),
            InlineKeyboardButton(
                "📸 Developer",
                url=DEVELOPER_URL
            )
        ],
        [
            InlineKeyboardButton(
                "🔗 Send Instagram Link",
                callback_data="send_link"
            )
        ]
    ])


def media_keyboard(download_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬇️ Download Media",
                callback_data=f"download:{download_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔗 Another Link",
                callback_data="send_link"
            ),
            InlineKeyboardButton(
                "📸 Developer",
                url=DEVELOPER_URL
            )
        ]
    ])


# =========================================================
# URL VALIDATION
# =========================================================

def is_instagram_url(url):

    try:

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower()

        return (
            hostname == "instagram.com"
            or hostname.endswith(".instagram.com")
            or hostname == "instagr.am"
        )

    except Exception:

        return False


def detect_content_type(url):

    try:

        path = urlparse(url).path.lower()

        if "/reel/" in path or "/reels/" in path:
            return "Reel"

        if "/p/" in path:
            return "Post"

        if "/stories/" in path:
            return "Story"

        if "/tv/" in path:
            return "Video"

        return "Instagram Media"

    except Exception:

        return "Instagram Media"


# =========================================================
# FILE CLEANUP
# =========================================================

def cleanup_expired_files():

    current_time = time.time()

    expired_ids = []

    for download_id, data in list(files.items()):

        created = data.get("created", 0)
        file_path = Path(data.get("path", ""))

        if current_time - created > FILE_EXPIRY_SECONDS:

            expired_ids.append(download_id)

            try:

                if file_path.exists():
                    file_path.unlink()

            except Exception as error:

                print(
                    "CLEANUP ERROR:",
                    repr(error),
                    flush=True
                )

    for download_id in expired_ids:

        files.pop(download_id, None)


# =========================================================
# DOWNLOAD FUNCTION
# =========================================================

def download_media(url):

    file_id = uuid.uuid4().hex

    output = str(
        DOWNLOAD_DIR / f"{file_id}.%(ext)s"
    )
    options = {
        "outtmpl": output,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        filename = Path(
            ydl.prepare_filename(info)
        )

    if filename.exists():

        return filename

    possible_files = list(
        DOWNLOAD_DIR.glob(
            f"{file_id}.*"
        )
    )

    if possible_files:

        return possible_files[0]

    return None


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    cleanup_expired_files()

    text = (
        "📥 <b>INSTAGRAM REEL • POST • STORY DOWNLOADER</b>\n\n"

        "🚀 <b>Fast & Simple Instagram Media Downloader</b>\n\n"

        "📌 <b>How to use</b>\n"
        "1️⃣ Copy a public Instagram link.\n"
        "2️⃣ Send the link to this bot.\n"
        "3️⃣ Wait while we process your media.\n"
        "4️⃣ Tap <b>Download Media</b> when ready.\n\n"

        "🎬 <b>Supported Content</b>\n"
        "• Instagram Reels\n"
        "• Instagram Posts\n"
        "• Accessible Stories*\n\n"

        "⚡ <b>Quick Commands</b>\n"
        "/start — Start the bot\n"
        "/help — How to use\n"
        "/about — About this bot\n"
        "/cancel — Cancel current operation\n\n"

        "👨‍💻 <b>Developer:</b> Prashant\n\n"

        "🔒 Please download content you have permission to use.\n\n"

        "<i>*Availability depends on Instagram access and privacy.</i>"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "📖 <b>HOW TO USE</b>\n\n"

        "1️⃣ <b>Copy the link</b>\n"
        "Copy a public Instagram Reel, Post, "
        "or accessible Story link.\n\n"

        "2️⃣ <b>Send the link</b>\n"
        "Paste it directly into this chat.\n\n"

        "3️⃣ <b>Wait for processing</b>\n"
        "The bot will fetch and prepare the media.\n\n"

        "4️⃣ <b>Download</b>\n"
        "When the media is ready, tap "
        "<b>⬇️ Download Media</b>.\n\n"

        "⚠️ <b>Important</b>\n"
        "Private, restricted, deleted, or unavailable "
        "content may not be processed."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔗 Send Instagram Link",
                    callback_data="send_link"
                )
            ]
        ])
    )


# =========================================================
# ABOUT
# =========================================================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "ℹ️ <b>ABOUT THIS BOT</b>\n\n"

        "📥 <b>Instagram Reel • Post • Story Downloader</b>\n\n"

        "A simple Telegram bot designed to process "
        "supported Instagram media links.\n\n"

        "✨ <b>Features</b>\n"
        "• Reel support\n"
        "• Post support\n"
        "• Accessible Story support\n"
        "• Download button\n"
        "• Automatic temporary-file cleanup\n"
        "• Simple and clean interface\n\n"

        "👨‍💻 <b>Developer:</b> Prashant"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📸 Developer Instagram",
                    url=DEVELOPER_URL
                )
            ]
        ])
    )
    # =========================================================
# CANCEL
# =========================================================

async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    processing = processing_messages.pop(
        chat_id,
        None
    )

    if processing:

        try:

            await processing.delete()

        except Exception:
            pass

        await update.message.reply_text(
            "🛑 <b>Operation cancelled.</b>\n\n"
            "You can send another Instagram link whenever you're ready.",
            parse_mode="HTML"
        )

    else:

        await update.message.reply_text(
            "ℹ️ <b>No active operation.</b>\n\n"
            "Send an Instagram link to start a new download.",
            parse_mode="HTML"
        )


# =========================================================
# HANDLE INSTAGRAM LINK
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    cleanup_expired_files()

    url = update.message.text.strip()

    chat_id = update.effective_chat.id

    if not is_instagram_url(url):

        await update.message.reply_text(
            "❌ <b>Invalid Instagram Link</b>\n\n"
            "Please send a valid public Instagram "
            "Reel, Post, or accessible Story link.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📖 How to Use",
                        callback_data="help"
                    )
                ]
            ])
        )

        return

    content_type = detect_content_type(url)

    processing = await update.message.reply_text(
        "⏳ <b>PROCESSING YOUR MEDIA</b>\n\n"

        "🔍 <b>Step 1:</b> Checking link\n"
        "📱 <b>Platform:</b> Instagram\n"
        f"🎬 <b>Type:</b> {content_type}\n\n"

        "📥 <b>Step 2:</b> Fetching media\n"
        "⚙️ <b>Step 3:</b> Preparing your file\n\n"

        "Please wait...",
        parse_mode="HTML"
    )

    processing_messages[chat_id] = processing

    try:

        file_path = await asyncio.to_thread(
            download_media,
            url
        )

        processing_messages.pop(
            chat_id,
            None
        )

        if not file_path:

            await processing.edit_text(
                "❌ <b>UNABLE TO PROCESS</b>\n\n"

                "Possible reasons:\n"
                "• The content is private.\n"
                "• The media is unavailable.\n"
                "• The link is invalid or expired.\n"
                "• Instagram is temporarily unavailable.\n\n"

                "Please try another accessible public link.",
                parse_mode="HTML"
            )

            return

        download_id = uuid.uuid4().hex

        files[download_id] = {
            "path": str(file_path),
            "created": time.time()
        }

        keyboard = media_keyboard(
            download_id
        )

        try:
            await processing.delete()
        except Exception as error:
            print(
                "PROCESSING MESSAGE DELETE ERROR:",
                repr(error),
                flush=True
                )

        extension = file_path.suffix.lower()

        caption = (
            "✅ <b>MEDIA READY!</b>\n\n"
            "📱 <b>Platform:</b> Instagram\n"
            f"🎬 <b>Type:</b> {content_type}\n"
            "📦 <b>Status:</b> Ready\n\n"
            "👇 <b>Choose an action below</b>"
        )

        # VIDEO

        if extension in [
            ".mp4",
            ".mov",
            ".mkv",
            ".webm"
        ]:

            with open(
                file_path,
                "rb"
            ) as video:

                await update.message.reply_video(
                    video=video,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        # IMAGE

        elif extension in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]:
            with open(
                file_path,
                "rb"
            ) as photo:

                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        # OTHER FILE

        else:

            with open(
                file_path,
                "rb"
            ) as document:

                await update.message.reply_document(
                    document=document,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

    except Exception as error:

        processing_messages.pop(
            chat_id,
            None
        )

        print(
            "TELEGRAM/PROCESSING ERROR:",
            repr(error),
            flush=True
        )

        # Do not show a false "Download failed" message.
        # The media may already have been downloaded successfully.
        return


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    cleanup_expired_files()

    # HELP

    if query.data == "help":

        await query.message.reply_text(
            "📖 <b>HOW TO USE</b>\n\n"

            "1️⃣ Copy a public Instagram Reel, "
            "Post, or accessible Story link.\n\n"

            "2️⃣ Send the link here.\n\n"

            "3️⃣ Wait while the media is processed.\n\n"

            "4️⃣ Tap <b>⬇️ Download Media</b> "
            "when your media is ready.\n\n"

            "⚠️ Private or unavailable content "
            "may not be processed.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔗 Send Instagram Link",
                        callback_data="send_link"
                    )
                ]
            ])
        )

        return

    # SEND LINK

    if query.data == "send_link":

        await query.message.reply_text(
            "🔗 <b>SEND YOUR INSTAGRAM LINK</b>\n\n"
            "Paste a public Instagram Reel, "
            "Post, or accessible Story URL here.",
            parse_mode="HTML"
        )

        return

    # DOWNLOAD

    if query.data.startswith("download:"):

        download_id = query.data.split(
            ":",
            1
        )[1]

        data = files.get(
            download_id
        )

        if not data:

            await query.message.reply_text(
                "❌ <b>DOWNLOAD EXPIRED</b>\n\n"
                "This file is no longer available.\n"
                "Please send the Instagram link again.",
                parse_mode="HTML"
            )

            return

        file_path = Path(
            data["path"]
        )

        if not file_path.exists():

            files.pop(
                download_id,
                None
            )

            await query.message.reply_text(
                "❌ <b>FILE NOT FOUND</b>\n\n"
                "Please send the Instagram link again.",
                parse_mode="HTML"
            )

            return

        try:

            await query.message.reply_document(
                document=str(file_path),
                caption=(
                    "⬇️ <b>DOWNLOAD READY!</b>\n\n"
                    "Your media file is attached above."
                ),
                parse_mode="HTML"
            )

        except Exception as error:
            print(
                "BUTTON ERROR:",
                repr(error),
                flush=True
            )

            await query.message.reply_text(
                "❌ Unable to prepare the download.",
                parse_mode="HTML"
            )


# =========================================================
# BOT COMMAND MENU
# =========================================================

async def setup_commands(
    application: Application
):

    await application.bot.set_my_commands([
        BotCommand(
            "start",
            "Start the downloader"
        ),
        BotCommand(
            "help",
            "How to use the bot"
        ),
        BotCommand(
            "about",
            "About this bot"
        ),
        BotCommand(
            "cancel",
            "Cancel current operation"
        ),
    ])


# =========================================================
# MAIN
# =========================================================

app = Application.builder().token(
    BOT_TOKEN
).post_init(
    setup_commands
).build()


app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CommandHandler(
        "help",
        help_command
    )
)

app.add_handler(
    CommandHandler(
        "about",
        about_command
    )
)

app.add_handler(
    CommandHandler(
        "cancel",
        cancel_command
    )
)

app.add_handler(
    CallbackQueryHandler(
        button_handler
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)


print(
    "🤖 Instagram Reel • Post • Story Downloader is running...",
    flush=True
)


app.run_polling()