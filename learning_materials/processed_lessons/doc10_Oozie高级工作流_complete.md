# 尚硅谷电商数仓6.0 - 模块10：Oozie高级工作流调度系统

> **对应视频**: 辅助文档集  
> **原始文档**: 尚硅谷大数据技术之Oozie.doc  
> **生成时间**: 2026-03-04  
> **难度评级**: ⭐⭐⭐⭐  
> **建议学习时长**: 6-8小时

---

## 🎯 课程开场（3分钟速览）

本模块是电商数仓项目的**工作流调度核心**，解决的核心问题是：**如何实现复杂数据处理任务的自动化、可靠性和可维护性调度管理**。

**你将学到**:
- Oozie 工作流引擎的核心架构和组件
- Workflow 与 Coordinator 的区别和应用场景
- Shell Action、MapReduce Action 等多种 Action 类型的配置
- 复杂工作流的决策节点（Decision Node）和错误处理机制
- 与 Hadoop 生态系统的深度集成（HDFS、YARN、MapReduce）
- 实际项目中的工作流部署和监控最佳实践

**面试高频考点**: 
- Oozie 与 Azkaban 的对比和选型
- 工作流的容错机制和重试策略
- 参数化工作流的设计模式
- 大规模作业调度的性能优化

---

## 📚 核心知识点详解

### 1. Oozie 架构概述

#### 1.1 核心组件
- **Oozie Server**: 主服务进程，负责工作流的解析、调度和状态管理
- **Oozie Client**: 客户端工具，用于提交、查询和控制工作流
- **Workflow Engine**: 工作流执行引擎
- **Coordinator Engine**: 协调器引擎，支持基于时间或数据可用性的触发

#### 1.2 工作流类型
- **Workflow**: 基于 DAG（有向无环图）的任务编排
- **Coordinator**: 基于时间或数据事件的周期性调度
- **Bundle**: 多个 Coordinator 的集合管理

### 2. Oozie 安装与配置

#### 2.1 环境准备
```bash
# 解压 Oozie 安装包
tar -zxvf oozie-4.0.0-cdh5.3.6.tar.gz -C ./

# 解压 Hadoop Libs
tar -zxvf oozie-hadooplibs-4.0.0-cdh5.3.6.tar.gz -C ./
```

#### 2.2 依赖库配置
```bash
# 创建 libext 目录
mkdir libext/

# 复制 Hadoop 依赖
cp -ra hadooplibs/hadooplib-2.5.0-cdh5.3.6.oozie-4.0.0-cdh5.3.6/* libext/

# 复制 MySQL 驱动
cp /opt/software/mysql-connector-java-5.1.27/mysql-connector-java-5.1.27-bin.jar ./

# 复制 ext-2.2.zip（Web UI 依赖）
cp /opt/software/cdh/ext-2.2.zip libext/
```

#### 2.3 数据库初始化
```xml
<!-- oozie-site.xml 关键配置 -->
<property>
    <name>oozie.service.JPAService.jdbc.driver</name>
    <value>com.mysql.jdbc.Driver</value>
</property>
<property>
    <name>oozie.service.JPAService.jdbc.url</name>
    <value>jdbc:mysql://hadoop102:3306/oozie</value>
</property>
<property>
    <name>oozie.service.JPAService.jdbc.username</name>
    <value>root</value>
</property>
<property>
    <name>oozie.service.JPAService.jdbc.password</name>
    <value>000000</value>
</property>
```

#### 2.4 启动服务
```bash
# 准备 ShareLib
bin/oozie-setup.sh sharelib create -fs hdfs://hadoop102:8020 -locallib oozie-sharelib-4.0.0-cdh5.3.6-yarn.tar.gz

# 准备 WAR 包
bin/oozie-setup.sh prepare-war

# 启动 Oozie
bin/oozied.sh start
```

### 3. 工作流开发实战

#### 3.1 Shell Action 工作流
**job.properties 配置**:
```properties
nameNode=hdfs://hadoop102:8020
jobTracker=hadoop103:8032
queueName=default
examplesRoot=oozie-apps
oozie.wf.application.path=${nameNode}/user/${user.name}/${examplesRoot}/shell
EXEC=p1.sh
```

