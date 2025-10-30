# 🚀 ULTIMATE FLASHLOAN SWARM - QUICK START

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (30 seconds)

```bash
pip install solana solders requests numpy pandas termcolor python-dotenv
```

### Step 2: Configure Environment (1 minute)

Create `.env` file in the project root:

```bash
# Required
SOLANA_PRIVATE_KEY="your_solana_private_key_here"
BIRDEYE_API_KEY="your_birdeye_api_key_here"
RPC_ENDPOINT="https://api.mainnet-beta.solana.com"

# Optional (for profit distribution)
BTC_WALLET_ADDRESS=""
ETH_WALLET_ADDRESS=""
```

**Get API Keys**:
- **BirdEye**: https://birdeye.so (free tier available)
- **Helius RPC** (recommended): https://helius.dev

### Step 3: Run the Bot (30 seconds)

```bash
python src/agents/ULTIMATE_FLASHLOAN_SWARM.py
```

That's it! 🎉

---

## 🎛️ Optional: Customize Settings (2 minutes)

Edit `flashloan_swarm_config.json`:

```json
{
  "initial_population": 5,
  "target_net_profit": 100.0,
  "min_confidence": 90.0,
  "destroyer_enabled": true
}
```

**Common Adjustments**:

### More Conservative
```json
{
  "target_net_profit": 50.0,
  "min_confidence": 95.0,
  "gas_safety_margin": 3.0
}
```

### More Aggressive
```json
{
  "target_net_profit": 200.0,
  "min_confidence": 85.0,
  "max_population": 30
}
```

---

## 📊 Monitor Performance

### Real-Time Output

```
✅ AGENT_0001: +$127.32
⚔️ FRONTRUN SUCCESS: +$63.66 | Damage: $63.66
🍼 AGENT_0001 → AGENT_0006

📊 SWARM STATISTICS
════════════════════════════════════════════════════════════════
   Runtime: 5.2 minutes
   Population: 6 alive / 1 dead (Peak: 6)
   Trades: 8/12 (66.7%)
   Total Profit: $847.23
   Net Profit: $834.78
════════════════════════════════════════════════════════════════
```

### Check Trade History

```bash
cat src/data/ultimate_flashloan_swarm/trades.csv
```

---

## 🔧 Troubleshooting

### "BIRDEYE_API_KEY not found"
**Fix**: Add `BIRDEYE_API_KEY="your_key"` to `.env`

### "No opportunities found"
**Fix**: Lower `target_net_profit` to 50.0 in config

### "All agents dying"
**Fix**: Lower `min_confidence` to 85.0 in config

### "Rate limit errors"
**Fix**: Get Helius RPC endpoint (faster, higher limits)

---

## 💡 Pro Tips

1. **Start Small**: Begin with conservative settings
2. **Monitor First Hour**: Watch for consistent profitability
3. **Adjust Gradually**: Increase aggression slowly
4. **Use VPS**: For 24/7 operation
5. **Check Logs**: `src/data/ultimate_flashloan_swarm/trades.csv`

---

## 📚 Full Documentation

- **Complete Guide**: `ULTIMATE_SWARM_README.md`
- **Validation Report**: `ULTIMATE_SWARM_VALIDATION.md`
- **Configuration**: `flashloan_swarm_config.json`

---

## 🎯 What to Expect

### First 10 Minutes
- Agents spawning
- Token discovery from BirdEye
- First opportunities detected
- Initial trades (may be conservative)

### First Hour
- Population stabilizes
- Success patterns emerge
- Profitable agents spawn children
- Weak agents die off

### First Day
- Optimized population established
- Consistent profit generation
- Competitor destruction active
- Strong genetic lineages emerge

---

## 🌙 Built by Moon Dev - To The Moon! 🚀

**Good luck and happy trading!** 💰
