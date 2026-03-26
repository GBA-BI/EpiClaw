import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerBuildDockerImageTool(api) {
  api.registerTool({
    name: "build_docker_image",
    description: "Submit a Docker image build request.",
    parameters: Type.Object({
      repo_name: Type.String({ minLength: 1, description: "Docker repository name for the image to build." }),
      tag: Type.String({ minLength: 1, description: "Image tag to build and publish." }),
      source_path: Type.String({ minLength: 1, description: "Absolute local path to the Docker build context." }),
      registry: Type.Optional(Type.String({ description: "Optional container registry hostname. Omit to use the default registry." })),
      namespace_name: Type.Optional(Type.String({ description: "Optional registry namespace or organization name." })),
    }),
    async execute(_id, params) {
      const args = [
        "--repo-name",
        params.repo_name,
        "--tag",
        params.tag,
        "--source-path",
        params.source_path,
      ];
      if (params.registry) args.push("--registry", params.registry);
      if (params.namespace_name) args.push("--namespace-name", params.namespace_name);

      const result = await runCliJson(api, "bioos_docker_build", args);
      return toTextResult(result.parsed, `Submitted docker build: ${params.repo_name}:${params.tag}`);
    },
  });
}
