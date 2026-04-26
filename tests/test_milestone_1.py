import pytest

# 如果没有拷贝环境，这里会跳过
try:
    from src.master_model import V3MasterModel
except ImportError:
    V3MasterModel = None

@pytest.mark.skipif(V3MasterModel is None, reason="尚未从之前拷贝 P1 引擎，框架无法打火")
def test_mesa_init_and_step_execution():
    """
    全生态初始化验证：必须确保 100 个爬行动物可以同时塞进这台模拟器里！
    """
    # 初始化环境 (10个散户，2个套利者，5个LP)
    model = V3MasterModel(n_noise=10, n_arb=2, n_lp=5)
    
    # 时钟滴答一声：必须保证没有任何一只动物的代码因为空指针错误！
    model.step()
    model.step()
    
    # 你的 DataCollector 是否正常生效？
    df = model.datacollector.get_model_vars_dataframe()
    assert len(df) == 2, "没有抓取到上帝视角的数据切面！"
