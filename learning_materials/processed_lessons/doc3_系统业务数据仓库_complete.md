# 尚硅谷电商数仓6.0 - 模块3：系统业务数据仓库

> **对应视频**: 110-154集  
> **原始文档**: 尚硅谷大数据项目之电商数仓（3系统业务数据仓库）.docx  
> **生成时间**: 2026-03-03  
> **难度评级**: ⭐⭐⭐⭐  
> **建议学习时长**: 4-5小时

---

## 🎯 课程开场（2分钟速览）

本模块是电商数仓项目的**第3阶段**，解决的核心问题是：**如何从业务系统的MySQL数据库中同步业务数据到数据仓库，并构建完整的维度建模体系？**

**你将学到**:
- 电商核心业务概念（SKU、SPU）
- 数据仓库建模理论（范式、维度建模）
- 四种表类型及其同步策略
- 拉链表实现技术
- GMV成交总额计算
- 用户转化率漏斗分析
- 品牌复购率统计
- Azkaban调度器使用

**面试高频考点**: 维度建模、拉链表、同步策略、GMV计算、转化率分析

---

## 📚 核心知识点详解

### 1. 电商核心业务概念

#### 1.1 SKU与SPU定义

**SKU (Stock Keeping Unit)**:
- 库存量基本单位，产品统一编号的简称
- 每种具体商品对应唯一的SKU号
- 例如：银色、128G内存、支持联通网络的iPhoneX

**SPU (Standard Product Unit)**:
- 商品信息聚合的最小单位
- 一组可复用、易检索的标准化信息集合
- 例如：iPhoneX手机（不区分颜色、内存等具体配置）

**业务意义**:
- SPU用于商品展示和分类管理
- SKU用于库存管理和订单处理
- 一个SPU可以对应多个SKU

#### 1.2 其他电商术语

| 术语 | 含义 | 示例 |
|------|------|------|
| GMV | Gross Merchandise Volume，成交总额 | 所有订单金额总和 |
| UV | Unique Visitor，独立访客数 | 去重后的访问用户数 |
| PV | Page View，页面浏览量 | 页面被访问的总次数 |
| 转化率 | 完成目标行为的用户占比 | 下单用户数/访问用户数 |

---

### 2. 数据仓库建模理论

#### 2.1 范式概念

**第一范式(1NF)**: 属性不可再分，确保每列保持原子性
**第二范式(2NF)**: 在1NF基础上，非主属性完全依赖于主键
**第三范式(3NF)**: 在2NF基础上，消除传递依赖

**数仓中的应用**:
- 关系型数据库通常遵循3NF以减少冗余
- 数据仓库为了查询性能，常常采用反范式设计
- 维度建模就是一种典型的反范式设计

#### 2.2 维度建模 vs 关系建模

| 特性 | 关系建模 | 维度建模 |
|------|----------|----------|
| 目标 | 减少数据冗余 | 优化查询性能 |
| 结构 | 规范化表结构 | 星型/雪花型结构 |
| 适用场景 | OLTP业务系统 | OLAP分析系统 |
| 查询复杂度 | 复杂多表关联 | 简单事实表+维度表 |

#### 2.3 三种维度模型

**星型模型**:
- 一个事实表，多个维度表直接关联
- 查询性能最好，但存在数据冗余

**雪花模型**:
- 维度表进一步规范化
- 减少冗余，但增加查询复杂度

**星座模型**:
- 多个事实表共享维度表
- 适用于复杂的分析场景

```
星型模型示例:
┌─────────────┐     ┌─────────────┐
│  时间维度   │←───→│             │
└─────────────┘     │             │
                    │   事实表    │
┌─────────────┐     │             │←───→┌─────────────┐
│  用户维度   │←───→│             │     │  商品维度   │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

### 3. 四种表类型及同步策略

#### 3.1 实体表

**定义**: 现实存在的业务对象，如用户、商品、商家等
**特点**: 数据量相对较小，变化频率低
**同步策略**: **每日全量**
- 每天存储一份完整数据
- 实现简单，便于历史追溯

```sql
-- 每日全量同步示例
INSERT OVERWRITE TABLE dwd_user_info_di 
PARTITION(dt='2026-03-03')
SELECT 
    id,
    name,
    birthday,
    gender,
    email,
    phone_num
