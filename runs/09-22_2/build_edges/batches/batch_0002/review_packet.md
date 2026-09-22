# 第 2 批 Edge Type Discovery 结果

## 一、批次信息

处理 Window：11–20
Prompt 版本：v0002
本批新增边类型：11
当前边类型总数：33

## 二、本批新增边类型

### NON_FATAL_WARNINGS_ACCEPTED_WITHOUT_REPAIR

name: NON_FATAL_WARNINGS_ACCEPTED_WITHOUT_REPAIR

definition: Non-fatal warnings reported during an otherwise successful execution step are treated as non-blocking, and the agent continues the workflow without modifying anything to address those warnings.

source_description: An execution observation that reports warnings while indicating the step completed successfully.

target_description: A subsequent agent action that continues the workflow without attempting to resolve the reported warnings.

### USES_OBSERVED_RESOURCE_AS_INPUT

name: USES_OBSERVED_RESOURCE_AS_INPUT

definition: A subsequent agent action consumes, operates on, or passes as arguments resources or entities that were enumerated in an earlier observation of the environment.

source_description: An earlier observation that enumerates available resources, files, or other environment entities (e.g., a directory listing or inventory of identifiers).

target_description: A subsequent agent action that operates on, passes, or otherwise consumes those enumerated resources as inputs.

### CONFLICTING_FIELDS_TRIGGER_RULE_BASED_SELECTION

name: CONFLICTING_FIELDS_TRIGGER_RULE_BASED_SELECTION

definition: An observation of multiple differing candidate values for the same required field within a source document or record triggers the application of a specified precedence rule to select one value.

source_description: An observation showing multiple conflicting candidate values for the same required field in a document or record.

target_description: An agent decision that selects one of the conflicting values according to a predefined precedence rule.

### MISSING_REQUIRED_FIELD_TRIGGERS_DEFAULT_ASSIGNMENT

name: MISSING_REQUIRED_FIELD_TRIGGERS_DEFAULT_ASSIGNMENT

definition: An observation that a required field is absent from source content triggers the assignment of a task-specified default value, such as zero or an empty string.

source_description: An observation of source content that lacks a required field.

target_description: An agent decision assigning the specified default value to the missing field.

### DERIVES_DECISION_FROM_OBSERVATION

name: DERIVES_DECISION_FROM_OBSERVATION

definition: An agent derives an interpretation, classification, or status decision by reading the content returned in an earlier tool observation, such as extracted document text or command output.

source_description: An earlier tool observation whose content provides the raw evidence needed for interpretation.

target_description: The agent's subsequent decision, classification, or interpretation derived from that observed content.

### CLEANS_UP_INTERMEDIATE_ARTIFACTS

name: CLEANS_UP_INTERMEDIATE_ARTIFACTS

definition: After the primary deliverables have been produced, the agent removes temporary or intermediate resources that were created during earlier execution steps.

source_description: Intermediate resources or artifacts created during earlier execution steps and no longer needed once the main task is complete.

target_description: A cleanup action that deletes or disposes of those intermediate resources.

### SUCCESSFUL_PROBE_ENABLES_BROADER_APPLICATION

name: SUCCESSFUL_PROBE_ENABLES_BROADER_APPLICATION

definition: A subsequent agent action generalizes or scales up a method that an earlier, smaller-scale probe first confirmed to work, applying it across multiple inputs or a larger scope.

source_description: An earlier execution result confirming that a method or capability works on a single test input or small-scale probe.

target_description: A subsequent agent action that applies the same confirmed method across multiple inputs or at a larger scale.

### EXTRACTS_REQUIRED_DATA_FROM_RESOURCE

name: EXTRACTS_REQUIRED_DATA_FROM_RESOURCE

definition: An agent inspects a provided resource (such as a file supplied with the task) and derives from its content a specific piece of required data or component that is retained for subsequent task execution.

source_description: An agent action that inspects or reads a provided resource to obtain task-relevant content.

target_description: The specific required data or component extracted from that resource and retained for later use in the task.

### CONSULTS_ALTERNATE_REFERENCE_TO_RESOLVE_DATA_ANOMALY

