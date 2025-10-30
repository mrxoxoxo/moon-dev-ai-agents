# 🌙 Moon Dev's Flashloan Arbitrage Swarm

**Evolutionary Self-Improving Flashloan Arbitrage System**

Built with love by Moon Dev 🚀

---

## 🎯 Overview

An autonomous swarm of AI agents that discover, execute, and learn from flashloan arbitrage opportunities on Solana DEXs. The system uses reinforcement learning, genetic algorithms, and adaptive strategies to maximize profits while maintaining 80%+ accuracy.

### Key Features

✅ **DEX-ONLY Trading** - No centralized exchanges, fully decentralized
✅ **90%+ Execution Threshold** - Only executes opportunities with ≥90% probability of profit
✅ **80%+ Accuracy Target** - Maintains high success rate through adaptive learning
✅ **MEV Protection** - Jito bundles, slippage protection, front-running prevention
✅ **Gas Fee Optimization** - All gas costs factored into profitability calculations
✅ **Autonomous Discovery** - Automatically finds new tokens and DEXs
✅ **Evolutionary Agents** - Agents evolve, reproduce, and die based on performance
✅ **Reinforcement Learning** - Learns from every trade to improve strategies
✅ **Slippage Prediction** - Advanced market impact modeling
✅ **Automatic Profit Distribution** - Splits profits to BTC and ETH wallets

---

## 🏗️ Architecture

### Core Components

```
flashloan_swarm_agent.py       → Main orchestrator
├── flashloan_core.py           → Flashloan execution engine
├── flashloan_baby_agent.py     → Individual evolving agents
├── flashloan_discovery.py      → Token/DEX discovery
├── flashloan_learning.py       → Reinforcement learning
├── flashloan_slippage.py       → Slippage prediction
├── flashloan_validator.py      → Execution validation (90%+ threshold)
└── flashloan_profit_distribution.py → Auto profit distribution
```

### Agent Lifecycle

```
1. BIRTH → Agent spawned with random genetics
2. SCAN → Searches for arbitrage opportunities
3. VALIDATE → Checks if opportunity meets 90%+ confidence
4. EXECUTE → Performs flashloan arbitrage (if validated)
5. LEARN → Updates strategy based on results
6. EVOLVE → Mutates genetics after successful trades
7. REPRODUCE → Spawns children if profitable
8. DIE → Dies after 3 consecutive failures
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# Required environment variables in .env
BIRDEYE_API_KEY=your_birdeye_key
SOLANA_PRIVATE_KEY=your_solana_private_key
RPC_ENDPOINT=your_solana_rpc_url
```

### Configuration

Create `src/data/flashloan_swarm/config.json`:

```json
{
  "initial_population": 5,
  "max_population": 20,
  "min_population": 2,
  "min_profit_threshold": 0.5,
  "max_slippage_tolerance": 2.0,
  "learning_rate": 0.1,
  "discount_factor": 0.95,
  "exploration_rate": 0.3,
  "profit_distribution": {
    "btc_wallet": "your_btc_wallet_address",
    "eth_wallet": "your_eth_wallet_address",
    "btc_allocation": 50.0,
    "eth_allocation": 50.0
  }
}
```

### Running the Swarm

```bash
# Navigate to agents directory
cd src/agents

# Run the swarm
python flashloan_swarm_agent.py
```

---

## 📊 Execution Rules

### 90% Confidence Threshold

**The system ONLY executes opportunities with ≥90% probability of profit**

Confidence calculation factors:
- **Profit Margin** (40% weight) - Higher margin = higher confidence
- **Slippage Prediction** (20% weight) - Based on historical data
- **Liquidity Depth** (20% weight) - More liquidity = more confident
- **Historical Accuracy** (10% weight) - Past performance
- **Price Stability** (10% weight) - Low slippage = stable prices

### Gas Fee Protection

**ALL gas fees are included in profitability calculations**

- Estimated gas cost × 1.5x safety margin
- Flashloan protocol fees
- DEX swap fees
- Slippage impact
- Market impact

**If net profit after ALL costs is not positive, the trade will NOT execute.**

### MEV Protection Layers

1. **Jito Bundle Submission** - Private mempool transactions
2. **Strict Slippage Limits** - 0.5% maximum slippage
3. **Transaction Deadlines** - 30 second expiry
4. **High Priority Fees** - Fast inclusion
5. **Pre-execution Validation** - Verify prices haven't moved

---

## 🧬 Evolution & Learning

### Genetic Algorithm

Agents have genetic traits that evolve:

