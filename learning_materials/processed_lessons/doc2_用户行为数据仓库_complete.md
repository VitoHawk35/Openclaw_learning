# 尚硅谷电商数仓6.0 - 模块2：用户行为数据仓库

> **对应视频**: 066-109集  
> **原始文档**: 尚硅谷大数据项目之电商数仓（2用户行为数据仓库）.docx  
> **生成时间**: 2026-03-03  
> **难度评级**: ⭐⭐⭐⭐  
> **建议学习时长**: 4-5小时

---

## 🎯 课程开场（2分钟速览）

本模块是整个电商数仓项目的**ODS到DWD层建设阶段**，解决的核心问题是：**如何将原始日志数据清洗、转换并构建分层的数据仓库？**

**你将学到**:
- Hive数仓环境搭建与Tez引擎优化
- ODS层和DWD层的表结构设计
- 用户活跃、新增、留存等核心指标的计算逻辑
- 数据质量监控与元数据备份策略

**面试高频考点**: 数仓分层设计、Hive性能优化、用户行为指标计算、Tez vs MR

---

## 📚 核心知识点详解

### 1. 数仓环境准备

#### 1.1 Hive & MySQL 安装配置

**Hive配置要点**:
```xml
<!-- hive-site.xml 关键配置 -->
<property>
    <name>hive.metastore.schema.verification</name>
    <value>false</value>
    <description>关闭元数据版本检查</description>
</property>
<property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://hadoop102:3306/metastore?useSSL=false</value>
</property>
<property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>com.mysql.jdbc.Driver</value>
</property>
```

**MySQL元数据库创建**:
```sql
-- 创建Hive元数据库
CREATE DATABASE metastore;
-- 授权用户
GRANT ALL PRIVILEGES ON metastore.* TO 'hive'@'%' IDENTIFIED BY 'hive';
FLUSH PRIVILEGES;
```

#### 1.2 Tez 引擎配置与优化 ⭐重点

**为什么选择Tez？**
- **性能优势**: Tez将多个有依赖的MR作业合并为一个作业，减少中间结果写入HDFS的次数
- **资源利用率**: 减少任务启动开销，提高集群资源利用率
- **执行效率**: DAG执行模型比MapReduce的两阶段模型更高效

**Tez安装步骤**:
```bash
# 1. 下载并解压Tez
tar -zxvf apache-tez-0.9.1-bin.tar.gz -C /opt/module/
mv /opt/module/apache-tez-0.9.1 /opt/module/tez-0.9.1

# 2. 配置Hive环境变量
echo 'export TEZ_HOME=/opt/module/tez-0.9.1' >> /opt/module/hive/conf/hive-env.sh
echo 'export TEZ_JARS=""' >> /opt/module/hive/conf/hive-env.sh
echo 'for jar in $TEZ_HOME/lib/*.jar; do' >> /opt/module/hive/conf/hive-env.sh
echo '    export TEZ_JARS=$TEZ_JARS:$jar' >> /opt/module/hive/conf/hive-env.sh
echo 'done' >> /opt/module/hive/conf/hive-env.sh
echo 'export HIVE_AUX_JARS_PATH=$HADOOP_HOME/share/hadoop/common/hadoop-lzo-0.4.20.jar:$TEZ_JARS' >> /opt/module/hive/conf/hive-env.sh

# 3. 创建tez-site.xml
cat > /opt/module/hive/conf/tez-site.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <property>
        <name>tez.lib.uris</name>
        <value>\${fs.defaultFS}/tez/tez-0.9.1,\${fs.defaultFS}/tez/tez-0.9.1/lib</value>
    </property>
    <property>
        <name>tez.use.cluster.hadoop-libs</name>
        <value>true</value>
    </property>
    <property>
        <name>tez.history.logging.service.class</name>
        <value>org.apache.tez.dag.history.logging.ats.ATSHistoryLoggingService</value>
    </property>
</configuration>
EOF

# 4. 上传Tez到HDFS
hadoop fs -mkdir /tez
hadoop fs -put /opt/module/tez-0.9.1/ /tez
```

