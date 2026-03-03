# 尚硅谷电商数仓6.0 - 模块4：即席查询数据仓库

> **对应视频**: 155-193集  
> **原始文档**: 尚硅谷大数据项目之电商数仓（4即席查询数据仓库）.docx  
> **生成时间**: 2026-03-03  
> **难度评级**: ⭐⭐⭐⭐⭐  
> **建议学习时长**: 5-6小时

---

## 🎯 课程开场（2分钟速览）

本模块是电商数仓项目的**第4阶段**，解决的核心问题是：**如何实现海量数据的快速即席查询？**

**你将学到**:
- Presto和Impala的架构原理与性能对比
- Presto集群的安装配置与优化技巧
- Druid实时OLAP引擎的部署与使用
- 即席查询的最佳实践与SQL优化策略

**面试高频考点**: Presto vs Impala、Druid架构、列式存储优化、分区策略

---

## 📚 核心知识点详解

### 1. 即席查询基础概念

**什么是即席查询？**
- 用户根据自己的需求，灵活地选择查询条件，系统能够根据用户的选择生成相应的统计结果
- 特点：查询模式不确定、响应时间要求高、数据量大

**传统方案的问题**:
- Hive基于MapReduce，查询延迟高（分钟级）
- 无法满足交互式分析需求
- 资源利用率低

**解决方案演进**:
```
Hive(MR) → Hive(Tez/Spark) → Presto/Impala → Druid/Kylin
```

---

### 2. Presto vs Impala 架构对比 ⭐重点

#### 2.1 性能测试结论

| 维度 | Presto | Impala |
|------|--------|--------|
| 查询性能 | 稍慢 | 稍快 |
| 数据源支持 | 丰富(Hive/MySQL/Redis/图数据库等) | 主要HDFS/HBase |
| 内存管理 | 基于堆内存 | 基于C++原生内存 |
| 容错能力 | 较好 | 较差 |
| 社区活跃度 | Facebook维护，社区活跃 | Cloudera维护 |

**选择建议**:
- 如果需要多数据源联邦查询 → 选择Presto
- 如果纯Hadoop生态，追求极致性能 → 选择Impala
- 生产环境推荐Presto（容错性更好）

#### 2.2 Presto架构原理

```
┌─────────────────────────────────────────────────────┐
│                    Coordinator                      │
│  ┌─────────────┐    ┌─────────────┐               │
│  │ SQL Parser  │───→│ Query Plan  │               │
│  └─────────────┘    └─────────────┘               │
│         ↓                                           │
│  ┌─────────────┐    ┌─────────────┐               │
│  │ Plan Split  │───→│ Task Queue  │               │
│  └─────────────┘    └─────────────┘               │
└─────────────────────────────────────────────────────┘
           ↓                ↓                ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Worker    │    │   Worker    │    │   Worker    │
│ ┌─────────┐ │    │ ┌─────────┐ │    │ ┌─────────┐ │
│ │ Executor│ │    │ │ Executor│ │    │ │ Executor│ │
│ └─────────┘ │    │ └─────────┘ │    │ └─────────┘ │
└─────────────┘    └─────────────┘    └─────────────┘
```

**核心组件**:
- **Coordinator**: 负责SQL解析、查询计划生成、任务调度
- **Worker**: 负责实际的数据处理和计算
- **Connector**: 连接不同数据源的插件

---

### 3. Presto安装配置详解

#### 3.1 Server端安装

**步骤1: 下载安装包**
```bash
# 下载Presto Server
wget https://repo1.maven.org/maven2/com/facebook/presto/presto-server/0.196/presto-server-0.196.tar.gz

# 解压到/opt/module目录
tar -zxvf presto-server-0.196.tar.gz -C /opt/module/
mv /opt/module/presto-server-0.196 /opt/module/presto
```

**步骤2: 配置node.properties**
```properties
# /opt/module/presto/etc/node.properties
node.environment=production
node.id=ffffffff-ffff-ffff-ffff-ffffffffffff
node.data-dir=/opt/module/presto/data
```

