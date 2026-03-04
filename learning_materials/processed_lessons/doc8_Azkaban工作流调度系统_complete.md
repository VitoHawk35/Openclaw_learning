# 尚硅谷电商数仓6.0 - 模块8：Azkaban工作流调度系统

> **对应视频**: 赠送课程集  
> **原始文档**: 尚硅谷大数据技术之Azkaban.docx  
> **生成时间**: 2026-03-03  
> **难度评级**: ⭐⭐⭐  
> **建议学习时长**: 4-6小时

---

## 🎯 课程开场（2分钟速览）

本模块是电商数仓项目的**工作流调度阶段**，解决的核心问题是：**如何实现复杂数据处理任务的自动化调度和依赖管理**。

**你将学到**:
- Azkaban 工作流调度系统的基本架构和核心组件
- Job 配置文件的编写和工作流定义
- 复杂依赖关系的工作流设计
- 与现有数仓架构（Hive、Sqoop、Shell脚本）的集成
- Web UI 操作和任务监控

**面试高频考点**: 
- Azkaban 与其他调度系统（Oozie、Airflow）的对比
- 工作流依赖配置的最佳实践
- 故障处理和重试机制

---

## 📚 核心知识点详解

### 1. Azkaban 系统架构

#### 1.1 核心组件
- **Web Server**: 提供 Web UI 和 API 接口
- **Executor Server**: 执行具体的 Job 任务
- **MySQL Database**: 存储项目、工作流、执行记录等元数据

#### 1.2 安装部署
**环境要求**：
- Java 8+
- MySQL 5.5+
- 网络端口：Web Server (8081), Executor Server (12321)

**安装步骤**：
```bash
# 1. 下载 Azkaban 发行包
wget https://github.com/azkaban/azkaban/releases/download/3.90.0/azkaban-web-server-3.90.0.tar.gz
wget https://github.com/azkaban/azkaban/releases/download/3.90.0/azkaban-exec-server-3.90.0.tar.gz
wget https://github.com/azkaban/azkaban/releases/download/3.90.0/azkaban-db-3.90.0.tar.gz

# 2. 解压并配置
tar -zxvf azkaban-web-server-3.90.0.tar.gz
tar -zxvf azkaban-exec-server-3.90.0.tar.gz
tar -zxvf azkaban-db-3.90.0.tar.gz

# 3. 初始化数据库
mysql -uroot -p < azkaban-db-3.90.0/create-all-sql-3.90.0.sql

# 4. 配置 Web Server
# 修改 conf/azkaban.properties
database.type=mysql
mysql.host=localhost
mysql.port=3306
mysql.database=azkaban
mysql.user=azkaban
mysql.password=password

# 5. 配置 Executor Server
# 修改 conf/azkaban.properties
database.type=mysql
mysql.host=localhost
mysql.port=3306
mysql.database=azkaban
mysql.user=azkaban
mysql.password=password

# 6. 启动服务
./bin/start-web.sh
./bin/start-exec.sh
```

### 2. Job 配置文件编写

#### 2.1 基础 Job 配置
**job 文件格式**（.job 扩展名）：
```properties
# command.job
type=command
command=echo "Hello Azkaban"
```

#### 2.2 常用 Job 类型
**Shell Job**：
```properties
# shell.job
type=command
command=/bin/bash /path/to/script.sh
```

**Java Job**：
```properties
# java.job
type=java
main.class=com.example.MyJob
classpath=/path/to/myapp.jar
Xms=64M
Xmx=256M
```

**Hive Job**：
```properties
# hive.job
type=command
command=hive -f /path/to/hive_script.hql
```

**Sqoop Job**：
```properties
# sqoop.job
type=command
command=sqoop import --connect jdbc:mysql://localhost:3306/db --table table_name --target-dir /hdfs/path
```

### 3. 工作流定义

#### 3.1 单个 Job 工作流
创建包含单个 .job 文件的 zip 包即可。

#### 3.2 多 Job 依赖工作流
**项目结构**：
```
my-workflow/
├── job1.job
├── job2.job  
├── job3.job
└── flow.flow
```

**依赖配置**（在 .job 文件中指定）：
```properties
# job2.job
type=command
command=echo "Job 2"
dependencies=job1

# job3.job  
type=command
command=echo "Job 3"
dependencies=job1,job2
```

#### 3.3 条件分支工作流
**条件判断**：
```properties
# conditional.job
type=command
command=bash /path/to/conditional_script.sh
condition=true
```

### 4. 电商数仓工作流实战

#### 4.1 数据采集工作流
**项目结构**：
```
data-collection/
├── log-generation.job
├── flume-start.job
├── kafka-check.job
└── hdfs-validate.job
```

**配置示例**：
```properties
# log-generation.job
type=command
command=/root/bin/lg.sh 2019-02-10

# flume-start.job
type=command
command=/opt/cloudera/parcels/CDH/bin/flume-ng agent --conf /etc/flume/conf --conf-file /etc/flume/conf/flume.conf --name a1
dependencies=log-generation

# kafka-check.job
type=command
command=/opt/cloudera/parcels/KAFKA/bin/kafka-topics --list --zookeeper hadoop102:2181
dependencies=flume-start

# hdfs-validate.job
type=command
command=hadoop fs -ls /origin_data/gmall/log/
dependencies=kafka-check
```

