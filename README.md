# tasi-dialog

一个可配置话术的对话系统

## 目录

- [python依赖](#python依赖)
- [用法](#用法)
- [API](#api)

## python依赖

- tensorflow 1.11
- tornado
- psycopg2
- pyyaml
- requests

## 用法

### 安装

```
git clone http://gitlab.tasitech.com.cn/bot/tasi_dialog.git
cd tasi_dialog
```

### 启动对话服务

启动对话系统需要对话配置文件和意图识别模型。

- 对话配置文件在dialog_config目录中，您在上一步骤安装的对话系统自带了电费催收机器人的配置文件。如果您想配置自己的对话系统，配置方法见[配置你的对话系统](#配置你的对话系统)。
- 意图识别模型包含两部分。分别是BERT预训练模型和用配置的训练语料finetune得到的模型
  - BERT预训练模型在oss://tasi-callcenter-audio-record/engine/model/bert/chinese_L-12_H-768_A-12/。下载后需放在model/bert/chinese_L-12_H-768_A-12目录下
  - 电费催收机器人的finetune模型在oss://tasi-callcenter-audio-record/engine/model/bert/checkpoints/sgcc_zj/intent/。下载后需放在oss://tasi-callcenter-audio-record/engine/model/bert/checkpoints/intent/下。

tasi-dialog提供文字版和语音版两种对话接口，分别可用于文本形式和语音形式的对话系统。

启动文字版对话系统服务端，默认端口是59998。

```python
python server_text.py -p 59998
```

测试文字版对话系统可以启动客户端。

```
python client_text.py
```

启动语音版对话系统服务端，默认端口是59999。

```
python server_phone.py
```

-p可指定端口。-m指定交互模式：1表示机器人说话时用户不能打断，2表示机器人说话时用户可以打断，默认是1。



### 配置你的对话机器人

定义对话机器人，对话机器人包含什么。对话机器人的顶层逻辑

#### 名词解释

##### 对话流(flow)

对话流用来描述业务逻辑，由一个个节点(Node)组成，节点有八种类型：

- 填槽节点(slot filling)
- 函数节点(function)
- 赋值节点(assignment)
- 子流程(flow)
- 分支节点(branch)
- 返回节点(return)
- 退出节点(exit)
- 回复节点(response)

为了实现每个节点的功能，我们还需要配置全局变量、意图、词典、函数。

##### 全局变量(global variables)

全局变量维护了对话的全局信息，对一个机器人的所有对话流都可见，相较于全局变量，槽是局部变量。

##### 意图(intent)

意图用来表示用户的需求，用来触发对话流或控制对话流节点的跳转。意图可以包含若干槽。

举例：机器人可将”我想买从北京到上海的机票“这句话识别为“买机票”意图，触发“买机票”流程。“出发地”、“目的地”和“时间”是该意图的槽

##### 值集合(value_set)

槽可取值的集合，即槽的取值范围。有两种类型：字典和正则表达式。当槽可取的值可枚举时用字典型，不可枚举可用正则表达式表示。比如“出发地”这个槽的词典可以是中国所有城市组成的集合。

##### 函数(function)

函数是一段代码，用来处理对话配置文件不好配置的业务逻辑。比如调用API时，可以写一段代码进行调用。

------

#### 配置说明

##### 对话流

配置文件：flows/对话流名称.json，如flows/查户号.json

- name：对话流名称。
- intent：触发该流程的意图。选填。
- nodes：对话流节点。
  - type：节点类型。可选“slot_filling”, “function”, "assignment", "flow", “branch”,  “return”, “exit”, "response"。
  - dm：对话管理。
    - cond：跳转条件。cond的语法详见[jsonlogic](http://jsonlogic.com/operations.html)。下面简要说明jsonlogic语法，并列出几点在jsonlogic基础上修改的地方。
      - cond由dict嵌套而成。dict的键是操作符，如“==”，"!=", ">"等；dict的值是元素列表。举例{”>=“：[3, 1]}相当于3>=1, 因此是true。
      - 元素列表不仅可以是上例中的静态值3和1，还可以从变量中取出，比如{“var”：“global.consumer_number”}就表示全局变量中的户号。举例{”!=“：[{“var”：“global.consumer_number”}, '123']}的意思是判断全局变量中的consumer_number是否不等于'123'。
    - nextNode：跳转至的节点编号。todo:写清楚用户什么时候输入，这时候会进行意图识别，产生可能的跳转
    - response：系统回复。选填

######  type配置说明

流程由不同类型的节点组成。


```python
{
    "name": "example",	# 流程名。创建一个流程时用户需要填，和json文件名相同。
    "intent": "example",
	"nodes": {
        # 子流程节点
        "0": {	# 节点编号，同一流程内的节点编号不可重复，不同流程内的节点编号可重复，一个流程中至少有一个节点的编号是"0"，作为入口节点。
            "type": "flow",  # 节点类型。
    		"flowName": ""  # 子流程名。
            "dm": [] # 节点跳转逻辑。配置方法，下一小节介绍
        },
        # 分支节点
        "1": {
            "type": "branch"
            "dm": []
        },
        # 填槽节点
        "2": {
            "type": "slot_filling",  # 节点类型。固定为slot_filling，不可更改
            "slots": [	# 待填槽列表
				{
                    "name": "",	# 槽的名称，例如出发时间。
                    "global_variable": "",	# 与槽绑定的全局变量名。填完槽后，将把该槽的值赋给绑定的全局变量
                    "response": "",	# 机器人询问用户的话，例如“您想订几点的车票”。选填
                }
            ],
            "dm": []
        },
        # 函数节点
        "3": {
            "type": "function",  # 节点类型。
        	"funcName": ""  # 函数名。
            "dm": []
        }
        # 赋值节点
        "4": {
            "type": "assignment",	# 节点类型。
            "assignments":[	# 赋值列表
                {
                    "g_var": "",	# 全局变量名。
                    "value": ""	# 全局变量值。
                }
            ],
            "dm": []
        },
        # 回复节点
        "5": {
            "type": "response"	# 节点类型。
            "response": ""	# 机器人回复内容。
            "dm": []
        },
        # 返回节点
        "6": {
            "type": "return"	# 节点类型。
        },
        # 退出节点
        "7": {
            "type": "exit",	# 节点类型。
            "todo":	""	# 挂断电话后续处理。可选值为["hangup", "fwd"]
        }
    }
}
```

###### dm配置说明

```python
{   
    "cond": None/dict/"else",	# 跳转条件。有三种可能，下面有详细解释。选填
    "nextNode": "" # 跳转目标节点的编号
    "response": None/""	# 跳转的时候，机器人对用户的回复。选填。
}
```

###### cond字段的三种情况：

1. 当"cond" == None（用户没填）时，表示无条件跳转，相当于True

2. 当"cond" == "else"时，当前面的条件都不满足时，走这条路径。

3. 当“cond”是一个字典时，按照下面方式配置：

```python
{   
    "op": "",	# 操作符。必填。可选项："==", "!=", ">", "<", ">=", "<=" todo：写全，比如与或非
    "values": []	# 值。必填。元素个数视操作符而定。目前固定为2个值，因为目前的操作符都是二元的。
}
# 例子：跳转条件为全局变量a>2。
"cond" = {
	"op": ">",
    "values": ["global.a", "2"]
}
```

----

##### 全局变量

配置文件：global_variables.json

定义并初始化全局变量。

以查天气对话流为例，可将日期初始化为当天，“2020-06-10”是一个例子。

```json
{
  "g_vars": {
    "address": null,
    "owe": null
  },
  "g_vars_need_init": [
    "address",
    "owe"
  ]
}
```

全局变量目前只支持None、字符串、数字。

对话系统有2个内置全局变量：intent和func_return，分别是最近一次意图识别结果和最近一次函数的返回。内置的全局变量以builtin开头，用于自定义的全局变量以global开头

------

##### 意图

配置文件：intents.json

- name：意图名称
- description：意图注释。选填。
- slots：槽
  - name：槽名称
  - chineseName：槽中文名。选填。
  - lexicon：词典。词典有内置(builtin)和自定义(user)两种。比如builtin.city，user.consumer_number。

```json
[
  {
    "name": "consumer_type_identification",
    "chineseName": "客户性质识别",
    "description": "客户性质识别",
    "slots": {
    }
  },
  {
    "name": "earlier_stage_work_order_inquiry",
    "chineseName": "查询前期工单",
    "description": "查询前期工单",
    "slots": {
    }
  },
  {
    "name": "查户号",
    "chineseName": "查询户号",
    "description": "查询户号",
    "slots": {
      "consumer_number": {
        "name": "consumer_number",
        "chineseName": "户号",
        "lexicon": "user.consumer_number"
      },
      "pay_to": {
        "name": "pay_to",
        "chineseName": "交费地点",
        "lexicon": "user.pay_to"
      },
      "meter_number": {
        "name": "meter_number",
        "chineseName": "电表号",
        "lexicon": "user.meter_number"
      }
    }
  }
]
```

------

##### 词典

词典是一类词的集合，比如中国所有的城市。在配置意图时，为意图中的每个槽指定一个词典，词典中的词是对应槽的取值范围。

配置文件：lexicon.json

- name：词典名称
- chineseName：词典中文名。选填。
- type：词典类型，可选“regex”和“dict”
- regex：正则表达式。如果type是regex，需要配置。
- dict：字典。如果type是dict，需要配置。键是词典中的词，值是同义词列表。

```json
{
  "consumer_number": {
    "name": "consumer_number",
    "chineseName": "用户编号",
    "type": "regex",
    "regex": "[0-9]{10}"
  },
  "city": {
    "name": "city",
    "chineseName": "城市",
    "type": "dict",
    "dict": {
      "广州": [
        "广州",
        "羊城"，
        "花城"
      ],
      "上海": [
        "上海"，
        "魔都"
      ],
      "杭州": [
        "杭州"
      ]
    }
  }
}
```

------

##### 函数

在functions.py中写自定义函数，供对话流的函数节点调用。函数的输入为最近一轮用户输入和全局变量。函数的返回值为全局变量builtin.func_return。

```python
# 预处理代码

# 自定义函数
def func1(user_utter, global_vars):
    #根据api调用结果改变用户信息等全局变量
    pass

def func2(user_utter, global_vars):
    #根据api调用结果改变用户信息等全局变量
    pass

...
```

##### 服务用语

在service_language.json中写服务用语。greeting是开场白。pardon是没有理解用户输入时的兜底话术

```
{
  "greeting": "喂，您好，我这边是萧山供电有限公司，您在[%global.address%]的房子电费已经欠费[%global.owe%]，请您这边及时交清电费，可以嘛。",
  "pardon": "您在[%global.address%]的房子电费已经欠费[%global.owe%]，请您这边及时交清电费。"
}
```

准备语料

#### 训练

```
python datasets/intent_recognition/build_datasets.py
```

todo：交代bert和模板的融合方式，门限

------

## API

客户端可通过post方式向服务端发送请求。

#### 请求参数

| 参数名   | 数据类型 | 描述                                                         |
| -------- | -------- | ------------------------------------------------------------ |
| userid   | str      | 对话唯一标识                                                 |
| inaction | int      | 指令标志。初始化对话时设为8 , 对话过程中设为最近一次从服务端接收到的相应中的outaction。8为初始化，9为正常交互，11为呼叫转移。 |
| inparams | json     | 客户端给服务端发送的参数列表                                 |

###### inaction=8（初始化）时的inparams如下表：

| **参数**    | **描述**             |
| ----------- | -------------------- |
| call_id     | 呼叫唯一标识         |
| call_sor_id | 外呼机器人唯一标识   |
| call_dst_id | 用户唯一标识         |
| start_time  | 对话开始时间         |
| queue_id    | 呼叫转移队列唯一标识 |
| extend      | 用户信息             |

###### inaction=9（正常交互）时的inparams如下表：

| **参数**  | **描述**     |
| --------- | ------------ |
| call_id   | 呼叫唯一标识 |
| inter_idx | 对话轮次     |
| input     | 用户说的话   |

###### inaction=11（呼叫转移）时的inparams如下表：

| **参数**     | **描述**     |
| ------------ | ------------ |
| call_id      | 呼叫唯一标识 |
| trans_result | 是否转移成功 |

#### 响应参数

| 参数名    | 数据类型 | 描述                                                        |
| --------- | -------- | ----------------------------------------------------------- |
| ret       | int      | 调用标识。0代表调用成功，其他代表调用失败                   |
| userid    | str      | 呼叫唯一标识 , 同call_id                                    |
| outaction | int      | 服务端返回的指令标志。9为正常交互，10为挂机，11为呼叫转移。 |
| outparams | json     | 服务端返回客户端的参数列表                                  |

###### outaction=9（正常交互）时的outparams如下表：

| **参数**    | **描述**                           |
| ----------- | ---------------------------------- |
| call_id     | 呼叫唯一标识                       |
| inter_idx   | 对话轮次                           |
| model_type  | 指令类型，控制语音放音和语音识别。 |
| prompt_text | 对话系统的回复                     |
| timeout     | 指令执行的时间限制                 |

###### outaction=10（挂机）时的outparams如下表：

| **参数**    | **描述**           |
| ----------- | ------------------ |
| call_id     | 呼叫唯一标识       |
| call_sor_id | 外呼机器人唯一标识 |
| call_dst_id | 用户唯一标识       |
| start_time  | 对话开始时间       |
| end_time    | 对话结束时间       |

###### outaction=11（呼叫转移）时的outparams如下表：

| **参数**    | **描述**             |
| ----------- | -------------------- |
| call_id     | 呼叫唯一标识         |
| call_dst_id | 用户唯一标识         |
| queue_id    | 呼叫转移队列唯一标识 |