**workflow.xml 定义**:
```xml
<workflow-app xmlns="uri:oozie:workflow:0.4" name="shell-wf">
    <start to="shell-node"/>
    <action name="shell-node">
        <shell xmlns="uri:oozie:shell-action:0.2">
            <job-tracker>${jobTracker}</job-tracker>
            <name-node>${nameNode}</name-node>
            <configuration>
                <property>
                    <name>mapred.job.queue.name</name>
                    <value>${queueName}</value>
                </property>
            </configuration>
            <exec>${EXEC}</exec>
            <file>/user/atguigu/oozie-apps/shell/${EXEC}#${EXEC}</file>
            <capture-output/>
        </shell>
        <ok to="end"/>
        <error to="fail"/>
    </action>
    <kill name="fail">
        <message>Shell action failed, error message[${wf:errorMessage(wf:lastErrorNode())}]</message>
    </kill>
    <end name="end"/>
</workflow-app>
```

#### 3.2 多步骤 Shell 工作流
**多脚本串联执行**:
```properties
EXEC1=p1.sh
EXEC2=p2.sh
```

```xml
<workflow-app xmlns="uri:oozie:workflow:0.4" name="shell-wf">
    <start to="p1-shell-node"/>
    <action name="p1-shell-node">
        <shell xmlns="uri:oozie:shell-action:0.2">
            <job-tracker>${jobTracker}</job-tracker>
            <name-node>${nameNode}</name-node>
            <exec>${EXEC1}</exec>
            <file>/user/atguigu/oozie-apps/shell/${EXEC1}#${EXEC1}</file>
            <capture-output/>
        </shell>
        <ok to="p2-shell-node"/>
        <error to="fail"/>
    </action>
    <action name="p2-shell-node">
        <shell xmlns="uri:oozie:shell-action:0.2">
            <job-tracker>${jobTracker}</job-tracker>
            <name-node>${nameNode}</name-node>
            <exec>${EXEC2}</exec>
            <file>/user/admin/oozie-apps/shell/${EXEC2}#${EXEC2}</file>
            <capture-output/>
        </shell>
        <ok to="end"/>
        <error to="fail"/>
    </action>
    <!-- 错误处理和结束节点 -->
</workflow-app>
```

#### 3.3 MapReduce Action 工作流
**WordCount 示例配置**:
```properties
nameNode=hdfs://hadoop102:8020
jobTracker=hadoop103:8032
queueName=default
examplesRoot=oozie-apps
oozie.wf.application.path=${nameNode}/user/${user.name}/${examplesRoot}/map-reduce/workflow.xml
outputDir=map-reduce
```

**MapReduce 工作流定义**:
```xml
<workflow-app xmlns="uri:oozie:workflow:0.2" name="map-reduce-wf">
    <start to="mr-node"/>
    <action name="mr-node">
        <map-reduce>
            <job-tracker>${jobTracker}</job-tracker>
            <name-node>${nameNode}</name-node>
            <prepare>
                <delete path="${nameNode}/output/"/>
            </prepare>
            <configuration>
                <property>
                    <name>mapred.job.queue.name</name>
                    <value>${queueName}</value>
                </property>
                <!-- New API 配置 -->
                <property>
                    <name>mapreduce.mapper.new-api</name>
                    <value>true</value>
                </property>
                <property>
                    <name>mapreduce.reducer.new-api</name>
                    <value>true</value>
                </property>
                <!-- Job Key/Value Class -->
                <property>
                    <name>mapreduce.job.output.key.class</name>
                    <value>org.apache.hadoop.io.Text</value>
                </property>
                <property>
                    <name>mapreduce.job.output.value.class</name>
                    <value>org.apache.hadoop.io.IntWritable</value>
                </property>
                <!-- Input/Output Directories -->
                <property>
                    <name>mapreduce.input.fileinputformat.inputdir</name>
                    <value>/input/</value>
                </property>
                <property>
                    <name>mapreduce.output.fileoutputformat.outputdir</name>
                    <value>/output/</value>
                </property>
                <!-- Mapper/Reducer Classes -->
                <property>
                    <name>mapreduce.job.map.class</name>
                    <value>org.apache.hadoop.examples.WordCount$TokenizerMapper</value>
                </property>
                <property>
                    <name>mapreduce.job.reduce.class</name>
                    <value>org.apache.hadoop.examples.WordCount$IntSumReducer</value>
                </property>
            </configuration>
        </map-reduce>
        <ok to="end"/>
        <error to="fail"/>
    </action>
    <kill name="fail">
        <message>Map/Reduce failed, error message[${wf:errorMessage(wf:lastErrorNode())}]</message>
    </kill>
    <end name="end"/>
</workflow-app>
```

