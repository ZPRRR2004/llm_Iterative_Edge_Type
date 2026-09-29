# 第 5 批 Edge Type Discovery 结果

## 一、批次信息

处理 Window：41–44
Prompt 版本：v0001
本批新增边类型：3
本批已有类型修订：0
当前边类型总数：19

## 二、本批新增边类型

### PROVISIONS_REQUIRED_TOOLING

name: PROVISIONS_REQUIRED_TOOLING

definition: An agent action installs or configures a tool, library, or runtime dependency that the agent's plan requires, thereby enabling a subsequent execution step that relies on the provisioned capability.

source_description: An agent action that installs or configures a tool, library, or dependency required by the agent's plan.

target_description: A subsequent agent execution step that relies on the provisioned tool, library, or dependency.

### REPLACES_STRATEGY_AFTER_DIAGNOSIS

name: REPLACES_STRATEGY_AFTER_DIAGNOSIS

definition: Diagnostic evidence explaining why the current method cannot succeed causes the agent to abandon that method and perform a subsequent action that implements a fundamentally different approach toward the same subgoal.

source_description: A diagnostic observation that reveals the root cause or limitation making the current method unsuitable for achieving the subgoal.

target_description: A subsequent agent action that implements a different strategy in place of the abandoned method to pursue the same subgoal.

### CONTINUES_INSPECTION_OF_PARTIALLY_VIEWED_RESULT

name: CONTINUES_INSPECTION_OF_PARTIALLY_VIEWED_RESULT

definition: After an earlier observation exposes only part of a produced result or a long output, a subsequent agent action retrieves or inspects the remaining, not-yet-examined portion of that same result in order to complete its examination.

source_description: An earlier observation that revealed only a subset of a produced result or long output, leaving the remainder unexamined.

target_description: A subsequent agent action that retrieves or inspects the remaining portion of the same result to continue its examination.

## 三、本批已有类型修订

本批没有修订已有边类型。

## 四、当前完整 Registry

### USES_PREVIOUS_RESULT_AS_INPUT

name: USES_PREVIOUS_RESULT_AS_INPUT

definition: A subsequent agent action, reasoning step, or produced artifact consumes a result, artifact, resource, reference, or observed format/constraint obtained from an earlier execution step as an input, dependency, conformance target, or basis for resolving an ambiguous value.

source_description: A result, artifact, resource, reference, or observed format/constraint obtained or produced by an earlier execution step.

target_description: A subsequent agent action, reasoning step, or produced artifact that uses that earlier result, artifact, resource, reference, or observed format as an input, dependency, conformance target, or basis for resolving an ambiguous value.

### PROBES_ENVIRONMENT_TO_INFORM_ACTION

name: PROBES_ENVIRONMENT_TO_INFORM_ACTION

definition: The agent obtains information about its execution environment, a reference artifact or implementation, or its own state, including by reading files, listing resources, supplying controlled probes, establishing a reference oracle, or re-examining the environment after expressing completion intent, and the resulting information informs subsequent reasoning, design, validation, or action.

source_description: An inspection, probe, controlled experiment, reference implementation execution, or diagnostic re-examination whose outcome reveals relevant state, behavior, specification, reference result, or overlooked condition.

target_description: A subsequent agent step, reasoning/design decision, validation action, or retained reference behavior/state that is selected, configured, or used based on the probe's outcome.

### VERIFIES_PREVIOUS_RESULT

name: VERIFIES_PREVIOUS_RESULT

definition: A subsequent agent action or reasoning step checks, re-executes, confirms, or monitors an earlier result, artifact, claim, state change, corrective action, or verified conclusion attributed to a previous execution step in order to confirm, refute, re-establish, or further exercise its outcome.

source_description: An earlier result, artifact, claim, state change, corrective action, launched asynchronous operation, or verified conclusion attributed to an execution step.

target_description: A subsequent independent check, status inspection, re-execution, or restatement that confirms, refutes, monitors, or further exercises that earlier result, artifact, claim, state change, action, operation, or conclusion.

### TRIGGERS_TASK_COMPLETION

name: TRIGGERS_TASK_COMPLETION

