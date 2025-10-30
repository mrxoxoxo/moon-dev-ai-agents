# Solana Flashloan Arbitrage Program

Smart contract for executing atomic flashloan arbitrage on Solana.

## Features

- ⚡ Atomic flashloan execution
- 🔄 Multi-DEX swap routing
- 💰 Automatic profit calculation
- 🛡️ Slippage protection
- 📊 Trade statistics tracking

## Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Add BPF target
rustup target add bpfel-unknown-unknown
```

## Build

```bash
cd solana_program
./build.sh
```

## Deploy

```bash
# Set cluster (devnet for testing)
solana config set --url devnet

# Deploy program
solana program deploy target/deploy/flashloan_arbitrage.so

# Note the program ID
```

## Usage

### 1. Initialize State

```bash
# Initialize your arbitrage state account
solana program call <PROGRAM_ID> initialize_state
```

### 2. Execute Arbitrage

The Python agent (`ULTIMATE_FLASHLOAN_SWARM.py`) will automatically:
1. Find arbitrage opportunities
2. Build transaction calling this program
3. Submit via Jito bundle
4. Program executes atomically:
   - Borrow flashloan
   - Swap on DEX 1 (buy)
   - Swap on DEX 2 (sell)
   - Repay flashloan
   - Keep profit

## Program Instructions

### ExecuteArbitrage

```rust
ExecuteArbitrage {
    amount: u64,           // Amount to borrow
    min_profit: u64,       // Minimum acceptable profit
    max_slippage_bps: u16, // Max slippage (100 = 1%)
}
```

**Accounts:**
0. [signer] User authority
1. [writable] User token account
2. [writable] Flashloan source
3. [] DEX Program 1
4. [] DEX Program 2
5. [writable] DEX Pool 1
6. [writable] DEX Pool 2
7. [] Token Program
8. [] System Program

### InitializeState

```rust
InitializeState {
    bump: u8, // PDA bump seed
}
```

## Integration with Python Agent

The `ULTIMATE_FLASHLOAN_SWARM.py` calls this program:

```python
# Build transaction
tx = Transaction()
tx.add(
    Instruction(
        program_id=FLASHLOAN_PROGRAM_ID,
        accounts=[...],
        data=serialize_instruction({
            'ExecuteArbitrage': {
                'amount': optimal_amount,
                'min_profit': min_profit_lamports,
                'max_slippage_bps': 100  # 1%
            }
        })
    )
)

# Submit via Jito
result = submit_jito_bundle(tx)
```

## Testing

```bash
# Run tests
cargo test-bpf
```

## Security

- ✅ Atomic execution (all-or-nothing)
- ✅ Profit verification before commit
- ✅ Slippage protection
- ✅ Authority checks
- ✅ No reentrancy possible

## Notes

- Program must be deployed on same cluster as DEXs
- Requires SOL for transaction fees
- Flashloan source must support flashloans
- Compatible with: Raydium, Orca, Jupiter, Meteora

## Production Checklist

- [ ] Deploy to mainnet
- [ ] Update program ID in Python agent
- [ ] Test with small amounts first
- [ ] Monitor gas costs
- [ ] Set appropriate min_profit thresholds

---

**Built with 💜 by Moon Dev**
