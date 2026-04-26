import mesa
import random


class NoiseTrader(mesa.Agent):
    """
    噪音散户：抛硬币的送财童子。
    他不在乎亏损，只在乎在 V3 里进行交易换钱，向系统提供手续费营养。
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 10000.0  # 进场本金
        self.trade_size_ratio = 0.01  # 每次交易金额占总财富的比例

    def step(self):
        # 使用 random() 判断要不要买
        if random.random() < 0.3:  # 30% 概率交易
            self.execute_random_trade()

    def execute_random_trade(self):
        """执行随机交易"""
        # 决定是买还是卖 (token_in=0 买 Token1, token_in=1 买 Token0)
        token_in = random.choice([0, 1])

        # 根据当前财富决定交易金额
        trade_value = self.wealth * self.trade_size_ratio * random.uniform(0.5, 1.5)

        if token_in == 0:
            # 买 Token1，需要先有 Token0
            amount_in = min(trade_value, self.wealth * 0.1)  # 最多10%仓位
            if amount_in < 1:
                return

            # 执行 swap
            amount_out, fee, slippage = self.model.v3_engine.execute_swap(
                agent=self,
                amount_in=amount_in,
                token_in=0,
                is_buy=True
            )

            # 更新财富 (获得 Token1，支付 Token0)
            self.wealth -= amount_in
            # 估算 Token1 的价值
            spot_price = self.model.v3_engine.get_spot_price()
            self.wealth += amount_out * spot_price * 0.9  # 扣除滑点和手续费

        else:
            # 卖 Token1，用 Token1 换 Token0
            spot_price = self.model.v3_engine.get_spot_price()
            token1_value = trade_value / spot_price
            amount_in = min(token1_value, self.wealth * 0.1 / spot_price)

            if amount_in < 0.001:
                return

            amount_out, fee, slippage = self.model.v3_engine.execute_swap(
                agent=self,
                amount_in=amount_in,
                token_in=1,
                is_buy=False
            )

            # 更新财富 (获得 Token0)
            self.wealth -= amount_in * spot_price  # 机会成本
            self.wealth += amount_out * 0.9  # 扣除滑点和手续费