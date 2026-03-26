import { spawn } from "node:child_process";
import path from "node:path";

const COMMAND_ALIASES = {
  bioos_workspace_list: ["bioos", "workspace", "list"],
  bioos_workspace_create: ["bioos", "workspace", "create"],
  bioos_workspace_export: ["bioos", "workspace", "export"],
  bioos_workspace_profile: ["bioos", "workspace", "profile"],
  bioos_workspace_dashboard_upload: ["bioos", "workspace", "dashboard-upload"],
  bioos_workspace_workflow_list: ["bioos", "workflow", "list"],
  bioos_workflow_inputs_template: ["bioos", "workflow", "input-template"],
  bioos_workflow_import: ["bioos", "workflow", "import"],
  bioos_workflow_import_status: ["bioos", "workflow", "import-status"],
  bioos_workflow_run_status: ["bioos", "workflow", "run-status"],
  bioos_workflow_submit: ["bioos", "workflow", "submit"],
  bioos_wdl_validate: ["bioos", "workflow", "validate"],
  bioos_workspace_submission_list: ["bioos", "submission", "list"],
  bioos_submission_delete: ["bioos", "submission", "delete"],
  bioos_submission_logs: ["bioos", "submission", "logs"],
  bioos_workspace_file_list: ["bioos", "file", "list"],
  bioos_workspace_file_download: ["bioos", "file", "download"],
  bioos_ies_create: ["bioos", "ies", "create"],
  bioos_ies_status: ["bioos", "ies", "status"],
  bioos_ies_events: ["bioos", "ies", "events"],
  bioos_dockstore_search: ["bioos", "dockstore", "search"],
  bioos_dockstore_wdl_fetch: ["bioos", "dockstore", "fetch"],
  bioos_docker_build: ["bioos", "docker", "build"],
  bioos_docker_build_status: ["bioos", "docker", "status"],
  bioos_docker_image_url: ["bioos", "docker", "url"],
};

function getPluginConfig(api) {
  return api?.config?.plugins?.entries?.["bioos-claw-plugin"]?.config ?? {};
}

function buildMissingCommandError(api, command) {
  const config = getPluginConfig(api);
  const configHint = config.bioosCommand
    ? `Configured bioosCommand: ${config.bioosCommand}`
    : "Set plugin config 'bioosCommand' to an absolute executable path if needed.";

  return new Error(
    [
      `Could not launch Bio-OS CLI command: ${command}`,
      "Make sure 'bioos --help' works in the same environment as OpenClaw.",
      configHint,
    ].join("\n"),
  );
}

export function resolveCommand(api, commandName) {
  const config = getPluginConfig(api);
  const commandParts = COMMAND_ALIASES[commandName] || [commandName];
  const defaultExecutable = commandParts[0];
  const prefixArgs = commandParts.slice(1);

  if (config.bioosCommand) {
    return {
      command: config.bioosCommand,
      prefixArgs,
    };
  }

  if (config.pybioosBin) {
    return {
      command: path.join(config.pybioosBin, defaultExecutable),
      prefixArgs,
    };
  }
  return {
    command: defaultExecutable,
    prefixArgs,
  };
}

export function runCliJson(api, commandName, args) {
  const { command, prefixArgs } = resolveCommand(api, commandName);
  const finalArgs = [...prefixArgs, ...args, "--output", "json"];

  return new Promise((resolve, reject) => {
    const child = spawn(command, finalArgs, {
      stdio: ["ignore", "pipe", "pipe"],
      env: process.env,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      if (error?.code === "ENOENT") {
        reject(buildMissingCommandError(api, command));
        return;
      }
      reject(error);
    });

    child.on("close", (code) => {
      const trimmedStdout = stdout.trim();
      const trimmedStderr = stderr.trim();

      if (code !== 0) {
        reject(
          new Error(
            trimmedStderr || trimmedStdout || `${commandName} exited with code ${code}`,
          ),
        );
        return;
      }

      try {
        const parsed = trimmedStdout ? JSON.parse(trimmedStdout) : {};
        resolve({
          parsed,
          stdout: trimmedStdout,
          stderr: trimmedStderr,
        });
      } catch (error) {
        reject(
          new Error(
            `Failed to parse JSON from ${commandName}: ${error instanceof Error ? error.message : String(error)}`,
          ),
        );
      }
    });
  });
}

export function runCliText(api, commandName, args) {
  const { command, prefixArgs } = resolveCommand(api, commandName);
  const finalArgs = [...prefixArgs, ...args];

  return new Promise((resolve, reject) => {
    const child = spawn(command, finalArgs, {
      stdio: ["ignore", "pipe", "pipe"],
      env: process.env,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      if (error?.code === "ENOENT") {
        reject(buildMissingCommandError(api, command));
        return;
      }
      reject(error);
    });

    child.on("close", (code) => {
      const trimmedStdout = stdout.trim();
      const trimmedStderr = stderr.trim();

      if (code !== 0) {
        reject(
          new Error(
            trimmedStderr || trimmedStdout || `${commandName} exited with code ${code}`,
          ),
        );
        return;
      }

      resolve({
        stdout: trimmedStdout,
        stderr: trimmedStderr,
        combined: [trimmedStdout, trimmedStderr].filter(Boolean).join("\n"),
      });
    });
  });
}

export function toTextResult(value, title) {
  return {
    content: [
      {
        type: "text",
        text: title ? `${title}\n${JSON.stringify(value, null, 2)}` : JSON.stringify(value, null, 2),
      },
    ],
  };
}

export function toPlainTextResult(text, title) {
  return {
    content: [
      {
        type: "text",
        text: title ? `${title}\n${text}` : text,
      },
    ],
  };
}