definition: A verified satisfactory execution outcome leads the agent to conclude that the task is complete and to mark it as finished.

source_description: A verified positive execution outcome, such as all checks passing and required deliverables being confirmed present.

target_description: The agent's decision to mark the task as complete.

### PRESERVES_STATE_BEFORE_MUTATION

name: PRESERVES_STATE_BEFORE_MUTATION

definition: An agent action creates a backup or snapshot copy of persistent or input state in a safe location before a subsequent operation that is expected to modify, overwrite, or consume that state, so that the original state can later be restored or compared against.

source_description: An agent action that copies or snapshots existing state (e.g., a data directory or an input file) to a separate location.

target_description: A subsequent operation that is expected to modify or consume that same state.

### RESOLVES_BLOCKING_CONDITION

name: RESOLVES_BLOCKING_CONDITION

definition: An earlier observed blocking condition, such as a failure, error, missing prerequisite, or incomplete setup, is followed by a subsequent agent action that attempts to resolve, satisfy, or remedy that condition to enable or proceed with the task.

source_description: An earlier observed blocking condition, such as a failure, error, defect, missing prerequisite, or incomplete setup.

target_description: A subsequent agent action intended to resolve, satisfy, or remedy that blocking condition.

### INVESTIGATES_ISSUE_OR_UNCERTAINTY

name: INVESTIGATES_ISSUE_OR_UNCERTAINTY

definition: A subsequent agent action or reasoning step inspects, searches, or reasons over diagnostic output, raw evidence, or related environment/state evidence produced by or associated with an earlier observed problem, such as a failure, error, discrepancy, blocked verification, or ambiguity/uncertainty, in order to determine its underlying cause or resolve the uncertainty.

source_description: An earlier observed problem, such as a failure, error, discrepancy, blocked verification, or ambiguity/uncertainty, whose diagnostic output or related environment/state evidence is available.

target_description: A subsequent agent diagnostic action or reasoning step that examines the problem's diagnostic output, raw evidence, or related environment state to identify its cause, missing prerequisite, or resolution of the uncertainty.

### IMPLEMENTS_PLANNED_ACTION

name: IMPLEMENTS_PLANNED_ACTION

definition: A tool call executes an action that the agent specified as intended in its immediately preceding plan or decision.

source_description: An agent reasoning step that states a plan or an intended action to be taken.

target_description: A subsequent tool call that carries out the planned action.

### ACTION_TRIGGERS_CONFIRMATION_REQUEST

name: ACTION_TRIGGERS_CONFIRMATION_REQUEST

definition: An agent action that the environment regards as requiring explicit confirmation causes the environment to return an observation requesting confirmation before the action is finalized.

source_description: An agent tool call or action whose finalization the environment gates behind explicit confirmation.

target_description: The resulting environment observation that requests the agent to confirm or repeat the prior action.

### RESPONDS_TO_CONFIRMATION_REQUEST

name: RESPONDS_TO_CONFIRMATION_REQUEST

definition: In direct response to an environment confirmation request, the agent issues a subsequent tool call that confirms or repeats the gated action.

source_description: An environment observation that requests confirmation of a previous agent action.

target_description: A tool call that repeats or confirms the prior action in order to satisfy the confirmation request.

### DERIVES_INFORMATION_FROM_OBSERVED_CONTENT

name: DERIVES_INFORMATION_FROM_OBSERVED_CONTENT

definition: An agent derives semantic or structured information, such as a category label, a field value, a selected value among conflicting candidates, or specific code locations/constructs requiring modification, from the content of an item observed in an earlier reading, extraction, diagnostic search, static-analysis, or codebase-scanning step.

source_description: An observation or diagnostic output containing the content of an item, multiple conflicting candidate values, or search/analysis results from an earlier reading, extraction, or scanning step.

target_description: The category label, structured attribute value, selected value, or specific code locations/constructs derived by the agent from that observed content or diagnostic output.

### CLEANS_UP_OR_RESTORES_STATE

name: CLEANS_UP_OR_RESTORES_STATE

definition: A subsequent agent action removes temporary or intermediate resources, or reverts unwanted state changes, to restore a clean or required state, either after task completion or before continuing a workflow.

