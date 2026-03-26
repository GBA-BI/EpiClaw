import { Type } from "@sinclair/typebox";

import { runCliText, toPlainTextResult } from "../lib/cli.js";

export function registerSubmitWorkflowTool(api) {
  api.registerTool({
    name: "submit_workflow",
    description: "Submit a Bio-OS workflow run via the bioos workflow submit CLI.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the target workflow." }),
      workflow_name: Type.String({ minLength: 1, description: "Workflow name to submit." }),
      input_json: Type.String({ minLength: 1, description: "Absolute local path to the workflow inputs.json file." }),
      data_model_name: Type.Optional(Type.String({ description: "Optional data model name used for batch array submissions." })),
      call_caching: Type.Optional(Type.Boolean({ description: "Whether to enable call caching for the workflow run." })),
      submission_desc: Type.Optional(Type.String({ description: "Optional human-readable description for this submission." })),
      force_reupload: Type.Optional(Type.Boolean({ description: "Whether to force re-upload of local input files even if they already exist remotely." })),
      mount_tos: Type.Optional(Type.Boolean({ description: "Whether to mount TOS storage into the workflow runtime environment." })),
      monitor: Type.Optional(Type.Boolean({ description: "Whether to wait and poll until the workflow run reaches a terminal state." })),
      monitor_interval: Type.Optional(Type.Number({ minimum: 0, description: "Polling interval in seconds when monitor is enabled." })),
      download_results: Type.Optional(Type.Boolean({ description: "Whether to download result artifacts after the submission completes." })),
      download_dir: Type.Optional(Type.String({ description: "Absolute local directory where downloaded results should be saved." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace_name", params.workspace_name);
      args.push("--workflow_name", params.workflow_name);
      args.push("--input_json", params.input_json);
      if (params.data_model_name) args.push("--data_model_name", params.data_model_name);
      if (params.call_caching === true) args.push("--call_caching");
      if (params.submission_desc) args.push("--submission_desc", params.submission_desc);
      if (params.force_reupload === true) args.push("--force_reupload");
      if (params.mount_tos === true) args.push("--mount_tos");
      if (params.monitor === true) args.push("--monitor");
      if (params.monitor_interval !== undefined) args.push("--monitor_interval", String(params.monitor_interval));
      if (params.download_results === true) args.push("--download_results");
      if (params.download_dir) args.push("--download_dir", params.download_dir);

      const result = await runCliText(api, "bioos_workflow_submit", args);
      return toPlainTextResult(result.combined || "No workflow submit output returned.", `Submitted workflow: ${params.workflow_name}`);
    },
  });
}
