#!/bin/bash
# Build script for Solana flashloan arbitrage program

set -e

echo "🔨 Building Solana Flashloan Arbitrage Program..."

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust not installed. Install from: https://rustup.rs"
    exit 1
fi

# Check if Solana CLI is installed
if ! command -v solana &> /dev/null; then
    echo "❌ Solana CLI not installed. Install from: https://docs.solana.com/cli/install-solana-cli-tools"
    exit 1
fi

# Build the program
echo "📦 Building program..."
cargo build-bpf

echo ""
echo "✅ Build complete!"
echo ""
echo "📍 Program binary: target/deploy/flashloan_arbitrage.so"
echo ""
echo "🚀 Deploy with:"
echo "   solana program deploy target/deploy/flashloan_arbitrage.so"
echo ""
