# 尚硅谷电商数仓6.0 - 模块1：用户行为数据采集

> **对应视频**: 001-047集  
> **原始文档**: 尚硅谷大数据项目之电商数仓（1用户行为数据采集）.docx  
> **生成时间**: 2026-03-02  
> **难度评级**: ⭐⭐⭐ (中等)  
> **建议学习时长**: 3-4小时

---

## 🎯 课程开场（2分钟速览）

本模块是整个电商数仓项目的**数据入口层**，解决的核心问题是：**如何从移动端App采集用户行为数据，并可靠地传输到数据仓库？**

**你将学到**:
- 埋点数据的JSON结构设计
- 12种用户行为事件的定义与采集
- Flume+Kafka的数据采集架构
- 数据生成脚本的Java实现

**面试高频考点**: 埋点设计、Flume拦截器、Kafka分区策略

---

## 📚 核心知识点详解

### 1. 数据仓库基础概念

**什么是数据仓库？**
- 面向主题的、集成的、相对稳定的、反映历史变化的数据集合
- 用于支持管理决策，而非日常业务操作

**与数据库的区别**:
| 特性 | 数据库(OLTP) | 数据仓库(OLAP) |
|------|-------------|---------------|
| 目的 | 业务操作 | 分析决策 |
| 数据更新 | 频繁增删改 | 批量加载，极少更新 |
| 数据量 | GB级 | TB/PB级 |
| 查询特点 | 简单、点查 | 复杂、全表扫描 |

---

### 2. 项目架构设计

#### 2.1 技术选型

```
┌─────────────────────────────────────────────────────────┐
│                    数据采集层                            │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │  App端  │───→│ Flume   │───→│  Kafka  │             │
│  │ 埋点SDK │    │ Agent   │    │ Topic   │             │
│  └─────────┘    └─────────┘    └─────────┘             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    数据存储层                            │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │  HDFS   │←───│ Hive    │←───│ Spark   │             │
│  │ 原始日志│    │ 数仓分层│    │ 计算引擎│             │
│  └─────────┘    └─────────┘    └─────────┘             │
└─────────────────────────────────────────────────────────┘
```

**核心技术栈**:
- 采集: Flume 1.9.0 + Kafka 2.4.1
- 存储: Hadoop 3.1.3 + HDFS
- 计算: Hive 3.1.2 + Spark 3.0.0
- 调度: Azkaban 3.84.4

#### 2.2 集群资源规划

| 节点 | 配置 | 运行服务 |
|------|------|---------|
| hadoop102 | 4核8G | NN, DN, NM, ZK, Kafka, Flume |
| hadoop103 | 4核8G | DN, NM, ZK, Kafka, Flume |
| hadoop104 | 4核8G | SNN, DN, NM, ZK, Kafka |

---

### 3. 埋点数据格式设计 ⭐重点

#### 3.1 JSON结构规范

```json
{
  "ap": "gmall",           // 项目来源: app/pc
  "cm": {                   // 【公共字段】所有事件共有
    "mid": "设备唯一标识",
    "uid": "用户ID",
    "vc": "版本号",
    "vn": "版本名",
    "l": "系统语言",
    "sr": "渠道号",
    "os": "Android版本",
    "ar": "区域",
    "md": "手机型号",
    "ba": "手机品牌",
    "sv": "SDK版本",
    "g": "gmail",
    "hw": "屏幕分辨率",
    "t": "日志产生时间戳",
    "nw": "网络模式",
    "ln": "经度",
    "la": "纬度"
  },
  "et": [                   // 【事件数组】具体行为事件
    {
      "ett": "事件时间戳",
      "en": "事件名称",
      "kv": {               // 事件自定义字段
        // 不同事件有不同字段
      }
    }
  ]
}
```

#### 3.2 为什么这样设计？

**优点**:
1. **扩展性强**: 新事件只需添加en和kv，不改整体结构
2. **压缩率高**: 公共字段只存一份，节省存储
3. **解析方便**: JSON标准格式，各语言都有成熟库
4. **兼容性好**: 字段缺失不影响其他字段解析