name: CONSULTS_ALTERNATE_REFERENCE_TO_RESOLVE_DATA_ANOMALY

definition: After an observed data artifact is found to contain an ambiguous, incomplete, or invalid placeholder value, the agent queries an independent reference source to determine the correct value to use.

source_description: An earlier observed data artifact whose content contains an anomaly, placeholder, or unresolvable value.

target_description: A subsequent agent action that queries an independent reference source to resolve that anomaly and obtain the correct value.

### ASSEMBLES_GATHERED_COMPONENTS_INTO_COMPOSITE_ARTIFACT

name: ASSEMBLES_GATHERED_COMPONENTS_INTO_COMPOSITE_ARTIFACT

definition: The agent constructs a single composite output by combining, in a specified arrangement, multiple distinct components that were previously identified or collected during the run.

source_description: A set of separately gathered or identified components that must be combined into one output.

target_description: An agent action that combines those components into a single composite artifact.

### PROMPTS_FURTHER_INVESTIGATION

name: PROMPTS_FURTHER_INVESTIGATION

definition: An observation whose interpretation is ambiguous, whose structure is unclear, or which leaves the agent with insufficient understanding is followed by a subsequent investigative action that gathers additional diagnostic detail to resolve that ambiguity.

source_description: An earlier observation whose meaning, structure, or interpretation is unclear or incomplete.

target_description: A subsequent investigative action that probes the data or environment further to resolve the ambiguity.

## 三、当前完整 Registry

### USES_PREVIOUSLY_PRODUCED_ARTIFACT

name: USES_PREVIOUSLY_PRODUCED_ARTIFACT

definition: A subsequent execution command consumes, loads, or invokes an artifact (such as a source file or script) that was produced by an earlier agent action within the same trajectory.

source_description: An earlier agent action that created a persistent artifact.

target_description: A later command that loads or executes the previously created artifact.

### REVEALS_MISSING_PREREQUISITE

name: REVEALS_MISSING_PREREQUISITE

definition: A preliminary environment probe performed by the agent returns evidence that a required tool or runtime is not available for the upcoming task.

source_description: An agent probe action that checks for the availability of a required tool or runtime.

target_description: An observation reporting that the probed prerequisite is absent from the environment.

### MISSING_PREREQUISITE_CAUSES_EXECUTION_FAILURE

name: MISSING_PREREQUISITE_CAUSES_EXECUTION_FAILURE

definition: A later execution attempt fails to run because it depends on the same prerequisite that an earlier observation reported as missing.

source_description: An earlier observation indicating that a required prerequisite is missing.

target_description: A subsequent command execution that fails because that prerequisite is unavailable.

### PLANS_REMEDIATION_FOR_MISSING_PREREQUISITE

name: PLANS_REMEDIATION_FOR_MISSING_PREREQUISITE

definition: The agent's plan or decision includes a conditional follow-up step to install or obtain a prerequisite in case an availability check reveals it is missing.

source_description: Evidence or anticipation that a required prerequisite may be missing from the environment.

target_description: An agent plan or decision to install or obtain the missing prerequisite.

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or missing prerequisite identified by an earlier execution step so that the blocked operation can proceed.

source_description: An earlier observed execution failure or error caused by a missing prerequisite (e.g., a required tool or program not being available).

target_description: A subsequent agent action intended to provide the missing prerequisite or otherwise resolve that failure.

### VERIFIES_PRODUCED_OUTPUT

name: VERIFIES_PRODUCED_OUTPUT

definition: A subsequent agent action independently inspects or validates an artifact whose production was reported by an earlier execution step, in order to confirm the reported output actually exists and is well-formed.

source_description: An earlier execution result that reports or claims that an output artifact was produced.

target_description: A subsequent action that independently checks the existence, content, size, or validity of that reported artifact.

### DECIDES_TASK_COMPLETION_FROM_VERIFIED_RESULTS

name: DECIDES_TASK_COMPLETION_FROM_VERIFIED_RESULTS

definition: Based on verified successful results for the required deliverables, the agent concludes that the task is complete and finalizes execution.

