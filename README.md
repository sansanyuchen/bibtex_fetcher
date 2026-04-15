# BibTeX Fetcher

[English](#english) | [中文](#chinese)

<a name="english"></a>
## English

BibTeX Fetcher is a simple tool designed to automatically retrieve BibTeX citations for academic papers from **arXiv** and **Google Scholar** using their titles. It can be used as a command-line interface (CLI) tool or run as a local Web service/API.

### Installation

1. Clone or download the repository to your local machine.
2. (Optional but recommended) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### 1. Command-Line Interface (CLI)

Run the `fetcher.py` script and provide the paper title as an argument.

```bash
python fetcher.py "Attention Is All You Need"
```

The script will query both arXiv and Google Scholar and print the corresponding BibTeX references directly to your console.

> **Note:** Google Scholar aggressively rate-limits automated requests. You might experience failures or blocks if you make too many requests in a short period through the Scholar module.

#### 2. Web Service / API

Run `app.py` to start a local Flask server.

```bash
python app.py
```

The server will default to running at `http://127.0.0.1:5000`.

* **Web UI**: Open `http://127.0.0.1:5000` in your web browser to use the simple graphical search interface.
* **REST API**: Send a JSON POST request to `/api/search`.

**API Usage Example:**
```bash
curl -X POST http://127.0.0.1:5000/api/search \
     -H "Content-Type: application/json" \
     -d '{"title": "Attention Is All You Need", "source": "both"}'
```
*(The `source` parameter is optional and can be set to `"arxiv"`, `"scholar"`, or `"both"`).*

---

<a name="chinese"></a>
## 中文

BibTeX Fetcher 是一个轻量级工具，旨在通过学术论文的标题从 **arXiv** 和 **Google Scholar (谷歌学术)** 自动获取 BibTeX 格式的引用信息。它既可以作为命令行工具（CLI）快速使用，也可以作为本地 Web 服务或 API 提供接口。

### 安装教程

1. 克隆或下载此仓库至本地。
2. （可选但强烈推荐）创建并激活一个虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS 或 Linux 系统
   # venv\Scripts\activate   # Windows 系统
   ```
3. 安装工程目录下必需的依赖模块：
   ```bash
   pip install -r requirements.txt
   ```

### 使用方式

#### 1. 命令行工具 (CLI) 模式

直接运行 `fetcher.py` 脚本，并将目标论文的标题作为参数传入即可。

```bash
python fetcher.py "Attention Is All You Need"
```

程序将默认同时搜索 arXiv 和 Google Scholar，并将获取到的 BibTeX 文本打印在终端面板中。

> **注意：** Google Scholar 对自动化脚本的请求频率限制极其严格，如果短时间内请求次数过多，容易遇到被限流或请求失败的情况。

#### 2. Web 网站 / API 服务模式

运行 `app.py` 即可启动一个基于 Flask 的本地 Web 服务器。

```bash
python app.py
```

启动后，服务默认运行在 `http://127.0.0.1:5000`。

* **网页可视化调用**：使用浏览器打开 `http://127.0.0.1:5000`，页面会提供一个便于操作的搜索引擎界面。
* **API 接口调用**：向 `/api/search` 发送附带论文标题的 JSON 格式 POST 请求。

**API 传参示例：**
```bash
curl -X POST http://127.0.0.1:5000/api/search \
     -H "Content-Type: application/json" \
     -d '{"title": "Attention Is All You Need", "source": "both"}'
```
*（传入的 JSON 参数中，`source` 是可选项，其支持的值为 `"arxiv"`、`"scholar"` 或 `"both"`，默认值是 `"both"`）。*