**Tez内存调优**:
```sql
-- 在Hive中设置Tez参数
SET hive.tez.container.size=2048;
SET hive.tez.java.opts=-Xmx1638m;
SET tez.grouping.max-size=32000000;
SET tez.grouping.min-size=16000000;
```

### 2. 数仓命名规范

#### 2.1 分层命名规则

| 层级 | 命名前缀 | 说明 |
|------|---------|------|
| ODS | ods_ | 原始数据层 |
| DWD | dwd_ | 明细数据层 |
| DWS | dws_ | 汇总数据层 |
| ADS | ads_ | 应用数据层 |

#### 2.2 数据库命名规范

- **临时表数据库**: `xxx_tmp`
- **备份数据数据库**: `xxx_bak`
- **业务数据库**: 按业务域命名，如 `gmall`

### 3. ODS层建设

#### 3.1 ODS层设计原则

- **保持原始性**: 不做任何清洗和转换
- **分区存储**: 按天分区，便于增量处理
- **压缩格式**: 使用LZO压缩，支持切片
- **列式存储**: 使用ORC或Parquet格式

#### 3.2 ODS层建表语句

```sql
-- 用户行为日志表
DROP TABLE IF EXISTS ods_log;
CREATE EXTERNAL TABLE ods_log (
    line STRING
)
PARTITIONED BY (dt STRING)
STORED AS 
INPUTFORMAT 'com.hadoop.mapred.DeprecatedLzoTextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION '/warehouse/gmall/ods/ods_log';

-- 加载数据
LOAD DATA INPATH '/origin_data/gmall/log/topic_log/2020-06-14' INTO TABLE ods_log PARTITION(dt='2020-06-14');
```

### 4. DWD层建设

#### 4.1 DWD层设计目标

- **数据清洗**: 去除空值、脏数据、异常值
- **字段解析**: 将JSON字符串解析为结构化字段
- **维度退化**: 将常用维度字段冗余到事实表中
- **数据标准化**: 统一字段命名和数据格式

#### 4.2 用户行为日志解析

**Flume拦截器实现**:
```java
public class LogInterceptor implements Interceptor {
    
    private static final Logger LOG = LoggerFactory.getLogger(LogInterceptor.class);
    
    @Override
    public Event intercept(Event event) {
        byte[] body = event.getBody();
        String log = new String(body, StandardCharsets.UTF_8);
        
        // 1. 验证JSON格式
        JSONObject jsonObject = JSON.parseObject(log);
        if (jsonObject.getString("cm") == null || jsonObject.getJSONArray("et") == null) {
            return null; // 过滤无效数据
        }
        
        // 2. 添加时间戳头信息
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        String dt = sdf.format(new Date());
        event.getHeaders().put("timestamp", String.valueOf(System.currentTimeMillis()));
        event.getHeaders().put("logType", "startup");
        
        return event;
    }
    
    @Override
    public List<Event> intercept(List<Event> events) {
        List<Event> intercepted = new ArrayList<>();
        for (Event event : events) {
            Event interceptedEvent = intercept(event);
            if (interceptedEvent != null) {
                intercepted.add(interceptedEvent);
            }
        }
        return intercepted;
    }
}
```

**Hive UDTF解析JSON**:
```java
public class BaseLogUDTF extends GenericUDTF {
    
    private ArrayList<String> outRecord = new ArrayList<String>();
    
    @Override
    public StructObjectInspector initialize(StructObjectInspector argOIs) throws UDFArgumentException {
        // 定义输出字段
        ArrayList<String> fieldNames = new ArrayList<String>();
        ArrayList<ObjectInspector> fieldOIs = new ArrayList<ObjectInspector>();
        
        fieldNames.add("mid");
        fieldOIs.add(PrimitiveObjectInspectorFactory.javaStringObjectInspector);
        fieldNames.add("uid");
        fieldOIs.add(PrimitiveObjectInspectorFactory.javaStringObjectInspector);
        // ... 其他公共字段
        
        return ObjectInspectorFactory.getStandardStructObjectInspector(fieldNames, fieldOIs);
    }
    
    @Override
    public void process(Object[] args) throws HiveException {
        String input = args[0].toString();
        JSONObject jsonObject = JSON.parseObject(input);
        JSONObject cm = jsonObject.getJSONObject("cm");
        
        outRecord.clear();
        outRecord.add(cm.getString("mid"));
        outRecord.add(cm.getString("uid"));
        // ... 解析其他字段
        
        forward(outRecord.toArray());
    }
    
    @Override
    public void close() throws HiveException {}
}
```