source_description: Verified execution results confirming that the required deliverables exist and behave correctly.

target_description: The agent's decision to mark the task as complete and terminate further execution.

### INVESTIGATES_FAILURE_CAUSE

name: INVESTIGATES_FAILURE_CAUSE

definition: A subsequent diagnostic action gathers information about the cause or environment of an earlier observed failure or blocker.

source_description: An earlier observed execution failure, error, or blocker.

target_description: A subsequent diagnostic action that inspects system state, constraints, or capabilities to determine the cause of that failure.

### DIAGNOSTIC_RESULT_GUIDES_REPAIR

name: DIAGNOSTIC_RESULT_GUIDES_REPAIR

definition: A diagnostic observation revealing an environmental constraint or incompatibility directs the selection of a specific corrective action.

source_description: A diagnostic observation that identifies a constraint, incompatibility, or capability gap.

target_description: A subsequent repair action selected to satisfy or work around that diagnostic finding.

### SUCCESSFUL_SETUP_ENABLES_SUBSEQUENT_USE

name: SUCCESSFUL_SETUP_ENABLES_SUBSEQUENT_USE

definition: A successful installation or environment-setup action makes a capability available that the agent subsequently relies on.

source_description: A successful setup or installation action result.

target_description: A subsequent action that uses the capability made available by that setup.

### VERIFIES_OUTCOME_OF_PREVIOUS_ACTION

name: VERIFIES_OUTCOME_OF_PREVIOUS_ACTION

definition: A subsequent agent action checks the completion status or result of an earlier action whose outcome is uncertain or asynchronous.

source_description: An earlier agent action whose outcome is uncertain, asynchronous, or needs confirmation.

target_description: A subsequent check or inspection that determines whether the earlier action completed or produced the expected result.

### CONFLICTING_RESULTS_TRIGGER_DISAMBIGUATING_ANALYSIS

name: CONFLICTING_RESULTS_TRIGGER_DISAMBIGUATING_ANALYSIS

definition: Multiple mutually inconsistent outputs produced by alternative methods applied to the same problem prompt the agent to perform additional targeted analysis to determine which result is correct.

source_description: A set of divergent or mutually inconsistent results produced by alternative methods or analyses of the same problem.

target_description: A follow-up analysis action designed to discriminate among the divergent results and select the correct one.

### REUSES_PRIOR_RESULT_AS_INPUT

name: REUSES_PRIOR_RESULT_AS_INPUT

definition: A result that was previously derived, evaluated, or selected is supplied as an input to a subsequent action.

source_description: An earlier derived, evaluated, or selected result such as a chosen structure or computed value.

target_description: A later action that consumes that earlier result as an input or parameter.

### USES_TEST_SPECIFICATION_TO_GUIDE_SOLUTION

name: USES_TEST_SPECIFICATION_TO_GUIDE_SOLUTION

definition: An agent examines an existing test harness or evaluation specification to understand how success is measured, and uses that understanding to direct or constrain subsequent solution construction.

source_description: An observation or analysis of a test harness, evaluation script, or acceptance criteria.

target_description: A subsequent agent plan or action aimed at satisfying the identified success criteria.

### CONFIRMS_PROPOSED_MECHANISM

name: CONFIRMS_PROPOSED_MECHANISM

definition: An observed result of an experiment performed to evaluate a proposed mechanism provides evidence that the mechanism behaves as hypothesized, validating the mechanism for subsequent adoption.

source_description: An experiment or probe execution performed by the agent to evaluate a proposed mechanism, approach, or prediction.

target_description: An observed execution result that provides evidence supporting the expected behavior of the proposed mechanism.

### RESPONDS_TO_FAILED_ATTEMPT_WITH_ALTERNATIVE

name: RESPONDS_TO_FAILED_ATTEMPT_WITH_ALTERNATIVE

definition: After an execution attempt fails to accomplish its intended goal (no effect, error, or unavailable tool or module), the agent selects a different action to accomplish the same goal by an alternative mechanism, rather than fixing the condition that caused the failure.

source_description: An execution attempt that failed to accomplish its intended goal or produced no usable result.

