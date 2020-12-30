# 湖南烟草问卷调查BOT约定

## 新增问卷流程
1. 新增问卷需要传一个如下结构的data.json问卷上服务器
2. 创建一个新的批次,指定编号比如是05,注意必须要是单数,因为bot_derive每次都会启动
3. 通过bot derive hnyc_survey 05命令生成一个新的hnyc_survey bot.服务会自动启动并服务

## 问卷结果返回
假设有如下的问卷.

```
[
  {
    "quest_bh": "0000001076",
    "quest_type": "01",
    "quest_name": "您对客户经理的服务态度是否满意?",
    "daarray": [
        {
          "dabh": "0000003963",
          "daname": "很满意"
        },
        {
          "dabh": "0000003964",
          "daname": "基本满意"
        },
        {
          "dabh": "0000003965",
          "daname": "不满意"
        }
    ]
  },
  {
    "quest_bh": "0000001077",
    "quest_type": "02",
    "quest_name": "您是通过何种途径了解卷烟零售户信用体的?",
    "daarray": [
        {
            "dabh": "0000003966",
            "daname": "烟草公司会议"
        },
        {
            "dabh": "0000003967",
            "daname": "客户经理宣传"
        },
        {
            "dabh": "0000003968",
            "daname": "其它零售户的介绍"
        }
    ]
  },
  {
    "quest_bh": "0000001078",
    "quest_type": "03",
    "quest_name": "关于我们的工作是否还有什么建议"
  }
]
```


那么最终的结果写到话务平台上的`ocm_callout_result`表内.自定义了字段callid, from_callid, content, extend, callresult.

* content字段存了所有的历史记录
* extend字段表存了所有的扩展字段(外呼bot没有上文所以是空).
* callresult存放了所有外呼bot的结果.单选题和多选题的结果以序号呈现,而问答题的结果以文本呈现.

## 示例返回数据
|id|callid|from_callid|content|extend|callresult|
|:--|:--|:--|:--|:--|:--|
| 50 |    123 |          -1 | 机器人：[单选题] 您对客户经理的服务态度是否满意? 很满意,基本满意,不满意#用户：马马虎虎#机器人：[多选题] 您是通过何种途径了解卷烟零售户信用体的? 烟草公司会议,客户经理宣传,其它零售户的介绍#用户：你们经理推荐我好多次了#机器人：[问答题] 关于我们的工作是否还有什么建议 #用户：没啥建议                                                                                                                                 | dummy#val0#val1#val2#val3#val4#val5#val6#val7#val8#val9 | None#0#1#没啥建议     |

