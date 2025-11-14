# Django知识图谱功能实现详细分析

## 功能概述

该系统实现了企业知识图谱功能，支持用户输入两个或多个企业名称，通过分析企业经营范围和关键词分词，识别企业间的共同特征，并以可视化图谱展示企业间的关联关系。

## 数据结构

### 核心数据源：data-words.csv

**文件位置**: `/django/gd/service/data-words.csv`

**数据规模**: 约6000+条企业记录

**数据结构**:
```csv
id,company_name,score,business_scope,words
1,广州第七轴智能设备有限公司,82,专用设备制造；工业机器人制造；智能机器人销售...,电子,研发,咨询服务,设计,计算机,技术开发...
2,广州电玩时代科技有限公司,57,科技中介服务；运行效能评估服务；机械设备研发...,研发,咨询服务,技术开发,机械设备,软件开发...
```

**字段说明**:
- `id`: 企业唯一标识
- `company_name`: 企业名称
- `score`: 企业评分（0-100）
- `business_scope`: 经营范围（原始文本，用分号分隔）
- `words`: 关键词分词结果（逗号分隔的词汇）

## 核心功能实现

### 1. 后端视图逻辑 (django/gd/views.py)

**路由**: `/graph/`

**主要函数**: `graph(request)`

**处理流程**:
```python
def graph(request):
    if request.method == "POST":
        if 'random' in request.POST:
            # 随机选择企业模式
            input_companies = get_random_companies()
        else:
            # 手动输入企业名称模式
            input_companies = request.POST.get("companies")
        # 调用图谱生成函数
        makeGraph.draw_graph(input_companies)
        # 返回结果页面
        return render(request, 'gd/graph.html', {
            'graph_generated': True,
            'graph_image': 'graph.png',
            'companies': input_companies
        })
    return render(request, 'gd/graph.html', {'graph_generated': False})
```

**关键功能**:
- 支持手动输入企业名称（逗号分隔）
- 支持随机选择企业功能
- 调用图谱生成模块
- 结果展示和状态管理

### 2. 图谱生成核心逻辑 (django/gd/service/makeGraph.py)

**主要函数**: `draw_graph(input_companies)`

**详细处理流程**:

#### 2.1 数据加载和筛选
```python
# 加载完整企业数据集
gd_data = pd.read_csv('gd/service/data-words.csv')

# 解析输入的企业名称
target_companies = [company.strip() for company in input_companies.split(',')]

# 筛选目标企业数据
filtered_data = gd_data[gd_data['company_name'].isin(target_companies)]
```

#### 2.2 图结构构建
```python
# 创建无向图
G = nx.Graph()

# 添加节点和边的函数
def add_nodes_edges(data):
    for index, row in data.iterrows():
        company_name = row['company_name']
        score = row['score']
        business_scope = row['business_scope']
        words = row['words']

        # 添加公司节点
        G.add_node(company_name, type='company', score=score, business_scope=business_scope)

        # 处理关键词节点和连接
        if pd.notna(words):
            keywords = words.split(',')
            for keyword in set(keywords):  # 使用set去重
                if not G.has_node(keyword):
                    G.add_node(keyword, type='keyword', count=0)
                G.nodes[keyword]['count'] += 1
                G.add_edge(company_name, keyword)
```

#### 2.3 关键词重叠识别
```python
# 识别多个公司共享的关键词
shared_keyword_nodes = [
    node for node, attrs in G.nodes(data=True)
    if attrs['type'] == 'keyword' and attrs['count'] > 1
]
```

#### 2.4 可视化配置
```python
# 图形设置
fig, ax = plt.subplots(figsize=(18, 12))
ax.patch.set_facecolor('#F5F5F5')
pos = nx.spring_layout(G, k=0.5)  # 弹簧布局算法

# 节点分类
company_nodes = [node for node, attrs in G.nodes(data=True) if attrs['type'] == 'company']
keyword_nodes = [node for node, attrs in G.nodes(data=True)
                if attrs['type'] == 'keyword' and node not in shared_keyword_nodes]

# 节点绘制
nx.draw_networkx_nodes(G, pos, nodelist=company_nodes, node_color='#87CEFA', node_size=900)
nx.draw_networkx_nodes(G, pos, nodelist=keyword_nodes, node_color='#7CCD7C', node_size=700)
nx.draw_networkx_nodes(G, pos, nodelist=shared_keyword_nodes, node_color='#8470FF', node_size=700)

# 边和标签绘制
nx.draw_networkx_edges(G, pos, edge_color='#BEBEBE')
nx.draw_networkx_labels(G, pos, font_size=15, font_color='black')

# 保存图片
plt.savefig("static/gd/graph.png", bbox_inches='tight', pad_inches=0)
```

