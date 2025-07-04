# wallet_summary.py

class WalletSummaryFormatter:
    def __init__(self, address: str, chain: str, portfolio: dict):
        self.address = address
        self.chain = chain
        self.native = portfolio.get("native", {})
        self.tokens = portfolio.get("tokens", [])

    def format_summary(self) -> str:
        native_amount = self.native.get("balance", 0)
        native_usd = float(self.native.get("usdValue", 0))
        native_symbol = self.native.get("symbol", self.chain.upper())

        token_count = len(self.tokens)
        token_usd_total = sum(float(t.get("usdValue", 0)) for t in self.tokens)
        total_usd = native_usd + token_usd_total

        top_tokens = sorted(
            self.tokens,
            key=lambda t: float(t.get("usdValue", 0)),
            reverse=True
        )[:3]

        token_summary = "\n".join(
            f"- {t['symbol']}: ${float(t['usdValue']):,.2f}"
            for t in top_tokens if float(t.get("usdValue", 0)) > 0
        )

        profile = self.get_profile(total_usd, token_count)

        return (
            f"🔍 Scanned wallet: `{self.address}`\n"
            f"🔗 Chain: `{self.chain}`\n"
            f"💰 Native balance: {native_amount:.6f} {native_symbol} "
            f"(${native_usd:,.2f})\n"
            f"📦 ERC-20 tokens held: {token_count}\n"
            f"💳 Token value: ${token_usd_total:,.2f}\n"
            f"🧮 Total portfolio value: ${total_usd:,.2f}\n\n"
            f"🎯 Profile: {profile}\n"
            f"{'🔥 Top tokens:\n' + token_summary if token_summary else '💤 No active tokens'}"
        )

    def get_profile(self, total_usd, token_count):
        if total_usd > 100_000:
            return "🦈 Whale wallet"
        elif total_usd > 10_000:
            return "💼 Pro trader"
        elif token_count > 20:
            return "📦 Degen collector"
        elif token_count == 0 and total_usd > 1_000:
            return "🔒 Cold storage"
        else:
            return "🧪 Fresh wallet or inactive"