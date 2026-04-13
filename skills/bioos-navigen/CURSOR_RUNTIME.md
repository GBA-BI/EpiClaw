# Bio-OS 在 Cursor / 无 OpenClaw 环境下的执行方式

在 **Cursor** 或未安装 `bioos-claw-plugin` 时，不存在 `validate_wdl`、`import_workflow` 等**插件工具**。你必须通过**终端**调用 **pybioos** 的 `bioos` 命令完成相同操作。

**在 Cursor 规则里只挂载某个子目录 skill 时**：请同时挂载本文件（或把下方对照表复制进规则），否则模型可能仍假设存在插件工具。

约定：

- 下表中标记 **JSON** 的命令：在整条命令末尾追加 `--output json`（与插件内部行为一致）。
- 标记 **文本** 的命令：**不要**加 `--output json`，直接阅读终端标准输出。
- 占位符：`WS`=workspace name，`WF`=workflow name，`SID`=submission id，`WID`=workflow id，`PATH`=本地绝对路径。

## 插件工具名 → `bioos` 命令对照

| 插件工具名 | 输出 | `bioos` 命令模板 |
|------------|------|------------------|
| `list_bioos_workspaces` | JSON | `bioos workspace list`（可选 `--page-size N`） |
| `create_workspace_bioos` | JSON | `bioos workspace create --workspace-name WS --workspace-description "DESC"` |
| `get_workspace_profile` | JSON | `bioos workspace profile --workspace-name WS`（可加 `--submission-limit`、`--artifact-limit-per-submission`、`--sample-rows-per-data-model`、`--include-artifacts` / `--no-include-artifacts` 等，与 pybioos 帮助一致） |
| `export_bioos_workspace` | JSON | `bioos workspace export --workspace-name WS --export-path PATH` |
| `upload_dashboard_file` | JSON | `bioos workspace dashboard-upload --workspace-name WS --local-file-path PATH` |
| `list_workflows_from_workspace` | JSON | `bioos workflow list --workspace-name WS`（可选 `--search-keyword`、`--page-number`、`--page-size`） |
| `generate_inputs_json_template_bioos` | JSON | `bioos workflow input-template --workspace-name WS --workflow-name WF` |
| `import_workflow` | 文本 | `bioos workflow import --workspace_name WS --workflow_name WF --workflow_source SRC`（可选 `--workflow_desc`、`--main_path`、`--monitor`、`--monitor_interval`） |
| `check_workflow_import_status` | 文本 | `bioos workflow import-status --workspace_name WS --workflow_id WID` |
| `validate_wdl` | JSON | `bioos workflow validate --wdl-path PATH` |
| `submit_workflow` | 文本 | `bioos workflow submit --workspace_name WS --workflow_name WF --input_json PATH`（可选 `--data_model_name`、`--call_caching`、`--submission_desc`、`--force_reupload`、`--mount_tos`；**长时间运行请加 `--monitor false` 或勿加 `--monitor`**，与 skill 中「不阻塞」一致） |
| `check_workflow_run_status` | 文本 | `bioos workflow run-status --workspace_name WS --submission_id SID`（可选 `--page_size N`） |
| `get_submission_logs` | 文本 | `bioos submission logs --workspace_name WS --submission_id SID`（可选 `--output_dir PATH`） |
| `delete_submission` | JSON | `bioos submission delete --workspace-name WS --submission-id SID` |
| `list_submissions_from_workspace` | JSON | `bioos submission list --workspace-name WS`（可选 `--workflow-name`、`--search-keyword`、`--status`、`--page-number`、`--page-size`） |
| `list_files_from_workspace` | JSON | `bioos file list --workspace-name WS`（可选 `--prefix`、`--recursive`） |
| `download_files_from_workspace` | JSON | `bioos file download --workspace-name WS --source S1 --source S2 ... --target DIR`（可选 `--flatten`） |
| `create_iesapp` | JSON | `bioos ies create --workspace-name WS --ies-name NAME --ies-desc "DESC"`（可选 `--ies-image`、`--ies-resource`、`--ies-storage` 等） |
| `check_ies_status` | JSON | `bioos ies status --workspace-name WS --ies-name NAME` |
| `get_ies_events` | JSON | `bioos ies events --workspace-name WS --ies-name NAME` |
| `search_dockstore` | JSON | `bioos dockstore search --query FIELD OPERATOR TERM`（可选 `--top-n`、`--query-type`、`--sentence`、`--output-full`） |
| `fetch_wdl_from_dockstore` | JSON | `bioos dockstore fetch --url URL`（可选 `--output-path PATH`） |
| `get_docker_image_url` | JSON | `bioos docker url --repo-name R --tag T`（可选 `--registry`、`--namespace-name`） |
| `build_docker_image` | JSON | `bioos docker build --repo-name R --tag T --source-path PATH`（可选 `--registry`、`--namespace-name`） |
| `check_build_status` | JSON | `bioos docker status --task-id TASK_ID` |

## 与 OpenClaw 插件的关系

`plugins/bioos-claw-plugin` 仅负责把上表左侧名字注册为工具并转发到同一套 `bioos` 子命令。**在 Cursor 里用终端跑 `bioos` 即等价于调用插件**，无需安装 OpenClaw。

若本机未安装 pybioos，请先在环境中安装并配置 `bioos auth`，再执行上表命令。