FROM ods_user_info_full
WHERE dt='2026-03-03';
```

#### 3.2 维度表

**定义**: 业务状态、编号的解释表，如地区表、订单状态等
**特点**: 数据量小，部分字段可能变化
**同步策略**: **每日全量**
- 对于可能变化的状态数据：每日全量
- 对于固定不变的维度（性别、地区等）：一次性导入

```sql
-- 维度表同步示例
INSERT OVERWRITE TABLE dwd_base_dic_full
SELECT 
    dic_code,
    dic_name,
    parent_code,
    create_time,
    operate_time
FROM ods_base_dic_full
WHERE dt='2026-03-03';
```

#### 3.3 事务型事实表

**定义**: 随业务发生不断产生的数据，如交易流水、操作日志等
**特点**: 数据量巨大，一旦发生不再变化
**同步策略**: **每日增量**
- 只同步当天新增数据
- 按日期分区存储

```sql
-- 事务型事实表同步示例
INSERT OVERWRITE TABLE dwd_order_info_inc
PARTITION(dt='2026-03-03')
SELECT 
    id,
    order_status,
    user_id,
    payment_way,
    out_trade_no,
    create_time,
    operate_time
FROM ods_order_info_inc
WHERE dt='2026-03-03';
```

#### 3.4 周期型事实表

**定义**: 随业务周期性推进而变化的数据，如订单状态变化
**特点**: 记录会随时间更新
**同步策略**: **拉链表**
- 记录数据的历史变化过程
- 通过生效时间和失效时间标识版本

---

### 4. 拉链表实现技术 ⭐重点

#### 4.1 拉链表原理

拉链表通过以下字段记录数据的历史版本：
- `start_date`: 数据生效日期
- `end_date`: 数据失效日期（9999-99-99表示当前有效）

#### 4.2 拉链表创建步骤

**步骤1: 创建拉链表结构**
```sql
CREATE TABLE dwd_order_info_his (
    id STRING COMMENT '订单ID',
    order_status STRING COMMENT '订单状态',
    user_id STRING COMMENT '用户ID',
    payment_way STRING COMMENT '支付方式',
    out_trade_no STRING COMMENT '支付流水号',
    create_time STRING COMMENT '创建时间',
    operate_time STRING COMMENT '操作时间',
    start_date STRING COMMENT '开始日期',
    end_date STRING COMMENT '结束日期'
) COMMENT '订单拉链表'
STORED AS PARQUET;
```

**步骤2: 首次全量加载**
```sql
INSERT OVERWRITE TABLE dwd_order_info_his
SELECT 
    id,
    order_status,
    user_id,
    payment_way,
    out_trade_no,
    create_time,
    operate_time,
    '2026-03-01' AS start_date,
    '9999-99-99' AS end_date
