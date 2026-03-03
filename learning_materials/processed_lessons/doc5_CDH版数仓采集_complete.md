# 尚硅谷电商数仓6.0 - 模块5：CDH版数仓采集

> **对应视频**: 赠送课程集  
> **原始文档**: 尚硅谷大数据项目之电商数仓（5CDH版数仓采集）.docx  
> **生成时间**: 2026-03-03  
> **难度评级**: ⭐⭐⭐⭐  
> **建议学习时长**: 8-10小时

---

## 🎯 课程开场（3分钟速览）

本模块是电商数仓项目的**第5阶段**，解决的核心问题是：**如何在企业级CDH集群环境中搭建完整的数据仓库架构**。

**你将学到**:
- Cloudera Manager (CM) 集群管理工具的完整安装与配置
- CDH生态系统组件（HDFS、YARN、Hive、Kafka、Flume、Sqoop、Oozie、Impala、Spark2）的集成部署
- 基于CDH的企业级数据采集、处理、存储、分析全流程实现
- 使用Hue进行可视化操作和Oozie工作流调度
- 完整的电商数仓分层架构（ODS→DWD→DWS→ADS）在CDH环境中的实践

**面试高频考点**: 
- CM集群部署的关键步骤和注意事项
- Flume拦截器的自定义开发与配置
- Kafka与Flume的集成模式
- 数仓分层建模在CDH环境中的具体实现
- Oozie工作流调度的配置与优化

---

## 📚 核心知识点详解

### 1. Cloudera Manager 集群部署

#### 1.1 CM简介与优势
Cloudera Manager是一个拥有集群自动化安装、中心化管理、集群监控、报警功能的企业级工具，使得：
- 集群安装时间从几天缩短到几小时内
- 运维人员从数十人降低到几人以内
- 极大提高集群管理效率和稳定性

#### 1.2 环境准备（三节点集群）
**硬件配置**：
- hadoop102: 16G内存（主节点）
- hadoop103: 4G内存（工作节点）
- hadoop104: 4G内存（工作节点）

**关键配置步骤**：
```bash
# 1. SSH免密登录配置
[root@hadoop102 .ssh]$ ssh-keygen -t rsa
[root@hadoop102 .ssh]$ ssh-copy-id hadoop102
[root@hadoop102 .ssh]$ ssh-copy-id hadoop103  
[root@hadoop102 .ssh]$ ssh-copy-id hadoop104

# 2. 集群同步脚本 xsync
#!/bin/bash
pcount=$#
if((pcount==0)); then echo no args; exit; fi
p1=$1
fname=`basename $p1`
pdir=`cd -P $(dirname $p1); pwd`
user=`whoami`
for((host=103; host<105; host++)); do
    echo ------------------- hadoop$host --------------
    rsync -av $pdir/$fname $user@hadoop$host:$pdir
done

# 3. JDK安装与环境变量配置
export JAVA_HOME=/opt/module/jdk1.8.0_144
export PATH=$PATH:$JAVA_HOME/bin

# 4. MySQL安装与数据库创建
mysql> create database amon DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
mysql> create database hive DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
mysql> create database oozie DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
mysql> create database hue DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
```

#### 1.3 CM安装与启动
**关键步骤**：
1. 创建cloudera-scm系统用户
2. 配置CM Agent指向server_host=hadoop102
3. 配置MySQL连接器：`/usr/share/java/mysql-connector-java.jar`
4. 执行数据库初始化：`scm_prepare_database.sh`
5. 配置Parcel仓库和LZO支持
6. 启动服务：7180端口访问Web UI

### 2. 数据采集架构搭建

#### 2.1 Flume日志采集（源头）
**架构设计**：
- Source: TAILDIR 监控 `/tmp/logs/*.log`
- Interceptors: 自定义ETL拦截器 + 日志类型区分拦截器
- Channel Selector: Multiplexing based on topic header
- Sinks: 双Kafka Sink (topic_start, topic_event)

**自定义拦截器开发**：
```java
// ETL拦截器 - 数据校验
public class LogETLInterceptor implements Interceptor {
    @Override
    public Event intercept(Event event) {
        String log = new String(event.getBody(), Charset.forName("UTF-8"));
        if (log.contains("start")) {
            return LogUtils.validateStart(log) ? event : null;
        } else {
            return LogUtils.validateEvent(log) ? event : null;
        }
    }
}

// 日志类型区分拦截器
public class LogTypeInterceptor implements Interceptor {
    @Override
    public Event intercept(Event event) {
        String log = new String(event.getBody(), Charset.forName("UTF-8"));
        Map<String, String> headers = event.getHeaders();
        headers.put("topic", log.contains("start") ? "topic_start" : "topic_event");
        return event;
    }
}
```

