import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerCheckBuildStatusTool(api) {
  api.registerTool({
    name: "check_build_status",
    description: "Check Docker image build status.",
    parameters: Type.Object({
      task_id: Type.String({ minLength: 1, description: "Docker build task ID returned by build_docker_image." }),
    }),
    async execute(_id, params) {
      const result = await runCliJson(api, "bioos_docker_build_status", ["--task-id", params.task_id]);
      return toTextResult(result.parsed, `Build status: ${params.task_id}`);
    },
  });
}
