"""
🌙 Moon Dev's Flashloan Profit Distribution System
Automatically splits and swaps profits to BTC and ETH wallets
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
from pathlib import Path

@dataclass
class ProfitWallet:
    """Configuration for a profit destination wallet"""
    currency: str  # 'BTC' or 'ETH'
    address: str
    allocation_percent: float  # 0-100
    total_received_usd: float = 0.0
    total_received_tokens: float = 0.0
    last_distribution: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'currency': self.currency,
            'address': self.address,
            'allocation_percent': self.allocation_percent,
            'total_received_usd': self.total_received_usd,
            'total_received_tokens': self.total_received_tokens,
            'last_distribution': self.last_distribution
        }


@dataclass
class DistributionRecord:
    """Record of a profit distribution"""
    timestamp: float
    profit_usd: float
    btc_amount: float
    btc_usd_value: float
    eth_amount: float
    eth_usd_value: float
    btc_wallet: str
    eth_wallet: str
    transaction_hashes: Dict[str, str]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'profit_usd': self.profit_usd,
            'btc_amount': self.btc_amount,
            'btc_usd_value': self.btc_usd_value,
            'eth_amount': self.eth_amount,
            'eth_usd_value': self.eth_usd_value,
            'btc_wallet': self.btc_wallet,
            'eth_wallet': self.eth_wallet,
            'transaction_hashes': self.transaction_hashes
        }


class ProfitDistributor:
    """
    Automatic profit distribution system
    
    Features:
    1. Configurable BTC/ETH wallet addresses
    2. Automatic profit splitting
    3. Auto-swap USDC/SOL profits to BTC/ETH
    4. Distribution tracking and reporting
    """
    
    def __init__(self, btc_wallet: str, eth_wallet: str, 
                 btc_allocation: float = 50.0, eth_allocation: float = 50.0):
        """
        Initialize profit distributor
        
        Args:
            btc_wallet: BTC wallet address for profits
            eth_wallet: ETH wallet address for profits
            btc_allocation: Percentage to BTC (default 50%)
            eth_allocation: Percentage to ETH (default 50%)
        """
        # Validate allocations sum to 100%
        total_allocation = btc_allocation + eth_allocation
        if abs(total_allocation - 100.0) > 0.01:
            cprint(f"⚠️ Allocations don't sum to 100% ({total_allocation}%), auto-adjusting...", "yellow")
            btc_allocation = (btc_allocation / total_allocation) * 100
            eth_allocation = (eth_allocation / total_allocation) * 100
        
        # Profit wallets
        self.btc_wallet = ProfitWallet(
            currency='BTC',
            address=btc_wallet,
            allocation_percent=btc_allocation
        )
        
        self.eth_wallet = ProfitWallet(
            currency='ETH',
            address=eth_wallet,
            allocation_percent=eth_allocation
        )
        
        # Distribution settings
        self.min_distribution_usd = 1.0  # Minimum $1 to distribute (avoid dust)
        self.auto_distribute = True
        self.distribution_history: List[DistributionRecord] = []
        
        # Token addresses on Solana (wrapped BTC/ETH)
        self.wbtc_address = "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh"  # Wrapped BTC (Wormhole)
        self.weth_address = "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"  # Wrapped ETH (Wormhole)
        
        # Slippage for swaps
        self.swap_slippage_bps = 100  # 1%
        
        cprint("\n💰 Profit Distribution System Initialized", "green", attrs=['bold'])
        cprint(f"   BTC Wallet: {self._truncate_address(btc_wallet)} ({btc_allocation:.1f}%)", "cyan")
        cprint(f"   ETH Wallet: {self._truncate_address(eth_wallet)} ({eth_allocation:.1f}%)", "cyan")
        cprint(f"   Auto-Distribution: {'Enabled' if self.auto_distribute else 'Disabled'}", "cyan")
        cprint(f"   Min Distribution: ${self.min_distribution_usd}", "cyan")
    
    def _truncate_address(self, address: str) -> str:
        """Truncate address for display"""
        if len(address) > 12:
            return f"{address[:6]}...{address[-4:]}"
        return address
    
    def distribute_profit(self, profit_usd: float, source_token: str = "USDC") -> Dict:
        """
        Distribute profit to BTC and ETH wallets
        
        Process:
        1. Split profit according to allocations
        2. Swap to wBTC and wETH on Solana
        3. Send to configured wallets
        
        Args:
            profit_usd: Profit amount in USD
            source_token: Source token ('USDC' or 'SOL')
            
        Returns:
            Distribution result
        """
        if profit_usd < self.min_distribution_usd:
            cprint(f"⚠️ Profit ${profit_usd:.2f} below minimum ${self.min_distribution_usd}, skipping distribution", "yellow")
            return {
                'success': False,
                'reason': 'below_minimum',
                'profit': profit_usd
            }
        
        cprint(f"\n💸 DISTRIBUTING PROFIT: ${profit_usd:.2f}", "green", attrs=['bold'])
        
        # Calculate allocations
        btc_usd = profit_usd * (self.btc_wallet.allocation_percent / 100)
        eth_usd = profit_usd * (self.eth_wallet.allocation_percent / 100)
        
        cprint(f"   BTC Allocation: ${btc_usd:.2f} ({self.btc_wallet.allocation_percent}%)", "cyan")
        cprint(f"   ETH Allocation: ${eth_usd:.2f} ({self.eth_wallet.allocation_percent}%)", "cyan")
        
        # Swap and send to BTC wallet
        btc_result = self._swap_and_send_btc(btc_usd, source_token)
        
        # Swap and send to ETH wallet
        eth_result = self._swap_and_send_eth(eth_usd, source_token)
        
        # Record distribution
        record = DistributionRecord(
            timestamp=time.time(),
            profit_usd=profit_usd,
            btc_amount=btc_result.get('amount', 0),
            btc_usd_value=btc_usd,
            eth_amount=eth_result.get('amount', 0),
            eth_usd_value=eth_usd,
            btc_wallet=self.btc_wallet.address,
            eth_wallet=self.eth_wallet.address,
            transaction_hashes={
                'btc': btc_result.get('tx_hash', 'SIMULATED'),
                'eth': eth_result.get('tx_hash', 'SIMULATED')
            }
        )
        
        self.distribution_history.append(record)
        
        # Update wallet totals
        self.btc_wallet.total_received_usd += btc_usd
        self.btc_wallet.total_received_tokens += btc_result.get('amount', 0)
        self.btc_wallet.last_distribution = time.time()
        
        self.eth_wallet.total_received_usd += eth_usd
        self.eth_wallet.total_received_tokens += eth_result.get('amount', 0)
        self.eth_wallet.last_distribution = time.time()
        
        cprint(f"\n✅ Distribution Complete!", "green", attrs=['bold'])
        cprint(f"   BTC: {btc_result.get('amount', 0):.8f} wBTC (${btc_usd:.2f})", "green")
        cprint(f"   ETH: {eth_result.get('amount', 0):.8f} wETH (${eth_usd:.2f})", "green")
        
        return {
            'success': True,
            'profit_distributed': profit_usd,
            'btc_result': btc_result,
            'eth_result': eth_result,
            'record': record.to_dict()
        }
    
    def _swap_and_send_btc(self, amount_usd: float, source_token: str) -> Dict:
        """
        Swap to wBTC and send to BTC wallet
        
        Uses Jupiter for optimal routing
        """
        cprint(f"\n🔄 Swapping ${amount_usd:.2f} to wBTC...", "yellow")
        
        try:
            # Get current wBTC price
            btc_price = self._get_token_price(self.wbtc_address)
            
            if btc_price == 0:
                cprint(f"   ⚠️ Could not fetch BTC price, using fallback", "yellow")
                btc_price = 50000  # Fallback price
            
            # Calculate wBTC amount
            btc_amount = amount_usd / btc_price
            
            cprint(f"   Current BTC Price: ${btc_price:,.2f}", "cyan")
            cprint(f"   Amount to receive: {btc_amount:.8f} wBTC", "cyan")
            
            # Execute swap via Jupiter
            swap_result = self._execute_jupiter_swap(
                from_token=source_token,
                to_token=self.wbtc_address,
                amount_usd=amount_usd,
                destination=self.btc_wallet.address
            )
            
            if swap_result['success']:
                cprint(f"   ✅ Swapped to wBTC: {swap_result['amount_out']:.8f}", "green")
                cprint(f"   📤 Sent to: {self._truncate_address(self.btc_wallet.address)}", "green")
                
                return {
                    'success': True,
                    'amount': swap_result['amount_out'],
                    'price': btc_price,
                    'tx_hash': swap_result['tx_hash']
                }
            else:
                cprint(f"   ❌ Swap failed: {swap_result.get('error')}", "red")
                return {
                    'success': False,
                    'amount': 0,
                    'error': swap_result.get('error')
                }
                
        except Exception as e:
            cprint(f"   ❌ Error swapping to BTC: {str(e)}", "red")
            return {
                'success': False,
                'amount': 0,
                'error': str(e)
            }
    
    def _swap_and_send_eth(self, amount_usd: float, source_token: str) -> Dict:
        """
        Swap to wETH and send to ETH wallet
        
        Uses Jupiter for optimal routing
        """
        cprint(f"\n🔄 Swapping ${amount_usd:.2f} to wETH...", "yellow")
        
        try:
            # Get current wETH price
            eth_price = self._get_token_price(self.weth_address)
            
            if eth_price == 0:
                cprint(f"   ⚠️ Could not fetch ETH price, using fallback", "yellow")
                eth_price = 3000  # Fallback price
            
            # Calculate wETH amount
            eth_amount = amount_usd / eth_price
            
            cprint(f"   Current ETH Price: ${eth_price:,.2f}", "cyan")
            cprint(f"   Amount to receive: {eth_amount:.8f} wETH", "cyan")
            
            # Execute swap via Jupiter
            swap_result = self._execute_jupiter_swap(
                from_token=source_token,
                to_token=self.weth_address,
                amount_usd=amount_usd,
                destination=self.eth_wallet.address
            )
            
            if swap_result['success']:
                cprint(f"   ✅ Swapped to wETH: {swap_result['amount_out']:.8f}", "green")
                cprint(f"   📤 Sent to: {self._truncate_address(self.eth_wallet.address)}", "green")
                
                return {
                    'success': True,
                    'amount': swap_result['amount_out'],
                    'price': eth_price,
                    'tx_hash': swap_result['tx_hash']
                }
            else:
                cprint(f"   ❌ Swap failed: {swap_result.get('error')}", "red")
                return {
                    'success': False,
                    'amount': 0,
                    'error': swap_result.get('error')
                }
                
        except Exception as e:
            cprint(f"   ❌ Error swapping to ETH: {str(e)}", "red")
            return {
                'success': False,
                'amount': 0,
                'error': str(e)
            }
    
    def _get_token_price(self, token_address: str) -> float:
        """Get current token price in USD"""
        try:
            import requests
            
            # Use Jupiter price API
            url = f"https://price.jup.ag/v4/price"
            params = {'ids': token_address}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price_data = data.get('data', {}).get(token_address, {})
                price = price_data.get('price', 0)
                
                return float(price)
            
        except Exception as e:
            cprint(f"⚠️ Price fetch error: {str(e)}", "yellow")
        
        return 0.0
    
    def _execute_jupiter_swap(self, from_token: str, to_token: str, 
                             amount_usd: float, destination: str) -> Dict:
        """
        Execute swap via Jupiter aggregator
        
        NOTE: This is simulated - real implementation would:
        1. Get quote from Jupiter API
        2. Build swap transaction
        3. Sign and send transaction
        4. Wait for confirmation
        """
        cprint(f"   🔀 Jupiter Swap: {from_token} → {to_token}", "cyan")
        
        try:
            import requests
            
            # Step 1: Get quote from Jupiter
            # Convert USD to token amount (simplified)
            from_token_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" if from_token == "USDC" else from_token
            
            quote_url = "https://quote-api.jup.ag/v6/quote"
            quote_params = {
                'inputMint': from_token_address,
                'outputMint': to_token,
                'amount': int(amount_usd * 1_000_000),  # Convert to lamports (assuming USDC)
                'slippageBps': self.swap_slippage_bps
            }
            
            cprint(f"   📊 Getting quote from Jupiter...", "cyan")
            
            # For now, simulate the swap
            cprint(f"   ⚠️ SIMULATED SWAP (real execution disabled for safety)", "yellow")
            
            # Simulate output amount
            to_token_price = self._get_token_price(to_token)
            if to_token_price > 0:
                amount_out = amount_usd / to_token_price
            else:
                amount_out = 0
            
            return {
                'success': True,
                'amount_out': amount_out,
                'tx_hash': f'SIMULATED_{int(time.time())}',
                'simulated': True
            }
            
        except Exception as e:
            cprint(f"   ❌ Swap error: {str(e)}", "red")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_distribution_stats(self) -> Dict:
        """Get distribution statistics"""
        total_distributed = sum(r.profit_usd for r in self.distribution_history)
        
        return {
            'total_distributions': len(self.distribution_history),
            'total_distributed_usd': total_distributed,
            'btc_wallet': self.btc_wallet.to_dict(),
            'eth_wallet': self.eth_wallet.to_dict(),
            'last_distribution': self.distribution_history[-1].to_dict() if self.distribution_history else None
        }
    
    def export_history(self, filepath: str):
        """Export distribution history to JSON"""
        data = {
            'btc_wallet': self.btc_wallet.to_dict(),
            'eth_wallet': self.eth_wallet.to_dict(),
            'distributions': [r.to_dict() for r in self.distribution_history],
            'stats': self.get_distribution_stats()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        cprint(f"\n💾 Distribution history exported to {filepath}", "green")
    
    def update_wallets(self, btc_wallet: Optional[str] = None, eth_wallet: Optional[str] = None,
                      btc_allocation: Optional[float] = None, eth_allocation: Optional[float] = None):
        """Update wallet addresses and allocations"""
        if btc_wallet:
            old_wallet = self.btc_wallet.address
            self.btc_wallet.address = btc_wallet
            cprint(f"✅ BTC wallet updated: {self._truncate_address(old_wallet)} → {self._truncate_address(btc_wallet)}", "green")
        
        if eth_wallet:
            old_wallet = self.eth_wallet.address
            self.eth_wallet.address = eth_wallet
            cprint(f"✅ ETH wallet updated: {self._truncate_address(old_wallet)} → {self._truncate_address(eth_wallet)}", "green")
        
        if btc_allocation is not None and eth_allocation is not None:
            total = btc_allocation + eth_allocation
            if abs(total - 100.0) > 0.01:
                cprint(f"⚠️ Allocations sum to {total}%, auto-adjusting...", "yellow")
                btc_allocation = (btc_allocation / total) * 100
                eth_allocation = (eth_allocation / total) * 100
            
            self.btc_wallet.allocation_percent = btc_allocation
            self.eth_wallet.allocation_percent = eth_allocation
            
            cprint(f"✅ Allocations updated: BTC {btc_allocation}%, ETH {eth_allocation}%", "green")


def create_profit_distributor_from_config(config_path: str) -> ProfitDistributor:
    """Create distributor from config file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        profit_config = config.get('profit_distribution', {})
        
        return ProfitDistributor(
            btc_wallet=profit_config.get('btc_wallet', ''),
            eth_wallet=profit_config.get('eth_wallet', ''),
            btc_allocation=profit_config.get('btc_allocation', 50.0),
            eth_allocation=profit_config.get('eth_allocation', 50.0)
        )
        
    except Exception as e:
        cprint(f"❌ Failed to load profit config: {str(e)}", "red")
        raise