source_description: An earlier action that produced temporary or unwanted state changes, or a point at which the primary task objectives are complete.

target_description: A subsequent agent action that cleans up or reverts those state changes to restore a clean or required state.

### EVALUATES_CANDIDATES_AGAINST_CRITERIA

name: EVALUATES_CANDIDATES_AGAINST_CRITERIA

definition: A subsequent agent action evaluates candidate alternatives or interpretations against a quantitative criterion or a known expected outcome/success constraint, and selects the satisfying or best-scoring candidate to carry forward or produce the required output artifact.

source_description: A known expected result, success criterion, or evaluation step that constrains or scores a set of candidate alternatives.

target_description: The satisfying or best-scoring candidate alternative or the agent action that selects it and produces the required output artifact.

### PROBES_ALTERNATIVE_RESOURCES_AFTER_FAILURE

name: PROBES_ALTERNATIVE_RESOURCES_AFTER_FAILURE

definition: After an attempt to access a specific resource fails, a subsequent agent action attempts to obtain the needed resource by trying alternative candidate resources, locations, or identifiers instead of remedying the failed one.

source_description: An observation reporting that a prior attempt to access a specific resource failed, such as a not-found, forbidden, or otherwise unsuccessful access response.

target_description: A subsequent agent action that tries alternative candidate resources, locations, or identifiers in order to obtain the needed resource.

### MONITORS_LONG_RUNNING_OPERATION

name: MONITORS_LONG_RUNNING_OPERATION

definition: An agent monitors a previously initiated long-running operation, such that an earlier operation state, progress observation, or monitoring action is followed by a subsequent monitoring action, progress observation, or reasoning step that checks, waits for, interprets, or estimates the operation's progress, state, liveness, or completion.

source_description: An earlier initiated long-running operation, or a prior observation, monitoring action, or progress estimate concerning its progress, state, liveness, or completion.

target_description: A subsequent monitoring action, progress observation, or reasoning step that checks, waits for, interprets, or estimates the progress, state, liveness, or completion of that operation.

### EXTENDS_VERIFICATION_FOR_IDENTIFIED_RISK

name: EXTENDS_VERIFICATION_FOR_IDENTIFIED_RISK

definition: An identified untested edge case, coverage gap, or potential failure mode in the current solution prompts the agent to construct and run an additional verification that specifically targets that previously uncovered scenario.

source_description: An agent reasoning step identifying an untested edge case, coverage gap, or potential failure mode in the current solution.

target_description: A newly constructed verification action designed to exercise and check that previously uncovered scenario.

### PROVISIONS_REQUIRED_TOOLING

name: PROVISIONS_REQUIRED_TOOLING

definition: An agent action installs or configures a tool, library, or runtime dependency that the agent's plan requires, thereby enabling a subsequent execution step that relies on the provisioned capability.

source_description: An agent action that installs or configures a tool, library, or dependency required by the agent's plan.

target_description: A subsequent agent execution step that relies on the provisioned tool, library, or dependency.

### REPLACES_STRATEGY_AFTER_DIAGNOSIS

name: REPLACES_STRATEGY_AFTER_DIAGNOSIS

definition: Diagnostic evidence explaining why the current method cannot succeed causes the agent to abandon that method and perform a subsequent action that implements a fundamentally different approach toward the same subgoal.

source_description: A diagnostic observation that reveals the root cause or limitation making the current method unsuitable for achieving the subgoal.

target_description: A subsequent agent action that implements a different strategy in place of the abandoned method to pursue the same subgoal.

### CONTINUES_INSPECTION_OF_PARTIALLY_VIEWED_RESULT

name: CONTINUES_INSPECTION_OF_PARTIALLY_VIEWED_RESULT

definition: After an earlier observation exposes only part of a produced result or a long output, a subsequent agent action retrieves or inspects the remaining, not-yet-examined portion of that same result in order to complete its examination.

source_description: An earlier observation that revealed only a subset of a produced result or long output, leaving the remainder unexamined.

target_description: A subsequent agent action that retrieves or inspects the remaining portion of the same result to continue its examination.
