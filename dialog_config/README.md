# 对话流配置

## 名词解释

#### 对话流(flow)

对话流用来描述业务逻辑，由一个个节点(Node)组成，节点有五种类型：填槽节点(sot filling)，函数节点(function)，对话流(flow)，返回(return)，退出(exit)。

#### 意图(intent)

意图用来表示用户的需求，用来触发对话流或控制对话流节点的跳转。意图可以包含若干槽。

举例：系统可将”我想买从北京到上海的机票“这句话识别为“买机票”意图，触发“买机票”流程。“出发地”、“目的地”和“时间”是该意图的槽

#### 全局变量(global variables)

全局变量维护了对话的全局信息，对所有对话流都可见。相较于全局变量，槽是局部变量。配置意图时定义槽的实体，在配置对话流时配置填槽规则，因此槽是局部的，只对某一对话流可见。

#### 实体(entity)

槽的取值范围。有两种类型：字典和正则表达式。当槽可取的值可枚举时用字典型，不可枚举可用正则表达式表示

#### 函数(function)

函数是一段代码，用来处理调用api等无法直接用对话配置文件来配的业务逻辑。



## 配置说明

#### 对话流

配置文件：flows/对话流名称.json，如flows/consumer_number_inquiry.json

- name：对话流名称。

- nodes：对话流节点。
  - type：节点类型。可选"flow"，"branch", "slot_filling",  "function"，"assignment", "response", "return"，“exit”
  - dm：对话管理。
    - cond：跳转条件。cond的语法详见[jsonlogic](http://jsonlogic.com/operations.html)。下面简要说明jsonlogic语法，并列出几点在jsonlogic基础上修改的地方。
      - cond由dict嵌套而成。dict的键是操作符，如“==”，"!=", ">"等；dict的值是元素列表。举例{”>=“：[3, 1]}相当于3>=1, 因此是true。
      - 元素列表不仅可以是上例中的静态值3和1，还可以从变量中取出，比如{“var”：“global.consumer_number”}就表示全局变量中的户号（目前变量类型只支持global，后续会加入local，如需使用其他变量，将‘consumer_number’换成相应变量名即可）。举例{”!=“：[{“var”：“global.consumer_number”}, 'CANT_INFORM']}的意思是判断全局变量中的consumer_number是否不等于'CANT_INFORM'。
    - nextNode：跳转至的节点编号
    - response：系统回复。选填
  - slots：待填槽。type为slot_filling时配置。
    - name：“意图名.槽名”
    - response：反问话术。选填，当该槽是必填槽时配置
    - global_variable: 全局变量。将该槽的值赋给该全局变量
  - funcName：函数名。type为function时配置。
  - assignments：待赋值的全局变量。type为assignment时配置。
    - g_var: 全局变量名
    - val: 全局变量值
  - response: 系统回复。type为response时配置。

```
{
  "name": "consumer_number_inquiry",
  "nodes": {
    "0": {
      "type": "slot_filling",
      "slots": [
        {
          "name": "consumer_number_inquiry.consumer_number",
          "global_variable": "consumer_number",
          "response": "请您提供您的客户编号"
        }
      ],
      "dm": [
        {
          "cond": {
            "==": [
              {
                "var": "global.consumer_number"
              },
              "CANT_INFORM"
            ]
          },
          "nextNode": "1"
        },
        {
          "cond": "else",
          "nextNode": "4",
          "response": "您好，请您提供用电凭证或电费通知单上面的用户名称"
        }
      ]
    },
    "1": {
      "type": "slot_filling",
      "slots": [
        {
          "name": "consumer_number_inquiry.pay_to",
          "response": "请问您的电费是交给国家电网公司还是物业？",
          "global_variable": "pay_to"
        }
      ],
      "dm": [
        {
          "cond": {
            "!=": [
              {
                "var": "global.pay_to"
              },
              "物业"
            ]
          },
          "nextNode": "2"
        },
        {
          "cond": "else",
          "nextNode": "6",
          "response": "先生/女士，对不起，由于您的电费不是交给国家电网，所以您不属于国家电网的直供户，如果您有任何用电需求请您与您所属的产权单位（物业）联系，感谢您的配合。"
        }
      ]
    },
    "2": {
      "type": "slot_filling",
      "slots": [
        {
          "name": "consumer_number_inquiry.meter_number",
          "response": "请您提供准确的电表号，我试着帮您查询客户编号",
          "global_variable": "meter_number"
        }
      ],
      "dm": [
        {
          "cond": {
            "!=": [
              {
                "var": "global.meter_number"
              },
              "CANT_INFORM"
            ]
          },
          "nextNode": "3"
        },
        {
          "cond": "else",
          "nextNode": "6",
          "response": "很抱歉，由于信息不准确无法查询到您要查询的信息，建议您找到总户号或表号后再与我们联系。"
        }
      ]
    },
    "3": {
      "type": "function",
      "funcName": "customer_info_inquire",
      "dm": [
        {
          "cond": {
            "==": [
              {
                "var": "global.consumer_info_access"
              },
              true
            ]
          },
          "nextNode": "4",
          "response": "您好，请您提供用电凭证或电费通知单上面的用户名称"
        },
        {
          "cond": "else",
          "nextNode": "6",
          "response": "很抱歉，由于信息不准确无法查询到您要查询的信息，建议您找到总户号或表号后再与我们联系。"
        }
      ]
    },
    "4": {
      "type": "function",
      "funcName": "verify_consumer",
      "dm": [
        {
          "cond": {
            "==": [
              {
                "var": "global.consumer_verify_success"
              },
              true
            ]
          },
          "nextNode": "5",
          "response": "客户信息验证通过，您的客户编号为[%global.consumer_number%]"
        },
        {
          "cond": "else",
          "nextNode": "6",
          "response": "很抱歉，由于信息不准确无法查询到您要查询的信息，建议您找到总户号或表号后再与我们联系。"
        }
      ]
    },
    "5": {
      "type": "return"
    },
    "6": {
      "type": "exit"
    }
  }
}
```



#### 意图

配置文件：intents.json

- name：意图名称
- chineseName：意图中文名
- description：意图注释
- slots：槽
  - name：槽名称
  - chineseName：槽中文名
  - entity：实体。实体有内置(builtin)和自定义(user)两种。比如builtin.city，user.consumer_number

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
    "name": "consumer_number_inquiry",
    "chineseName": "查询户号",
    "description": "查询户号",
    "slots": {
      "consumer_number": {
        "name": "consumer_number",
        "chineseName": "户号",
        "entity": "user.consumer_number"
      },
      "pay_to": {
        "name": "pay_to",
        "chineseName": "交费地点",
        "entity": "user.pay_to"
      },
      "meter_number": {
        "name": "meter_number",
        "chineseName": "电表号",
        "entity": "user.meter_number"
      }
    }
  }
]
```



#### 全局变量

配置文件：global_variables.json

定义并初始化全局变量

```json
{
  "on_hook": false,
  "consumer_number": null,
  "pay_to": null,
  "meter_number": null,
  "consumer_info_access": null,
  "consumer_info": null,
  "consumer_verify_success": null,
  "is_sgcc_consumer": null,
  "earlier_stage_work_order_status": null,
  "electrical_bill": null,
  "tou_price_status": null
}
```



#### 实体

配置文件：entities.json

- name：实体名称
- chineseName：实体中文名
- type：实体类型，可选“regex”和“dict”
- regex：正则表达式。如果type是regex，需要配置。
- dict：字典。如果type是dict，需要配置。键是实体，值是实体的别名列表

```json
{
  "consumer_number": {
    "name": "consumer_number",
    "chineseName": "户号",
    "type": "regex",
    "regex": "[0-9]{10}"
  },
  "pay_to": {
    "name": "pay_to",
    "chineseName": "交费地点",
    "type": "dict",
    "dict": {
      "国家电网公司": [
        "国家电网公司",
        "国网"
      ],
      "支付宝": [
        "支付宝"
      ],
      "物业": [
        "物业"
      ]
    }
  }
}
```



#### 函数

在functions.py中写自定义函数，供对话流调用。函数的输入为全局变量和最近一轮用户输入。函数的返回值可以用在dm的cond和response中

```python
# 预处理代码

# 自定义函数
def customer_info_inquire():
    #根据api调用结果改变用户信息等全局变量
   pass

def verify_consumer():
   pass

...
```