**坑点提醒**:
- `t`和`ett`都是时间戳，但含义不同！
  - `t`: 客户端日志产生时间（可能不准，用户可篡改）
  - `ett`: 单个事件的产生时间
  - 服务端收到时间才是真正的业务时间
- 所有时间戳都是**毫秒级**Unix时间戳

---

### 4. 十二大事件类型详解

| 事件名 | 英文名 | 触发场景 | 核心字段 |
|--------|--------|---------|---------|
| 启动 | start | 打开App | entry, open_ad_type, action |
| 错误 | error | 程序崩溃 | errorBrief, errorDetail |
| 商品列表 | loading | 浏览商品列表 | action, loading_time, type |
| 商品点击 | display | 点击商品 | action, goodsid, place |
| 商品详情 | newsdetail | 进入详情页 | entry, action, news_staytime |
| 广告 | ad | 广告相关 | entry, action, source |
| 消息通知 | notification | 推送消息 | action, type, ap_time |
| 前台活跃 | active_foreground | App切换到前台 | push_id, access |
| 后台活跃 | active_background | App切换到后台 | active_source |
| 评论 | comment | 发表评论 | comment_id, content, praise_count |
| 收藏 | favorites | 收藏商品 | course_id, add_time |
| 点赞 | praise | 点赞内容 | target_id, type |

#### 4.1 启动事件 (start) - 最重要

```json
{
  "en": "start",
  "kv": {
    "entry": "1",        // 入口: 1-push, 2-widget, 3-icon, 4-notification
    "open_ad_type": "1", // 开屏广告类型: 1-原生, 2-插屏
    "action": "1",       // 状态: 1-成功, 2-失败
    "loading_time": "1500", // 加载时长(ms)
    "detail": "",        // 失败码
    "extend1": ""        // 失败信息
  }
}
```

**业务意义**: 计算DAU、留存率、渠道转化率的基石数据

#### 4.2 商品点击事件 (display)

```json
{
  "en": "display",
  "kv": {
    "action": "2",       // 1-曝光, 2-点击
    "goodsid": "236",    // 商品ID
    "place": "2",        // 位置序号(从0开始)
    "extend1": "1",      // 曝光类型: 1-首次, 2-重复
    "category": "75"     // 分类ID
  }
}
```

**业务意义**: CTR计算、推荐算法效果评估

---

### 5. Java数据生成模块

#### 5.1 Maven依赖配置

```xml
<properties>
    <slf4j.version>1.7.20</slf4j.version>
    <logback.version>1.0.7</logback.version>
</properties>

<dependencies>
    <!-- 阿里巴巴JSON解析 -->
    <dependency>
        <groupId>com.alibaba</groupId>
        <artifactId>fastjson</artifactId>
        <version>1.2.51</version>
    </dependency>
    
    <!-- 日志框架 -->
    <dependency>
        <groupId>ch.qos.logback</groupId>
        <artifactId>logback-core</artifactId>
        <version>${logback.version}</version>
    </dependency>
    <dependency>
        <groupId>ch.qos.logback</groupId>
        <artifactId>logback-classic</artifactId>
        <version>${logback.version}</version>
    </dependency>
</dependencies>
```

#### 5.2 Bean设计模式

**继承关系设计**:
```
AppBase (公共字段)
  ├── AppStart (启动)
  ├── AppErrorLog (错误)
  ├── AppDisplay (商品点击)
  ├── AppNewsDetail (商品详情)
  ├── AppLoading (商品列表)
  ├── AppAd (广告)
  ├── AppNotification (通知)
  ├── AppActive_foreground (前台活跃)
  ├── AppActive_background (后台活跃)
  ├── AppComment (评论)
  ├── AppFavorites (收藏)
  └── AppPraise (点赞)
```