target_description: An alternative agent action intended to accomplish the same goal by a different mechanism.

### RESPONDS_TO_CONFIRMATION_REQUEST

name: RESPONDS_TO_CONFIRMATION_REQUEST

definition: A subsequent agent action provides the explicit confirmation demanded by a tool observation that refused to execute a final, irreversible, or high-impact operation until the agent reconfirmed its intent.

source_description: A tool observation that prompts for confirmation before executing a final or high-impact operation instead of carrying it out.

target_description: A subsequent agent action that confirms the operation, typically by re-issuing the original tool call with explicit confirmation.

### REAFFIRMS_PRIOR_CONCLUSION

name: REAFFIRMS_PRIOR_CONCLUSION

definition: A later agent reasoning step restates a conclusion or justification that was already established by an earlier reasoning step, without adding new evidence or changing the conclusion.

source_description: An earlier agent thought or analysis that states a conclusion or justification.

target_description: A subsequent agent thought or analysis that repeats the same conclusion or justification.

### PROBES_ENVIRONMENT_FOR_PREREQUISITES

name: PROBES_ENVIRONMENT_FOR_PREREQUISITES

definition: An agent action inspects the runtime environment to determine whether the tools, libraries, or versions required for a planned or in-progress task step are available.

source_description: A planned or in-progress task step whose execution depends on external prerequisites such as tools, libraries, or specific versions.

target_description: A diagnostic action that reports the presence, versions, or availability status of those prerequisites.

### SCANS_SOURCE_FOR_INCOMPATIBLE_USAGE

name: SCANS_SOURCE_FOR_INCOMPATIBLE_USAGE

definition: An agent action systematically searches the source tree to enumerate code locations that use patterns known to be deprecated, removed, or otherwise incompatible with the constraints of the current environment.

source_description: An observation establishing a compatibility constraint or requirement, such as a required dependency version or target runtime present in the environment.

target_description: A search action that enumerates candidate source locations requiring modification to satisfy that constraint.

### INSPECTS_BUILD_CONFIGURATION

name: INSPECTS_BUILD_CONFIGURATION

definition: An agent action reads a build or packaging configuration artifact to determine the components, extensions, or dependencies that the build or installation process must handle.

source_description: A task step that requires building, compiling, or installing a package from source.

target_description: An inspection of the build or packaging configuration that defines the required components, extensions, or dependencies.

### VERIFIES_REPAIR_SUCCESS

name: VERIFIES_REPAIR_SUCCESS

definition: After a corrective action modifies, rebuilds, or reinstalls an artifact to resolve an earlier observed failure, a subsequent agent action re-executes the previously failing operation to determine whether the correction actually resolved that failure.

source_description: A corrective agent action that modified, rebuilt, or reinstalled an artifact in an attempt to resolve an earlier observed failure.

target_description: A subsequent re-execution of the previously failing operation or check, performed to confirm that the failure has been resolved.

### NON_FATAL_WARNINGS_ACCEPTED_WITHOUT_REPAIR

name: NON_FATAL_WARNINGS_ACCEPTED_WITHOUT_REPAIR

definition: Non-fatal warnings reported during an otherwise successful execution step are treated as non-blocking, and the agent continues the workflow without modifying anything to address those warnings.

source_description: An execution observation that reports warnings while indicating the step completed successfully.

target_description: A subsequent agent action that continues the workflow without attempting to resolve the reported warnings.

### USES_OBSERVED_RESOURCE_AS_INPUT

name: USES_OBSERVED_RESOURCE_AS_INPUT

definition: A subsequent agent action consumes, operates on, or passes as arguments resources or entities that were enumerated in an earlier observation of the environment.

source_description: An earlier observation that enumerates available resources, files, or other environment entities (e.g., a directory listing or inventory of identifiers).

target_description: A subsequent agent action that operates on, passes, or otherwise consumes those enumerated resources as inputs.

### CONFLICTING_FIELDS_TRIGGER_RULE_BASED_SELECTION

name: CONFLICTING_FIELDS_TRIGGER_RULE_BASED_SELECTION