**颜色编码**:
- 🔵 **蓝色节点 (#87CEFA)**: 企业节点
- 🟢 **绿色节点 (#7CCD7C)**: 企业独有关键词
- 🟣 **紫色节点 (#8470FF)**: 多企业共享关键词

### 3. 前端用户界面 (templates/gd/graph.html)

**界面组成**:

#### 3.1 输入区域
```html
<div class="search-container">
    <!-- 手动输入表单 -->
    <form method="post">
        <input type="text" name="companies" placeholder="请输入两个企业名称（用英文逗号分隔）" required>
        <button type="submit">生成图形</button>
    </form>

    <!-- 随机选择表单 -->
    <form method="post">
        <input type="hidden" name="random" value="true">
        <button type="submit">随机生成两个企业</button>
    </form>
</div>
```

#### 3.2 结果展示
```html
{% if graph_generated %}
    <h3>企业-经营范围-分词-知识图谱-生成结果</h3>
    <img src="{% static 'gd/graph.png' %}" alt="Graph">
{% endif %}
```

**用户交互流程**:
1. 用户访问 `/graph/` 页面
2. 输入企业名称或选择随机生成
3. 提交表单，触发POST请求
4. 后端处理并生成图谱
5. 页面刷新显示可视化结果

## 技术架构

### 依赖库和框架
- **后端**: Django (Python Web框架)
- **数据处理**: Pandas (数据分析库)
- **图算法**: NetworkX (网络分析库)
- **可视化**: Matplotlib (绘图库)
- **前端**: HTML/CSS/JavaScript

### 字体和国际化支持
```python
# 支持中文字符显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
matplotlib.use('Agg')  # 非交互式后端
```

## 关键算法特点

### 1. 图算法选择
- **图类型**: 无向图 (undirected graph)
- **布局算法**: 弹簧布局 (spring layout) - 自动节点位置优化
- **社区检测**: 基于关键词重叠识别关联性

### 2. 关键词处理
- **去重处理**: 使用`set(keywords)`避免重复关键词
- **重叠计算**: 通过`count`属性统计关键词被多少企业共享
- **可视化区分**: 用不同颜色标识独有关键词和共享关键词

### 3. 性能优化
- **数据筛选**: 只处理用户指定的企业数据，减少计算量
- **内存管理**: 使用`plt.close()`释放绘图资源
- **图片缓存**: 生成静态PNG文件，避免重复计算

## 应用场景

1. **竞品分析**: 识别竞争对手的业务重叠领域
2. **投资决策**: 分析企业间的协同效应
3. **产业链分析**: 理解企业间的上下游关系
4. **创新研究**: 发现技术交叉点和合作机会
5. **市场研究**: 识别行业趋势和共同特点

## 扩展可能性

1. **动态图谱**: 实时更新企业数据
2. **交互式可视化**: 使用D3.js等前端技术
3. **智能推荐**: 基于图谱相似度的企业推荐
4. **时间维度**: 追踪企业业务范围的时间变化
5. **聚类分析**: 自动识别企业群组和行业类别

## 部署配置

### 目录结构
```
django/
├── gd/
│   ├── views.py           # 视图逻辑
│   ├── urls.py           # 路由配置
│   └── service/
│       ├── makeGraph.py  # 图谱生成核心
│       └── data-words.csv # 企业数据
├── static/
│   └── gd/
│       └── graph.png     # 生成的图谱图片
└── templates/
    └── gd/
        └── graph.html    # 前端模板
```

### 依赖安装
```bash
pip install django pandas networkx matplotlib
```

该系统通过整合企业数据分析、图算法和可视化技术，为企业关系分析提供了直观且功能强大的工具支持。