# tasi_dialog

一个可配置话术的对话系统

## 目录

- [python依赖](#python依赖)
- [用法](#用法)
- [创建你的对话机器人](#创建你的对话机器人)
- [API](#API)

## python依赖

- tensorflow==1.11
- tornado
- psycopg2
- pyyaml
- requests

如不想自行安装python依赖，可参考README_docker.md，用docker提供tasi_dialog的运行环境。

## 用法

### 安装

```
git clone http://gitlab.tasitech.com.cn/bot/tasi_dialog.git
cd tasi_dialog
```

### 选择机器人

```python
cd bots/{bot_name}
```

把{bot_name}替换成你所要选择的机器人的名字。如想创建自己的机器人见[创建你的对话机器人](#创建你的对话机器人)。

### 启动对话服务

tasi_dialog提供文字版和电话版两种对话接口，分别可用于文本形式和电话形式的对话系统。文字版和电话版的区别在于文字版对话机器人回复给用户的是文字，电话版对话机器人回复给用户的是语音。文字能瞬间展现给用户，语音的播放需要一段时间，因此电话版对话机器人有打断和非打断两种模式，打断模式是指在机器人说话时用户如果插话机器人会停止播放语音去听用户说的话。

如果要使用基于BERT的意图识别模型，启动对话系统之前需要下载BERT预训练和finetune得到的模型。

- BERT预训练模型在oss://tasi-callcenter-audio-record/engine/model/bert/chinese_L-12_H-768_A-12/。下载后需放在src/models/bert/chinese_L-12_H-768_A-12目录下。
- finetune模型在oss://tasi-callcenter-audio-record/engine/model/bert/checkpoints/{bot_name}/intent/。下载后需放在对话系统的bots/{bot_name}/checkpoints/intent/下。如需要重新训练意图识别模型见[训练意图识别模型](#意图识别模型)。

启动文字版对话系统服务端，默认端口是59998。

```python
bash run_server_text.sh
```

测试文字版对话系统可以启动客户端。在命令行与机器人进行对话。

```
bash run_client_text.sh
```

启动电话版对话系统服务端，默认端口是59999。

```
bash run_server_phone.sh
```



## 创建你的对话机器人

对话机器人是一个能和人用自然语言交流的计算机系统。创建对话机器人的过程分为4步：

1. 按照业务流程[配置对话机器人](#配置对话机器人)，让机器人按您希望的方式回答用户。
2. [训练意图识别模型](#意图识别模型)，让机器人更好地理解用户说的话。
3. [编写运行脚本](#编写运行脚本)，方便启动对话机器人。
4. [配置机器人参数](#配置机器人参数)，配置对话机器人的参数。

### 配置对话机器人

---

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

为了实现每个节点的功能，我们还需要配置全局变量、意图、值集合、函数。

##### 意图(intent)

意图表示用户的需求，用来触发对话流。意图可以包含若干槽。槽是指机器人帮助用户完成一个意图需要向用户询问的信息。

举例：机器人可将”我想买从北京到上海的机票“这句话识别为“买机票”意图，触发“买机票”流程。“出发地”、“目的地”和“时间”是该意图的槽。

##### 全局变量(global variable)

全局变量维护了对话的全局信息。

##### 值集合(value_set)

槽可取值的集合，即槽的取值范围。有两种类型：字典和正则表达式。当槽可取的值可枚举时用字典型，不可枚举可用正则表达式表示。比如“出发地”这个槽的值集合可以是中国所有城市组成的集合。

##### 函数(function)

函数是一段代码，用来处理用对话配置文件不能配置的业务逻辑。比如调用API时，可以写一段代码进行调用。

------

#### 配置方法

对话配置文件放在dialog_config目录中。

##### 对话流

配置文件：flows/对话流名称.json，如flows/查电费.json。需要配置的字段如下：

- name：对话流名称。
- intent：触发该流程的意图。选填。
- nodes：对话流节点集合。数据类型是字典，键是节点编号，一个流程中至少有一个节点的编号是"0"，作为入口节点，即进入一个对话流后，首先处理的节点。值是对话流节点。对话流节点需要配置以下字段：
  - [type](#type配置说明)：节点类型。
  - [dm](#dm配置说明)：对话管理(dialog manage)。

######  type配置说明

流程由不同类型的节点组成。不同类型的节点完成不同的功能，可选的类型包括“slot_filling”, “function”, "assignment", "flow", “branch”,  “return”, “exit”, "response"。为了完成节点的功能，需要配置与节点类型对应的字段。各类型节点的配置方法如下：


```
{
    "name": "example",	# 流程名。创建一个流程时用户需要填，和json文件名相同。
    "intent": "example",
	"nodes": {
        # 子流程节点
        "0": {	# 节点编号。
            "type": "flow",  # 节点类型：子流程节点。
    		"flowName": ""  # 子流程名。
            "dm": list
        },
        # 分支节点
        "1": {
            "type": "branch",  # 节点类型：分支节点。
            "dm": list
        },
        # 填槽节点
        "2": {
            "type": "slot_filling",  # 节点类型：填槽节点。
            "slots": [	# 待填槽列表
				{
                    "name": "",	# 槽的名称，例如出发时间。
                    "global_variable": "",	# 与槽绑定的全局变量名。填完槽后，将把该槽的值赋给绑定的全局变量
                    "response": "",	# 机器人询问用户的话，例如“您想订几点的车票”。
                    "response_before_filling": true/false	# 在询问用户之前是否用最近一轮用户说的话尝试填槽。比如查天气这个意图中有城市这个槽，在询问用户想查询的城市之前用户可能已经说了城市，比如“北京的天气怎么样”。可以先尝试填槽，如果每没填上就回复给用户“response”。选填，不填的时候默认为false。
                }
            ],
            "dm": list
        },
        # 函数节点
        "3": {
            "type": "function",  # 节点类型：函数节点。
        	"funcName": ""  # 函数名。
            "dm": list
        }
        # 赋值节点
        "4": {
            "type": "assignment",	# 节点类型：赋值节点。
            "assignments":[	# 赋值列表
                {
                    "g_var": "",	# 全局变量名。
                    "value": ""	# 全局变量值。
                }
            ],
            "dm": list
        },
        # 回复节点
        "5": {
            "type": "response"	# 节点类型：回复节点。
            "response": ""	# 机器人回复内容。
            "dm": list
        },
        # 返回节点
        "6": {
            "type": "return"	# 节点类型：返回节点。
        },
        # 退出节点
        "7": {
            "type": "exit",	# 节点类型：结束节点。
            "todo":	""	# 挂断电话后续处理。可选值为"hangup"/"fwd"
        }
    }
}
```

###### dm配置说明

机器人处理完每个节点分两步：先实现type指定的任务，比如填槽节点的填槽。然后根据dm找出下一个要处理的节点。因为return节点和exit节点是对话流的出口节点，没有对应的下一个节点，因此不需要配置“dm”。

dm是一个列表，每一个元素是一个字典，表示一个跳转路径，由跳转条件，跳转至的节点编号和系统回复组成，指明在某一条件下跳转至某一节点并生成一句对用户的回复。

```
{   
    "cond": true/dict/"else",	# 跳转条件。有三种可能，下面有详细解释。
    "nextNode": "", # 跳转目标节点的编号
    "response": ""	# 跳转的时候，机器人对用户的回复。选填。
}
```

机器人按顺序判断dm中每个元素的cond，如果cond==true，则跳转至nextNode，如果有response，就给用户回复response。如果cond==false，则判断dm中下一元素的cond。如果条件均不成立，则留在该节点。

cond字段的三种情况：

1. 当"cond" == true时，表示条件成立。

2. 当"cond" == "else"时，当其他条件都不满足时，走这条路径。

3. 当“cond”是一个字典时，按照下面方式配置：

   cond的语法详见[jsonlogic](http://jsonlogic.com/operations.html)。下面简要说明jsonlogic语法：

- dict的键是操作符，如“==”，"!=", ">"等；dict的值是元素列表。举例{”>=“：[3, 1]}相当于3>=1, 因此是true。
- 元素列表不仅可以是上例中的静态值3和1，还可以从变量中取出，比如{“var”：“global.consumer_number”}就表示全局变量中的户号。举例{”!=“：[{“var”：“global.consumer_number”}, '123']}的意思是判断全局变量中的consumer_number是否不等于'123'。
- 元素列表中的元素除了静态值和变量外，还可以是另一个字典表示的cond。

###### 主流程

主流程是一个特殊的对话流。用‘flows/main.json’配置，流程名为‘main’。除了主流程外的普通流程是为了实现用户意图的流程，而主流程是用来实现机器人意图的流程。举个例子，客服机器人没有自己的意图，只是帮助客户解决问题，因此不需要配置主流程。而外呼机器人有自己的意图，比如催费、推销等，可通过主流程配置。主流程和普通流程在处理上也有很大区别。当普通流程执行到一半时，如果识别到别的意图，那么会丢弃当前状态，下次再次识别到该流程对应的意图时，会从该对话流的入口节点开始执行。而处理完别的流程再回来执行主流程时，会从主流程上次离开的节点继续执行。

----

##### 全局变量

配置文件：global_variables.json

定义并初始化全局变量。

```
{
  "g_vars": {
    "address": null,
    "owe": null
  },
  # g_vars_need_init字段表示初始化一个机器人时需要用外部传入参数初始化的全局变量列表。是g_vars中键的子集。举个例子：催费机器人在打给一个用户之前需要知道用户的个人信息，如欠费和地址。
  "g_vars_need_init": [
    "address",
    "owe"
  ]
}
```

全局变量目前只支持null、字符串、数字、bool。

对话系统有2个内置全局变量：intent和func_return，分别是最近一次意图识别结果和最近一次函数的返回。内置的全局变量以builtin开头，用户自定义的全局变量以global开头。

------

##### 意图

配置文件：intents.json。

内容为意图列表。每一个意图为一个字典，需要配置以下字段：

- name：意图名称

- description：意图注释。选填。

- slots：槽。选填。
  
  为了帮助用户实现该意图，机器人需要引导用户填上一些槽。slots的数据类型为字典。键是槽的名称，值是槽的配置信息，槽的配置信息包含以下字段：
  
  - name：槽名称
  - chineseName：槽中文名。选填。
  - value_set：值集合。值集合有内置(builtin)和自定义(user)两种。内置的值集合可直接调用。目前内置的值集合有city和month两个。自定义的值集合需要自己配置，配置方法参考[值集合](#值集合)。

```
[
  {
    "name": "consumer_type_identification",
    "description": "客户性质识别",
    "slots": {
    }
  },
  {
    "name": "查户号",
    "description": "查询户号",
    "slots": {
      "consumer_number": {
        "name": "consumer_number",
        "chineseName": "户号",
        "value_set": "user.consumer_number" # 内置值集合以builtin.开头，自定义值集合以user.开头
      },
      "pay_to": {
        "name": "pay_to",
        "chineseName": "交费地点",
        "value_set": "user.pay_to"
      },
      "meter_number": {
        "name": "meter_number",
        "chineseName": "电表号",
        "value_set": "user.meter_number"
      }
    }
  }
]
```

------

##### 值集合

值集合是槽可取值的集合，比如中国所有的城市。在配置意图时，为意图中的每个槽指定一个值集合，值集合中的词是对应槽的取值范围。

配置文件：lexicon.json

- name：词典名称
- chineseName：词典中文名。选填。
- type：值集合类型，可选“regex”和“dict”
- regex：正则表达式。如果type是regex，需要配置。
- dict：字典。如果type是dict，需要配置。字典的键是值集合中的值，字典的值是值集合中值的别名列表。

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
        "羊城",
        "花城"
      ],
      "上海": [
        "上海",
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

在functions.py中写自定义函数，供对话流的函数节点调用。函数的输入为最近一轮用户输入和全局变量。函数的返回值会被赋值给全局变量builtin.func_return。

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

---

##### 服务用语

在service_language.json中写服务用语。greeting是开场白。pardon是没有理解用户输入时的兜底话术

```
{
  "greeting": "喂，您好，我这边是萧山供电有限公司，您在[%global.address%]的房子电费已经欠费[%global.owe%]，请您这边及时交清电费，可以嘛。",
  "pardon": "您在[%global.address%]的房子电费已经欠费[%global.owe%]，请您这边及时交清电费。"
}
```

备注：如果配置了主流程，且主流程中执行中产生了response，那么会用主流程执行过程中产生的第一句response代替greeting作为开场白。

---

#### 机器人如何按照配置文件执行？

机器人给出开场白后会与用户进行多轮对话。一轮对话由一句用户输入和一句机器人回复组成。机器人收到用户输入后，会先进行意图识别。如果此时没有待处理的流程，并且也没有识别到用户意图，则回复兜底话术。如果此时有待处理流程，但是别到的意图对应的流程不是待处理流程，那么机器人去执行识别到的意图所对应的对话流，否则执行待处理流程。然后机器人开始处理对话流中的节点，然后跳转至下一节点，不断循环，只到在dm或回复节点或填槽节点产生了response，即机器人回复，此时在下一待处理节点处停止，把response回复给用户，一轮交互完成。接着等待用户输入，开始下一轮的交互。

---

### 意图识别模型

#### 基于BERT的意图识别模型

在dialog_config/corpus/samples.json中放置训练样本。数据类型为字典。每个意图至少配置20句以上的样本，越多越好。有一个特殊意图为’others‘，表示不属于任何其他意图，可用来配置反例。

```
{
  "intent_name": {
    "name": "intent_name", # 意图名。与intents.json中的意图名相对应。
    "samples": [ # 属于该意图的样本列表
      "sample0",
      "sample1",
      "sample2"
    ]
  },
  "查天气": {
    "name": "查天气",
    "samples": [
      "北京今天天气怎么样"，
      "查天气"，
      "今天有雨么",
      ...
    ]
  }
  ...
}
```

准备好训练样本后，我们可以训练意图识别模型了，但是在训练模型之前我们需要下载BERT预训练模型。BERT预训练模型在oss://tasi-callcenter-audio-record/engine/model/bert/chinese_L-12_H-768_A-12/。下载后需放在src/models/bert/chinese_L-12_H-768_A-12目录下。

在bots/{bot_name}文件加下，运行以下命令即可训练意图识别模型。

```
bash train_bert.sh
```

#### 基于匹配的意图识别

除了可以使用训练得到的模型进行意图识别，还可以通过正则匹配进行意图识别。在dialog_config/corpus/templates.json中放置匹配模板。模板中可用选则框和通配符增强泛化能力：
- 选项框：选项框有[]和()两种，[]是可选框，()是必选框，在选项框中填入各选项并用“|”隔开。比如```[帮我|给我](查|报)一下天气```这个模板可匹配“查一下天气”，但不能匹配“帮我一下天气”。
- 通配符：.{n,m}代表n~m个字，n和m是数字。比如```查.{0,3}快递```这个模板可匹配“查一下快递”，但不能匹配“查一下那个快递”。

```
{
  "intent_name": {
    "name": "intent_name", # 意图名。与intents.json中的意图名相对应。
    "templates": [ # 属于该意图的样本列表
      "template0",
      "template1",
      "template2"
    ]
  },
  "查天气": {
    "name": "查天气",
    "templates": [
      "[帮我|给我]查一下天气"，
      "[我想|我要]查天气"
      ...
    ]
  }
  ...
}
```

在识别用户意图时，机器人先用BERT模型识别一次，如果识别结果不为others，且置信度高于一个阈值，则把BERT模型的识别结果作为用户意图，否则以正则匹配的结果作为用户意图。置信度阈值默认为0.93，可通过dialog_config/thresholds.json中的intent_bert字段更改阈值。

---

### 编写运行脚本

可在脚本模板基础上改写得到您自己的运行脚本。

##### 文字版对话系统服务端启动脚本：run_server_text.sh

```
#!/bin/bash
python ../../src/server_text.py
```

##### 文字版对话系统客户端启动脚本：run_client_text.sh

```
#!/bin/bash
python ../../src/client_text.py
```

##### 电话版对话系统服务端启动脚本：run_server_phone.sh

```
#!/bin/bash
python ../../src/server_phone.py
```

##### 意图识别模型训练脚本：train_bert.sh

```
#!/bin/bash
ckpt_dir=checkpoints/intent
data_dir=datasets/intent
bert_dir=../../src/models/bert
pretrained_ckpt_dir=$bert_dir/chinese_L-12_H-768_A-12
python ../../src/models/build_datasets.py

rm -rf $ckpt_dir

python $bert_dir/run_classifier.py \
  --task_name=intent \
  --do_train=true \
  --do_eval=true \
  --do_predict=true \
  --data_dir=$data_dir \
  --vocab_file=$pretrained_ckpt_dir/vocab.txt \
  --bert_config_file=$pretrained_ckpt_dir/bert_config.json \
  --init_checkpoint=$pretrained_ckpt_dir/bert_model.ckpt \
  --max_seq_length=64 \
  --train_batch_size=32 \
  --learning_rate=2e-5 \
  --num_train_epochs=10.0 \
  --output_dir=$ckpt_dir
```

---

### 配置机器人参数

##### 文字版机器人参数配置文件：config_text.yml

```
port: 59998 # 服务端端口。默认为59998
```

##### 电话版机器人参数配置文件：config_phone.yml

```
port: 59999 # 服务端端口。默认为59999
bot:
  interruptable: False # 机器人说话时，用户是否可以打断。默认为False
```

---



## API

客户端可通过post方式向服务端发送请求。

### 文字版对话机器人API

#### 请求参数

| 参数名   | 数据类型 | 描述                                                         |
| -------- | -------- | ------------------------------------------------------------ |
| userid   | str      | 对话唯一标识                                                 |
| inaction | int      | 指令标志。初始化对话时设为8 , 对话过程中设为最近一次从服务端接收到的相应中的outaction。8为初始化，9为正常交互。 |
| inparams | json     | 客户端给服务端发送的参数列表                                 |

###### inaction=8（初始化）时的inparams如下表：

| **参数**    | 数据类型 | **描述**                                                     |
| ----------- | -------- | ------------------------------------------------------------ |
| call_id     | str      | 呼叫唯一标识                                                 |
| call_sor_id | str      | 用户唯一标识                                                 |
| start_time  | str      | 对话开始时间                                                 |
| user_info   | str      | 用户信息。用‘#’隔开，参数内容为[全局变量](#全局变量)配置文件中g_vars_need_init字段中变量列表的变量值。 |

###### inaction=9（正常交互）时的inparams如下表：

| **参数**         | 数据类型 | **描述**                                                     |
| ---------------- | -------- | ------------------------------------------------------------ |
| call_id          | str      | 呼叫唯一标识                                                 |
| inter_idx        | str      | 对话轮次。从outaction=10时的outparams中的inter_idx获得       |
| input            | str      | flow_result_type==’1‘时表示用户说的话；flow_result_type==’3‘时表示无识别结果的原因。'hangup'表示用户主动挂机，'timeout'表示识别超时，'nomatch'表示ASR异常。 |
| flow_result_type | str      | '1'表示有正常的识别结果。'3'表示无识别结果                   |

#### 响应参数

| 参数名    | 数据类型 | 描述                                                        |
| --------- | -------- | ----------------------------------------------------------- |
| ret       | int      | 调用标识。0代表调用成功，其他代表调用失败                   |
| userid    | str      | 呼叫唯一标识 , 同call_id                                    |
| outaction | int      | 服务端返回的指令标志。9为正常交互，10为挂机，11为呼叫转移。 |
| outparams | json     | 服务端返回客户端的参数列表                                  |

###### outaction=9（正常交互）时的outparams如下表：

| **参数**    | 数据类型 | **描述**                                                     |
| ----------- | -------- | ------------------------------------------------------------ |
| call_id     | str      | 呼叫唯一标识                                                 |
| inter_idx   | str      | 对话轮次。表示是一段对话中的第几轮。                         |
| model_type  | str      | 指令类型，控制语音放音和语音识别。一共2个数字，分别代表是否执行放音和识别操作，‘1’代表是，‘0’代表否。例如’11‘表示既放音也是别，’10‘表示只放音不识别。 |
| prompt_text | str      | 对话系统的回复。                                             |
| timeout     | str      | 指令执行的时间限制。设置指令执行的最大时间，单位为s，超出最大时间时被认定为超时。 |

###### outaction=10（挂机）时的outparams如下表：

| **参数**    | 数据类型 | **描述**     |
| ----------- | -------- | ------------ |
| call_id     | str      | 呼叫唯一标识 |
| call_sor_id | str      | 用户唯一标识 |
| start_time  | str      | 对话开始时间 |
| end_time    | str      | 对话结束时间 |

### 电话版对话机器人API

#### 请求参数

| 参数名   | 数据类型 | 描述                                                         |
| -------- | -------- | ------------------------------------------------------------ |
| userid   | str      | 对话唯一标识                                                 |
| inaction | int      | 指令标志。初始化对话时设为8 , 对话过程中设为最近一次从服务端接收到的相应中的outaction。8为初始化，9为正常交互，11为呼叫转移。 |
| inparams | json     | 客户端给服务端发送的参数列表                                 |

###### inaction=8（初始化）时的inparams如下表：

| **参数**    | 数据类型 | **描述**                                                     |
| ----------- | -------- | ------------------------------------------------------------ |
| call_id     | str      | 呼叫唯一标识                                                 |
| call_sor_id | str      | 机器人唯一标识                                               |
| call_dst_id | str      | 用户唯一标识                                                 |
| start_time  | str      | 对话开始时间                                                 |
| queue_id    | str      | 呼叫转移队列唯一标识                                         |
| extend      | str      | 用户信息。用‘#’隔开，参数内容为[全局变量](#全局变量)配置文件中g_vars_need_init字段中变量列表的变量值。 |

###### inaction=9（正常交互）时的inparams如下表：

| **参数**         | 数据类型 | **描述**                                                     |
| ---------------- | -------- | ------------------------------------------------------------ |
| call_id          | str      | 呼叫唯一标识                                                 |
| inter_idx        | str      | 对话轮次。从outaction=10时的outparams中的inter_idx获得       |
| input            | str      | flow_result_type==’1‘时表示用户说的话；flow_result_type==’3‘时表示无识别结果的原因。'hangup'表示用户主动挂机，'timeout'表示识别超时，'nomatch'表示ASR异常。 |
| flow_result_type | str      | '1'表示有正常的识别结果。'3'表示无识别结果                   |

###### inaction=11（呼叫转移）时的inparams如下表：

| **参数**     | 数据类型 | **描述**                               |
| ------------ | -------- | -------------------------------------- |
| call_id      | str      | 呼叫唯一标识                           |
| trans_result | str      | 是否转移成功。‘1’代表成功，‘0’代表失败 |

#### 响应参数

| 参数名    | 数据类型 | 描述                                                        |
| --------- | -------- | ----------------------------------------------------------- |
| ret       | int      | 调用标识。0代表调用成功，其他代表调用失败                   |
| userid    | str      | 呼叫唯一标识 , 同call_id                                    |
| outaction | int      | 服务端返回的指令标志。9为正常交互，10为挂机，11为呼叫转移。 |
| outparams | json     | 服务端返回客户端的参数列表                                  |

###### outaction=9（正常交互）时的outparams如下表：

| **参数**    | 数据类型 | **描述**                                                     |
| ----------- | -------- | ------------------------------------------------------------ |
| call_id     | str      | 呼叫唯一标识                                                 |
| inter_idx   | str      | 对话轮次。表示是一段对话中的第几轮                           |
| model_type  | str      | 指令类型，控制语音放音和语音识别。一共7个数字。后五个固定为‘0’。前两位分别代表是否执行放音和识别操作，‘1’代表是，‘0’代表否。例如’1100000‘表示既放音也是别，’1000000‘表示只放音不识别，’0100000‘表示不放音只识别。 |
| prompt_text | str      | 对话系统的回复                                               |
| timeout     | str      | 指令执行的时间限制。设置指令执行的最大时间，单位为s，超出最大时间时被认定为超时。 |

###### outaction=10（挂机）时的outparams如下表：

| **参数**    | 数据类型 | **描述**           |
| ----------- | -------- | ------------------ |
| call_id     | str      | 呼叫唯一标识       |
| call_sor_id | str      | 外呼机器人唯一标识 |
| call_dst_id | str      | 用户唯一标识       |
| start_time  | str      | 对话开始时间       |
| end_time    | str      | 对话结束时间       |

###### outaction=11（呼叫转移）时的outparams如下表：

| **参数**    | 数据类型 | **描述**             |
| ----------- | -------- | -------------------- |
| call_id     | str      | 呼叫唯一标识         |
| call_dst_id | str      | 用户唯一标识         |
| queue_id    | str      | 呼叫转移队列唯一标识 |



# contact

zhangyi24stu@qq.com