**代码示例 - 基类AppBase**:
```java
public class AppBase {
    private String mid;  // 设备唯一标识
    private String uid;  // 用户uid
    private String vc;   // versionCode
    private String vn;   // versionName
    private String l;    // 系统语言
    private String sr;   // 渠道号
    private String os;   // Android版本
    private String ar;   // 区域
    private String md;   // 手机型号
    private String ba;   // 手机品牌
    private String sv;   // sdkVersion
    private String g;    // gmail
    private String hw;   // 屏幕宽高
    private String t;    // 日志产生时间
    private String nw;   // 网络模式
    private String ln;   // 经度
    private String la;   // 纬度
    
    // Getter & Setter...
}
```

**设计亮点**:
- 使用继承复用公共字段，避免重复代码
- 每个事件独立成类，职责清晰
- 字段命名与埋点文档完全一致，便于对照

---

## 💼 企业实战案例

### 场景: 模拟一天100万条用户行为日志

**需求**: 为测试环境生成真实的用户行为数据，用于验证数据采集链路的正确性

**完整实现代码**:

```java
package com.atguigu.appclient;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.atguigu.bean.*;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Random;

public class AppMain {
    
    static Random rand = new Random();
    static String[] mids = {"m1","m2","m3"}; // 模拟设备池
    static String[] uids = {"u1","u2","u3",""}; // 部分未登录用户
    static String[] channels = {"xiaomi","huawei","oppo","vivo","appstore"};
    
    public static void main(String[] args) {
        // 生成10000条日志
        for (int i = 0; i < 10000; i++) {
            String log = generateLog();
            System.out.println(log);
        }
    }
    
    static String generateLog() {
        JSONObject log = new JSONObject();
        
        // 1. 填充公共字段
        AppBase base = new AppBase();
        base.setMid(mids[rand.nextInt(mids.length)]);
        base.setUid(uids[rand.nextInt(uids.length)]);
        base.setVc("2");
        base.setVn("1.0.1");
        base.setL("zh");
        base.setSr(channels[rand.nextInt(channels.length)]);
        base.setOs("10.0");
        base.setAr("CN");
        base.setMd("MI10");
        base.setBa("Xiaomi");
        base.setSv("V2.5.0");
        base.setT(System.currentTimeMillis() + "");
        base.setNw(rand.nextBoolean() ? "WIFI" : "4G");
        
        log.put("ap", "gmall");
        log.put("cm", base);
        
        // 2. 随机生成1-3个事件
        JSONArray events = new JSONArray();
        int eventCount = rand.nextInt(3) + 1;
        
        for (int i = 0; i < eventCount; i++) {
            JSONObject event = generateRandomEvent();
            events.add(event);
        }
        log.put("et", events);
        
        return JSON.toJSONString(log);
    }
    
    static JSONObject generateRandomEvent() {
        JSONObject event = new JSONObject();
        event.put("ett", System.currentTimeMillis() + "");
        
        int type = rand.nextInt(5);
        switch (type) {
            case 0: // 启动
                event.put("en", "start");
                AppStart start = new AppStart();
                start.setEntry(rand.nextInt(4) + 1 + "");
                start.setAction("1");
                start.setLoading_time(rand.nextInt(3000) + "");
                event.put("kv", start);
                break;
            case 1: // 商品点击
                event.put("en", "display");
                AppDisplay display = new AppDisplay();
                display.setAction("2");
                display.setGoodsid(rand.nextInt(1000) + "");
                display.setPlace(rand.nextInt(10) + "");
                display.setCategory(rand.nextInt(50) + "");
                event.put("kv", display);
                break;
            case 2: // 商品详情
                event.put("en", "newsdetail");
                AppNewsDetail detail = new AppNewsDetail();
                detail.setEntry("1");
                detail.setAction("2");
                detail.setGoodsid(rand.nextInt(1000) + "");
                detail.setNews_staytime(rand.nextInt(60000) + "");
                event.put("kv", detail);
                break;
            case 3: // 前台活跃
                event.put("en", "active_foreground");
                AppActive_foreground fg = new AppActive_foreground();
                fg.setAccess(rand.nextInt(3) + 1 + "");
                event.put("kv", fg);
                break;
            case 4: // 广告
                event.put("en", "ad");
                AppAd ad = new AppAd();
                ad.setEntry("1");
                ad.setAction(rand.nextInt(5) + 1 + "");
                ad.setSource(rand.nextInt(4) + 1 + "");
                event.put("kv", ad);
                break;
        }
        return event;
    }
}
```