definition: An observation of multiple differing candidate values for the same required field within a source document or record triggers the application of a specified precedence rule to select one value.

source_description: An observation showing multiple conflicting candidate values for the same required field in a document or record.

target_description: An agent decision that selects one of the conflicting values according to a predefined precedence rule.

### MISSING_REQUIRED_FIELD_TRIGGERS_DEFAULT_ASSIGNMENT

name: MISSING_REQUIRED_FIELD_TRIGGERS_DEFAULT_ASSIGNMENT

definition: An observation that a required field is absent from source content triggers the assignment of a task-specified default value, such as zero or an empty string.

source_description: An observation of source content that lacks a required field.

target_description: An agent decision assigning the specified default value to the missing field.

### DERIVES_DECISION_FROM_OBSERVATION

name: DERIVES_DECISION_FROM_OBSERVATION

definition: An agent derives an interpretation, classification, or status decision by reading the content returned in an earlier tool observation, such as extracted document text or command output.

source_description: An earlier tool observation whose content provides the raw evidence needed for interpretation.

target_description: The agent's subsequent decision, classification, or interpretation derived from that observed content.

### CLEANS_UP_INTERMEDIATE_ARTIFACTS

name: CLEANS_UP_INTERMEDIATE_ARTIFACTS

definition: After the primary deliverables have been produced, the agent removes temporary or intermediate resources that were created during earlier execution steps.

source_description: Intermediate resources or artifacts created during earlier execution steps and no longer needed once the main task is complete.

target_description: A cleanup action that deletes or disposes of those intermediate resources.

### SUCCESSFUL_PROBE_ENABLES_BROADER_APPLICATION

name: SUCCESSFUL_PROBE_ENABLES_BROADER_APPLICATION

definition: A subsequent agent action generalizes or scales up a method that an earlier, smaller-scale probe first confirmed to work, applying it across multiple inputs or a larger scope.

source_description: An earlier execution result confirming that a method or capability works on a single test input or small-scale probe.

target_description: A subsequent agent action that applies the same confirmed method across multiple inputs or at a larger scale.

### EXTRACTS_REQUIRED_DATA_FROM_RESOURCE

name: EXTRACTS_REQUIRED_DATA_FROM_RESOURCE

definition: An agent inspects a provided resource (such as a file supplied with the task) and derives from its content a specific piece of required data or component that is retained for subsequent task execution.

source_description: An agent action that inspects or reads a provided resource to obtain task-relevant content.

target_description: The specific required data or component extracted from that resource and retained for later use in the task.

### CONSULTS_ALTERNATE_REFERENCE_TO_RESOLVE_DATA_ANOMALY

name: CONSULTS_ALTERNATE_REFERENCE_TO_RESOLVE_DATA_ANOMALY

definition: After an observed data artifact is found to contain an ambiguous, incomplete, or invalid placeholder value, the agent queries an independent reference source to determine the correct value to use.

source_description: An earlier observed data artifact whose content contains an anomaly, placeholder, or unresolvable value.

target_description: A subsequent agent action that queries an independent reference source to resolve that anomaly and obtain the correct value.

### ASSEMBLES_GATHERED_COMPONENTS_INTO_COMPOSITE_ARTIFACT

name: ASSEMBLES_GATHERED_COMPONENTS_INTO_COMPOSITE_ARTIFACT

definition: The agent constructs a single composite output by combining, in a specified arrangement, multiple distinct components that were previously identified or collected during the run.

source_description: A set of separately gathered or identified components that must be combined into one output.

target_description: An agent action that combines those components into a single composite artifact.

### PROMPTS_FURTHER_INVESTIGATION

name: PROMPTS_FURTHER_INVESTIGATION

definition: An observation whose interpretation is ambiguous, whose structure is unclear, or which leaves the agent with insufficient understanding is followed by a subsequent investigative action that gathers additional diagnostic detail to resolve that ambiguity.

source_description: An earlier observation whose meaning, structure, or interpretation is unclear or incomplete.

target_description: A subsequent investigative action that probes the data or environment further to resolve the ambiguity.