FROM ods_order_info_full
WHERE dt='2026-03-01';
```

**步骤3: 每日增量更新**
```sql
-- 创建临时表存储合并结果
WITH tmp AS (
    -- 旧数据：未变化的数据保持原样
    SELECT 
        id,
        order_status,
        user_id,
        payment_way,
        out_trade_no,
        create_time,
        operate_time,
        start_date,
        CASE 
            WHEN order_status_new IS NOT NULL THEN DATE_SUB('2026-03-02', 1)
            ELSE end_date
        END AS end_date
    FROM dwd_order_info_his old
    LEFT JOIN (
        SELECT *
        FROM ods_order_info_inc
        WHERE dt='2026-03-02'
    ) new ON old.id = new.id
    
    UNION ALL
    
    -- 新数据：新增或变化的数据
    SELECT 
        id,
        order_status,
        user_id,
        payment_way,
        out_trade_no,
        create_time,
        operate_time,
        '2026-03-02' AS start_date,
        '9999-99-99' AS end_date
    FROM ods_order_info_inc
    WHERE dt='2026-03-02'
)
INSERT OVERWRITE TABLE dwd_order_info_his
SELECT * FROM tmp;
```

#### 4.3 拉链表查询示例

**查询某天的有效数据**:
```sql
SELECT *
FROM dwd_order_info_his
WHERE '2026-03-02' BETWEEN start_date AND end_date;
```

**坑点提醒**:
- 注意日期格式的一致性
- 处理好首次加载和增量更新的逻辑
- 考虑数据延迟到达的情况

---

### 5. 核心业务需求实现

#### 5.1 GMV成交总额计算

**GMV定义**: 所有订单金额的总和（包括未支付订单）

**DWS层汇总**:
```sql
-- 日粒度GMV汇总
INSERT OVERWRITE TABLE dws_trade_user_order_td
PARTITION(dt='2026-03-03')
SELECT 
    user_id,
    COUNT(order_id) AS order_count,
    SUM(total_amount) AS order_amount
FROM dwd_order_info_his
WHERE start_date <= '2026-03-03' 
  AND end_date >= '2026-03-03'
GROUP BY user_id;
```

**ADS层最终结果**:
```sql
-- 当日GMV
INSERT OVERWRITE TABLE ads_gmv_sum_day
SELECT 
    '2026-03-03' AS dt,
    SUM(order_amount) AS gmv_amount
FROM dws_trade_user_order_td
WHERE dt='2026-03-03';
```

#### 5.2 用户转化率漏斗分析

**转化漏斗路径**:
1. 页面浏览 → 2. 商品点击 → 3. 加入购物车 → 4. 下单 → 5. 支付

**DWS层用户行为宽表**:
```sql
-- 构建用户行为宽表
INSERT OVERWRITE TABLE dws_user_action_wide_day
PARTITION(dt='2026-03-03')
SELECT 
    COALESCE(page.user_id, display.user_id, cart.user_id, order.user_id, payment.user_id) AS user_id,
    page_count,
    display_count,
    cart_count,
    order_count,
    payment_count
FROM (
    SELECT user_id, COUNT(*) AS page_count
    FROM dwd_page_log
    WHERE dt='2026-03-03' AND last_page_id IS NOT NULL
    GROUP BY user_id
) page
FULL OUTER JOIN (
    SELECT user_id, COUNT(*) AS display_count  
    FROM dwd_display_log
    WHERE dt='2026-03-03'
    GROUP BY user_id
) display ON page.user_id = display.user_id
-- ... 其他JOIN类似
```

**转化率计算**:
```sql
-- 各环节转化率
INSERT OVERWRITE TABLE ads_user_convert_day
SELECT 
    '2026-03-03' AS dt,
    SUM(display_count) / SUM(page_count) AS page_to_display_rate,
    SUM(cart_count) / SUM(display_count) AS display_to_cart_rate,
    SUM(order_count) / SUM(cart_count) AS cart_to_order_rate,
    SUM(payment_count) / SUM(order_count) AS order_to_payment_rate
FROM dws_user_action_wide_day
WHERE dt='2026-03-03';
```

#### 5.3 品牌复购率统计

**复购率定义**: 购买2次以上商品的用户占比

**实现思路**:
1. 统计每个用户每个品牌的购买次数
2. 筛选购买次数≥2的用户
3. 计算复购用户占比

```sql
-- 品牌复购率
INSERT OVERWRITE TABLE ads_brand_repurchase_day
SELECT 
    '2026-03-03' AS dt,
    brand,
    COUNT(DISTINCT IF(buy_count >= 2, user_id, NULL)) / COUNT(DISTINCT user_id) AS repurchase_rate