**步骤3: 配置jvm.config**
```properties
# /opt/module/presto/etc/jvm.config
-server
-Xmx16G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+UseGCOverheadLimit
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:OnOutOfMemoryError=kill -9 %p
```

**步骤4: 配置config.properties (Coordinator)**
```properties
# /opt/module/presto/etc/config.properties
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
query.max-memory=50GB
query.max-memory-per-node=16GB
discovery-server.enabled=true
discovery.uri=http://hadoop102:8080
```

**步骤5: 配置config.properties (Worker)**
```properties
# hadoop103/hadoop104上的配置
coordinator=false
http-server.http.port=8080
query.max-memory=50GB
query.max-memory-per-node=16GB
discovery.uri=http://hadoop102:8080
```

#### 3.2 Client端安装

**命令行客户端**:
```bash
# 下载客户端
wget https://repo1.maven.org/maven2/com/facebook/presto/presto-cli/0.196/presto-cli-0.196-executable.jar

# 重命名并添加执行权限
mv presto-cli-0.196-executable.jar prestocli
chmod +x prestocli

# 启动客户端
./prestocli --server hadoop102:8080 --catalog hive --schema default
```

**可视化客户端(Yanagishima)**:
```bash
# 解压yanagishima
unzip yanagishima-18.0.zip
cd yanagishima-18.0

# 配置yanagishima.properties
vim conf/yanagishima.properties
# 添加以下配置：
jetty.port=8083
presto.query.max-run-time-seconds=3600
presto.address=hadoop102
presto.port=8080
presto.catalog=hive
presto.schema=default
```

---

### 4. Presto性能优化策略 ⭐重点

#### 4.1 存储层优化

**合理设置分区**:
```sql
-- GOOD: 使用分区字段过滤
SELECT user_id, event_type 
FROM dwd_page_log 
WHERE dt = '2022-01-01' 
  AND hour = '12';

-- BAD: 不使用分区字段
SELECT user_id, event_type 
FROM dwd_page_log 
WHERE event_time BETWEEN '2022-01-01 12:00:00' AND '2022-01-01 12:59:59';
```

**使用列式存储**:
- Presto对ORC格式有特殊优化
- 相比Parquet，ORC在Presto中性能更好
- 创建表时指定ORC格式：

```sql
CREATE TABLE dwd_user_action (
  user_id STRING,
  item_id STRING,
  action STRING,
  ts BIGINT
) 
PARTITIONED BY (dt STRING)
STORED AS ORC;
```

**使用Snappy压缩**:
- Snappy压缩率适中，解压速度快
- 适合即席查询场景
- 在Hive中创建表时指定：

```sql
SET hive.exec.compress.output=true;
SET mapred.output.compression.codec=org.apache.hadoop.io.compress.SnappyCodec;
```

#### 4.2 查询层优化

**只选择需要的字段**:
```sql
-- GOOD: 只选择必要字段
SELECT user_id, page_id, duration 
FROM dwd_page_log 
WHERE dt = '2022-01-01';

-- BAD: SELECT *
SELECT * 
FROM dwd_page_log 
WHERE dt = '2022-01-01';
```

**Group By字段排序**:
```sql
-- 将distinct值少的字段放在前面
SELECT province, city, COUNT(*) 
FROM dwd_user_info 
GROUP BY province, city;  -- province的distinct值 < city
```

**Join优化**:
```sql
-- 将大表放在左边（Broadcast Join）
SELECT a.user_id, b.user_name 
FROM large_table a 
JOIN small_table b ON a.user_id = b.user_id;

-- 对于两个大表，使用Partitioned Join
SET session join_distribution_type = 'PARTITIONED';
```

**Order By配合Limit**:
```sql
-- 查询Top N时一定要加LIMIT
SELECT user_id, total_amount 
FROM dws_user_order_sum 
ORDER BY total_amount DESC 
LIMIT 100;
```

---

### 5. Druid实时OLAP引擎

#### 5.1 Druid架构设计

