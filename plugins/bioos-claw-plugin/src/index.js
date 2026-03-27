import { registerCheckBuildStatusTool } from "./tools/check_build_status.js";
import { registerCheckIesStatusTool } from "./tools/check_ies_status.js";
import { registerCheckWorkflowImportStatusTool } from "./tools/check_workflow_import_status.js";
import { registerCheckWorkflowRunStatusTool } from "./tools/check_workflow_run_status.js";
import { registerCreateIesappTool } from "./tools/create_iesapp.js";
import { registerCreateWorkspaceBioosTool } from "./tools/create_workspace_bioos.js";
import { registerDeleteSubmissionTool } from "./tools/delete_submission.js";
import { registerDownloadFilesFromWorkspaceTool } from "./tools/download_files_from_workspace.js";
import { registerExportBioosWorkspaceTool } from "./tools/export_bioos_workspace.js";
import { registerFetchWdlFromDockstoreTool } from "./tools/fetch_wdl_from_dockstore.js";
import { registerGenerateInputsJsonTemplateTool } from "./tools/generate_inputs_json_template_bioos.js";
import { registerGetDockerImageUrlTool } from "./tools/get_docker_image_url.js";
import { registerGetIesEventsTool } from "./tools/get_ies_events.js";
import { registerGetSubmissionLogsTool } from "./tools/get_submission_logs.js";
import { registerGetWorkspaceProfileTool } from "./tools/get_workspace_profile.js";
import { registerImportWorkflowTool } from "./tools/import_workflow.js";
import { registerListBioosWorkspacesTool } from "./tools/list_bioos_workspaces.js";
import { registerListFilesFromWorkspaceTool } from "./tools/list_files_from_workspace.js";
import { registerListSubmissionsFromWorkspaceTool } from "./tools/list_submissions_from_workspace.js";
import { registerListWorkflowsFromWorkspaceTool } from "./tools/list_workflows_from_workspace.js";
import { registerSearchDockstoreTool } from "./tools/search_dockstore.js";
import { registerSubmitWorkflowTool } from "./tools/submit_workflow.js";
import { registerUploadDashboardFileTool } from "./tools/upload_dashboard_file.js";
import { registerValidateWdlTool } from "./tools/validate_wdl.js";
import { registerBuildDockerImageTool } from "./tools/build_docker_image.js";

const plugin = {
  id: "bioos-claw-plugin",
  name: "BioOS Plugin",
  register(api) {
    registerListBioosWorkspacesTool(api);
    registerCreateWorkspaceBioosTool(api);
    registerListWorkflowsFromWorkspaceTool(api);
    registerListSubmissionsFromWorkspaceTool(api);
    registerListFilesFromWorkspaceTool(api);
    registerDownloadFilesFromWorkspaceTool(api);
    registerExportBioosWorkspaceTool(api);
    registerUploadDashboardFileTool(api);
    registerGenerateInputsJsonTemplateTool(api);
    registerImportWorkflowTool(api);
    registerCheckIesStatusTool(api);
    registerGetIesEventsTool(api);
    registerCreateIesappTool(api);
    registerSearchDockstoreTool(api);
    registerFetchWdlFromDockstoreTool(api);
    registerGetDockerImageUrlTool(api);
    registerBuildDockerImageTool(api);
    registerCheckBuildStatusTool(api);
    registerCheckWorkflowImportStatusTool(api);
    registerCheckWorkflowRunStatusTool(api);
    registerSubmitWorkflowTool(api);
    registerGetSubmissionLogsTool(api);
    registerDeleteSubmissionTool(api);
    registerValidateWdlTool(api);
    registerGetWorkspaceProfileTool(api);
  },
};

export default plugin;