FROM (
    SELECT 
        user_id,
        brand,
        COUNT(*) AS buy_count
    FROM dwd_order_detail_his od
    JOIN dwd_sku_info_his si ON od.sku_id = si.id
    WHERE od.start_date <= '2026-03-03' 
      AND od.end_date >= '2026-03-03'
      AND si.start_date <= '2026-03-03'
      AND si.end_date >= '2026-03-03'
    GROUP BY user_id, brand
) t
GROUP BY brand;
```

---

### 6. Azkaban调度器

#### 6.1 Azkaban架构

```
┌─────────────────┐
│   Web Server    │ ←─── 用户界面
└─────────────────┘
        ↓
┌─────────────────┐
│   Executor      │ ←─── 任务执行
└─────────────────┘
        ↓
┌─────────────────┐
│   Hadoop集群    │ ←─── 实际作业运行
└─────────────────┘
```

#### 6.2 工作流配置

**job文件示例** (ods_to_dwd.job):
```properties
type=command
command=/bin/bash /opt/module/bin/ods_to_dwd.sh 2026-03-03
dependencies=init_db
```

**工作流文件示例** (workflow.flow):
```properties
type=flow
flow.name=gmall_workflow
```

#### 6.3 调度脚本示例

```bash
#!/bin/bash
# ods_to_dwd.sh
dt=$1

# 执行Hive脚本
hive -f /opt/module/bin/sql/ods_to_dwd_order_info.sql -d dt=$dt

# 检查执行结果
if [ $? -ne 0 ]; then
    echo "ODS to DWD failed"
    exit 1
fi