### 4. 高级特性与最佳实践

#### 4.1 决策节点（Decision Node）
支持条件分支逻辑：
```xml
<decision name="check-output">
    <switch>
        <case to="end">
            ${wf:actionData('shell-node')['my_output'] eq 'Hello Oozie'}
        </case>
        <default to="fail-output"/>
    </switch>
</decision>
```

#### 4.2 错误处理机制
- **Kill 节点**: 终止工作流并记录错误信息
- **Retry 机制**: 自动重试失败的任务
- **Email 通知**: 集成邮件告警系统

#### 4.3 参数化工作流
通过 job.properties 文件传递参数，实现工作流的复用和灵活性。

#### 4.4 工作流部署流程
1. **本地开发**: 编写 workflow.xml 和 job.properties
2. **HDFS 上传**: 将应用目录上传到 HDFS
3. **提交执行**: 使用 Oozie CLI 提交工作流
4. **监控管理**: 通过 Web UI 或 CLI 监控执行状态

### 5. 实际项目集成

#### 5.1 电商数仓调度场景
- **每日数据采集**: Flume 日志采集 → Kafka → Flume → HDFS
- **ODS 层加载**: 原始数据分区加载
- **DWD 层处理**: 数据清洗、维度退化、格式转换
- **DWS 层聚合**: 用户行为宽表构建
- **ADS 层统计**: GMV、UV 等业务指标计算
- **结果导出**: Sqoop 导出到 MySQL 供 BI 展示

#### 5.2 调度依赖管理
- **时间依赖**: 按小时、天、周、月调度
- **数据依赖**: 下游任务等待上游数据就绪
- **资源依赖**: 合理分配 YARN 资源，避免资源竞争

---

## 💡 实践要点总结

### 环境部署关键点
1. **依赖完整性**: 确保所有 Hadoop 生态组件的 JAR 包都包含在 ShareLib 中
2. **数据库配置**: MySQL 驱动版本兼容性，数据库字符集设置
3. **HDFS 权限**: Oozie 用户对 HDFS 目录的读写权限
4. **YARN 配置**: 资源队列配置，避免任务因资源不足失败

### 开发调试技巧
1. **本地测试**: 先在本地环境测试 Shell 脚本和 MapReduce 作业
2. **参数验证**: 使用 `oozie validate` 命令验证工作流 XML 语法
3. **日志分析**: 通过 Oozie Web UI 查看详细的执行日志
4. **增量部署**: 修改后只需重新上传变更的文件，无需全量部署

### 常见问题排查
1. **ClassNotFoundException**: 检查 ShareLib 是否包含所需的 JAR 包
2. **权限拒绝**: 检查 HDFS 目录权限和 Oozie 用户配置
3. **连接超时**: 检查 Hadoop 集群各组件的网络连通性
4. **资源不足**: 调整 YARN 资源配置或优化作业并行度

---

## 📋 学习路线建议

**第一阶段（1-2天）**：环境搭建与基础概念
- 完成 Oozie 单机部署
- 理解 Workflow 和 Coordinator 的区别
- 运行官方示例工作流

**第二阶段（2-3天）**：工作流开发
- 开发 Shell Action 工作流
- 开发 MapReduce Action 工作流
- 实现多步骤串联和决策逻辑

**第三阶段（1-2天）**：项目集成
- 将 Oozie 集成到电商数仓项目中
- 实现完整的数据处理调度链
- 配置监控和告警机制

---

## 🔗 相关资源

- **官方文档**: Apache Oozie 官方文档
- **社区支持**: Cloudera 社区论坛
- **最佳实践**: 企业级 Oozie 调度架构设计
- **扩展学习**: Oozie 与 Airflow 对比分析

---

*Generated by OpenClaw Doc Processor - Enhanced Version*
*Based on complete original content analysis*