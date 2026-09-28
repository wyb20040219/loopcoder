# FastAPI User API

一个简单的分层 FastAPI 示例项目。

## Architecture

Router -> Service -> Repository

## Business Rule

创建用户时，email 必须唯一。

重复 email 应拒绝创建，并抛出：

```text
ValueError("email already exists")