#### 4.2 数仓分层工作流
**完整工作流设计**：
```
dwd-layer/
├── ods-load.job
├── dwd-process.job
├── dws-aggregate.job
└── ads-report.job
```

**ODS 层加载**：
```properties
# ods-load.job
type=command
command=/root/bin/ods_log.sh 2019-02-10
```

**DWD 层处理**：
```properties
# dwd-process.job
type=command
command=/root/bin/dwd_start_log.sh 2019-02-10
dependencies=ods-load
```

**DWS 层聚合**：
```properties
# dws-aggregate.job
type=command
command=/root/bin/dws_log.sh 2019-02-10
dependencies=dwd-process
```

**ADS 层报表**：
```properties
# ads-report.job
type=command
command=/root/bin/ads_uv_log.sh 2019-02-10
dependencies=dws-aggregate
```

#### 4.3 业务数据工作流
**Sqoop 导入工作流**：
```properties
# sqoop-import.job
type=command
command=/root/bin/sqoop_import.sh all 2019-02-10

# ods-business.job
type=command
command=/root/bin/ods_db.sh 2019-02-10
dependencies=sqoop-import

# dwd-business.job
type=command
command=/root/bin/dwd_db.sh 2019-02-10
dependencies=ods-business

# gmv-calculation.job
type=command
command=/root/bin/ads_db_gmv.sh 2019-02-10
dependencies=dwd-business
```

### 5. Web UI 操作指南

#### 5.1 项目创建和上传
1. 登录 Web UI (http://localhost:8081)
2. 点击 "Create Project"
3. 填写项目名称和描述
4. 上传 zip 格式的工作流包

#### 5.2 工作流执行
1. 进入项目页面
2. 点击 "Execute Flow"
3. 选择要执行的工作流
4. 配置运行参数（可选）
5. 点击 "Schedule" 或 "Execute"

#### 5.3 监控和调试
- **实时监控**: 查看任务执行状态和日志
- **历史记录**: 查看历史执行记录和性能指标
- **错误处理**: 查看错误日志并进行重试

### 6. 高级特性

#### 6.1 参数化配置
**全局参数**：
```properties
# 在项目级别设置
date=${date}
env=production
```

**Job 级别参数**：
```properties
# 在具体 job 中使用
command=/root/bin/script.sh ${date} ${env}
```

#### 6.2 并行执行
**并行 Job 配置**：
```properties
# job-a.job
type=command
command=task-a.sh

# job-b.job  
type=command
command=task-b.sh

# job-c.job
type=command
command=task-c.sh
dependencies=job-a,job-b
```

#### 6.3 错误处理和重试
**重试配置**：
```properties
# retry.job
type=command
command=risky-task.sh
retries=3
retry.backoff=10000
```

### 7. 与 Oozie 对比

| 特性 | Azkaban | Oozie |
|------|---------|-------|
| **易用性** | 简单直观，学习成本低 | 复杂，需要 XML 配置 |
| **Web UI** | 功能完善，操作简单 | 功能较弱 |
| **依赖管理** | 基于文件依赖 | 基于 XML 工作流定义 |
| **社区支持** | LinkedIn 维护，活跃度一般 | Apache 顶级项目，社区活跃 |
| **集成能力** | 支持命令行工具 | 深度集成 Hadoop 生态 |

---

## 💡 实践要点总结

### 部署关键点
1. **数据库配置**: 确保 MySQL 连接正常，权限配置正确
2. **端口冲突**: 检查 8081 和 12321 端口是否被占用
3. **内存配置**: 根据集群规模调整 JVM 内存参数
4. **安全配置**: 配置 HTTPS 和用户认证（生产环境）

### 开发调试技巧
1. **本地测试**: 先在本地测试单个 Job，再组合成工作流
2. **日志查看**: 利用 Web UI 的日志功能快速定位问题
3. **参数验证**: 使用 echo 命令验证参数传递是否正确
4. **依赖检查**: 确保依赖的 Job 名称完全匹配

### 常见问题排查
1. **Job 执行失败**: 检查命令路径、权限、依赖库
2. **工作流卡住**: 检查依赖 Job 是否完成，资源是否充足
3. **参数不生效**: 检查参数名称大小写，引用格式是否正确
4. **Web UI 无法访问**: 检查服务是否启动，防火墙配置

---

## 📋 学习路线建议

**第一阶段（1天）**：环境搭建
- 完成 Azkaban 集群部署
- 验证 Web UI 访问和基本功能

**第二阶段（1-2天）**：基础使用
- 编写简单的 Shell Job
- 创建和执行单 Job 工作流

**第三阶段（2-3天）**：数仓集成
- 将现有数仓脚本转换为 Azkaban Job
- 设计完整的数仓分层工作流

**第四阶段（1天）**：优化提升
- 配置参数化和错误处理
- 学习高级特性和最佳实践

---

## 🔗 相关资源

- **官方文档**: https://azkaban.github.io/
- **GitHub 仓库**: https://github.com/azkaban/azkaban
- **社区论坛**: Azkaban 用户邮件列表
- **最佳实践**: LinkedIn Azkaban 使用指南

---

*Generated by OpenClaw Doc Processor - Enhanced Version*
*Based on complete original content analysis*