echo "ODS to DWD success"
```

---

## 💼 企业实战案例

### 场景: 构建完整的电商数仓DWD层

**需求**: 将MySQL业务数据同步到Hive数仓，构建规范的DWD层

**完整实现步骤**:

#### 步骤1: MySQL数据导出到HDFS

```bash
# 使用DataX或Sqoop导出
sqoop import \
--connect jdbc:mysql://hadoop102:3306/gmall \
--username root \
--password 000000 \
--table order_info \
--target-dir /origin_data/gmall/db/order_info/2026-03-03 \
--delete-target-dir \
--fields-terminated-by '\t' \
--compress \
--compression-codec lzop
```

#### 步骤2: ODS层建表

```sql
-- ODS层全量表
CREATE EXTERNAL TABLE ods_order_info_full (
    id STRING COMMENT '订单ID',
    order_status STRING COMMENT '订单状态',
    user_id STRING COMMENT '用户ID',
    payment_way STRING COMMENT '支付方式',
    out_trade_no STRING COMMENT '支付流水号',
    create_time STRING COMMENT '创建时间',
    operate_time STRING COMMENT '操作时间'
) COMMENT '订单表全量'
PARTITIONED BY (dt STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS PARQUET
LOCATION '/warehouse/gmall/ods/ods_order_info_full';

-- 加载数据
LOAD DATA INPATH '/origin_data/gmall/db/order_info/2026-03-03' 
INTO TABLE ods_order_info_full PARTITION(dt='2026-03-03');
```

#### 步骤3: DWD层拉链表实现

```sql
-- 首次全量加载
INSERT OVERWRITE TABLE dwd_order_info_his
SELECT 
    id,
    order_status,
    user_id,
    payment_way,
    out_trade_no,
    create_time,
    operate_time,
    '2026-03-01' AS start_date,
    '9999-99-99' AS end_date
FROM ods_order_info_full
WHERE dt='2026-03-01';
```

#### 步骤4: 验证数据质量

```sql
-- 检查拉链表数据连续性
SELECT 
    start_date,
    end_date,
    COUNT(*) AS record_count
FROM dwd_order_info_his
GROUP BY start_date, end_date
ORDER BY start_date;

-- 验证某天数据完整性
SELECT COUNT(*) 
FROM dwd_order_info_his 
WHERE '2026-03-02' BETWEEN start_date AND end_date;
```

---

## 📝 自测题库

### 题目1
**什么是拉链表？为什么要使用拉链表？**
- A. 拉链表是一种压缩存储格式
- B. 拉链表用于记录数据的历史变化过程
- C. 拉链表只存储当前最新数据
- D. 拉链表用于提高查询性能

<details>
<summary>答案</summary>
B. 拉链表通过start_date和end_date字段记录数据的历史版本，能够追溯任意时间点的数据状态。
</details>

### 题目2
**以下哪种表类型适合使用每日全量同步策略？**
- A. 订单事实表
- B. 用户实体表
- C. 页面浏览日志
- D. 支付流水表

<details>
<summary>答案</summary>
B. 用户实体表数据量相对较小且变化频率低，适合每日全量同步。
</details>

### 题目3
**GMV的计算应该包含哪些订单？**
- A. 只包含已支付订单
- B. 包含所有下单订单（无论是否支付）
- C. 只包含已完成订单
- D. 包含退款订单

<details>
<summary>答案</summary>
B. GMV（Gross Merchandise Volume）是成交总额，包含所有下单的订单金额，无论是否支付。
</details>

### 题目4
**在维度建模中，星型模型和雪花模型的主要区别是什么？**
- A. 星型模型查询性能更好，雪花模型数据冗余更少
- B. 星型模型支持更多维度，雪花模型支持更多事实
- C. 星型模型只能用于OLTP，雪花模型只能用于OLAP
- D. 星型模型需要更多存储空间，雪花模型需要更少计算资源

<details>
<summary>答案</summary>
A. 星型模型通过反范式设计减少JOIN操作，提升查询性能；雪花模型通过规范化减少数据冗余。
</details>

### 题目5
**拉链表中end_date为'9999-99-99'表示什么？**
- A. 数据已过期
- B. 数据当前有效
- C. 数据将在9999年过期
- D. 数据无效

<details>
<summary>答案</summary>
B. '9999-99-99'是一个特殊值，表示该记录当前有效，还没有被新版本替代。
</details>

---

## 🎓 课后任务

### 必做练习
1. [ ] 实现订单表的拉链表逻辑
2. [ ] 计算当日GMV并验证结果
3. [ ] 构建用户行为转化漏斗
4. [ ] 统计TOP10品牌的复购率

### 扩展阅读
- [ ] 《The Data Warehouse Toolkit》- Ralph Kimball
- [ ] Hive官方文档: 分区表和分桶表
- [ ] Azkaban官方文档: 工作流调度

---

## 💡 学习建议

### 时间规划
| 阶段 | 内容 | 时长 |
|------|------|------|
| 第1遍 | 理解建模理论和同步策略 | 60分钟 |
| 第2遍 | 动手实现拉链表 | 90分钟 |
| 第3遍 | 完成业务需求开发 | 120分钟 |
| 复习 | 遮住答案重做自测题 | 30分钟 |

### 面试准备重点
1. **能清晰解释四种表类型的同步策略**
2. **能手写拉链表的SQL实现**
3. **理解GMV、转化率、复购率的业务含义和计算逻辑**
4. **能画出维度建模的星型/雪花模型**

### 常见面试题
- Q: 如何处理缓慢变化维度？
  - A: Type1（直接覆盖）、Type2（拉链表）、Type3（新增字段）
- Q: 全量同步和增量同步的优缺点？
  - A: 全量简单但资源消耗大；增量高效但逻辑复杂
- Q: 如何保证数据一致性？
  - A: 原子性操作、幂等设计、数据校验

---

## ✅ 进度检查

完成本模块后，你应该能：
- [ ] 解释SKU/SPU等电商核心概念
- [ ] 设计合理的维度模型
- [ ] 实现拉链表同步逻辑
- [ ] 计算GMV、转化率、复购率等核心指标
- [ ] 使用Azkaban进行任务调度

---

> **下一步**: 继续学习 [模块4: 即席查询数据仓库]（对应文档4）