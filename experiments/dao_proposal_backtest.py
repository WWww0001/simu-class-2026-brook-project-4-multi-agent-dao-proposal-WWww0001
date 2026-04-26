"""
DAO Proposal 回测脚本
用于验证和测试 Multi-Agent Micro-Market Game 的各项机制
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.master_model import V3MasterModel


def run_simulation(n_steps=100, n_noise=10, n_arb=2, n_lp=5):
    """
    运行模拟实验

    Args:
        n_steps: 模拟步数
        n_noise: 噪音散户数量
        n_arb: 套利者数量
        n_lp: 智能LP数量

    Returns:
        DataFrame: 包含模拟结果
    """
    print(f"启动模拟: {n_noise}散户, {n_arb}套利者, {n_lp}LP, {n_steps}步")

    # 初始化模型
    model = V3MasterModel(
        n_noise=n_noise,
        n_arb=n_arb,
        n_lp=n_lp,
        initial_price=1.0,
        oracle_volatility=0.002
    )

    # 运行模拟
    for i in range(n_steps):
        model.step()
        if (i + 1) % 20 == 0:
            print(f"  进度: {i+1}/{n_steps} | "
                  f"Oracle价格: {model.oracle_price:.4f} | "
                  f"池子价格: {model.v3_engine.get_spot_price():.4f}")

    print("模拟完成！")

    return model


def analyze_results(model):
    """分析模拟结果"""
    print("\n" + "=" * 60)
    print("模拟结果分析")
    print("=" * 60)

    # 获取模型数据
    df = model.datacollector.get_model_vars_dataframe()

    print(f"\n最终状态:")
    print(f"  Oracle 价格: {model.oracle_price:.4f}")
    print(f"  池子现货价格: {model.v3_engine.get_spot_price():.4f}")
    print(f"  池子 Reserve0: {model.v3_engine.reserve0:,.2f}")
    print(f"  池子 Reserve1: {model.v3_engine.reserve1:,.2f}")

    print(f"\n各类群体总财富:")
    print(f"  噪音散户: {model.get_agent_wealth_by_type(__import__('src.agents.noise_trader', fromlist=['NoiseTrader']).NoiseTrader):,.2f}")
    print(f"  套利者: {model.get_agent_wealth_by_type(__import__('src.agents.arbitrageur', fromlist=['Arbitrageur']).Arbitrageur):,.2f}")
    print(f"  智能LP: {model.get_agent_wealth_by_type(__import__('src.agents.smart_lp', fromlist=['SmartLPAgent']).SmartLPAgent):,.2f}")

    return df


def plot_results(df, save_path=None):
    """可视化结果"""
    sns.set_style("darkgrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 价格走势
    ax1 = axes[0, 0]
    ax1.plot(df['Oracle_Price'], label='Oracle Price', alpha=0.7)
    ax1.plot(df['Spot_Price'], label='Spot Price', alpha=0.7)
    ax1.set_xlabel('Step')
    ax1.set_ylabel('Price')
    ax1.set_title('Price Comparison: Oracle vs Spot')
    ax1.legend()

    # 池子储备
    ax2 = axes[0, 1]
    ax2.plot(df['Reserve0'], label='Reserve0', alpha=0.7)
    ax2.plot(df['Reserve1'], label='Reserve1', alpha=0.7)
    ax2.set_xlabel('Step')
    ax2.set_ylabel('Reserve Amount')
    ax2.set_title('Pool Reserves Over Time')
    ax2.legend()

    # 群体财富
    ax3 = axes[1, 0]
    ax3.plot(df['Total_Noise_Wealth'], label='Noise Traders', alpha=0.7)
    ax3.plot(df['Total_Arb_Wealth'], label='Arbitrageurs', alpha=0.7)
    ax3.plot(df['Total_LP_Wealth'], label='Smart LPs', alpha=0.7)
    ax3.set_xlabel('Step')
    ax3.set_ylabel('Total Wealth')
    ax3.set_title('Agent Wealth Over Time')
    ax3.legend()

    # 代理人数
    ax4 = axes[1, 1]
    ax4.plot(df['Num_Agents'], label='Total Agents', color='purple', alpha=0.7)
    ax4.set_xlabel('Step')
    ax4.set_ylabel('Count')
    ax4.set_title('Number of Agents')
    ax4.legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"\n图表已保存至: {save_path}")
    else:
        plt.show()

    plt.close()


def main():
    """主函数"""
    print("=" * 60)
    print("DAO Proposal 回测实验")
    print("=" * 60)

    # 运行模拟
    model = run_simulation(n_steps=100, n_noise=10, n_arb=2, n_lp=5)

    # 分析结果
    df = analyze_results(model)

    # 可视化
    plot_results(df, save_path='experiments/simulation_results.png')

    print("\n" + "=" * 60)
    print("回测完成！")
    print("=" * 60)

    return model, df


if __name__ == "__main__":
    main()