**运行方式**:
```bash
# 打包
mvn clean package

# 运行并输出到文件
java -jar log-collector-1.0-SNAPSHOT-jar-with-dependencies.jar > app.log

# 模拟实时产生（每秒100条）
while true; do
    java -jar log-collector.jar >> app.log
    sleep 1
done
```

---

## 📝 自测题库

### 题目1
**埋点JSON中的`t`字段代表什么？**
- A. 服务端接收时间
- B. 客户端日志产生时间
- C. 事件产生时间
- D. 数据入库时间

<details>
<summary>答案</summary>
B. 客户端日志产生时间。注意这是客户端上报的时间，可能被篡改，服务端需要用接收时间作为业务时间。
</details>

### 题目2
**以下哪个不是启动事件(start)的字段？**
- A. entry
- B. open_ad_type
- C. goodsid
- D. loading_time

<details>
<summary>答案</summary>
C. goodsid是商品点击事件(display)的字段，不是启动事件的。
</details>

### 题目3
**为什么要将公共字段抽取到AppBase基类？**
- A. 减少代码量
- B. 提高解析性能
- C. 统一数据格式，便于维护
- D. 以上都是

<details>
<summary>答案</summary>
D. 继承设计既减少了重复代码，又保证了所有事件公共字段的一致性，同时让代码更易维护。
</details>

### 题目4
**Flume采集日志时，为什么要使用拦截器？**
- A. 过滤无效数据
- B. 添加时间戳头部
- C. 数据脱敏
- D. 以上都可以

<details>
<summary>答案</summary>
D. 拦截器可以在数据传输过程中进行各种处理，包括过滤、增强、脱敏等。
</details>

### 题目5
**如果用户快速切换App前后台，会产生哪些事件？**
- A. 只有active_foreground
- B. 只有active_background
- C. active_background + active_foreground
- D. start + active_foreground

<details>
<summary>答案</summary>
C. 切换到后台产生active_background，切回前台产生active_foreground。start只在冷启动时产生。
</details>

---

## 🎓 课后任务

### 必做练习
1. [ ] 完成AppMain代码，能生成包含全部12种事件的日志
2. [ ] 修改代码，让同一设备的mid保持一致（模拟真实用户）
3. [ ] 统计生成的日志中，各事件类型的占比

### 扩展阅读
- [ ] 《阿里巴巴大数据实践》- 第3章 数据采集
- [ ] Flume官方文档: Interceptors章节
- [ ] Kafka官方文档: Producers配置优化

---

## 💡 学习建议

### 时间规划
| 阶段 | 内容 | 时长 |
|------|------|------|
| 第1遍 | 通读本文档，理解整体架构 | 30分钟 |
| 第2遍 | 手写Bean类代码，不要复制 | 60分钟 |
| 第3遍 | 完成课后任务，运行测试 | 90分钟 |
| 复习 | 遮住答案重做自测题 | 20分钟 |

### 面试准备重点
1. **能画出数据采集架构图**，讲清楚数据流向
2. **能解释为什么选择Flume+Kafka**，而不是直接写HDFS
3. **熟悉至少5个事件类型的字段含义**
4. **能说出埋点设计的优缺点**

### 常见面试题
- Q: 如果埋点数据丢失怎么办？
  - A: 客户端本地缓存+重试机制；服务端幂等处理
- Q: 如何保证数据顺序性？
  - A: Kafka单分区有序；按用户ID分区保证同用户有序
- Q: 如何识别作弊流量？
  - A: 异常检测（频率过高、字段异常）；设备指纹；行为模式分析

---

## ✅ 进度检查

完成本模块后，你应该能：
- [ ] 画出项目整体架构图
- [ ] 写出完整的埋点JSON示例
- [ ] 解释12种事件的业务含义
- [ ] 独立完成Java日志生成代码
- [ ] 回答所有自测题

---

> **下一步**: 继续学习 [模块2: ODS层建设]（对应文档2）