**核心优势**:
- 实时数据摄入（秒级延迟）
- 亚秒级查询响应
- 高并发查询支持
- 数据自动过期

**架构组件**:
```
┌─────────────┐    ┌─────────────┐
│   Broker    │←──→│   Historical│
└─────────────┘    └─────────────┘
       ↑                   ↑
┌─────────────┐    ┌─────────────┐
│   Router    │    │ MiddleManager│
└─────────────┘    └─────────────┘
                           ↑
                    ┌─────────────┐
                    │   Overlord  │
                    └─────────────┘
```

#### 5.2 Imply安装部署

**步骤1: 下载Imply**
```bash
# 从官网下载Imply（包含Druid）
wget https://static.imply.io/get-started/imply-2022.07.1.tar.gz
tar -zxvf imply-2022.07.1.tar.gz -C /opt/module/
mv /opt/module/imply-2022.07.1 /opt/module/imply
```

**步骤2: 启动服务**
```bash
# 启动所有服务
/opt/module/imply/bin/supervise -c /opt/module/imply/conf/supervise/quickstart.conf

# 访问Web UI
# http://hadoop102:9095
```

**步骤3: 数据摄入配置**
```json
{
  "type": "index_parallel",
  "spec": {
    "dataSchema": {
      "dataSource": "page_views",
      "timestampSpec": {
        "column": "ts",
        "format": "millis"
      },
      "dimensionsSpec": {
        "dimensions": ["user_id", "page_id", "browser"]
      },
      "metricsSpec": [
        {"type": "count", "name": "count"},
        {"type": "longSum", "name": "duration", "fieldName": "duration"}
      ]
    }
  }
}
```

---

### 6. SQL语法差异与注意事项

#### 6.1 字段名引用
```sql
-- MySQL: 反引号
SELECT `user_id` FROM table1;

-- Presto: 双引号
SELECT "user_id" FROM table1;
```

#### 6.2 时间函数处理
```sql
-- MySQL: 直接比较
SELECT * FROM table1 WHERE ts > '2022-01-01 00:00:00';

-- Presto: 需要显式转换
SELECT * FROM table1 WHERE ts > TIMESTAMP '2022-01-01 00:00:00';
```

#### 6.3 不支持的语法
```sql
-- Presto不支持INSERT OVERWRITE
-- 需要先DELETE再INSERT
DELETE FROM target_table WHERE dt = '2022-01-01';
INSERT INTO target_table SELECT ...;
```

#### 6.4 Parquet格式限制
- Presto支持Parquet查询，但不支持Parquet写入
- 建议使用ORC格式进行写操作

---

## 💼 企业实战案例

### 场景: 构建电商实时分析平台

**需求**: 为电商平台构建实时用户行为分析系统，支持以下查询：
1. 实时PV/UV统计（5分钟延迟）
2. 用户路径分析（页面跳转序列）
3. 商品点击热力图
4. 实时转化漏斗分析

**技术选型**:
- 批处理: Presto（T+1数据）
- 实时处理: Druid（实时数据）
- 存储: HDFS + Kafka

**完整架构**:
```
App埋点 → Flume → Kafka → 
    ├──→ Spark Streaming → Druid (实时)
    └──→ HDFS → Hive → Presto (离线)
```

**Presto查询示例 - 用户路径分析**:
```sql
-- 分析用户页面跳转路径
WITH user_sessions AS (
  SELECT 
    user_id,
    page_id,
    ts,
    LAG(page_id) OVER (PARTITION BY user_id ORDER BY ts) as prev_page
  FROM dwd_page_log 
  WHERE dt = '2022-01-01'
)
SELECT 
  prev_page,
  page_id,
  COUNT(*) as transition_count
FROM user_sessions 
WHERE prev_page IS NOT NULL
GROUP BY prev_page, page_id
ORDER BY transition_count DESC
LIMIT 20;
```