```python
{
  "min_profit_threshold": 0.5-5.0%,    # Minimum profit to attempt
  "max_trade_size_usd": $100-100k,     # Maximum trade size
  "risk_tolerance": 0.1-1.0,           # Risk acceptance
  "dex_preference": ["raydium"...],    # Preferred DEXs
  "aggression": 0.1-1.0,               # Execution speed
  "adaptability": 0.1-1.0              # Mutation rate
}
```

**Evolution happens when:**
- Agent successfully completes trades
- Every 3 successful trades triggers mutation
- Successful agents spawn children
- Children inherit mutated genetics

### Reinforcement Learning

**Q-Learning Algorithm**

```
Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
```

Where:
- `s` = Current state (opportunity + agent stats)
- `a` = Action (execute/skip)
- `r` = Reward (profit = +, loss = -)
- `α` = Learning rate (0.1)
- `γ` = Discount factor (0.95)

**Reward Structure:**
- Profitable trade: +profit * 10
- Failed trade: -1.0
- Agent death: -10.0
- High efficiency bonus: +50%

---

## 💰 Profit Distribution

### Automatic Splitting

After each profitable trade, profits are automatically:

1. **Split** according to configured allocations (default 50/50)
2. **Swapped** to wBTC and wETH via Jupiter
3. **Sent** to your configured wallet addresses

### Example Flow

```
$10 Profit → $5 to BTC wallet + $5 to ETH wallet
           ↓
      Swap via Jupiter
           ↓
   0.0001 wBTC sent to BTC wallet
   0.00166 wETH sent to ETH wallet
```

### Updating Wallets

```python
# Update wallet addresses
swarm.profit_distributor.update_wallets(
    btc_wallet="new_btc_address",
    eth_wallet="new_eth_address",
    btc_allocation=60.0,  # 60% to BTC
    eth_allocation=40.0   # 40% to ETH
)
```

---

## 📈 Monitoring

### Real-time Statistics

The swarm prints statistics every iteration:

```
📊 SWARM STATISTICS
═══════════════════

👥 Population:
   Alive: 8
   Dead: 3
   Total Born: 11

💼 Trading:
   Total Attempts: 45
   Successful: 38
   Success Rate: 84.4%

💰 Profit/Loss:
   Total Profit: $127.34
   Total Loss: $12.45
   Net P/L: $114.89

🧠 Learning:
   Experiences: 45
   Avg Reward: 12.34
   Exploration: 0.245

🏆 Top Agents:
   1. AGENT_0003: $34.56 (Gen 4)
   2. AGENT_0007: $28.91 (Gen 2)
   3. AGENT_0005: $22.33 (Gen 3)
```

### Data Persistence

The swarm automatically saves:

- **Agent states** - Every 5 minutes
- **RL model** - Q-table and learning stats
- **Discoveries** - Tokens and DEXs found
- **Distribution history** - All profit distributions

Saved to: `src/data/flashloan_swarm/`

---

## 🛡️ Safety Features

### Multi-Layer Validation

Every opportunity goes through **7 validation checks**:

1. ✅ Gas fees must be profitable
2. ✅ Net profit must be positive (after ALL costs)
3. ✅ Confidence must be ≥90%
4. ✅ Risk score must be acceptable
5. ✅ Profit margin must be reasonable
6. ✅ Trade size must be valid
7. ✅ Prices must be sane

**If ANY check fails, the trade is rejected.**

### Adaptive Thresholds

The system learns and adapts:

- **Accuracy < 80%** → Increase confidence requirement (up to 98%)
- **Accuracy > 95%** → Decrease to 90% (never below)
- **High gas spikes** → Increase gas safety margin
- **Low liquidity** → Reduce trade sizes

### Emergency Shutdown

Automatic shutdown triggers:

- Net loss exceeds configured threshold (default $100)
- Ctrl+C for manual shutdown
- All state is saved before exit

---

## 🎓 How It Works

### 1. Discovery Phase

```python
# Every 5 minutes, discover new tokens
tokens = discovery.discover_new_tokens(limit=100)

# Filter by liquidity and volume
profitable_tokens = filter_by_metrics(tokens)

# Score opportunities
scored_tokens = calculate_scores(profitable_tokens)
```

### 2. Opportunity Scanning

```python
# Each agent scans for arbitrage
opportunities = core.scan_arbitrage_opportunities(
    tokens=agent.tokens,
    min_profit_percent=agent.genetics.min_profit_threshold
)

# Only DEX-to-DEX (no CEX)
dex_only_opps = filter_dex_only(opportunities)
```

### 3. Validation