#### 2.2 Kafka消息队列
**Topic管理**：
```bash
# 创建Topic
bin/kafka-topics --create --replication-factor 1 --partitions 1 --topic topic_start
bin/kafka-topics --create --replication-factor 1 --partitions 1 --topic topic_event

# 生产/消费测试
bin/kafka-console-producer --broker-list hadoop102:9092 --topic topic_start
bin/kafka-console-consumer --bootstrap-server hadoop102:9092 --from-beginning --topic topic_start
```

#### 2.3 Flume消费Kafka写入HDFS
**配置要点**：
- Source: KafkaSource 批量消费
- Channel: Memory Channel with high capacity
- Sink: HDFS Sink with LZO compression
- 文件滚动策略：避免小文件问题

### 3. 业务数据数仓搭建

#### 3.1 Sqoop数据导入
**增量导入脚本设计**：
```bash
import_data() {
    sqoop import \
    --connect jdbc:mysql://hadoop102:3306/gmall \
    --username root --password 000000 \
    --target-dir /origin_data/gmall/db/$1/$db_date \
    --delete-target-dir --num-mappers 1 \
    --fields-terminated-by "\t" \
    --query "$2 and $CONDITIONS;"
}
```

#### 3.2 数仓分层建模

**ODS层（原始数据层）**：
- 外部表，按天分区
- 保持原始数据格式，不做任何处理
- LOCATION指向HDFS原始数据路径

**DWD层（明细数据层）**：
- Parquet格式存储，Snappy压缩
- 维度退化：商品表关联三级分类信息
- 数据清洗：过滤空值记录

**DWS层（汇总数据层）**：
- 用户行为宽表：聚合用户单日行为
- 使用CTE和UNION ALL实现多指标聚合

**ADS层（应用数据层）**：
- GMV成交总额统计
- 支持业务报表和数据分析

#### 3.3 全流程调度（Oozie + Hue）
**工作流设计**：
1. 数据生成 → 2. Sqoop导入 → 3. ODS层加载 → 4. DWD层处理 → 5. DWS层聚合 → 6. ADS层统计 → 7. Sqoop导出

**关键配置**：
- 在Hue中可视化创建工作流
- 上传Shell脚本到HDFS
- 配置任务依赖关系和参数传递

### 4. 即席查询与计算引擎升级

#### 4.1 Impala即席查询
- 安装Impala服务
- 配置Hue支持Impala查询
- 实现低延迟的交互式查询

#### 4.2 Spark2.1升级
**升级策略**：
- Spark1.6和Spark2.x并行安装
- 使用离线Parcel包避免网络下载
- 解决Java路径兼容性问题

**关键问题解决**：
```bash
# 创建Java软链接解决CM找不到JDK问题
[root@hadoop102 ~]# ln -s /opt/module/jdk1.8.0_144/ /usr/java/jdk1.8
```

---

## 💡 实践要点总结

### 环境部署关键点
1. **网络配置**：确保三台机器网络互通，主机名解析正确
2. **权限管理**：cloudera-scm用户权限，目录所有权设置
3. **依赖安装**：第三方依赖包（MySQL驱动、LZO等）的正确放置
4. **内存配置**：YARN容器内存调整为4G以支持复杂作业

### 开发调试技巧
1. **日志查看**：CM Web UI中的服务日志定位问题
2. **脚本测试**：单个Shell脚本独立测试后再集成
3. **数据验证**：每层数据处理后进行抽样验证
4. **性能优化**：合理设置Mapper数量、文件格式、压缩算法

### 常见问题排查
1. **CM启动失败**：检查7180端口占用，数据库连接配置
2. **Flume启动失败**：检查自定义拦截器JAR包位置和权限
3. **Sqoop导入失败**：验证MySQL驱动和连接参数
4. **Oozie工作流失败**：检查HDFS脚本权限和参数配置

---

## 📋 学习路线建议

**第一阶段（1-2天）**：环境搭建
- 完成CM集群部署
- 验证各组件基本功能

**第二阶段（2-3天）**：数据采集
- 实现Flume+Kafka+Flume完整链路
- 测试日志生成和数据传输

**第三阶段（2-3天）**：数仓建模
- 逐层实现ODS→DWD→DWS→ADS
- 验证各层数据质量和完整性

**第四阶段（1-2天）**：调度优化
- 配置Oozie工作流
- 实现端到端自动化

---

## 🔗 相关资源

- **官方文档**：Cloudera官方文档中心
- **社区支持**：Cloudera社区论坛
- **最佳实践**：企业级CDH集群运维指南
- **扩展学习**：Kerberos安全认证、高可用配置

---

*Generated by OpenClaw Doc Processor - Enhanced Version*
*Based on complete original content analysis*