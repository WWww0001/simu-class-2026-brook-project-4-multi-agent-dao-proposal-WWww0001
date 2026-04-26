import mesa
import math


class Arbitrageur(mesa.Agent):
    """
    剧毒的机械猎兵（MEV / Toxic Arbitrageur）。
    他什么风险都不承担，他的唯一目标是盯着池子里的价格与外界比对。
    如果有油水，一秒钟抽干它！
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 100000.0  # 它拥有天量级的吸血资金
        self.threshold = 0.005  # 千分之五差价才值得动手（覆盖池子手续费）

    def step(self):
        # 1. 向主神获取当前外部的真理天平价格 (Oracle Price)
        oracle_price = self.model.oracle_price

        # 2. 从 self.model.v3_engine 捞取目前池子里的实际推算价格
        spot_price = self.model.v3_engine.get_spot_price()

        # 3. 计算偏差
        price_deviation = (spot_price - oracle_price) / oracle_price if oracle_price > 0 else 0

        # 4. 如果偏差 > threshold，开启核弹攻击！
        if abs(price_deviation) > self.threshold:
            self.execute_arbitrage(price_deviation, oracle_price)

    def execute_arbitrage(self, deviation, oracle_price):
        """
        执行套利：精准计算需要多少交易来把池子价格推平到 Oracle 价格。
        """
        spot_price = self.model.v3_engine.get_spot_price()

        # 判断套利方向
        if deviation > 0:
            # 池子价格高于 Oracle，应该卖出 Token1 买入 Token0
            # 这会降低池子的 Token1/Token0 价格比例
            token_in = 1  # 卖 Token1
        else:
            # 池子价格低于 Oracle，应该买入 Token1 卖出 Token0
            token_in = 0  # 买 Token1
            deviation = -deviation

        # 计算需要的交易金额来纠正价格
        # 使用泰勒展开近似: Δprice ≈ (d price / d x) * Δx
        # 对于 constant product: price = reserve1 / reserve0
        # d price / d x ≈ -reserve1 / reserve0^2 (当卖 reserve0)
        # 或者: d price / d x ≈ 1 / reserve0 (当卖 reserve1)

        reserve0 = self.model.v3_engine.reserve0
        reserve1 = self.model.v3_engine.reserve1

        # 需要的输入金额近似
        # Δprice / price ≈ Δx / reserve0 (for selling Token1)
        required_input = abs(deviation) * reserve0 * 0.8

        # 限制交易规模
        max_trade = min(self.wealth * 0.2, reserve0 * 0.1, reserve1 * 0.1)
        amount_in = min(required_input, max_trade)

        if amount_in < 1:
            return

        # 执行套利
        amount_out, fee, slippage = self.model.v3_engine.execute_swap(
            agent=self,
            amount_in=amount_in,
            token_in=token_in,
            is_buy=(token_in == 0)
        )

        # 更新财富
        if token_in == 0:
            # 买 Token1
            self.wealth -= amount_in
            self.wealth += amount_out * oracle_price * 0.995  # 按 oracle 计价
        else:
            # 卖 Token1
            self.wealth += amount_out  # 获得 Token0
            self.wealth -= amount_in * oracle_price  # 付出 Token1

        # 限制 wealth 为非负
        self.wealth = max(0, self.wealth)