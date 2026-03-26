# bioos-claw-plugin

`bioos-claw-plugin` is an OpenClaw plugin that exposes Bio-OS capabilities through the `pybioos` CLI.

After installation, OpenClaw can directly use Bio-OS platform capabilities such as:

- workspace management
- workflow import and submission
- workflow status and logs
- workspace file operations
- IES instance management
- Dockstore workflow discovery
- Docker image helpers

The execution chain is:

```text
OpenClaw
  -> bioos-claw-plugin
    -> pybioos CLI
      -> Bio-OS
```

This plugin is intentionally thin:

- Bio-OS business logic stays in `pybioos`
- the plugin only registers OpenClaw tools and forwards calls to `bioos ...`
- authentication is handled by `pybioos`, not by the plugin

## Prerequisites

Before installing this plugin, make sure you already have:

1. OpenClaw installed
2. `pybioos` `0.0.22` or later installed
3. Bio-OS credentials configured for the current user

Recommended first check:

```bash
bioos --help
bioos auth status
bioos workspace list
```

If these commands do not work yet, fix `pybioos` first and install this plugin afterwards.

For `pybioos` installation, upgrade notes, and authentication setup, please refer to the `pybioos` repository and its `0.0.22` upgrade guide.

## Install the plugin

Clone this repository to your local machine or server, then install dependencies:

```bash
cd /path/to/bioos-claw-plugin
npm install
npm run check
```

Install the plugin into OpenClaw from the local path:

```bash
openclaw plugins install -l /path/to/bioos-claw-plugin
```

## Enable the plugin

Add the plugin to the allow list and enable it:

```bash
openclaw config set 'plugins.allow' '["bioos-claw-plugin"]' --strict-json
openclaw config set 'plugins.entries.bioos-claw-plugin.enabled' 'true' --strict-json
```

## Configure `bioosCommand`

The most important setting is:

```text
bioosCommand
```

It tells OpenClaw which `bioos` executable should be launched by the plugin.

### Option A: `bioos` already works in your shell

If this works:

```bash
bioos --help
```

then you can configure:

```bash
openclaw config set 'plugins.entries.bioos-claw-plugin.config.bioosCommand' '"bioos"' --strict-json
```

### Option B: use the absolute path from `which bioos`

If you want the more reliable setup, or `bioos` is installed inside a virtual environment, first run:

```bash
which bioos
```

Example output:

```bash
/root/miniforge3/envs/py310/bin/bioos
```

Then configure that exact path:

```bash
openclaw config set 'plugins.entries.bioos-claw-plugin.config.bioosCommand' '"/root/miniforge3/envs/py310/bin/bioos"' --strict-json
```

If you are unsure whether OpenClaw and your terminal are using the same environment, prefer the absolute path.

## Adjust OpenClaw tool settings

If this step is skipped, the current OpenClaw session may only see generic coding tools and not the Bio-OS plugin tools.

We recommend:

```bash
openclaw config set 'tools.profile' '"full"' --strict-json
openclaw config set 'tools.allow' '["bioos-claw-plugin"]' --strict-json
```

Explanation:

- `tools.profile = full`: exposes a fuller tool set to the session
- `tools.allow = ["bioos-claw-plugin"]`: explicitly allows Bio-OS plugin tools

## Restart OpenClaw gateway

After configuration:

```bash
openclaw gateway restart
```

## Verify the plugin

Check plugin status:

```bash
openclaw plugins list
```

If everything is correct, you should see something like:

- `BioOS Plugin`
- `ID: bioos-claw-plugin`
- `Status: loaded`

## Start a fresh session

After restarting the gateway, do **not** continue using an old session.

Create a new OpenClaw session and ask:

```text
你现在有什么工具？
```

If the plugin is active, the model should see a Bio-OS tool group, such as:

- workspace management
- workflow import, submission, and monitoring
- WDL validation and input template generation
- IES instance management
- Dockstore workflow search
- Docker image helpers

If the model still only sees generic tools like:

- `read`
- `write`
- `edit`
- `exec`
- `web_search`

then usually one of these is true:

- the session was not recreated
- `tools.profile` is still too restrictive
- `tools.allow` has not been applied

In that case, re-run:

```bash
openclaw gateway restart
```

and start a fresh session again.

## Minimal example

If `bioos --help` already works directly:

```bash
cd /path/to/bioos-claw-plugin
npm install
npm run check
openclaw plugins install -l /path/to/bioos-claw-plugin
openclaw config set 'plugins.allow' '["bioos-claw-plugin"]' --strict-json
openclaw config set 'plugins.entries.bioos-claw-plugin.enabled' 'true' --strict-json
openclaw config set 'plugins.entries.bioos-claw-plugin.config.bioosCommand' '"bioos"' --strict-json
openclaw config set 'tools.profile' '"full"' --strict-json
openclaw config set 'tools.allow' '["bioos-claw-plugin"]' --strict-json
openclaw gateway restart
```

If you want to use the absolute path from `which bioos`:

```bash
cd /path/to/bioos-claw-plugin
npm install
npm run check
openclaw plugins install -l /path/to/bioos-claw-plugin
openclaw config set 'plugins.allow' '["bioos-claw-plugin"]' --strict-json
openclaw config set 'plugins.entries.bioos-claw-plugin.enabled' 'true' --strict-json
openclaw config set 'plugins.entries.bioos-claw-plugin.config.bioosCommand' '"/absolute/path/to/bioos"' --strict-json
openclaw config set 'tools.profile' '"full"' --strict-json
openclaw config set 'tools.allow' '["bioos-claw-plugin"]' --strict-json
openclaw gateway restart
```

## Notes

- This repository does not bundle a private skill pack by default. The plugin itself focuses on registering Bio-OS tools for OpenClaw.
- Bio-OS authentication is handled by `pybioos`, preferably through `~/.bioos/config.yaml`.
- `bioosCommand` is the recommended user-facing configuration. `pybioosBin` remains supported as a legacy fallback.
