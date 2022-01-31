1、基于neo4j图数据库，实现rasa多轮对话；其功能有
a: 基于图数据库的单轮问答，如问答1哮喘怎么预防
b: 同一用户在60s内如连续问答，机器人会根据用户问题的历史记录，智能化的回答用户；如问哮喘怎么预防后，接着问治疗周期，机器人会回答哮喘的治疗周期，
c: 可以实现闲聊

效果展示：
1.哮喘怎么预防：
平时应注意锻炼，如常用冷水洗浴，干毛巾擦身等，以便肺，气管，支气管的迷走神经的紧张状态得到缓和。

2.治疗周期:
15天

3.治疗方式：
 ['药物治疗', '支持性治疗']


 1.启动neo4j服务
 2.启动rasa actions服务 
 3.启动rasa run --debug -p 5056




