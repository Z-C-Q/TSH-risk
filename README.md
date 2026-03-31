# 🏥 TSH代谢风险评估工具

基于NHANES数据的甲状腺功能驱动代谢风险预测Web应用

## 📋 功能特点

### 核心功能
- ✅ **糖尿病风险预测** - 基于Logistic回归+RCS非线性模型
- ✅ **代谢风险评分** - 低/中/高三等级分类
- ✅ **OR计算** - 相对于参考TSH的比值比
- ✅ **人群百分位** - TSH在总体中的位置
- ✅ **实时可视化** - 剂量反应曲线+风险仪表盘

### 输入参数
| 参数 | 类型 | 必填 | 参考范围 |
|------|------|------|----------|
| TSH | 滑动条 | ✅ | 0.1-10 mIU/L |
| 年龄 | 滑动条 | ✅ | 20-90岁 |
| 性别 | 单选 | ✅ | 男/女 |
| BMI | 滑动条 | ✅ | 15-50 kg/m² |
| HDL | 数字输入 | ❌ | 20-100 mg/dL |
| TG | 数字输入 | ❌ | 50-500 mg/dL |
| CRP | 数字输入 | ❌ | 0.1-20 mg/L |
| HbA1c | 数字输入 | ❌ | 4-15% |

### 输出内容
1. **风险指标卡片** - 风险百分比、等级、OR值、百分位
2. **风险解读** - 根据风险等级提供个性化解释
3. **TSH分析** - 临床意义解读和参考值对比
4. **风险仪表盘** - 动态可视化风险水平
5. **剂量反应曲线** - 标记用户位置的RCS曲线
6. **健康建议** - 基于TSH水平和代谢风险的个性化建议

## 🚀 快速开始

### 方式1：本地运行

```bash
# 1. 克隆/下载项目
cd tsh_risk_app

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
streamlit run app.py

# 5. 浏览器访问
# http://localhost:8501
```

### 方式2：Streamlit Cloud部署（免费）

```bash
# 1. 将代码推送到GitHub
# 2. 访问 https://streamlit.io/cloud
# 3. 连接GitHub仓库
# 4. 选择app.py作为主文件
# 5. 自动部署完成！
```

### 方式3：Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# 构建镜像
docker build -t tsh-risk-app .

# 运行容器
docker run -p 8501:8501 tsh-risk-app
```

## 📊 模型说明

### 统计模型
- **基础模型**: Logistic回归
- **非线性**: 限制性立方样条（RCS）近似
- **数据来源**: NHANES 2007-2008 (n=6,160)
- **统计方法**: 复杂抽样设计加权

### 模型系数（简化版）
```python
MODEL_COEFFICIENTS = {
    'intercept': -4.2,
    'log_tsh': -0.072,    # TSH (log2转换)
    'age': 0.045,          # 年龄
    'female': -0.15,       # 女性
    'bmi': 0.065,          # BMI
    'hdl': -0.008,         # HDL (可选)
    'tg': 0.002,           # 甘油三酯 (可选)
    'crp': 0.15,           # log(CRP) (可选)
    'hba1c': 0.8           # HbA1c (可选)
}
```

### RCS节点
```python
RCS_KNOTS = [-0.95, 0.31, 0.99, 2.17]  # log2(TSH)尺度
```

## 🎨 界面预览

### 侧边栏输入
- 滑动条输入（TSH、年龄、BMI）
- 单选按钮（性别）
- 可折叠的高级选项（HDL、TG、CRP、HbA1c）
- 参考范围说明

### 主界面
1. **指标卡片** - 4个关键指标实时显示
2. **风险解读** - 根据风险等级显示不同颜色
3. **TSH分析** - 临床意义解释
4. **风险仪表盘** - 动态仪表盘可视化
5. **剂量反应曲线** - 交互式Plotly图表
6. **健康建议** - 个性化建议

## ⚙️ 技术栈

| 技术 | 用途 |
|------|------|
| Streamlit | Web应用框架 |
| Plotly | 交互式可视化 |
| NumPy | 数值计算 |
| Pandas | 数据处理 |
| HTML/CSS | 自定义样式 |

## 📁 文件结构

```
tsh_risk_app/
├── app.py                 # 主应用文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
└── .streamlit/
    └── config.toml       # Streamlit配置（可选）
```

## 🔧 自定义配置

### 修改模型参数
编辑 `app.py` 中的 `MODEL_COEFFICIENTS` 字典

### 调整风险阈值
```python
RISK_THRESHOLDS = {
    'low': 0.05,      # <5%
    'moderate': 0.15,  # 5-15%
    'high': 0.15       # >15%
}
```

### 更改样式
修改 `st.markdown()` 中的CSS代码块

## 📱 兼容性

- ✅ Chrome/Edge/Firefox/Safari
- ✅ 桌面端（推荐）
- ✅ 移动端（响应式适配）
- ✅ iOS/Android浏览器

## 🌐 在线演示

部署后可通过以下链接访问：
- Streamlit Cloud: `https://your-app-name.streamlit.app`
- 自有服务器: `http://your-server:8501`

## 📝 更新日志

### v1.0.0 (2024-03-30)
- ✨ 初始版本发布
- 📊 基于NHANES数据的预测模型
- 📈 实时RCS剂量反应曲线
- 🎨 医学专业风格界面

## 📧 技术支持

**开发者**: 上海肽波文科技有限公司

**功能请求/问题反馈**: 
- 邮箱: [待添加]
- GitHub Issues: [待添加]

## 📄 许可证

MIT License - 可自由使用和修改

## ⚠️ 免责声明

本工具基于统计模型开发，仅供参考：
- 不替代专业医疗诊断
- 预测结果存在不确定性
- 临床决策请咨询医生
- 模型基于美国人群数据，其他人群可能适用性有限

---

**最新版本**: v1.0.0  
**更新日期**: 2024-03-30