```python
# Predict slippage
slippage = slippage_predictor.predict_slippage(
    dex=opportunity.buy_dex,
    token=opportunity.token_address,
    trade_size=opportunity.optimal_amount
)

# Validate execution
decision = validator.validate_execution(
    opportunity=opportunity,
    slippage_prediction=slippage,
    market_impact=impact_analysis
)

# Only execute if ≥90% confidence
if decision.should_execute and decision.confidence >= 90.0:
    execute_trade()
```

### 4. Execution

```python
# Build MEV-protected transaction
tx = core._build_mev_protected_transaction(opportunity)

# Simulate with slippage checks
simulation = core._simulate_with_mev_checks(tx, opportunity)

# Execute via Jito bundle (private mempool)
result = core._execute_via_jito_bundle(tx, opportunity)
```

### 5. Learning

```python
# Create experience
experience = TradeExperience(
    state=current_state,
    action=action_taken,
    reward=calculate_reward(result),
    next_state=new_state,
    terminal=agent_died
)

# Update Q-values
rl_learner.learn_from_experience(experience)

# Replay past experiences
rl_learner.replay_training(batch_size=32)
```

### 6. Evolution

```python
# Check if agent should evolve
if agent.successful_attempts % 3 == 0:
    agent.evolve()  # Mutate genetics

# Check if agent can reproduce
if agent.total_profit >= $1.00:
    child = agent.spawn_child()
    swarm.agents[child.id] = child

# Check if agent should die
if agent.consecutive_failures >= 3:
    agent.die()
```

---

## 📁 Data Files

### Agent State

```json
{
  "id": "AGENT_0001",
  "is_alive": true,
  "generation": 3,
  "total_attempts": 15,
  "successful_attempts": 12,
  "total_profit": 45.67,
  "genetics": {
    "min_profit_threshold": 0.7,
    "max_trade_size_usd": 15000,
    "risk_tolerance": 0.6,
    "dex_preference": ["raydium", "orca"],
    "aggression": 0.75,
    "adaptability": 0.5
  }
}
```

### Distribution Record

```json
{
  "timestamp": 1234567890,
  "profit_usd": 10.50,
  "btc_amount": 0.000105,
  "btc_usd_value": 5.25,
  "eth_amount": 0.00175,
  "eth_usd_value": 5.25,
  "btc_wallet": "bc1q...",
  "eth_wallet": "0x...",
  "transaction_hashes": {
    "btc": "abc123...",
    "eth": "def456..."
  }
}
```

---

## ⚙️ Advanced Configuration

### Fine-tuning Learning

```json
{
  "learning_rate": 0.05,        // Lower = slower but stable learning
  "discount_factor": 0.99,      // Higher = value long-term rewards
  "exploration_rate": 0.2,      // Lower = more exploitation
  "replay_training_every": 5    // More frequent = faster learning
}
```

### Population Dynamics

```json
{
  "initial_population": 10,     // Start with more agents
  "max_population": 50,         // Allow larger swarm
  "min_population": 5,          // Maintain minimum diversity
  "reproduction_threshold": 3   // Agents can reproduce earlier
}
```

### Risk Management

```json
{
  "min_profit_threshold": 1.0,  // Higher = more conservative
  "max_slippage_tolerance": 1.0, // Lower = safer trades
  "emergency_shutdown_loss": 50.0, // Tighter stop-loss
  "max_consecutive_failures": 2  // Faster agent culling
}
```

---

## 🐛 Troubleshooting

### No Opportunities Found

**Problem:** Swarm not finding arbitrage opportunities

**Solutions:**
1. Lower `min_profit_threshold` in config
2. Increase `max_tokens_tracked` for more discovery
3. Check RPC endpoint is working
4. Verify BirdEye API key is valid

### Low Accuracy (<80%)

**Problem:** Too many failed trades

**System Response:** Automatically increases confidence threshold

**Manual Solutions:**
1. Increase `min_profit_threshold`
2. Reduce `max_slippage_tolerance`
3. Wait for more learning (system will adapt)

### Gas Fees Too High

**Problem:** Profits eaten by gas costs

**Solutions:**
1. Increase `min_profit_threshold`
2. System will automatically adjust `gas_safety_multiplier`
3. Wait for lower network congestion

---

## 📜 License

MIT License - Built with love by Moon Dev 🌙

---

## 🌟 Credits

Inspired by the moon-dev-ai-agents-for-trading architecture:
- Multi-agent orchestration patterns
- Model factory abstraction
- Exchange manager design
- Agent-based architecture

---

## ⚠️ Disclaimer

**This is experimental software for educational purposes.**

- Substantial risk of loss
- No guarantees of profitability
- Use at your own risk
- Never invest more than you can afford to lose
- Test thoroughly on devnet first

---

## 🚀 See You on the Moon! 🌙

Questions? Join the Moon Dev community on YouTube and Discord!