#### 4.3 DWD层建表示例

```sql
-- 用户启动日志明细表
DROP TABLE IF EXISTS dwd_start_log;
CREATE EXTERNAL TABLE dwd_start_log(
    `mid_id` string,
    `user_id` string,
    `version_code` string,
    `version_name` string,
    `lang` string,
    `source` string,
    `os` string,
    `area` string,
    `model` string,
    `brand` string,
    `sdk_version` string,
    `gmail` string,
    `height_width` string,
    `app_time` string,
    `network` string,
    `lng` string,
    `lat` string,
    `entry` string,
    `open_ad_type` string,
    `action` string,
    `loading_time` string,
    `detail` string,
    `extend1` string
)
PARTITIONED BY (dt string)
STORED AS ORC
LOCATION '/warehouse/gmall/dwd/dwd_start_log'
TBLPROPERTIES('orc.compress' = 'snappy');

-- 插入数据
INSERT OVERWRITE TABLE dwd_start_log PARTITION(dt='2020-06-14')
SELECT 
    mid_id,
    user_id,
    version_code,
    version_code,
    lang,
    source,
    os,
    area,
    model,
    brand,
    sdk_version,
    gmail,
    height_width,
    app_time,
    network,
    lng,
    lat,
    get_json_object(kv,'$.entry') entry,
    get_json_object(kv,'$.open_ad_type') open_ad_type,
    get_json_object(kv,'$.action') action,
    get_json_object(kv,'$.loading_time') loading_time,
    get_json_object(kv,'$.detail') detail,
    get_json_object(kv,'$.extend1') extend1
FROM dwd_base_event_log
WHERE dt='2020-06-14' AND event_name='start';
```

### 5. 核心业务指标计算

#### 5.1 用户活跃主题

**DWS层用户日活表**:
```sql
-- 每日活跃设备表
DROP TABLE IF EXISTS dws_uv_detail_daycount;
CREATE EXTERNAL TABLE dws_uv_detail_daycount(
    `mid_id` string,
    `brand` string,
    `model` string,
    `login_count` bigint,
    `visit_count` bigint
)
PARTITIONED BY (dt string)
STORED AS PARQUET
LOCATION '/warehouse/gmall/dws/dws_uv_detail_daycount';

-- 计算日活
INSERT OVERWRITE TABLE dws_uv_detail_daycount PARTITION(dt='2020-06-14')
SELECT 
    mid_id,
    brand,
    model,
    sum(if(event_name='start',1,0)) login_count,
    sum(if(event_name='display',1,0)) visit_count
FROM dwd_base_event_log
WHERE dt='2020-06-14'
GROUP BY mid_id, brand, model;
```

#### 5.2 用户新增主题

**新增用户识别逻辑**:
- **定义**: 首次联网使用应用的用户
- **关键点**: 卸载再安装的设备不会被算作新增
- **实现**: 通过设备ID首次出现时间判断

```sql
-- 创建首日表
DROP TABLE IF EXISTS dwd_new_mid_count;
CREATE EXTERNAL TABLE dwd_new_mid_count(
    `mid_id` string,
    `brand` string,
    `model` string,
    `first_login_time` string
)
COMMENT '每日新增设备'
PARTITIONED BY (dt string)
STORED AS PARQUET
LOCATION '/warehouse/gmall/dwd/dwd_new_mid_count';

-- 计算新增设备
WITH tmp AS (
    SELECT 
        mid_id,
        brand,
        model,
        min(dt) first_login_date
    FROM dwd_start_log
    GROUP BY mid_id, brand, model
)
INSERT OVERWRITE TABLE dwd_new_mid_count PARTITION(dt='2020-06-14')
SELECT 
    mid_id,
    brand,
    model,
    first_login_date
FROM tmp
WHERE first_login_date='2020-06-14';
```