**Druid查询示例 - 实时PV统计**:
```json
{
  "queryType": "timeseries",
  "dataSource": "page_views",
  "intervals": ["2022-01-01T00:00:00.000Z/2022-01-01T01:00:00.000Z"],
  "granularity": "minute",
  "aggregations": [
    {"type": "count", "name": "pv"},
    {"type": "hyperUnique", "name": "uv", "fieldName": "user_id"}
  ]
}
```

---

## 📝 自测题库

### 题目1
**Presto和Impala的主要区别是什么？**
- A. Presto基于Java，Impala基于C++
- B. Presto支持更多数据源，Impala性能稍好
- C. Presto容错性更好，Impala对内存要求更高
- D. 以上都是

<details>
<summary>答案</summary>
D. 以上都是。Presto用Java开发，Impala用C++；Presto支持多数据源联邦查询；Presto容错性更好；Impala内存管理更高效但容错性差。
</details>

### 题目2
**在Presto中，以下哪种存储格式性能最好？**
- A. TextFile
- B. SequenceFile
- C. ORC
- D. Parquet

<details>
<summary>答案</summary>
C. ORC。Presto对ORC格式做了特殊优化，相比Parquet性能更好。
</details>

### 题目3
**以下哪个Presto查询优化策略是错误的？**
- A. 只选择需要的字段
- B. 将大表放在Join的左边
- C. Group By时将distinct值多的字段放前面
- D. Order By时配合Limit使用

<details>
<summary>答案</summary>
C. 应该将distinct值少的字段放前面，这样可以减少中间结果集的大小。
</details>

### 题目4
**Druid适合什么场景？**
- A. 批处理分析
- B. 实时OLAP查询
- C. 事务处理
- D. 图计算

<details>
<summary>答案</summary>
B. Druid是专门为实时OLAP（在线分析处理）设计的，支持亚秒级查询响应。
</details>

### 题目5
**Presto不支持以下哪个SQL语法？**
- A. INSERT OVERWRITE
- B. SELECT *
- C. JOIN
- D. GROUP BY

<details>
<summary>答案</summary>
A. Presto不支持INSERT OVERWRITE语法，需要先DELETE再INSERT。
</details>

---

## 🎓 课后任务

### 必做练习
1. [ ] 完成Presto集群的安装配置
2. [ ] 使用Presto查询Hive中的电商数据
3. [ ] 对比Presto和Hive的查询性能差异
4. [ ] 配置Yanagishima可视化界面

### 扩展阅读
- [ ] Presto官方文档: Performance Tuning章节
- [ ] Druid官方文档: Data Ingestion指南
- [ ] 《高性能MySQL》- 第8章 查询优化

---

## 💡 学习建议

### 时间规划
| 阶段 | 内容 | 时长 |
|------|------|------|
| 第1遍 | 理解即席查询概念和架构 | 30分钟 |
| 第2遍 | 动手安装Presto集群 | 90分钟 |
| 第3遍 | 实践查询优化技巧 | 120分钟 |
| 第4遍 | 学习Druid实时分析 | 90分钟 |
| 复习 | 完成自测题和课后任务 | 60分钟 |

### 面试准备重点
1. **能画出Presto架构图**，解释各组件作用
2. **掌握至少5个Presto优化技巧**
3. **理解Druid的适用场景和优势**
4. **能对比不同即席查询引擎的优缺点**

### 常见面试题
- Q: 为什么选择Presto而不是直接用Hive？
  - A: Presto基于内存计算，查询延迟从分钟级降到秒级，适合交互式分析
- Q: 如何优化Presto的大表Join？
  - A: 使用Partitioned Join，或者将小表广播到所有Worker节点
- Q: Druid和Presto如何配合使用？
  - A: Druid处理实时数据（秒级延迟），Presto处理历史数据（T+1），通过统一接口对外提供服务

---

## ✅ 进度检查

完成本模块后，你应该能：
- [ ] 独立安装配置Presto集群
- [ ] 编写优化的Presto SQL查询
- [ ] 理解Druid的基本原理和使用场景
- [ ] 回答所有自测题
- [ ] 解释即席查询的最佳实践

---

> **下一步**: 继续学习 [模块5: CDH版数仓采集]（对应文档5）