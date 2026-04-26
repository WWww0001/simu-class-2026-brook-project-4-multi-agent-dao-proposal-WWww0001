"""
V3 AMM Core Engine (Uniswap V3 Style)
This is the battlefield where all agents compete.
"""
import math
import random

class V3Engine:
    """
    Uniswap V3 style AMM with concentrated liquidity.
    """
    def __init__(self, fee_tier=0.003, gas_fee=0.001):
        """
        Initialize the V3 AMM pool.
        """
        self.fee_tier = fee_tier  # 0.3% default fee
        self.gas_fee = gas_fee    # gas cost for rebalancing

        # Initial liquidity setup
        self.reserve0 = 1000000.0  # Token0 (e.g., USDC)
        self.reserve1 = 1000000.0  # Token1 (e.g., ETH)
        self.liquidity = math.sqrt(self.reserve0 * self.reserve1)

        # Price tracking
        self.sqrt_price = math.sqrt(self.reserve1 / self.reserve0)
        self.tick = 0

        # External oracle price (set by master model)
        self.oracle_price = self.reserve1 / self.reserve0

        # Position tracking for Smart LP
        self.positions = {}

    def get_spot_price(self):
        """Get current spot price (Token1/Token0)."""
        return self.reserve1 / self.reserve0

    def get_sqrt_price(self):
        """Get current sqrt price."""
        return self.sqrt_price

    def execute_swap(self, agent, amount_in, token_in, is_buy):
        """
        Execute a swap: is Buy means buying Token1 (paying Token0).
        Returns (amount_out, fee_paid, slippage)
        """
        if token_in == 0:
            # Agent pays Token0, receives Token1
            if amount_in <= 0:
                return 0, 0, 0

            # Calculate output with fee
            fee = amount_in * self.fee_tier
            amount_in_after_fee = amount_in - fee

            # Constant product formula: x * y = k
            # (reserve0 + dx) * (reserve1 - dy) = reserve0 * reserve1
            amount_out = (amount_in_after_fee * self.reserve1) / (self.reserve0 + amount_in_after_fee)

            if amount_out > self.reserve1 * 0.5:
                amount_out = self.reserve1 * 0.5  # Prevent draining

            # Apply slippage based on size
            expected_out = amount_in * self.get_spot_price()
            slippage = abs(amount_out - expected_out) / expected_out if expected_out > 0 else 0

            # Update reserves
            self.reserve0 += amount_in
            self.reserve1 -= amount_out

            # Update sqrt price
            self.sqrt_price = math.sqrt(self.reserve1 / self.reserve0)

            return amount_out, fee, slippage

        else:
            # Agent pays Token1, receives Token0
            if amount_in <= 0:
                return 0, 0, 0

            fee = amount_in * self.fee_tier
            amount_in_after_fee = amount_in - fee

            amount_out = (amount_in_after_fee * self.reserve0) / (self.reserve1 + amount_in_after_fee)

            if amount_out > self.reserve0 * 0.5:
                amount_out = self.reserve0 * 0.5

            expected_out = amount_in * (1 / self.get_spot_price())
            slippage = abs(amount_out - expected_out) / expected_out if expected_out > 0 else 0

            self.reserve1 += amount_in
            self.reserve0 -= amount_out

            self.sqrt_price = math.sqrt(self.reserve1 / self.reserve0)

            return amount_out, fee, slippage

    def addLiquidity(self, agent_id, amount0, amount1, tick_lower, tick_upper):
        """
        Add liquidity to a specific range (Uniswap V3 style).
        """
        if amount0 <= 0 or amount1 <= 0:
            return 0

        # Calculate liquidity based on amount and range
        sqrt_price = self.get_sqrt_price()
        sqrt_lower = 1.0001 ** tick_lower
        sqrt_upper = 1.0001 ** tick_upper

        # Simple liquidity calculation
        delta_liquidity0 = amount0 * (sqrt_upper * sqrt_lower) / (sqrt_upper - sqrt_lower)
        delta_liquidity1 = amount1 / (sqrt_upper - sqrt_lower)
        liquidity = min(delta_liquidity0, delta_liquidity1)

        # Store position
        position_value = amount0 + amount1 * self.get_spot_price()
        self.positions[agent_id] = {
            'liquidity': liquidity,
            'tick_lower': tick_lower,
            'tick_upper': tick_upper,
            'amount0': amount0,
            'amount1': amount1,
            'value': position_value
        }

        # Update reserves
        self.reserve0 += amount0
        self.reserve1 += amount1

        return liquidity

    def removeLiquidity(self, agent_id):
        """
        Remove liquidity from a position.
        """
        if agent_id not in self.positions:
            return 0, 0

        pos = self.positions[agent_id]
        amount0 = pos['amount0']
        amount1 = pos['amount1']

        # Update reserves
        self.reserve0 -= amount0
        self.reserve1 -= amount1

        del self.positions[agent_id]

        return amount0, amount1

    def rebalance_position(self, agent_id, new_tick_lower, new_tick_upper):
        """
        Rebalance a Smart LP position (incurs gas cost).
        Returns (new_amount0, new_amount1) after rebalancing.
        """
        if agent_id not in self.positions:
            return 0, 0

        # Remove old position
        amount0, amount1 = self.removeLiquidity(agent_id)

        # Add new position with same amounts but new range
        self.addLiquidity(agent_id, amount0, amount1, new_tick_lower, new_tick_upper)

        return amount0, amount1

    def is_in_range(self, agent_id):
        """
        Check if an LP position is in the current price range.
        """
        if agent_id not in self.positions:
            return False

        pos = self.positions[agent_id]
        current_tick = int(math.log(self.sqrt_price) / math.log(1.0001))
        return pos['tick_lower'] <= current_tick <= pos['tick_upper']

    def get_pool_stats(self):
        """Get current pool statistics."""
        return {
            'reserve0': self.reserve0,
            'reserve1': self.reserve1,
            'spot_price': self.get_spot_price(),
            'sqrt_price': self.sqrt_price,
            'liquidity': self.liquidity,
            'total_positions': len(self.positions)
        }

    def update_oracle_price(self, new_price):
        """Update the external oracle price."""
        self.oracle_price = new_price