#### 5.3 用户留存主题

**留存率计算公式**:
- **N日留存率** = 第N天仍活跃的用户数 / 首日新增用户数

```sql
-- 创建留存分析表
DROP TABLE IF EXISTS ads_user_retention_day_rate;
CREATE EXTERNAL TABLE ads_user_retention_day_rate(
    `stat_date` string COMMENT '统计日期',
    `create_date` string COMMENT '新增日期',
    `retention_day` int COMMENT '截至当前日期留存天数',
    `retention_count` bigint COMMENT '留存数量',
    `new_mid_count` bigint COMMENT '新增数量',
    `retention_ratio` decimal(10,2) COMMENT '留存率'
)
COMMENT '每日用户留存率'
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
LOCATION '/warehouse/gmall/ads/ads_user_retention_day_rate';

-- 计算留存率
INSERT OVERWRITE TABLE ads_user_retention_day_rate
SELECT
    '2020-06-14' stat_date,
    create_date,
    retention_day,
    retention_count,
    new_mid_count,
    cast(retention_count/new_mid_count*100 as decimal(10,2)) retention_ratio
FROM
(
    SELECT
        '2020-06-14' stat_date,
        create_date,
        datediff('2020-06-14',create_date) retention_day,
        count(*) retention_count
    FROM
    (
        SELECT
            t1.mid_id,
            t1.create_date,
            t2.dt login_date
        FROM
        (
            SELECT
                mid_id,
                dt create_date
            FROM dwd_new_mid_count
            WHERE dt >= date_sub('2020-06-14',7) AND dt <= '2020-06-14'
        ) t1
        JOIN
        (
            SELECT
                mid_id,
                dt
            FROM dwd_start_log
            WHERE dt='2020-06-14'
        ) t2
        ON t1.mid_id=t2.mid_id
    ) t3
    GROUP BY create_date
) t4
JOIN
(
    SELECT
        dt create_date,
        count(*) new_mid_count
    FROM dwd_new_mid_count
    WHERE dt >= date_sub('2020-06-14',7) AND dt <= '2020-06-14'
    GROUP BY dt
) t5
ON t4.create_date=t5.create_date;
```

### 6. 元数据备份策略

#### 6.1 备份重要性

- **风险**: 元数据损坏可能导致整个集群无法运行
- **要求**: 每日零点后备份到其他服务器，至少保留两个副本
- **工具**: 使用mysqldump进行MySQL元数据备份

#### 6.2 自动化备份脚本

```bash
#!/bin/bash
# backup_metastore.sh

DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backup/metastore"
MYSQL_USER="root"
MYSQL_PASS="000000"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份Hive元数据库
mysqldump -u$MYSQL_USER -p$MYSQL_PASS --single-transaction --routines --triggers metastore > $BACKUP_DIR/metastore_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "metastore_*.sql" -mtime +7 -delete

# 同步到备份服务器
rsync -avz $BACKUP_DIR/metastore_$DATE.sql backup-server:/backup/metastore/
```

---

## 💼 企业实战案例

### 场景: 构建完整的用户行为分析数据管道

**需求**: 从原始日志到用户活跃、新增、留存指标的完整数据管道

**完整实现流程**:

1. **数据采集层**: Flume + Kafka 采集用户行为日志
2. **ODS层**: Hive外部表存储原始日志，按天分区
3. **DWD层**: 解析JSON日志，构建明细事实表
4. **DWS层**: 聚合用户行为，构建主题宽表
5. **ADS层**: 计算核心业务指标

**关键挑战与解决方案**:

- **挑战1**: JSON日志解析性能问题
  - **方案**: 使用自定义UDTF + Tez引擎优化
  
