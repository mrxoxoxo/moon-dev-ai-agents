"""
🌙 Moon Dev's Flashloan Discovery Engine
Autonomous DEX and Token discovery for the swarm
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from termcolor import cprint
from datetime import datetime, timedelta

@dataclass
class DiscoveredToken:
    """A newly discovered token on Solana"""
    address: str
    symbol: str
    name: str
    decimals: int
    liquidity_usd: float
    volume_24h: float
    price_usd: float
    dex_markets: List[str]
    discovered_at: float
    score: float = 0.0  # Opportunity score
    
    def to_dict(self) -> Dict:
        return {
            'address': self.address,
            'symbol': self.symbol,
            'name': self.name,
            'decimals': self.decimals,
            'liquidity': self.liquidity_usd,
            'volume_24h': self.volume_24h,
            'price': self.price_usd,
            'dex_markets': self.dex_markets,
            'discovered_at': self.discovered_at,
            'score': self.score
        }


@dataclass
class DiscoveredDEX:
    """A newly discovered DEX or liquidity pool"""
    name: str
    program_id: str
    type: str  # 'AMM', 'CLMM', 'OrderBook'
    total_liquidity_usd: float
    volume_24h: float
    fee_tier: float
    token_count: int
    discovered_at: float
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'program_id': self.program_id,
            'type': self.type,
            'liquidity': self.total_liquidity_usd,
            'volume_24h': self.volume_24h,
            'fee_tier': self.fee_tier,
            'token_count': self.token_count,
            'discovered_at': self.discovered_at
        }


class FlashloanDiscovery:
    """
    Autonomous discovery engine for DEXs and tokens
    
    Capabilities:
    1. Discover new tokens with high liquidity
    2. Identify active liquidity pools
    3. Find new DEX protocols
    4. Score opportunities for the swarm
    """
    
    def __init__(self):
        """Initialize discovery engine"""
        self.birdeye_api_key = os.getenv("BIRDEYE_API_KEY")
        if not self.birdeye_api_key:
            raise ValueError("BIRDEYE_API_KEY not found")
        
        # Discovery history
        self.discovered_tokens: Dict[str, DiscoveredToken] = {}
        self.discovered_dexs: Dict[str, DiscoveredDEX] = {}
        self.blacklisted_tokens: Set[str] = set()
        
        # Known Solana DEX program IDs (seed list, will discover more)
        self.known_dex_programs = {
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium V4",
            "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Whirlpool",
            "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter V6",
            "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "Meteora",
            "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": "Orca V2",
            "EewxydAPCCVuNEyrVN68PuSYdQ7wKn27V9Gjeoi8dy3S": "Lifinity",
            "PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY": "Phoenix",
            "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": "Serum/OpenBook V1"
        }
        
        # Discovery thresholds
        self.min_liquidity_usd = 10000  # Minimum $10k liquidity
        self.min_volume_24h = 1000      # Minimum $1k daily volume
        self.min_dex_liquidity = 100000  # $100k for DEX discovery
        
        cprint("\n🔍 Flashloan Discovery Engine Initialized", "cyan", attrs=['bold'])
        cprint(f"   Known DEXs: {len(self.known_dex_programs)}", "cyan")
        cprint(f"   Min Token Liquidity: ${self.min_liquidity_usd:,}", "cyan")
        cprint(f"   Min DEX Liquidity: ${self.min_dex_liquidity:,}", "cyan")
    
    def discover_new_tokens(self, limit: int = 100) -> List[DiscoveredToken]:
        """
        Discover new high-liquidity tokens on Solana
        
        Args:
            limit: Maximum number of tokens to discover
            
        Returns:
            List of discovered tokens sorted by opportunity score
        """
        cprint("\n🔍 Discovering new tokens...", "cyan")
        
        discovered = []
        
        try:
            # Use BirdEye to get trending/new tokens
            url = "https://public-api.birdeye.so/defi/tokenlist"
            headers = {"X-API-KEY": self.birdeye_api_key}
            params = {
                "sort_by": "v24hUSD",  # Sort by 24h volume
                "sort_type": "desc",
                "offset": 0,
                "limit": limit
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tokens = data.get('data', {}).get('tokens', [])
                
                cprint(f"   Found {len(tokens)} tokens from BirdEye", "green")
                
                for token_data in tokens:
                    try:
                        address = token_data.get('address')
                        
                        # Skip if already discovered or blacklisted
                        if address in self.discovered_tokens or address in self.blacklisted_tokens:
                            continue
                        
                        # Get detailed token info
                        token_info = self._get_token_details(address)
                        
                        if token_info:
                            discovered.append(token_info)
                            self.discovered_tokens[address] = token_info
                            
                            cprint(f"   ✅ {token_info.symbol}: ${token_info.liquidity_usd:,.0f} liquidity", "green")
                    
                    except Exception as e:
                        continue
                
            else:
                cprint(f"   ⚠️ BirdEye API error: {response.status_code}", "yellow")
        
        except Exception as e:
            cprint(f"   ❌ Discovery error: {str(e)}", "red")
        
        # Sort by opportunity score
        discovered.sort(key=lambda x: x.score, reverse=True)
        
        cprint(f"\n✅ Discovered {len(discovered)} new tokens", "green")
        
        return discovered
    
    def _get_token_details(self, address: str) -> Optional[DiscoveredToken]:
        """Get detailed information about a token"""
        try:
            # Get token overview from BirdEye
            url = f"https://public-api.birdeye.so/defi/token_overview"
            headers = {"X-API-KEY": self.birdeye_api_key}
            params = {"address": address}
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code != 200:
                return None
            
            data = response.json().get('data', {})
            
            # Extract key metrics
            liquidity = float(data.get('liquidity', 0))
            volume_24h = float(data.get('v24hUSD', 0))
            price = float(data.get('price', 0))
            
            # Filter by thresholds
            if liquidity < self.min_liquidity_usd or volume_24h < self.min_volume_24h:
                self.blacklisted_tokens.add(address)
                return None
            
            # Get DEX markets for this token
            dex_markets = self._get_token_dex_markets(address)
            
            # Calculate opportunity score
            score = self._calculate_token_score(liquidity, volume_24h, len(dex_markets))
            
            token = DiscoveredToken(
                address=address,
                symbol=data.get('symbol', 'UNKNOWN'),
                name=data.get('name', 'Unknown Token'),
                decimals=int(data.get('decimals', 9)),
                liquidity_usd=liquidity,
                volume_24h=volume_24h,
                price_usd=price,
                dex_markets=dex_markets,
                discovered_at=time.time(),
                score=score
            )
            
            return token
            
        except Exception as e:
            return None
    
    def _get_token_dex_markets(self, token_address: str) -> List[str]:
        """Find which DEXs have liquidity for this token"""
        markets = []
        
        try:
            # Get market data from BirdEye
            url = f"https://public-api.birdeye.so/defi/v3/token/market-data"
            headers = {"X-API-KEY": self.birdeye_api_key}
            params = {"address": token_address}
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                
                # Check for different DEX pools
                if 'raydium' in str(data).lower():
                    markets.append('raydium')
                if 'orca' in str(data).lower():
                    markets.append('orca')
                if 'jupiter' in str(data).lower():
                    markets.append('jupiter')
                if 'meteora' in str(data).lower():
                    markets.append('meteora')
        
        except:
            pass
        
        # Fallback: assume Jupiter aggregates most tokens
        if not markets:
            markets = ['jupiter']
        
        return markets
    
    def _calculate_token_score(self, liquidity: float, volume: float, dex_count: int) -> float:
        """
        Calculate opportunity score for a token
        
        Higher score = better arbitrage potential
        """
        # Base score from liquidity (log scale)
        liquidity_score = min(100, (liquidity / 10000) ** 0.5)
        
        # Volume score (activity indicator)
        volume_score = min(100, (volume / 1000) ** 0.5)
        
        # DEX diversity score (more DEXs = more arb opportunities)
        dex_score = min(100, dex_count * 25)
        
        # Weighted combination
        total_score = (
            liquidity_score * 0.4 +
            volume_score * 0.4 +
            dex_score * 0.2
        )
        
        return total_score
    
    def discover_new_dexs(self) -> List[DiscoveredDEX]:
        """
        Discover new DEX protocols on Solana
        
        Uses on-chain analysis and API data to find new trading venues
        """
        cprint("\n🔍 Discovering new DEXs...", "cyan")
        
        discovered = []
        
        try:
            # Get list of all markets from BirdEye
            url = "https://public-api.birdeye.so/defi/markets"
            headers = {"X-API-KEY": self.birdeye_api_key}
            params = {"sort_by": "liquidity", "sort_type": "desc", "limit": 50}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                markets = data.get('items', [])
                
                # Analyze markets to identify DEX programs
                program_stats = {}
                
                for market in markets:
                    try:
                        # Extract DEX info (would need actual on-chain analysis)
                        # For now, use known patterns
                        source = market.get('source', 'unknown')
                        liquidity = float(market.get('liquidity', 0))
                        volume = float(market.get('volume24h', 0))
                        
                        if source not in program_stats:
                            program_stats[source] = {
                                'liquidity': 0,
                                'volume': 0,
                                'token_count': 0
                            }
                        
                        program_stats[source]['liquidity'] += liquidity
                        program_stats[source]['volume'] += volume
                        program_stats[source]['token_count'] += 1
                    
                    except:
                        continue
                
                # Create DiscoveredDEX objects for new DEXs
                for name, stats in program_stats.items():
                    if stats['liquidity'] >= self.min_dex_liquidity:
                        # Check if this is a new DEX
                        if name not in [d.name for d in self.discovered_dexs.values()]:
                            dex = DiscoveredDEX(
                                name=name,
                                program_id="DISCOVERY_NEEDED",  # Would need on-chain lookup
                                type="AMM",  # Would need to determine type
                                total_liquidity_usd=stats['liquidity'],
                                volume_24h=stats['volume'],
                                fee_tier=0.003,  # Would need to fetch actual fee
                                token_count=stats['token_count'],
                                discovered_at=time.time()
                            )
                            
                            discovered.append(dex)
                            self.discovered_dexs[name] = dex
                            
                            cprint(f"   ✅ {name}: ${stats['liquidity']:,.0f} liquidity", "green")
        
        except Exception as e:
            cprint(f"   ❌ DEX discovery error: {str(e)}", "red")
        
        cprint(f"\n✅ Discovered {len(discovered)} new DEXs", "green")
        
        return discovered
    
    def get_top_opportunities(self, count: int = 20) -> List[DiscoveredToken]:
        """
        Get top token opportunities for arbitrage
        
        Args:
            count: Number of top opportunities to return
            
        Returns:
            List of tokens sorted by opportunity score
        """
        # Filter tokens that are on multiple DEXs (arbitrage potential)
        multi_dex_tokens = [
            token for token in self.discovered_tokens.values()
            if len(token.dex_markets) >= 2
        ]
        
        # Sort by score
        multi_dex_tokens.sort(key=lambda x: x.score, reverse=True)
        
        return multi_dex_tokens[:count]
    
    def export_discoveries(self, filepath: str):
        """Export discovered tokens and DEXs to JSON"""
        export_data = {
            'timestamp': time.time(),
            'tokens': [t.to_dict() for t in self.discovered_tokens.values()],
            'dexs': [d.to_dict() for d in self.discovered_dexs.values()],
            'stats': {
                'total_tokens': len(self.discovered_tokens),
                'total_dexs': len(self.discovered_dexs),
                'blacklisted_tokens': len(self.blacklisted_tokens)
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        cprint(f"\n💾 Discoveries exported to {filepath}", "green")
    
    def import_discoveries(self, filepath: str):
        """Import previously discovered tokens and DEXs"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Import tokens
            for token_data in data.get('tokens', []):
                token = DiscoveredToken(**token_data)
                self.discovered_tokens[token.address] = token
            
            # Import DEXs
            for dex_data in data.get('dexs', []):
                dex = DiscoveredDEX(**dex_data)
                self.discovered_dexs[dex.name] = dex
            
            cprint(f"\n📥 Imported {len(self.discovered_tokens)} tokens and {len(self.discovered_dexs)} DEXs", "green")
            
        except Exception as e:
            cprint(f"❌ Import error: {str(e)}", "red")
