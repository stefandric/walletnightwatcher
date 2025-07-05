import re
import asyncio
import requests
import nest_asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from models import User, Wallet
from db import get_db, init_db
from scan import WalletScanner
from summary import WalletSummaryFormatter
from dotenv import load_dotenv
import os
from security_scanner import SecurityScanner
from telegram.helpers import escape_markdown

CHAIN_ID_MAP = {
    "eth": "1", "ethereum": "1",
    "bsc": "56", "binance": "56",
    "polygon": "137", "matic": "137",
    "fantom": "250", "ftm": "250",
    "avax": "43114", "avalanche": "43114",
    "arbitrum": "42161", "optimism": "10",
    "sol": "101", "solana": "101"
}

BOT_TOKEN = os.getenv("BOT_TOKEN")
ETHERSCAN_API_KEY = os.getenv("DB_URL", "sqlite:///default.db")  # optional default

class NightWatcherBot:
    def __init__(self):
        self.app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("add", self.add_wallet))
        self.app.add_handler(CommandHandler("list", self.list_wallets))
        self.app.add_handler(CommandHandler("stop", self.stop_tracking))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_input)
        )
        self.app.add_handler(CommandHandler("scan", self.scan_wallet))
        self.app.add_handler(CommandHandler("check", check_command))

    async def scan_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 2:
            await update.message.reply_text("❗ Usage: /scan <wallet> <chain>")
            return
        
        address, chain = context.args
        wscanner = WalletScanner()
        data = wscanner.fetch_evm_portfolio(address, chain)

        if not data:
            await update.message.reply_text("⚠️ Could not fetch wallet data.")
            return

        # summary = wscanner.format_summary(address, chain, data)
        summary = WalletSummaryFormatter(address, chain, data).format_summary()
        await update.message.reply_text(summary, parse_mode='Markdown')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Welcome to NightWatcher!\n"
            # "Use /add <ETH_ADDRESS> to track a wallet.\n"
            # "Use /list to view tracked wallets.\n"
            "Use /scan <ADDRESS> chain to get all info about the wallet"
            "Use /check <ADDRESS> chain to make sure that the address is safe"
            # "Use /stop to delete all tracked wallets."
        )

    async def add_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if len(context.args) != 1:
            await update.message.reply_text("❗ Usage: /add <wallet_address>")
            return

        wallet = context.args[0].lower()
        if not re.match(r"^0x[a-fA-F0-9]{40}$", wallet):
            await update.message.reply_text("⚠️ Invalid Ethereum address.")
            return

        async for session in get_db():
            user = await session.scalar(select(User).where(User.chat_id == chat_id))
            if not user:
                user = User(chat_id=chat_id)
                session.add(user)
                await session.flush()

            existing = await session.scalar(
                select(Wallet).where(
                    Wallet.address == wallet, Wallet.user_id == user.id
                )
            )
            if existing:
                await update.message.reply_text(
                    "ℹ️ You're already tracking this wallet."
                )
            else:
                balance = self.get_eth_balance(wallet)
                session.add(
                    Wallet(address=wallet, user_id=user.id, last_balance=balance or 0)
                )
                await update.message.reply_text(f"✅ Now tracking: {wallet}")
            await session.commit()

    async def list_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        async for session in get_db():
            user = await session.scalar(select(User).where(User.chat_id == chat_id))
            if not user:
                await update.message.reply_text("🕵️ You're not tracking any wallets.")
                return

            wallets = await session.scalars(
                select(Wallet.address).where(Wallet.user_id == user.id)
            )
            addresses = wallets.all()
            if addresses:
                await update.message.reply_text(
                    "📋 Your tracked wallets:\n" + "\n".join(addresses)
                )
            else:
                await update.message.reply_text("🕵️ You're not tracking any wallets.")

    async def unknown_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 I didn't understand that. Try one of these:\n"
            "/add <wallet>\n/list\n/stop"
        )

    async def stop_tracking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        async for session in get_db():
            user = await session.scalar(select(User).where(User.chat_id == chat_id))
            if not user:
                await update.message.reply_text(
                    "ℹ️ You're not currently tracking anything."
                )
                return

            await session.execute(delete(Wallet).where(Wallet.user_id == user.id))
            await session.delete(user)
            await session.commit()

            await update.message.reply_text(
                "🛑 Stopped tracking all your wallets. You’ve been removed."
            )

    def get_eth_balance(self, wallet: str) -> float | None:
        url = (
            f"https://api.etherscan.io/api"
            f"?module=account&action=balance"
            f"&address={wallet}&tag=latest&apikey={ETHERSCAN_API_KEY}"
        )
        try:
            res = requests.get(url).json()
            if res["status"] == "1":
                return int(res["result"]) / 1e18
        except Exception:
            pass
        return None

    async def balance_watcher(self):
        while True:
            async for session in get_db():
                result = await session.execute(select(Wallet, User).join(User))
                rows = result.all()

                for wallet, user in rows:
                    current = self.get_eth_balance(wallet.address)
                    if current is None:
                        continue

                    if abs(current - wallet.last_balance) > 0:
                        diff = current - wallet.last_balance
                        wallet.last_balance = current
                        await session.commit()

                        sign = "⬆️" if diff > 0 else "⬇️"
                        msg = (
                            f"💸 Wallet: {wallet.address}\n"
                            f"{sign} Balance changed by {diff:+.6f} ETH\n"
                            f"New balance: {current:.6f} ETH"
                        )
                        try:
                            await self.app.bot.send_message(
                                chat_id=user.chat_id, text=msg
                            )
                        except Exception as e:
                            print(f"❗ Failed to notify {user.chat_id}: {e}")
            await asyncio.sleep(15)


    async def run(self):
        await init_db()
        asyncio.create_task(self.balance_watcher())
        print("✅ Bot is running...")
        await self.app.run_polling()



async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check <wallet_address> <chain>")
        return

    address = context.args[0]
    chain = context.args[1].lower() if len(context.args) > 1 else "eth"
    chain_id = CHAIN_ID_MAP.get(chain)

    if not chain_id:
        await update.message.reply_text(f"❌ Unknown chain: `{chain}`", parse_mode="MarkdownV2")
        return

    scanner = SecurityScanner(chain_id=chain_id)
    result = scanner.check_address(address)

    if not result["success"]:
        await update.message.reply_text(f"❌ Error: {result['error']}")
        return

    data = result["data"]
    flagged = data.get("is_sanctioned", False)
    flags = data.get("flags", [])

    if not flagged:
        await update.message.reply_text(
            f"✅ `{escape_markdown(address, version=2)}` appears safe",
            parse_mode="MarkdownV2"
        )
        return

    reason_text = ""
    if flags:
        escaped_flags = "\n• " + "\n• ".join(
            escape_markdown(flag, version=2) for flag in flags
        )
        reason_text = f"\n⚠️ *Reasons flagged:*\n{escaped_flags}"

    message = [
        f"⚠️ *Suspicious activity detected* for `{escape_markdown(address, version=2)}`{reason_text}"
    ]

    await update.message.reply_text("\n".join(message), parse_mode="MarkdownV2")



    