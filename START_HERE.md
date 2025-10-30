# 🚀 START HERE - Flashloan Arbitrage Swarm

## 🎯 Quick Decision Guide

**Want to trade NOW?**
→ Use `ULTIMATE_FLASHLOAN_SWARM.py` (production-ready)

**Want agent personalities & research?**
→ Use `ELIZA_FLASHLOAN_SWARM.py` (ElizaOS-inspired)

**Need on-chain execution?**
→ Build & deploy `solana_program/` (Rust smart contract)

---

## 📦 What You Have

### 1. Production Trading Bot
**File**: `src/agents/ULTIMATE_FLASHLOAN_SWARM.py`

**Features**:
- Complete flashloan arbitrage
- Monte Carlo simulation (10k iterations)
- Game theory gas bidding
- Competitor destruction
- Real BirdEye & Jupiter APIs
- $100+ profit targeting
- 90%+ confidence threshold

**Use for**: Real trading, profit generation

---

### 2. Research/Experimental Bot  
**File**: `src/agents/ELIZA_FLASHLOAN_SWARM.py`

**ElizaOS-Inspired Features**:
- **Agent Personalities**: 4 character types (Alpha, Sigma, Beta, Gamma)
- **Memory System**: Episodic, semantic, procedural memory
- **Action/Evaluator**: Memory-based decision making
- **Provider Architecture**: Clean data source separation
- **Character Communication**: Each agent speaks in their style

**Use for**: Research, experimentation, multi-agent coordination studies

---

### 3. Solana Smart Contract
**Files**: `solana_program/src/lib.rs` + `Cargo.toml`

**Features**:
- Atomic flashloan execution
- Multi-DEX swap routing
- Slippage protection
- Profit verification
- On-chain state tracking

**Use for**: On-chain execution (required for real flashloans)

---

## ⚡ Quick Start

### Option A: Test ULTIMATE Version (Production)

```bash
# 1. Install
pip install solana solders requests numpy pandas termcolor python-dotenv

# 2. Configure
cat > .env << EOF
SOLANA_PRIVATE_KEY="your_key"
BIRDEYE_API_KEY="your_key"
RPC_ENDPOINT="https://api.mainnet-beta.solana.com"
EOF

# 3. Run
python src/agents/ULTIMATE_FLASHLOAN_SWARM.py
```

### Option B: Test ELIZA Version (Research)

```bash
# Same setup as above, then:
python src/agents/ELIZA_FLASHLOAN_SWARM.py
```

**You'll see different outputs:**
- **ULTIMATE**: Focus on profits, stats, Monte Carlo results
- **ELIZA**: Agent personalities, memory consolidation, character-driven decisions

### Option C: Deploy Smart Contract (Advanced)

```bash
# 1. Install Rust & Solana CLI
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# 2. Build program
cd solana_program
./build.sh

# 3. Deploy (testnet first!)
solana config set --url devnet
solana program deploy target/deploy/flashloan_arbitrage.so
```

---

## 🎭 ELIZA vs ULTIMATE - Key Differences

| Feature | ULTIMATE | ELIZA |
|---------|----------|-------|
| **Purpose** | Production trading | Research/experimentation |
| **Agent Behavior** | Purely performance-driven | Personality-driven |
| **Memory** | Basic statistics | Full episodic/semantic system |
| **Communication** | Stats-focused | Character-based dialogue |
| **Decision Making** | Monte Carlo + Game Theory | Memory + Character evaluation |
| **Best For** | Making money | Understanding agents |

---

## 🎯 ElizaOS Patterns Implemented

### 1. Memory System
```
Episodic Memory → Stores specific events
   "I made $150 on SOL/USDC at 14:30"

Semantic Memory → Learns patterns  
   "14:00-15:00 is most profitable time"

Procedural Memory → Remembers strategies
   "How to execute Raydium→Orca arbitrage"
```

### 2. Agent Characters

**Alpha (Aggressive Hunter)**
- High aggression (0.9)
- Attacks competitors constantly
- Communication: "⚔️ ATTACKING: Crushing competitor..."

