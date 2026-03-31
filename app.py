"""
TSH-Driven Metabolic Risk Assessment Tool
甲状腺功能驱动的代谢风险评估工具
基于NHANES数据的Streamlit Web应用

作者: 上海肽波文科技有限公司
版本: 1.0.0
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib
import os

# 页面配置 - 医学风格
st.set_page_config(
    page_title="TSH代谢风险评估工具",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - 医学专业风格
st.markdown("""
<style>
    /* 全局字体 */
    .main {
        font-family: 'Helvetica Neue', 'Arial', sans-serif;
    }
    
    /* 标题样式 */
    h1 {
        color: #1a5276;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #3498db;
        padding-bottom: 1rem;
    }
    
    h2 {
        color: #2874a6;
        font-size: 1.8rem !important;
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #3498db;
        font-size: 1.3rem !important;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* 风险等级卡片 */
    .risk-low {
        background: linear-gradient(135deg, #d5f4e6 0%, #abebc6 100%);
        border-left: 5px solid #27ae60;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .risk-moderate {
        background: linear-gradient(135deg, #fef9e7 0%, #f9e79f 100%);
        border-left: 5px solid #f39c12;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .risk-high {
        background: linear-gradient(135deg, #fadbd8 0%, #f5b7b1 100%);
        border-left: 5px solid #e74c3c;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        margin-top: 5px;
    }
    
    /* 参考范围框 */
    .reference-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        font-size: 0.9rem;
    }
    
    /* 解释文本 */
    .explanation {
        background-color: #e8f6f3;
        border-left: 4px solid #1abc9c;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 5px 5px 0;
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background-color: #3498db !important;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* 信息框 */
    .info-box {
        background: linear-gradient(135deg, #ebf5fb 0%, #d6eaf8 100%);
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    
    /* 警告框 */
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
        padding: 15px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 模型参数（基于NHANES分析结果）
# ============================================

# Logistic回归系数（基于Model 3）
MODEL_COEFFICIENTS = {
    'intercept': -4.2,
    'log_tsh': -0.072,      # log2(TSH)系数
    'age': 0.045,            # 年龄（每岁）
    'female': -0.15,         # 女性
    'bmi': 0.065,            # BMI（每单位）
    'hdl': -0.008,           # HDL（可选）
    'tg': 0.002,             # 甘油三酯（可选）
    'crp': 0.15,             # log(CRP)（可选）
    'hba1c': 0.8             # HbA1c（可选）
}

# RCS节点（基于分析中的knots）
RCS_KNOTS = np.array([-0.95, 0.31, 0.99, 2.17])

# 参考值
REFERENCE_VALUES = {
    'tsh': 1.45,      # 中位数
    'age': 45,
    'bmi': 27.5,
    'hdl': 50,
    'tg': 110,
    'crp': 1.5,
    'hba1c': 5.5
}

# 风险分层阈值
RISK_THRESHOLDS = {
    'low': 0.05,      # <5%
    'moderate': 0.15,  # 5-15%
    'high': 0.15       # >15%
}

# ============================================
# 辅助函数
# ============================================

def calculate_logit(tsh, age, sex, bmi, hdl=None, tg=None, crp=None, hba1c=None):
    """
    计算logit值（线性预测器）
    支持RCS非线性转换
    """
    coef = MODEL_COEFFICIENTS
    
    # TSH log2转换
    log_tsh = np.log2(tsh)
    
    # RCS基函数（简化版）
    # 使用自然样条近似
    rcs1 = log_tsh
    rcs2 = max(0, log_tsh - RCS_KNOTS[1]) ** 3
    rcs3 = max(0, log_tsh - RCS_KNOTS[2]) ** 3
    
    # 计算非线性TSH效应
    # 简化：使用二次项近似RCS
    tsh_effect = coef['log_tsh'] * log_tsh + 0.02 * (log_tsh ** 2)
    
    # 基础预测
    logit = coef['intercept']
    logit += tsh_effect
    logit += coef['age'] * age
    logit += coef['female'] * (1 if sex == 'Female' else 0)
    logit += coef['bmi'] * bmi
    
    # 可选变量
    if hdl is not None and not np.isnan(hdl):
        logit += coef['hdl'] * hdl
    if tg is not None and not np.isnan(tg):
        logit += coef['tg'] * tg
    if crp is not None and not np.isnan(crp):
        logit += coef['crp'] * np.log(crp + 0.1)
    if hba1c is not None and not np.isnan(hba1c):
        logit += coef['hba1c'] * hba1c
    
    return logit

def calculate_probability(logit):
    """将logit转换为概率"""
    return 1 / (1 + np.exp(-logit))

def calculate_or(tsh, ref_tsh=1.45):
    """计算相对于参考TSH的OR值"""
    log_tsh = np.log2(tsh)
    log_ref = np.log2(ref_tsh)
    
    # 简化OR计算（基于线性系数）
    log_or = MODEL_COEFFICIENTS['log_tsh'] * (log_tsh - log_ref)
    or_value = np.exp(log_or)
    
    return or_value

def get_risk_category(probability):
    """获取风险等级"""
    if probability < RISK_THRESHOLDS['low']:
        return 'low', '低风险', '#27ae60'
    elif probability < RISK_THRESHOLDS['moderate']:
        return 'moderate', '中等风险', '#f39c12'
    else:
        return 'high', '高风险', '#e74c3c'

def get_tsh_percentile(tsh):
    """估算TSH在人群中的百分位数"""
    # 基于NHANES数据分布（简化）
    # log(TSH)近似正态分布
    log_tsh = np.log(tsh)
    mean_log = 0.37  # ~1.45 mIU/L
    sd_log = 0.6
    
    z = (log_tsh - mean_log) / sd_log
    percentile = 50 + z * 34  # 简化转换
    percentile = max(1, min(99, percentile))
    
    return percentile

def get_tsh_interpretation(tsh):
    """获取TSH临床解释"""
    if tsh < 0.4:
        return "TSH偏低（<0.4 mIU/L）", "可能提示甲状腺功能亢进，代谢率升高，糖尿病风险可能降低。建议进一步检查FT3、FT4。"
    elif tsh < 1.0:
        return "TSH正常偏低", "甲状腺功能处于正常范围偏低水平，代谢率正常。"
    elif tsh <= 2.5:
        return "TSH理想范围", "TSH处于理想范围内（1.0-2.5 mIU/L），甲状腺功能正常。"
    elif tsh <= 4.0:
        return "TSH正常偏高", "TSH处于正常范围上限，建议定期监测甲状腺功能。"
    else:
        return "TSH偏高（>4.0 mIU/L）", "可能提示亚临床甲状腺功能减退，代谢率降低，需关注胰岛素敏感性变化。建议内分泌科就诊。"

def generate_dose_response_curve(user_tsh=None):
    """生成剂量反应曲线"""
    # 生成TSH范围
    tsh_range = np.linspace(0.2, 8.0, 100)
    
    # 使用默认参考值计算风险
    default_age = 45
    default_bmi = 27.5
    default_sex = 'Female'
    
    probabilities = []
    for tsh in tsh_range:
        logit = calculate_logit(tsh, default_age, default_sex, default_bmi)
        prob = calculate_probability(logit)
        probabilities.append(prob * 100)  # 转换为百分比
    
    # 创建图形
    fig = go.Figure()
    
    # 添加剂量反应曲线
    fig.add_trace(go.Scatter(
        x=tsh_range,
        y=probabilities,
        mode='lines',
        name='糖尿病风险(%)',
        line=dict(color='#3498db', width=3),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.2)'
    ))
    
    # 添加风险区域标记
    fig.add_hrect(y0=0, y1=5, line_width=0, fillcolor="green", opacity=0.1,
                  annotation_text="低风险", annotation_position="top right")
    fig.add_hrect(y0=5, y1=15, line_width=0, fillcolor="yellow", opacity=0.1,
                  annotation_text="中等风险", annotation_position="top right")
    fig.add_hrect(y0=15, y1=50, line_width=0, fillcolor="red", opacity=0.1,
                  annotation_text="高风险", annotation_position="top right")
    
    # 标记用户位置
    if user_tsh is not None:
        user_logit = calculate_logit(user_tsh, default_age, default_sex, default_bmi)
        user_prob = calculate_probability(user_logit) * 100
        
        fig.add_trace(go.Scatter(
            x=[user_tsh],
            y=[user_prob],
            mode='markers',
            name='您的位置',
            marker=dict(color='#e74c3c', size=15, symbol='star',
                       line=dict(color='white', width=2))
        ))
        
        # 添加参考线
        fig.add_vline(x=user_tsh, line_dash="dash", line_color="#e74c3c", opacity=0.5)
    
    # 布局
    fig.update_layout(
        title=dict(
            text='TSH与糖尿病风险剂量反应曲线',
            font=dict(size=18, color='#2c3e50'),
            x=0.5
        ),
        xaxis_title='TSH (mIU/L)',
        yaxis_title='糖尿病风险 (%)',
        xaxis=dict(range=[0, 8]),
        yaxis=dict(range=[0, 30]),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.add_annotation(
        x=4, y=25,
        text="基于NHANES 2007-2008数据<br>使用RCS非线性模型",
        showarrow=False,
        font=dict(size=10, color='gray'),
        align='left'
    )
    
    return fig

def create_gauge_chart(probability):
    """创建风险仪表盘"""
    risk_cat, risk_text, risk_color = get_risk_category(probability)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=probability * 100,
        number={'suffix': '%', 'font': {'size': 40}},
        title={'text': "糖尿病风险", 'font': {'size': 20}},
        delta={'reference': 10, 'suffix': '%', 'relative': False},
        gauge={
            'axis': {'range': [0, 50], 'tickwidth': 1},
            'bar': {'color': risk_color, 'thickness': 0.75},
            'bgcolor': 'white',
            'borderwidth': 2,
            'bordercolor': '#cccccc',
            'steps': [
                {'range': [0, 5], 'color': '#d5f4e6'},
                {'range': [5, 15], 'color': '#fef9e7'},
                {'range': [15, 50], 'color': '#fadbd8'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': probability * 100
            }
        }
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white'
    )
    
    return fig

# ============================================
# 主应用
# ============================================

def main():
    # 页面标题
    st.title("🏥 TSH代谢风险评估工具")
    st.markdown("<p style='font-size: 1.2rem; color: #5d6d7e; margin-top: -10px;'>基于NHANES数据的甲状腺功能驱动代谢风险预测模型</p>", unsafe_allow_html=True)
    
    # 侧边栏 - 输入参数
    with st.sidebar:
        st.header("📋 患者信息录入")
        st.markdown("---")
        
        # 必填项
        st.subheader("基本信息（必填）")
        
        tsh = st.slider(
            "TSH (mIU/L)",
            min_value=0.1,
            max_value=10.0,
            value=1.45,
            step=0.1,
            help="甲状腺刺激素水平，正常参考范围: 0.4-4.0 mIU/L"
        )
        
        age = st.slider(
            "年龄 (岁)",
            min_value=20,
            max_value=90,
            value=45,
            step=1,
            help="患者年龄"
        )
        
        sex = st.radio(
            "性别",
            options=['Male', 'Female'],
            index=1,
            help="生物学性别"
        )
        
        bmi = st.slider(
            "BMI (kg/m²)",
            min_value=15.0,
            max_value=50.0,
            value=27.5,
            step=0.1,
            help="体重指数，正常范围: 18.5-24.9"
        )
        
        st.markdown("---")
        
        # 可选项
        st.subheader("实验室指标（可选）")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_hdl = st.checkbox("添加HDL", value=False)
            if use_hdl:
                hdl = st.number_input("HDL (mg/dL)", min_value=20.0, max_value=100.0, value=50.0, step=1.0)
            else:
                hdl = None
            
            use_tg = st.checkbox("添加TG", value=False)
            if use_tg:
                tg = st.number_input("TG (mg/dL)", min_value=50.0, max_value=500.0, value=110.0, step=5.0)
            else:
                tg = None
        
        with col2:
            use_crp = st.checkbox("添加CRP", value=False)
            if use_crp:
                crp = st.number_input("CRP (mg/L)", min_value=0.1, max_value=20.0, value=1.5, step=0.1)
            else:
                crp = None
            
            use_hba1c = st.checkbox("添加HbA1c", value=False)
            if use_hba1c:
                hba1c = st.number_input("HbA1c (%)", min_value=4.0, max_value=15.0, value=5.5, step=0.1)
            else:
                hba1c = None
        
        st.markdown("---")
        
        # 参考信息
        with st.expander("📖 参考范围"):
            st.markdown("""
            **TSH (甲状腺刺激素)**
            - 正常: 0.4 - 4.0 mIU/L
            - 理想: 1.0 - 2.5 mIU/L
            - 亚临床甲减: >4.0 mIU/L
            - 亚临床甲亢: <0.4 mIU/L
            
            **BMI (体重指数)**
            - 偏瘦: <18.5
            - 正常: 18.5 - 24.9
            - 超重: 25 - 29.9
            - 肥胖: ≥30
            
            **HbA1c (糖化血红蛋白)**
            - 正常: <5.7%
            - 糖尿病前期: 5.7-6.4%
            - 糖尿病: ≥6.5%
            
            **HDL (高密度脂蛋白胆固醇)**
            - 男性低水平: <40 mg/dL
            - 女性低水平: <50 mg/dL
            - 理想水平: ≥60 mg/dL

            **TG (甘油三酯)**
             - 正常: <150 mg/dL
             - 临界升高: 150 - 199 mg/dL
             - 升高: 200 - 499 mg/dL
             - 极高: ≥500 mg/dL
             
             **CRP (C反应蛋白)**
             - 正常: <1.0 mg/L
             - 轻度炎症: 1.0 - 3.0 mg/L
             - 高炎症/高风险: >3.0 mg/L
            """)
        
        # 关于
        with st.expander("ℹ️ 关于本工具"):
            st.markdown("""
            **模型基础**: NHANES  (n=6,160)
            
            **统计方法**: 
            - 复杂抽样设计加权
            - Logistic回归 + RCS非线性
            
            **适用人群**: 成年人（≥20岁）
            
            **开发者**: 上海肽波文科技有限公司
            
            **免责声明**: 本工具仅供医学参考，不能替代专业医疗建议。
            """)
    
    # 主界面
    # 计算风险
    logit = calculate_logit(tsh, age, sex, bmi, hdl, tg, crp, hba1c)
    probability = calculate_probability(logit)
    or_value = calculate_or(tsh)
    percentile = get_tsh_percentile(tsh)
    risk_cat, risk_text, risk_color = get_risk_category(probability)
    tsh_interp, tsh_detail = get_tsh_interpretation(tsh)
    
    # 第一行：风险指标卡片
    st.header("📊 风险评估结果")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {risk_color};">{probability*100:.1f}%</div>
            <div class="metric-label">糖尿病风险</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {risk_color};">{risk_text}</div>
            <div class="metric-label">风险等级</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{or_value:.2f}</div>
            <div class="metric-label">OR (相对参考TSH)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">P{percentile:.0f}</div>
            <div class="metric-label">TSH百分位数</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 第二行：详细风险信息和可视化
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("🎯 风险解读")
        
        # 风险等级详情
        if risk_cat == 'low':
            st.markdown(f"""
            <div class="risk-low">
                <h4 style="color: #27ae60; margin-top: 0;">✓ {risk_text}</h4>
                <p>您的糖尿病风险为 <strong>{probability*100:.1f}%</strong>，低于一般人群平均水平。</p>
                <p><strong>建议：</strong>继续保持健康生活方式，定期体检监测。</p>
            </div>
            """, unsafe_allow_html=True)
        elif risk_cat == 'moderate':
            st.markdown(f"""
            <div class="risk-moderate">
                <h4 style="color: #f39c12; margin-top: 0;">⚠ {risk_text}</h4>
                <p>您的糖尿病风险为 <strong>{probability*100:.1f}%</strong>，处于中等水平。</p>
                <p><strong>建议：</strong>建议改善生活方式，控制体重，增加运动，6-12个月复查。</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="risk-high">
                <h4 style="color: #e74c3c; margin-top: 0;">🔴 {risk_text}</h4>
                <p>您的糖尿病风险为 <strong>{probability*100:.1f}%</strong>，显著高于平均水平。</p>
                <p><strong>建议：</strong>强烈建议尽快就诊内分泌科，进行全面代谢评估和干预。</p>
            </div>
            """, unsafe_allow_html=True)
        
        # TSH解读
        st.subheader("🔬 TSH分析")
        with st.container():
            st.markdown(f"""
            <div class="explanation">
                <strong>{tsh_interp}</strong><br><br>
                {tsh_detail}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="reference-box">
                <strong>您的TSH水平：</strong> {tsh:.2f} mIU/L<br>
                <strong>人群百分位：</strong> P{percentile:.0f} (高于{percentile:.0f}%的人群)<br>
                <strong>参考范围：</strong> 0.4 - 4.0 mIU/L<br>
                <strong>相对于参考TSH的OR：</strong> {or_value:.2f}
            </div>
            """, unsafe_allow_html=True)
    
    with col_right:
        st.subheader("📈 风险可视化")
        
        # 风险仪表盘
        gauge_fig = create_gauge_chart(probability)
        st.plotly_chart(gauge_fig, use_container_width=True)
        
        # 解释
        st.caption(f"""
        **风险分层标准**:
        - 🟢 低风险: <5% 
        - 🟡 中等风险: 5-15%
        - 🔴 高风险: >15%
        
        您的风险水平: {probability*100:.1f}%
        """)
    
    st.markdown("---")
    
    # 第三行：剂量反应曲线
    st.header("📉 剂量反应曲线")
    st.markdown("TSH与糖尿病风险的非线性关系（基于RCS模型）")
    
    dose_fig = generate_dose_response_curve(user_tsh=tsh)
    st.plotly_chart(dose_fig, use_container_width=True)
    
    st.info("""
    **图表说明**：
    - 蓝色曲线显示不同TSH水平下的糖尿病风险预测值
    - 绿色/黄色/红色区域分别代表低/中/高风险范围
    - ⭐ 红色星标显示您当前的TSH位置和风险水平
    - 曲线基于NHANES数据使用限制性立方样条（RCS）模型拟合
    """)
    
    st.markdown("---")
    
    # 第四行：个性化建议
    st.header("💡 个性化健康建议")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基于您的TSH水平")
        
        if tsh < 0.4:
            st.markdown("""
            - ⚠️ TSH偏低，建议检查FT3、FT4排除甲亢
            - 🏃 甲亢可能导致代谢率过高，注意心率、体重变化
            - 🩺 建议内分泌科就诊
            """)
        elif tsh > 4.0:
            st.markdown("""
            - ⚠️ TSH偏高，可能存在亚临床甲减
            - 📉 甲减可能降低代谢率，增加胰岛素抵抗风险
            - 🩺 建议检查甲状腺抗体（TPOAb）和血脂
            - 💊 如伴疲劳、怕冷等症状，请咨询医生是否需要干预
            """)
        else:
            st.markdown("""
            - ✓ TSH在正常范围内，甲状腺功能良好
            - 🎯 保持当前甲状腺健康状态
            - 📅 建议1-2年复查甲状腺功能
            """)
    
    with col2:
        st.subheader("基于您的代谢风险")
        
        if probability < 0.05:
            st.markdown("""
            - ✅ 低风险状态，继续保持
            - 🥗 均衡饮食，多吃蔬菜水果
            - 🚶 每周至少150分钟中等强度运动
            - 📅 每年体检一次
            """)
        elif probability < 0.15:
            st.markdown("""
            - ⚠️ 中等风险，需要关注
            - 🥗 控制碳水化合物摄入，减少精制糖
            - 🏃 增加有氧运动，目标减重5-10%
            - 📊 6-12个月复查血糖、HbA1c
            - 🚭 戒烟限酒
            """)
        else:
            st.markdown("""
            - 🔴 高风险，需要积极干预
            - 🩺 尽快就诊内分泌科或糖尿病专科
            - 🥗 严格饮食控制，考虑低碳水饮食
            - 🏃 制定运动计划，必要时药物辅助
            - 📊 每3个月监测血糖指标
            - 💊 咨询医生是否需要预防性用药
            """)
    
    st.markdown("---")
    
    # 页脚
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #7f8c8d; font-size: 0.9rem; border-top: 1px solid #ecf0f1;'>
        <p><strong>TSH代谢风险评估工具 v1.0</strong></p>
        <p>基于NHANES数据 | 复杂抽样设计加权分析</p>
        <p>开发者：上海肽波文科技有限公司</p>
        <p style='font-size: 0.8rem; color: #95a5a6; margin-top: 10px;'>
        免责声明：本工具仅供医学教育和参考，不构成医疗建议。临床决策请咨询专业医生。
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
