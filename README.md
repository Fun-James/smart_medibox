# Smart MediBox 家庭智能药箱管理系统

## 项目简介
Smart MediBox 是一个基于 Flask + SQLAlchemy + MySQL 的家庭药品管理系统。系统支持药品、成员、药箱、处方等信息的管理，并提供了美观的登录界面和基础的权限控制（简单登录）。适合家庭或小型场景下的药品库存与用药记录管理。

## 主要功能
- 用户登录/登出
- 药品信息管理（增删查改、库存预警、过期提醒等）
- 家庭成员信息管理
- 药箱位置管理
- 处方与用药记录管理
- 数据初始化与批量导入

## 技术栈
- Python 3
- Flask
- Flask-SQLAlchemy
- MySQL（通过 PyMySQL 连接）
- HTML/CSS（含美化的登录界面）

## 快速开始
1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
2. **配置数据库**
   - 修改 `config.py` 中的 `SQLALCHEMY_DATABASE_URI`，确保数据库已创建。
3. **初始化数据库表**
   - 首次运行时会自动创建所有表。
4. **运行项目**
   ```bash
   python run.py
   ```
5. **访问系统**
   - 打开浏览器访问 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
   - 首次需手动在数据库 `userinfo` 表插入一条用户记录（如 admin/123456）。

## 目录结构
```
smart_medibox/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── static/
│   │   └── styles.css
│   └── templates/
│       ├── index.html
│       └── login.html
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## 其他说明
- 登录功能为演示用途，密码未加密，生产环境请务必加密存储。
- 如需自定义功能或界面，可直接修改 `app/routes.py`、`app/templates/` 和 `app/static/` 下相关文件。

---
如有问题欢迎反馈！