- **挑战2**: 数据倾斜导致任务失败
  - **方案**: 对热点设备ID进行随机前缀打散
  
- **挑战3**: 新增用户识别准确性
  - **方案**: 结合设备指纹 + 用户行为模式双重验证

---

## 📝 自测题库

### 题目1
**为什么在Hive中要关闭元数据版本检查（hive.metastore.schema.verification=false）？**
- A. 提高性能
- B. 避免版本不兼容导致启动失败
- C. 减少内存占用
- D. 提高安全性

<details>
<summary>答案</summary>
B. 关闭元数据版本检查可以避免Hive版本与MySQL元数据库版本不匹配导致的启动失败问题。
</details>

### 题目2
**Tez相比MapReduce的主要优势是什么？**
- A. 支持更多数据源
- B. 减少中间结果写入HDFS的次数
- C. 更好的SQL语法支持
- D. 自动数据压缩

<details>
<summary>答案</summary>
B. Tez采用DAG执行模型，可以将多个有依赖的作业合并，减少中间结果持久化到HDFS的次数，从而提升性能。
</details>

### 题目3
**在计算用户留存率时，分母应该是什么？**
- A. 当日活跃用户数
- B. 当日新增用户数
- C. 首日新增用户数
- D. 总注册用户数

<details>
<summary>答案</summary>
C. 留存率的分母是首日新增用户数，分子是第N天仍然活跃的用户数。
</details>

### 题目4
**DWD层的主要作用是什么？**
- A. 存储原始数据
- B. 数据清洗和标准化
- C. 业务指标计算
- D. 数据可视化

<details>
<summary>答案</summary>
B. DWD层（明细数据层）主要负责数据清洗、字段解析、维度退化等标准化处理。
</details>

### 题目5
**为什么ODS层要使用LZO压缩而不是Gzip？**
- A. LZO压缩率更高
- B. LZO支持切片，Gzip不支持
- C. LZO压缩速度更快
- D. LZO是开源的

<details>
<summary>答案</summary>
B. LZO压缩支持切片（splittable），可以在MapReduce任务中并行处理，而Gzip不支持切片。
</details>

---

## 🎓 课后任务

### 必做练习
1. [ ] 完成Tez引擎的完整配置，并验证Hive查询性能提升
2. [ ] 实现用户行为日志的JSON解析UDTF
3. [ ] 计算连续7天的用户活跃、新增、留存指标

### 扩展阅读
- [ ] 《Hive编程指南》- 第8章 性能调优
- [ ] Tez官方文档: DAG执行模型详解
- [ ] Apache Flume官方文档: 拦截器开发

---

## 💡 学习建议

### 时间规划
| 阶段 | 内容 | 时长 |
|------|------|------|
| 第1遍 | 通读本文档，理解整体架构 | 40分钟 |
| 第2遍 | 动手实践环境配置和建表 | 90分钟 |
| 第3遍 | 完成指标计算和优化 | 120分钟 |
| 复习 | 遮住答案重做自测题 | 30分钟 |

### 面试准备重点
1. **能画出数仓分层架构图**，解释各层的作用
2. **能详细说明Tez的工作原理**和性能优势
3. **熟悉用户行为指标的计算逻辑**
4. **能回答数据质量问题的处理方案**

### 常见面试题
- Q: 如何处理数据倾斜问题？
  - A: 对热点key加随机前缀；使用MapJoin；调整分区策略
- Q: 为什么要做数仓分层？
  - A: 降低复杂度；提高复用性；便于维护；隔离原始数据
- Q: 如何保证数据质量？
  - A: 数据校验规则；监控告警；数据血缘追踪；定期数据审计

---

## ✅ 进度检查

完成本模块后，你应该能：
- [ ] 独立完成Hive+Tez环境搭建
- [ ] 设计合理的数仓分层结构
- [ ] 实现用户行为日志的完整解析流程
- [ ] 计算核心业务指标（活跃、新增、留存）
- [ ] 回答所有自测题

---

> **下一步**: 继续学习 [模块3: 系统业务数据仓库]（对应文档3）