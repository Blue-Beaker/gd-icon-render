# GD Icon Render HTTP Server

A Geometry Dash icon rendering HTTP server, powered by [gdicons](https://pypi.org/project/gdicons/).

---

[中文版本 ↓](#gd-icon-render-http-server-1)

---

## Usage

```bash
# Install dependencies
pip install pillow

# Start the server
python server.py --host 127.0.0.1 --port 8080
```

### Environment Variables

- `GDICONS_RESOURCES` — Path to the Geometry Dash `Resources` folder (optional; defaults to searching `Resources/` next to the script and in CWD)

The Resources folder must contain:
- `icons/`
- `Robot_AnimDesc.plist`
- `Spider_AnimDesc.plist`

### API

#### `GET /icon`

Renders and returns a GD icon as PNG.

| Parameter   | Description                                    | Values                                                          | Default   |
|-------------|------------------------------------------------|-----------------------------------------------------------------|-----------|
| `gamemode`  | Player form                                    | `cube`, `ship`, `ball`, `ufo`, `wave`, `robot`, `spider`, `swing`, `jetpack` | — |
| `id`        | Icon ID                                        | Integer                                                         | —         |
| `primary`   | Primary colour                                 | Hex (`#rrggbb`), colour name, or GD colour ID (0–123)           | —         |
| `secondary` | Secondary colour                               | Same as `primary`                                               | —         |
| `glow`      | Glow colour                                    | Same as `primary`, or `false` to disable                        | `false`   |
| `quality`   | Texture quality                                | `low` / `normal`, `hd`, `uhd`                                   | `uhd`     |

Example:

```bash
curl 'http://localhost:8080/icon?gamemode=cube&id=133&primary=%23ffff00&secondary=%23b900ff&glow=%23b900ff' -o icon.png
```

#### `GET /`

Returns server status info.

## License

This project is licensed under the **GNU Affero General Public License v3 (AGPLv3)**.

### Acknowledgements

This project includes a modified copy of [gdicons](https://pypi.org/project/gdicons/) (originally by Bradley Pierce), which is licensed under the **GNU Affero General Public License v3 (AGPLv3)**.

Modifications made:
- Removed the module-level Windows default path call in `gdicons/script.py`; initialisation is now done explicitly by the caller via `set_resources_path()`

See the `gdicons/` directory for the original source.

---

---

# GD Icon Render HTTP Server

基于 [gdicons](https://pypi.org/project/gdicons/) 的 Geometry Dash 图标渲染 HTTP 服务。

## 使用方法

```bash
# 安装依赖
pip install pillow

# 启动服务
python server.py --host 127.0.0.1 --port 8080
```

### 环境变量

- `GDICONS_RESOURCES` — Geometry Dash `Resources` 文件夹路径（可选，默认搜索脚本所在目录及当前目录下的 `Resources/`）

Resources文件夹下需要放入:
- `icons`
- `Robot_AnimDesc.plist`
- `Spider_AnimDesc.plist`

### API

#### `GET /icon`

渲染并返回一个 GD 图标 PNG。

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `gamemode` | 游戏模式 | `cube`, `ship`, `ball`, `ufo`, `wave`, `robot`, `spider`, `swing`, `jetpack` | — |
| `id` | 图标 ID | 整数 | — |
| `primary` | 主颜色 | Hex (`#rrggbb`)、颜色名称或 GD 颜色 ID (0-123) | — |
| `secondary` | 副颜色 | 同上 | — |
| `glow` | 辉光颜色 | 同上，或 `false` 禁用 | `false` |
| `quality` | 纹理质量 | `low`/`normal`, `hd`, `uhd` | `uhd` |

示例：

```bash
curl 'http://localhost:8080/icon?gamemode=cube&id=133&primary=%23ffff00&secondary=%23b900ff&glow=%23b900ff' -o icon.png
```

#### `GET /`

返回服务状态信息。

## 协议

本项目基于 **GNU Affero General Public License v3 (AGPLv3)** 发布。

### 致谢

本项目包含 [gdicons](https://pypi.org/project/gdicons/)（原作者 Bradley Pierce）的一份修改副本，原始协议为 **GNU Affero General Public License v3 (AGPLv3)**。

修改内容：
- 移除了 `gdicons/script.py` 中模块级别的 Windows 默认路径调用，改为由调用方显式初始化 `set_resources_path()`

请参见 `gdicons/` 目录下的原始代码。
