"""
🌙 Moon Dev's Flashloan Slippage Predictor
Predicts and calculates slippage to benefit from market impacts
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import math
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from termcolor import cprint
from collections import deque

@dataclass
class SlippageModel:
    """Slippage prediction model for a specific pool"""
    dex: str
    token_pair: str
    reserve_0: float
    reserve_1: float
    fee_tier: float
    last_updated: float
    
    # Historical slippage data
    observed_slippages: List[Tuple[float, float]] = None  # (trade_size, slippage)
    
    def __post_init__(self):
        if self.observed_slippages is None:
            self.observed_slippages = []
    
    def predict_slippage(self, trade_size_usd: float, is_buy: bool = True) -> float:
        """
        Predict slippage for a given trade size using constant product formula
        
        AMM Formula: x * y = k (constant product)
        Price impact = (trade_size / (reserve + trade_size)) * 100
        """
        if not self.reserve_0 or not self.reserve_1:
            # Fallback to linear estimate
            return self._linear_slippage_estimate(trade_size_usd)
        
        # Determine which reserve to use based on direction
        reserve = self.reserve_0 if is_buy else self.reserve_1
        
        # Calculate price impact using constant product formula
        # Δy = (y * Δx) / (x + Δx)
        # Price impact = Δy / y
        
        price_impact = (trade_size_usd / (reserve + trade_size_usd)) * 100
        
        # Add fee impact
        fee_impact = self.fee_tier * 100
        
        # Total slippage
        total_slippage = price_impact + fee_impact
        
        return total_slippage
    
    def _linear_slippage_estimate(self, trade_size_usd: float) -> float:
        """Fallback linear slippage estimate"""
        # Use observed data if available
        if len(self.observed_slippages) > 5:
            # Find similar trade sizes
            similar = [s for ts, s in self.observed_slippages if abs(ts - trade_size_usd) < trade_size_usd * 0.5]
            if similar:
                return np.mean(similar)
        
        # Default estimate: 0.1% per $10k traded
        base_slippage = (trade_size_usd / 10000) * 0.1
        return base_slippage + self.fee_tier * 100
    
    def update_from_observation(self, trade_size_usd: float, actual_slippage: float):
        """Update model based on observed slippage"""
        self.observed_slippages.append((trade_size_usd, actual_slippage))
        
        # Keep only recent observations (last 100)
        if len(self.observed_slippages) > 100:
            self.observed_slippages = self.observed_slippages[-100:]


class SlippagePredictor:
    """
    Advanced slippage prediction and market impact calculator
    
    Features:
    1. Pool-specific slippage models
    2. Historical slippage learning
    3. Optimal trade size calculation
    4. Market impact exploitation
    """
    
    def __init__(self):
        """Initialize slippage predictor"""
        self.slippage_models: Dict[str, SlippageModel] = {}
        self.historical_trades: deque = deque(maxlen=1000)
        
        # Default slippage parameters
        self.default_fee_tiers = {
            'raydium': 0.0025,
            'orca': 0.0030,
            'jupiter': 0.0000,  # Aggregator finds best route
            'meteora': 0.0020
        }
        
        cprint("\n📊 Slippage Predictor Initialized", "cyan", attrs=['bold'])
        cprint("   Features:", "cyan")
        cprint("   ✅ Constant Product AMM modeling", "green")
        cprint("   ✅ Historical slippage learning", "green")
        cprint("   ✅ Market impact optimization", "green")
        cprint("   ✅ Dynamic trade sizing", "green")
    
    def get_or_create_model(self, dex: str, token_pair: str, 
                           reserve_0: float = 0, reserve_1: float = 0) -> SlippageModel:
        """Get existing slippage model or create new one"""
        key = f"{dex}_{token_pair}"
        
        if key not in self.slippage_models:
            fee_tier = self.default_fee_tiers.get(dex, 0.003)
            
            self.slippage_models[key] = SlippageModel(
                dex=dex,
                token_pair=token_pair,
                reserve_0=reserve_0,
                reserve_1=reserve_1,
                fee_tier=fee_tier,
                last_updated=time.time()
            )
        
        return self.slippage_models[key]
    
    def predict_slippage(self, dex: str, token_address: str, trade_size_usd: float,
                        is_buy: bool = True, liquidity: float = 0) -> Dict:
        """
        Predict slippage for a trade
        
        Args:
            dex: DEX name
            token_address: Token being traded
            trade_size_usd: Size of trade in USD
            is_buy: True for buy, False for sell
            liquidity: Available liquidity in pool
            
        Returns:
            Slippage prediction dict
        """
        token_pair = f"{token_address}_USDC"
        
        # Estimate reserves from liquidity
        # Assume 50/50 split for simplicity
        reserve_0 = liquidity / 2 if liquidity > 0 else 100000
        reserve_1 = liquidity / 2 if liquidity > 0 else 100000
        
        model = self.get_or_create_model(dex, token_pair, reserve_0, reserve_1)
        
        # Predict slippage
        predicted_slippage_pct = model.predict_slippage(trade_size_usd, is_buy)
        
        # Calculate price impact breakdown
        price_impact = self._calculate_price_impact(trade_size_usd, reserve_0 if is_buy else reserve_1)
        fee_impact = model.fee_tier * 100
        
        # Calculate expected received amount
        expected_amount_before_slippage = trade_size_usd
        slippage_loss = expected_amount_before_slippage * (predicted_slippage_pct / 100)
        expected_amount_after_slippage = expected_amount_before_slippage - slippage_loss
        
        result = {
            'predicted_slippage_pct': predicted_slippage_pct,
            'price_impact_pct': price_impact,
            'fee_impact_pct': fee_impact,
            'slippage_loss_usd': slippage_loss,
            'expected_amount_usd': expected_amount_after_slippage,
            'efficiency': (expected_amount_after_slippage / expected_amount_before_slippage) * 100 if expected_amount_before_slippage > 0 else 0,
            'model_confidence': self._calculate_confidence(model)
        }
        
        return result
    
    def _calculate_price_impact(self, trade_size: float, reserve: float) -> float:
        """Calculate price impact percentage"""
        if reserve <= 0:
            return 5.0  # Default high impact if unknown
        
        impact = (trade_size / (reserve + trade_size)) * 100
        return impact
    
    def _calculate_confidence(self, model: SlippageModel) -> float:
        """
        Calculate confidence in slippage prediction
        
        Higher confidence = more historical data points
        """
        num_observations = len(model.observed_slippages)
        
        if num_observations == 0:
            return 0.3  # Low confidence, no data
        elif num_observations < 5:
            return 0.5  # Medium-low confidence
        elif num_observations < 20:
            return 0.7  # Medium-high confidence
        else:
            return 0.9  # High confidence
    
    def calculate_optimal_trade_size(self, max_trade_size: float, liquidity: float,
                                     target_slippage_pct: float = 1.0) -> Dict:
        """
        Calculate optimal trade size to stay within target slippage
        
        This is KEY for maximizing profits while minimizing slippage impact
        
        Args:
            max_trade_size: Maximum we want to trade
            liquidity: Available pool liquidity
            target_slippage_pct: Maximum acceptable slippage
            
        Returns:
            Optimal trade parameters
        """
        cprint(f"\n🎯 Calculating optimal trade size...", "cyan")
        cprint(f"   Max Trade: ${max_trade_size:,.2f}", "cyan")
        cprint(f"   Liquidity: ${liquidity:,.2f}", "cyan")
        cprint(f"   Target Slippage: {target_slippage_pct}%", "cyan")
        
        # Binary search for optimal size
        optimal_size = self._binary_search_optimal_size(
            max_size=max_trade_size,
            liquidity=liquidity,
            target_slippage=target_slippage_pct
        )
        
        # Calculate efficiency at optimal size
        predicted_slippage = self._calculate_price_impact(optimal_size, liquidity / 2)
        
        result = {
            'optimal_size_usd': optimal_size,
            'predicted_slippage_pct': predicted_slippage,
            'liquidity_usage_pct': (optimal_size / liquidity) * 100 if liquidity > 0 else 0,
            'size_reduction_pct': ((max_trade_size - optimal_size) / max_trade_size) * 100 if max_trade_size > 0 else 0,
            'recommended': optimal_size > 0
        }
        
        cprint(f"   ✅ Optimal Size: ${optimal_size:,.2f} ({result['size_reduction_pct']:.1f}% reduction)", "green")
        cprint(f"   📊 Expected Slippage: {predicted_slippage:.2f}%", "green")
        
        return result
    
    def _binary_search_optimal_size(self, max_size: float, liquidity: float,
                                    target_slippage: float) -> float:
        """Binary search for trade size that meets slippage target"""
        if liquidity <= 0:
            return max_size * 0.1  # Conservative default
        
        low = max_size * 0.01  # Min 1% of max
        high = max_size
        best_size = low
        
        for _ in range(20):  # 20 iterations for precision
            mid = (low + high) / 2
            
            # Calculate slippage at this size
            slippage = self._calculate_price_impact(mid, liquidity / 2)
            
            if slippage <= target_slippage:
                # Can trade more
                best_size = mid
                low = mid
            else:
                # Need to trade less
                high = mid
            
            # Converged
            if abs(high - low) < max_size * 0.001:
                break
        
        return best_size
    
    def split_trade_for_minimal_impact(self, total_size: float, liquidity: float,
                                       num_splits: int = 3) -> List[Dict]:
        """
        Split large trade into smaller chunks to minimize total slippage
        
        This can reduce total slippage by allowing pool to rebalance between trades
        
        Args:
            total_size: Total trade size
            liquidity: Pool liquidity
            num_splits: Number of sub-trades
            
        Returns:
            List of sub-trade recommendations
        """
        cprint(f"\n✂️ Splitting trade into {num_splits} parts...", "cyan")
        
        # Calculate optimal size per split
        size_per_split = total_size / num_splits
        
        splits = []
        cumulative_slippage = 0
        
        for i in range(num_splits):
            # Each split experiences slippage
            slippage = self._calculate_price_impact(size_per_split, liquidity / 2)
            cumulative_slippage += slippage
            
            split_info = {
                'split_number': i + 1,
                'size_usd': size_per_split,
                'predicted_slippage_pct': slippage,
                'delay_seconds': i * 2 if i > 0 else 0  # 2 second delay between splits
            }
            
            splits.append(split_info)
            
            cprint(f"   Split {i+1}: ${size_per_split:,.2f} @ {slippage:.2f}% slippage", "cyan")
        
        # Compare to single trade
        single_trade_slippage = self._calculate_price_impact(total_size, liquidity / 2)
        
        avg_slippage = cumulative_slippage / num_splits
        improvement = single_trade_slippage - avg_slippage
        
        cprint(f"   📊 Single trade slippage: {single_trade_slippage:.2f}%", "yellow")
        cprint(f"   📊 Average split slippage: {avg_slippage:.2f}%", "green")
        cprint(f"   💰 Improvement: {improvement:.2f}%", "green" if improvement > 0 else "red")
        
        return splits
    
    def exploit_market_impact(self, opportunity, liquidity_buy: float, 
                             liquidity_sell: float) -> Dict:
        """
        Analyze how to exploit market impact for maximum profit
        
        Key insight: Larger trades have more slippage, but might still be profitable
        if the price difference is large enough
        
        Args:
            opportunity: Arbitrage opportunity
            liquidity_buy: Liquidity on buy DEX
            liquidity_sell: Liquidity on sell DEX
            
        Returns:
            Market impact exploitation strategy
        """
        cprint(f"\n💎 Analyzing market impact exploitation...", "magenta", attrs=['bold'])
        
        # Calculate slippage at different trade sizes
        trade_sizes = [
            opportunity.optimal_amount * 0.5,
            opportunity.optimal_amount * 1.0,
            opportunity.optimal_amount * 1.5,
            opportunity.optimal_amount * 2.0
        ]
        
        scenarios = []
        
        for size in trade_sizes:
            # Buy side slippage
            buy_slippage = self._calculate_price_impact(size, liquidity_buy / 2)
            buy_cost = size * (1 + buy_slippage / 100)
            
            # Sell side slippage
            sell_slippage = self._calculate_price_impact(size, liquidity_sell / 2)
            sell_revenue = size * (1 - sell_slippage / 100)
            
            # Net profit after slippage
            gross_profit = sell_revenue - buy_cost
            
            # Gas costs
            gas_cost = opportunity.estimated_gas_cost_usd
            flashloan_fee = size * opportunity.buy_price * 0.0005
            
            net_profit = gross_profit - gas_cost - flashloan_fee
            
            roi = (net_profit / buy_cost) * 100 if buy_cost > 0 else 0
            
            scenario = {
                'trade_size_usd': size,
                'buy_slippage_pct': buy_slippage,
                'sell_slippage_pct': sell_slippage,
                'total_slippage_pct': buy_slippage + sell_slippage,
                'gross_profit_usd': gross_profit,
                'net_profit_usd': net_profit,
                'roi_pct': roi,
                'profitable': net_profit > 0
            }
            
            scenarios.append(scenario)
            
            color = "green" if net_profit > 0 else "red"
            cprint(f"   ${size:,.0f} trade: {buy_slippage:.2f}% + {sell_slippage:.2f}% slippage = ${net_profit:.2f} profit", color)
        
        # Find best scenario
        profitable_scenarios = [s for s in scenarios if s['profitable']]
        
        if profitable_scenarios:
            best = max(profitable_scenarios, key=lambda x: x['net_profit_usd'])
            
            cprint(f"\n   ✅ BEST STRATEGY:", "green", attrs=['bold'])
            cprint(f"   Trade Size: ${best['trade_size_usd']:,.2f}", "green")
            cprint(f"   Total Slippage: {best['total_slippage_pct']:.2f}%", "green")
            cprint(f"   Net Profit: ${best['net_profit_usd']:.2f}", "green")
            cprint(f"   ROI: {best['roi_pct']:.2f}%", "green")
            
            return {
                'recommended_size': best['trade_size_usd'],
                'expected_profit': best['net_profit_usd'],
                'total_slippage': best['total_slippage_pct'],
                'scenarios': scenarios,
                'strategy': 'exploit_market_impact'
            }
        else:
            cprint(f"\n   ⚠️ No profitable scenario found with market impact", "yellow")
            
            return {
                'recommended_size': 0,
                'expected_profit': 0,
                'total_slippage': 0,
                'scenarios': scenarios,
                'strategy': 'skip_trade'
            }
    
    def learn_from_execution(self, dex: str, token_address: str, trade_size: float,
                            expected_slippage: float, actual_slippage: float):
        """
        Update slippage models based on actual execution results
        
        This is the learning component - models improve over time
        """
        token_pair = f"{token_address}_USDC"
        model = self.get_or_create_model(dex, token_pair)
        
        # Update model with observation
        model.update_from_observation(trade_size, actual_slippage)
        
        # Track prediction error
        error = abs(expected_slippage - actual_slippage)
        error_pct = (error / expected_slippage * 100) if expected_slippage > 0 else 0
        
        # Store in historical trades
        self.historical_trades.append({
            'dex': dex,
            'token': token_address,
            'size': trade_size,
            'expected_slippage': expected_slippage,
            'actual_slippage': actual_slippage,
            'error_pct': error_pct,
            'timestamp': time.time()
        })
        
        color = "green" if error_pct < 10 else "yellow" if error_pct < 25 else "red"
        cprint(f"📚 Learning: Expected {expected_slippage:.2f}%, Got {actual_slippage:.2f}% (error: {error_pct:.1f}%)", color)
    
    def get_learning_stats(self) -> Dict:
        """Get statistics on slippage prediction accuracy"""
        if not self.historical_trades:
            return {'status': 'no_data'}
        
        recent_trades = list(self.historical_trades)[-100:]
        
        errors = [t['error_pct'] for t in recent_trades]
        avg_error = np.mean(errors)
        
        accurate_predictions = len([e for e in errors if e < 10])
        accuracy_rate = (accurate_predictions / len(errors)) * 100
        
        return {
            'total_predictions': len(self.historical_trades),
            'recent_predictions': len(recent_trades),
            'avg_error_pct': avg_error,
            'accuracy_rate': accuracy_rate,
            'models_trained': len(self.slippage_models),
            'improving': avg_error < 15  # Less than 15% error is good
        }
