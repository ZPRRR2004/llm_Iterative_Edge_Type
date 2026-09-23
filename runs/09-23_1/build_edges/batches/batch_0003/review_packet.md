# 第 3 批 Edge Type Discovery 结果

## 一、批次信息

处理 Window：21–21
Prompt 版本：v0001
本批新增边类型：0
本批已有类型修订：0
当前边类型总数：7

## 二、本批新增边类型

本批没有接受新的边类型。

## 三、本批已有类型修订

本批没有修订已有边类型。

## 四、当前完整 Registry

### USES_PRIOR_RESULT_TO_GUIDE_ACTION

name: USES_PRIOR_RESULT_TO_GUIDE_ACTION

definition: A subsequent agent action, decision, or derived result uses a prior result, observation, plan, or confirmed evidence produced or observed during earlier execution as an input, basis, or justification.

source_description: A prior result, artifact, observation, plan, or confirmed finding produced or observed during earlier execution.

target_description: A subsequent agent action, decision, or derived result that consumes, applies, or is based on that prior result.

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or unmet prerequisite identified during an earlier execution step, for example by retrying with a revised artifact or alternative approach, or by installing or otherwise providing a missing component.

source_description: An earlier observed execution failure or a prerequisite reported as missing or unavailable.

target_description: A subsequent agent action intended to resolve that failure or unmet prerequisite.

### VERIFIES_OUTCOME_OR_PREREQUISITE

name: VERIFIES_OUTCOME_OR_PREREQUISITE

definition: A subsequent agent action independently checks, validates, or confirms whether a previously produced artifact, repaired state, candidate, derived output, or identified prerequisite satisfies its intended requirement, exists, or is available.

source_description: A prior agent action or state that produced, identified, or repaired an artifact, candidate, output, or prerequisite whose status, correctness, or fidelity must be confirmed.

target_description: A subsequent verification or validation action that inspects, executes, probes, compares, or otherwise checks that prior artifact, candidate, output, repair, or prerequisite.

### COMPLETES_TASK_AFTER_VERIFICATION

name: COMPLETES_TASK_AFTER_VERIFICATION

definition: The agent concludes the task, either by declaring completion or by reasoning that cites successful verification evidence, after execution results have been verified as satisfying the task requirements.

source_description: Successful verification, test, or execution results confirming that the task objective or requirements have been met.

target_description: A task-completion declaration or completion reasoning that ends the workflow.

### MONITORS_OR_WAITS_FOR_ASYNCHRONOUS_OPERATION

name: MONITORS_OR_WAITS_FOR_ASYNCHRONOUS_OPERATION

definition: A long-running or asynchronous operation launched earlier by the agent is subsequently monitored or waited for by a separate action that inspects its output or log, or pauses or polls until it has finished, to determine progress or outcome.

source_description: An agent action that launches a long-running or asynchronous operation in the background without waiting for it to finish.

target_description: A subsequent action that inspects the launched operation's output or log, or pauses or polls until it has finished, to determine progress or outcome.

### INVESTIGATES_OR_RESOLVES_PROBLEMATIC_OBSERVATION

name: INVESTIGATES_OR_RESOLVES_PROBLEMATIC_OBSERVATION

definition: A subsequent agent action investigates, diagnoses, disambiguates, retrieves missing content for, or otherwise resolves an earlier observation that is problematic due to failure, error, unexpected result, ambiguity, incompleteness, or conflicting values, in order to understand it or determine the next step.

source_description: An earlier observation that is problematic, such as a failure, error, unexpected or incompatible result, ambiguous or incomplete content, or conflicting candidate values.

target_description: A subsequent diagnostic, investigative, information-gathering, or resolution action intended to understand, clarify, disambiguate, complete, or resolve that observation.

### CLEANS_UP_TEMPORARY_RESOURCES

name: CLEANS_UP_TEMPORARY_RESOURCES

definition: After the main task objective has been achieved and its outcome confirmed, a subsequent agent action removes temporary or intermediate resources that were created during execution and are no longer needed.

source_description: A state or confirmation indicating that the main task objective has been completed.

target_description: A subsequent cleanup action that deletes temporary or intermediate resources created during execution.