**Sigma (Strategic Analyzer)**
- High patience (0.9)
- Waits for perfect setups
- Communication: "📊 Analyzing: Evaluating opportunity..."

**Beta (Balanced Trader)**
- Balanced traits (0.5 all)
- Adapts to any situation
- Communication: "💬 Executing: Taking calculated risk..."

**Gamma (Risk Taker)**
- High risk tolerance (0.9)
- Goes all-in
- Communication: "🎲 YOLO: All-in on this trade!"

### 3. Action/Evaluator Pattern

```python
Action → Evaluator checks memory → Calculate confidence → Decide

Example:
1. "execute_flashloan_arb" action proposed
2. Evaluator recalls last 5 flashloan trades
3. 4 out of 5 were successful = 80% confidence
4. Character trait check (aggression > 0.5)
5. Decision: EXECUTE (confidence meets threshold + character allows)
```

### 4. Provider Architecture

```python
# Clean separation
birdeye_provider = BirdEyeProvider()
jupiter_provider = JupiterProvider()

# Easy to extend
class CustomProvider(Provider):
    def get_data(self, params):
        # Your custom data source
        pass
```

---

## 📊 Expected Output Examples

### ULTIMATE Version
```
╔═══════════════════════════════════════════════════════════╗
║         🌙 ULTIMATE FLASHLOAN ARBITRAGE SWARM             ║
╚═══════════════════════════════════════════════════════════╝

✅ Flashloan Core initialized
🔥 COMPETITOR DESTROYER ONLINE

👶 AGENT_0001 BORN (Gen 1)
🔍 Found 12 opportunities
✅ AGENT_0001: +$127.32

📊 SWARM STATISTICS
   Net Profit: $834.78
   ROI: 6605.2%
```

### ELIZA Version
```
🌙 ELIZA-INSPIRED FLASHLOAN SWARM

👤 ELIZA_0001 spawned as 'Alpha'
   Role: Aggressive MEV Hunter
   Style: aggressive

ELIZA_0001: ⚔️ ATTACKING: Execute flashloan arbitrage trade
  ⚔️ Alpha: Found profitable opportunity: $125.50
  ⚔️ Alpha: ✅ Success! Profit: $127.32

🧠 Learned new pattern: pattern_1698765432
   
👤 ELIZA_0002 spawned as 'Sigma'
   Role: Strategic Analyzer
   Style: analytical
   
ELIZA_0002: 📊 Analyzing: Execute flashloan arbitrage trade
  📊 Sigma: Waiting for optimal conditions...
```

---

## 🔧 Configuration

Edit `flashloan_swarm_config.json`:

```json
{
  "target_net_profit": 100.0,
  "min_confidence": 90.0,
  "destroyer_enabled": true,
  "mc_simulations": 10000
}
```

---

## 📚 Documentation

- **Complete Guide**: `FLASHLOAN_SWARM_README.md`
- **System Overview**: `SYSTEM_COMPLETE.md`
- **Smart Contract**: `solana_program/README.md`

---

## ⚠️ Important Notes

1. **ULTIMATE** is optimized for trading
2. **ELIZA** is optimized for research & agent behavior studies
3. **Smart Contract** is required for real flashloans on-chain
4. Both Python versions work with simulated mode by default
5. Enable real trading by deploying smart contract + updating config

---

## 🎓 Learn More

**ElizaOS Patterns**:
- Memory consolidation (episodic → semantic)
- Character-driven behavior
- Action/Evaluator decision making
- Provider architecture

**Trading Patterns**:
- Monte Carlo simulation
- Game theory optimal gas bidding
- Competitor destruction strategies
- Triple-layer profitability guarantee

---

**Choose your path and start now!** 🚀

```bash
# Production trading
python src/agents/ULTIMATE_FLASHLOAN_SWARM.py

# Research/experimentation  
python src/agents/ELIZA_FLASHLOAN_SWARM.py
```

---

**Built with 💜 by Moon Dev** | *Inspired by ElizaOS*
