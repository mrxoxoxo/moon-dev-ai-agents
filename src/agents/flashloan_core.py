"""
🌙 Moon Dev's Flashloan Arbitrage Core
Multi-DEX flashloan execution engine for Solana
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import base64
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.hash import Hash
from solana.rpc.api import Client
from dotenv import load_dotenv

load_dotenv()

# Solana DEX Program IDs
RAYDIUM_V4 = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
ORCA_WHIRLPOOL = Pubkey.from_string("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")
JUPITER_V6 = Pubkey.from_string("JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4")
METEORA = Pubkey.from_string("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo")

# System programs
SYSTEM_PROGRAM = Pubkey.from_string("11111111111111111111111111111111")
TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

@dataclass
class ArbitrageOpportunity:
    """Represents a potential arbitrage opportunity"""
    token_address: str
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    profit_percent: float
    estimated_profit_usd: float
    liquidity_available: float
    optimal_amount: float
    route: List[str]
    timestamp: float
    
    def to_dict(self) -> Dict:
        return {
            'token': self.token_address,
            'buy_dex': self.buy_dex,
            'sell_dex': self.sell_dex,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'profit_percent': self.profit_percent,
            'estimated_profit': self.estimated_profit_usd,
            'liquidity': self.liquidity_available,
            'optimal_amount': self.optimal_amount,
            'route': self.route,
            'timestamp': self.timestamp
        }


class FlashloanCore:
    """Core flashloan arbitrage execution engine"""
    
    def __init__(self):
        """Initialize flashloan core with Solana connection"""
        self.rpc_endpoint = os.getenv('RPC_ENDPOINT', 'https://api.mainnet-beta.solana.com')
        self.client = Client(self.rpc_endpoint)
        
        # Load wallet
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not private_key:
            raise ValueError("SOLANA_PRIVATE_KEY not found in environment")
        
        # Parse private key
        try:
            if ',' in private_key:
                key_bytes = bytes([int(x) for x in private_key.split(',')])
            else:
                key_bytes = base64.b64decode(private_key)
            self.keypair = Keypair.from_bytes(key_bytes[:32])
        except Exception as e:
            raise ValueError(f"Failed to parse private key: {str(e)}")
        
        self.wallet_address = str(self.keypair.pubkey())
        cprint(f"✅ Flashloan Core initialized", "green")
        cprint(f"   Wallet: {self.wallet_address[:8]}...{self.wallet_address[-6:]}", "cyan")
        
        # DEX configurations
        self.dex_configs = {
            'raydium': {'program_id': RAYDIUM_V4, 'fee': 0.0025},
            'orca': {'program_id': ORCA_WHIRLPOOL, 'fee': 0.003},
            'jupiter': {'program_id': JUPITER_V6, 'fee': 0.0},  # Jupiter is aggregator
            'meteora': {'program_id': METEORA, 'fee': 0.002}
        }
        
        # Flashloan providers on Solana (simulated - would need actual protocol integration)
        self.flashloan_providers = {
            'solend': {'max_borrow': 1000000, 'fee': 0.0003},
            'kamino': {'max_borrow': 2000000, 'fee': 0.0001},
            'custom': {'max_borrow': 5000000, 'fee': 0.0005}
        }
        
    def scan_arbitrage_opportunities(self, tokens: List[str], min_profit_percent: float = 0.5) -> List[ArbitrageOpportunity]:
        """
        Scan multiple DEXs for arbitrage opportunities
        
        Args:
            tokens: List of token addresses to scan
            min_profit_percent: Minimum profit percentage threshold
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        for token in tokens:
            try:
                # Get prices from multiple DEXs
                prices = self._get_multi_dex_prices(token)
                
                if len(prices) < 2:
                    continue
                
                # Find best buy and sell prices
                sorted_prices = sorted(prices.items(), key=lambda x: x[1]['price'])
                buy_dex, buy_data = sorted_prices[0]
                sell_dex, sell_data = sorted_prices[-1]
                
                buy_price = buy_data['price']
                sell_price = sell_data['price']
                
                # Calculate profit
                profit_percent = ((sell_price - buy_price) / buy_price) * 100
                
                if profit_percent >= min_profit_percent:
                    # Calculate optimal amount based on liquidity
                    liquidity = min(buy_data.get('liquidity', 0), sell_data.get('liquidity', 0))
                    optimal_amount = self._calculate_optimal_amount(
                        buy_price, sell_price, liquidity, profit_percent
                    )
                    
                    estimated_profit = optimal_amount * (sell_price - buy_price)
                    
                    opportunity = ArbitrageOpportunity(
                        token_address=token,
                        buy_dex=buy_dex,
                        sell_dex=sell_dex,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        profit_percent=profit_percent,
                        estimated_profit_usd=estimated_profit,
                        liquidity_available=liquidity,
                        optimal_amount=optimal_amount,
                        route=[buy_dex, sell_dex],
                        timestamp=time.time()
                    )
                    
                    opportunities.append(opportunity)
                    
            except Exception as e:
                cprint(f"⚠️ Error scanning {token}: {str(e)}", "yellow")
                continue
        
        # Sort by profit potential
        opportunities.sort(key=lambda x: x.estimated_profit_usd, reverse=True)
        return opportunities
    
    def _get_multi_dex_prices(self, token_address: str) -> Dict:
        """Get token prices from multiple DEXs"""
        prices = {}
        
        # Use Jupiter API for aggregated pricing
        try:
            import requests
            
            # Get quote from Jupiter
            url = f"https://quote-api.jup.ag/v6/quote"
            params = {
                'inputMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'outputMint': token_address,
                'amount': 1000000,  # 1 USDC
                'slippageBps': 50
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Parse route markets
                routes = data.get('routePlan', [])
                for route in routes:
                    for swap in route.get('swapInfo', []):
                        label = swap.get('label', 'unknown')
                        in_amount = float(swap.get('inAmount', 0))
                        out_amount = float(swap.get('outAmount', 0))
                        
                        if in_amount > 0 and out_amount > 0:
                            price = in_amount / out_amount
                            
                            if label not in prices or prices[label]['price'] > price:
                                prices[label.lower()] = {
                                    'price': price,
                                    'liquidity': out_amount,
                                    'source': 'jupiter'
                                }
                
        except Exception as e:
            cprint(f"⚠️ Jupiter API error: {str(e)}", "yellow")
        
        # Fallback to BirdEye for additional data
        try:
            from src.nice_funcs import token_price
            birdeye_price = token_price(token_address)
            
            if birdeye_price:
                prices['birdeye'] = {
                    'price': birdeye_price,
                    'liquidity': 0,
                    'source': 'birdeye'
                }
        except:
            pass
        
        return prices
    
    def _calculate_optimal_amount(self, buy_price: float, sell_price: float, 
                                  liquidity: float, profit_percent: float) -> float:
        """
        Calculate optimal trade amount based on slippage and liquidity
        
        Uses a simplified model that accounts for:
        - Available liquidity
        - Estimated slippage impact
        - Fee structures
        """
        # Start with 10% of available liquidity to minimize slippage
        base_amount = liquidity * 0.1
        
        # Adjust based on profit margin (higher profit = can handle more slippage)
        if profit_percent > 2.0:
            base_amount = min(liquidity * 0.3, base_amount * 2)
        elif profit_percent > 1.0:
            base_amount = min(liquidity * 0.2, base_amount * 1.5)
        
        # Cap at reasonable maximums
        max_amount = min(100000, liquidity * 0.5)  # Max $100k or 50% of liquidity
        
        return min(base_amount, max_amount)
    
    def execute_flashloan_arbitrage(self, opportunity: ArbitrageOpportunity, 
                                   provider: str = 'custom') -> Dict:
        """
        Execute flashloan arbitrage trade
        
        Args:
            opportunity: Arbitrage opportunity to execute
            provider: Flashloan provider to use
            
        Returns:
            Execution result dictionary
        """
        cprint(f"\n⚡ Executing flashloan arbitrage:", "cyan")
        cprint(f"   Token: {opportunity.token_address[:8]}...", "cyan")
        cprint(f"   Route: {opportunity.buy_dex} → {opportunity.sell_dex}", "cyan")
        cprint(f"   Profit: {opportunity.profit_percent:.2f}% (${opportunity.estimated_profit_usd:.2f})", "green")
        
        try:
            # Build flashloan transaction
            transaction = self._build_flashloan_transaction(opportunity, provider)
            
            if not transaction:
                return {
                    'success': False,
                    'error': 'Failed to build transaction',
                    'opportunity': opportunity.to_dict()
                }
            
            # Simulate transaction first
            simulation = self._simulate_transaction(transaction)
            
            if not simulation['success']:
                cprint(f"❌ Simulation failed: {simulation.get('error')}", "red")
                return {
                    'success': False,
                    'error': f"Simulation failed: {simulation.get('error')}",
                    'opportunity': opportunity.to_dict()
                }
            
            cprint(f"✅ Simulation successful - estimated profit: ${simulation.get('profit', 0):.2f}", "green")
            
            # Execute transaction
            # NOTE: Commented out actual execution for safety - enable when ready
            # result = self._send_transaction(transaction)
            
            # For now, return simulation result
            return {
                'success': True,
                'simulated': True,
                'profit': simulation.get('profit', 0),
                'opportunity': opportunity.to_dict(),
                'message': 'Simulation successful - real execution disabled for safety'
            }
            
        except Exception as e:
            cprint(f"❌ Execution error: {str(e)}", "red")
            return {
                'success': False,
                'error': str(e),
                'opportunity': opportunity.to_dict()
            }
    
    def _build_flashloan_transaction(self, opportunity: ArbitrageOpportunity, 
                                     provider: str) -> Optional[VersionedTransaction]:
        """
        Build a flashloan arbitrage transaction
        
        NOTE: This is a simplified structure. Real implementation would need:
        1. Integration with actual flashloan protocols (Solend, Kamino, etc.)
        2. Proper account derivation for each DEX
        3. CPI (Cross-Program Invocation) instructions
        4. Proper error handling and slippage protection
        """
        try:
            # This would build a transaction with:
            # 1. Flashloan borrow instruction
            # 2. Swap on buy DEX
            # 3. Swap on sell DEX
            # 4. Flashloan repay instruction
            # All in a single atomic transaction
            
            cprint("⚠️ Transaction building is simulated - need real protocol integration", "yellow")
            return None
            
        except Exception as e:
            cprint(f"❌ Failed to build transaction: {str(e)}", "red")
            return None
    
    def _simulate_transaction(self, transaction) -> Dict:
        """Simulate transaction execution"""
        # Simplified simulation
        # Real implementation would use Solana's simulateTransaction RPC
        return {
            'success': True,
            'profit': 0,  # Would calculate from simulation logs
            'gas_cost': 0.00005  # Example SOL cost
        }
    
    def get_balance(self) -> float:
        """Get wallet SOL balance"""
        try:
            response = self.client.get_balance(self.keypair.pubkey())
            if response.value:
                return response.value / 1e9  # Convert lamports to SOL
        except Exception as e:
            cprint(f"⚠️ Failed to get balance: {str(e)}", "yellow")
        return 0.0
