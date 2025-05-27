# kcp.py
Python 绑定及基于 KCP 协议的网络通信实现。

## 什么是 KCP？
KCP 是一种专注于低延迟数据传输并保证数据可靠性的协议，可作为 TCP 协议的替代方案。

## 如何安装？
kcp.py 已发布至 [PyPi](https://pypi.org/project/kcp/)，只需执行以下命令即可安装：
```sh
pip install kcp
```

## 示例
### 原始连接操作
除了提供多种预设的 KCP 使用方式（见下文），kcp.py 也允许直接管理 KCP 连接。以下示例展示了本地两个独立连接的交互。
```py
from kcp import KCP

# 使用相同的会话ID创建两个连接。
kcp1 = KCP(
    conv_id=1,
)

kcp2 = KCP(
    conv_id=1,
)

# 更新连接的计时信息。
kcp1.update()
kcp2.update()


# 设置各连接的出站数据处理（通常需通过网络层传输，此处为示例简化直接对接）。
@kcp1.outbound_handler
def send_kcp1(_, data: bytes) -> None:
    kcp2.receive(data)


@kcp2.outbound_handler
def send_kcp2(_, data: bytes) -> None:
    kcp1.receive(data)

# 将数据加入发送队列并立即发送。
kcp1.enqueue(b"Hello, world!")
kcp1.flush()

print(kcp2.get_received()) # b"Hello, world!"
```

### 异步服务器
kcp.py 使用事件循环协议 API 实现了异步服务器。
```py
from kcp.server import Connection
from kcp.server import KCPServerAsync

# 初始化服务器实例。
server = KCPServerAsync(
    "127.0.0.1",
    9999,
    conv_id=1,
    no_delay=True,
)

# 支持在初始化后设置性能参数。
server.set_performance_options(
    update_interval=10,
)


# 服务器启动时触发。
@server.on_start
async def on_start() -> None:
    print("服务器已启动！")


# 收到连接数据时触发。
@server.on_data
async def on_data(connection: Connection, data: bytes) -> None:
    print(f"接收到来自 {connection.address} 的数据：{data}")


server.start()
```

### 客户端
kcp.py 同时提供基于 Python 原生套接字与线程的同步客户端实现。
```py
from kcp import KCPClientSync

client = KCPClientSync(
    "127.0.0.1",
    9999,
    conv_id=1,
)


@client.on_data
def handle_data(data: bytes) -> None:
    print(data)


@client.on_start
def on_start() -> None:
    print("已连接至服务器！")

    while True:
        client.send(b"Data!")


client.start()
```

更多示例可在项目仓库的 `examples` 目录中找到。

## 功能特性
- [x] 原生集成 KCP 的 C 语言实现
- [x] 基于 C 实现的 Python 风格 API
- [ ] 异步 KCP 客户端
- [x] 同步 KCP 客户端
- [x] 异步 KCP 服务器
- [x] 完整的 pip 安装支持

## 致谢
kcp.py 底层使用了 [官方 KCP 实现](https://github.com/skywind3000/kcp)。