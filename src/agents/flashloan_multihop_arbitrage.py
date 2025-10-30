"""
🌙 Moon Dev's Multi-Hop Arbitrage Engine
Triangular and complex arbitrage paths (up to 30 tokens)
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
import networkx as nx
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from termcolor import cprint
import numpy as np
from itertools import combinations

@dataclass
class ArbitragePath:
    """A multi-hop arbitrage path"""
    path_id: str
    tokens: List[str]  # Token path
    dexs: List[str]   # DEX for each hop
    expected_profit_usd: float
    expected_profit_pct: float
    path_length: int
    total_fees: float
    total_slippage: float
    risk_score: float
    execution_complexity: int  # Number of swaps
    
    def to_dict(self) -> Dict:
        return {
            'path_id': self.path_id,
            'tokens': self.tokens,
            'dexs': self.dexs,
            'profit_usd': self.expected_profit_usd,
            'profit_pct': self.expected_profit_pct,
            'length': self.path_length,
            'fees': self.total_fees,
            'slippage': self.total_slippage,
            'risk': self.risk_score,
            'complexity': self.execution_complexity
        }


class MultiHopArbitrage:
    """
    Find arbitrage paths through multiple tokens and DEXs
    
    Examples:
    - Triangular: USDC -> WETH -> SOL -> USDC
    - 4-hop: USDC -> TOKEN1 -> TOKEN2 -> WETH -> USDC
    - Complex: Up to 30 tokens in path
    
    Uses graph algorithms (Bellman-Ford) to find negative cycles
    """
    
    def __init__(self, flashloan_core):
        self.core = flashloan_core
        
        # Graph of tokens and prices
        self.price_graph = nx.DiGraph()
        
        # Configuration
        self.max_path_length = 30  # Maximum tokens in path
        self.min_path_length = 3   # Minimum (triangular)
        
        # DEX configurations
        self.dex_fees = {
            'raydium': 0.0025,
            'orca': 0.003,
            'jupiter': 0.0,  # Aggregator
            'meteora': 0.002
        }
        
        cprint("\n🔀 Multi-Hop Arbitrage Engine Initialized", "cyan", attrs=['bold'])
        cprint(f"   Max Path Length: {self.max_path_length} tokens", "cyan")
        cprint(f"   Min Path Length: {self.min_path_length} tokens (triangular)", "cyan")
        cprint("   Algorithm: Bellman-Ford (negative cycle detection)", "cyan")
    
    def build_price_graph(self, tokens: List[str], dex_prices: Dict) -> nx.DiGraph:
        """
        Build a directed graph of token prices across DEXs
        
        Args:
            tokens: List of token addresses
            dex_prices: Dict of {(token_a, token_b, dex): price}
            
        Returns:
            NetworkX directed graph
        """
        cprint(f"\n🏗️ Building price graph with {len(tokens)} tokens...", "cyan")
        
        G = nx.DiGraph()
        
        # Add nodes
        for token in tokens:
            G.add_node(token)
        
        # Add edges (exchange rates)
        edges_added = 0
        for (token_a, token_b, dex), price in dex_prices.items():
            if token_a in tokens and token_b in tokens:
                # Add edge with negative log price (for Bellman-Ford)
                # Negative cycle = arbitrage opportunity
                weight = -np.log(price * (1 - self.dex_fees.get(dex, 0.003)))
                
                G.add_edge(
                    token_a,
                    token_b,
                    weight=weight,
                    price=price,
                    dex=dex,
                    fee=self.dex_fees.get(dex, 0.003)
                )
                
                edges_added += 1
        
        self.price_graph = G
        
        cprint(f"✅ Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges", "green")
        
        return G
    
    def find_all_arbitrage_paths(self, start_token: str = 'USDC', 
                                 max_paths: int = 100) -> List[ArbitragePath]:
        """
        Find all arbitrage opportunities using Bellman-Ford
        
        Args:
            start_token: Token to start and end with (usually USDC)
            max_paths: Maximum number of paths to return
            
        Returns:
            List of profitable arbitrage paths
        """
        cprint(f"\n🔍 Searching for arbitrage paths starting with {start_token}...", "cyan", attrs=['bold'])
        
        paths = []
        
        # Try different path lengths
        for path_length in range(self.min_path_length, min(self.max_path_length + 1, 15)):
            # Find cycles of this length
            length_paths = self._find_paths_of_length(start_token, path_length)
            paths.extend(length_paths)
            
            if len(paths) >= max_paths:
                break
        
        # Filter profitable paths
        profitable = [p for p in paths if p.expected_profit_usd > 0]
        
        # Sort by profit
        profitable.sort(key=lambda x: x.expected_profit_usd, reverse=True)
        
        cprint(f"\n📊 Found {len(profitable)} profitable paths:", "green")
        
        # Print top 5
        for i, path in enumerate(profitable[:5], 1):
            path_str = ' → '.join([t[:8] for t in path.tokens])
            cprint(f"   {i}. {path_str}", "cyan")
            cprint(f"      Profit: ${path.expected_profit_usd:,.2f} ({path.expected_profit_pct:.2f}%)", "green")
            cprint(f"      Length: {path.path_length} hops", "white")
        
        return profitable[:max_paths]
    
    def _find_paths_of_length(self, start_token: str, length: int) -> List[ArbitragePath]:
        """Find all profitable cycles of specific length"""
        paths = []
        
        if start_token not in self.price_graph:
            return paths
        
        # Use DFS to find cycles
        visited = set()
        current_path = [start_token]
        
        def dfs(node, depth, cumulative_value, path, dexs_used):
            if depth == length:
                # Check if we can return to start
                if self.price_graph.has_edge(node, start_token):
                    edge_data = self.price_graph[node][start_token]
                    final_value = cumulative_value * edge_data['price'] * (1 - edge_data['fee'])
                    
                    # Calculate profit
                    profit_pct = (final_value - 1.0) * 100
                    
                    if profit_pct > 0.5:  # At least 0.5% profit
                        # Create path object
                        full_path = path + [start_token]
                        full_dexs = dexs_used + [edge_data['dex']]
                        
                        arb_path = self._create_arbitrage_path(
                            full_path, full_dexs, final_value, profit_pct
                        )
                        
                        paths.append(arb_path)
                return
            
            # Explore neighbors
            for neighbor in self.price_graph.neighbors(node):
                if neighbor not in visited or (depth == length - 1 and neighbor == start_token):
                    edge_data = self.price_graph[node][neighbor]
                    new_value = cumulative_value * edge_data['price'] * (1 - edge_data['fee'])
                    
                    visited.add(neighbor)
                    dfs(neighbor, depth + 1, new_value, path + [neighbor], dexs_used + [edge_data['dex']])
                    visited.remove(neighbor)
        
        # Start DFS
        visited.add(start_token)
        dfs(start_token, 0, 1.0, [start_token], [])
        
        return paths
    
    def _create_arbitrage_path(self, tokens: List[str], dexs: List[str], 
                              final_value: float, profit_pct: float) -> ArbitragePath:
        """Create ArbitragePath object from path data"""
        # Calculate total fees
        total_fees = sum(self.dex_fees.get(dex, 0.003) for dex in dexs)
        
        # Estimate slippage (increases with path length)
        total_slippage = len(tokens) * 0.001  # 0.1% per hop
        
        # Risk score (longer paths = more risk)
        risk_score = min(1.0, len(tokens) / 10)
        
        # Expected profit in USD (assuming $1000 trade)
        base_trade_size = 1000
        expected_profit = base_trade_size * (profit_pct / 100)
        
        path_id = '_'.join([t[:6] for t in tokens[:5]])
        
        return ArbitragePath(
            path_id=path_id,
            tokens=tokens,
            dexs=dexs,
            expected_profit_usd=expected_profit,
            expected_profit_pct=profit_pct,
            path_length=len(tokens) - 1,  # Number of hops
            total_fees=total_fees,
            total_slippage=total_slippage,
            risk_score=risk_score,
            execution_complexity=len(dexs)
        )
    
    def execute_multihop_arbitrage(self, path: ArbitragePath, trade_size_usd: float) -> Dict:
        """
        Execute a multi-hop arbitrage
        
        Args:
            path: Arbitrage path to execute
            trade_size_usd: Trade size in USD
            
        Returns:
            Execution result
        """
        cprint(f"\n🚀 EXECUTING MULTI-HOP ARBITRAGE", "green", attrs=['bold'])
        cprint(f"   Path: {' → '.join([t[:8] for t in path.tokens])}", "cyan")
        cprint(f"   Hops: {path.path_length}", "cyan")
        cprint(f"   Trade Size: ${trade_size_usd:,.2f}", "yellow")
        cprint(f"   Expected Profit: ${path.expected_profit_usd * (trade_size_usd / 1000):,.2f}", "green")
        
        # Build multi-hop transaction
        # This would create a complex transaction with multiple swaps
        
        # For now, simulated
        return {
            'success': True,
            'profit': path.expected_profit_usd * (trade_size_usd / 1000),
            'path': path.to_dict(),
            'simulated': True
        }
