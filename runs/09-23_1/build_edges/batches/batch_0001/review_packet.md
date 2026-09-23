# 第 1 批 Edge Type Discovery 结果

## 一、批次信息

处理 Window：1–10
Prompt 版本：v0001
本批新增边类型：23
本批已有类型修订：3
当前边类型总数：23

## 二、本批新增边类型

### USES_PREVIOUSLY_PRODUCED_ARTIFACT_AS_INPUT

name: USES_PREVIOUSLY_PRODUCED_ARTIFACT_AS_INPUT

definition: A later agent action consumes an artifact that was produced by an earlier agent action, using that previously produced artifact as an input, for example by loading, sourcing, or executing a file or module created earlier.

source_description: An agent action that creates or produces an artifact, such as writing a source file to disk.

target_description: A later agent action that loads, sources, executes, or otherwise consumes the previously produced artifact as an input.

### EXECUTION_BLOCKED_BY_PREVIOUSLY_OBSERVED_MISSING_DEPENDENCY

name: EXECUTION_BLOCKED_BY_PREVIOUSLY_OBSERVED_MISSING_DEPENDENCY

definition: A subsequent agent action is attempted even though an earlier observation already reported that a required tool, interpreter, or dependency is unavailable, and the action consequently fails on account of that missing dependency.

source_description: An observation reporting that a required tool, interpreter, or dependency is missing or unavailable in the environment.

target_description: A later agent action that requires the missing dependency and fails because of it, for example with a command-not-found error.

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure identified during an earlier execution step, for example by installing or otherwise providing a missing prerequisite so that the failed step can be retried successfully.

source_description: An earlier observed execution failure caused by a missing or unavailable prerequisite.

target_description: A subsequent agent action intended to resolve that failure.

### PLANNED_CONTINGENCY_CONFIRMED_BY_OBSERVATION

name: PLANNED_CONTINGENCY_CONFIRMED_BY_OBSERVATION

definition: An agent's plan states a contingency or explicit expectation about a possible execution condition, and a later observation confirms that the anticipated condition holds, so the planned contingency applies.

source_description: An agent plan or reasoning step that states a contingency or expectation about a possible execution condition.

target_description: A subsequent observation or execution result that confirms the anticipated condition actually holds.

### INVESTIGATES_BEFORE_REMEDIATION

name: INVESTIGATES_BEFORE_REMEDIATION

definition: An agent action gathers information about the execution environment in order to determine how to address a previously observed failure or unmet prerequisite.

source_description: A previously observed execution failure or unmet prerequisite that must be addressed.

target_description: A subsequent information-gathering action performed to select an appropriate remediation strategy.

### VERIFIES_PRODUCED_ARTIFACT

name: VERIFIES_PRODUCED_ARTIFACT

definition: A subsequent agent action independently inspects the existence or content of an artifact that an earlier agent action produced or reported producing, in order to confirm the reported result.

source_description: An earlier agent action that produced or reported creating an artifact or output.

target_description: A later action that independently inspects or validates the existence and content of that artifact.

### TERMINATES_WORKFLOW_AFTER_VERIFIED_SUCCESS

name: TERMINATES_WORKFLOW_AFTER_VERIFIED_SUCCESS

definition: The agent declares the task complete after execution results have been verified as satisfying all task requirements.

source_description: Verified successful execution results that confirm the task requirements are satisfied.

target_description: A task-completion declaration that ends the workflow.

### RESPONDS_TO_CONFIRMATION_PROMPT

name: RESPONDS_TO_CONFIRMATION_PROMPT

definition: An agent action repeats or reaffirms a previously issued decision in response to an explicit confirmation request emitted by the environment.

source_description: A confirmation request emitted by the environment in response to an earlier agent action.

target_description: A repeated agent action that reaffirms the earlier decision.

### SELECTS_ALTERNATIVE_APPROACH

name: SELECTS_ALTERNATIVE_APPROACH

definition: After an earlier intended approach or tool is observed to be blocked, unavailable, or otherwise infeasible in the environment, the agent abandons that approach and adopts a different tool or strategy to pursue the same overall goal.

source_description: An observation that an earlier intended approach or tool is blocked, unavailable, or otherwise infeasible in the environment.

target_description: A subsequent agent action that employs an alternative tool or strategy in place of the abandoned approach.

### CAPABILITY_PROBE_INFORMS_TOOL_SELECTION

name: CAPABILITY_PROBE_INFORMS_TOOL_SELECTION

definition: The result of an environment or tooling probe is used to determine which available capability or tool should be applied in a subsequent action.

source_description: An observation reporting the availability or configuration of environment capabilities, such as present interpreters, installed packages, or tool versions.

target_description: A subsequent agent action that leverages a capability revealed by that probe to carry out the task.

### MONITORS_ASYNCHRONOUS_OPERATION

name: MONITORS_ASYNCHRONOUS_OPERATION

definition: A long-running operation that an earlier action launched in the background without waiting for completion is subsequently monitored by a separate action that inspects its output or log to determine progress or outcome.

source_description: An agent action that launches a long-running operation in the background without waiting for it to finish.

target_description: A subsequent action that inspects the launched operation's output or log file to determine whether it has completed and with what result.

### RESOLVES_AMBIGUITY_IN_PRIOR_RESULT

name: RESOLVES_AMBIGUITY_IN_PRIOR_RESULT

definition: A subsequent analytical or diagnostic step is performed to investigate and disambiguate an earlier result that is ambiguous, conflicting, or inconsistent with known constraints, in order to determine which interpretation or outcome is correct.

source_description: An earlier agent result that is ambiguous, conflicting, or inconsistent with known constraints (for example, multiple analysis methods yielding different structures).

target_description: A subsequent analytical or diagnostic step performed to disambiguate or investigate that earlier result.

### SELECTS_CANDIDATE_BASED_ON_EVALUATION

name: SELECTS_CANDIDATE_BASED_ON_EVALUATION

definition: The agent selects one among several competing candidate solutions, structures, or configurations on the basis of comparative evaluation evidence, such as scores or test outcomes, produced during earlier steps.

source_description: Comparative evaluation evidence, such as scores, metrics, or statistical test outcomes, that distinguishes competing candidates.

target_description: The candidate solution, structure, or configuration selected on the basis of that comparative evaluation evidence.

### DERIVES_BYPASS_FROM_IMPLEMENTATION_OBSERVATION

name: DERIVES_BYPASS_FROM_IMPLEMENTATION_OBSERVATION

definition: An agent uses observed details of a mechanism's implementation to construct an action that exploits a discrepancy between that mechanism's behavior and the behavior of the system the mechanism is intended to model.

source_description: An observation that reveals the implementation details or parsing behavior of a mechanism, such as the source code of a filter or checker.

target_description: A subsequent agent action that constructs an artifact designed to pass or bypass that mechanism by exploiting the observed discrepancy.

### VALIDATES_CANDIDATE_AGAINST_TRANSFORMATION

name: VALIDATES_CANDIDATE_AGAINST_TRANSFORMATION

definition: An agent subjects a candidate artifact it produced to the transformation the candidate must survive, and inspects the resulting output to judge whether the candidate retained the required property.

source_description: A candidate artifact produced by the agent, such as a crafted payload written to a file.

target_description: An execution that applies the transformation to the candidate, whose resulting output is inspected to judge whether the candidate survived.

### DIAGNOSES_FAILURE_CAUSE

name: DIAGNOSES_FAILURE_CAUSE

definition: An agent's reasoning examines an observed failing execution result to identify why it failed and to derive constraints that a subsequent attempt must satisfy.

source_description: An observed execution result that failed to meet the objective, such as a candidate artifact whose required property was removed or altered.

target_description: Agent reasoning that identifies the cause of the failure and articulates the constraints for the next attempt.

### USES_CONFIRMED_RESULT_TO_APPLY_SOLUTION

name: USES_CONFIRMED_RESULT_TO_APPLY_SOLUTION

definition: An observation from an exploratory execution that empirically confirms a candidate technique or artifact achieves the desired effect is used as the basis for applying that confirmed technique to construct or deploy the final solution.

source_description: An earlier exploratory execution observation confirming that a candidate technique or artifact actually produces the desired effect.

target_description: A subsequent agent action that applies the confirmed technique to construct or deploy the final solution artifact.

### USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

name: USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

definition: A diagnostic conclusion identifying the cause of an earlier failure determines the specific corrective action the agent takes next in order to address that cause.

source_description: A diagnostic analysis identifying the root cause of an earlier failure.

target_description: A subsequent repair action selected to address the identified root cause.

### JUSTIFIES_TASK_COMPLETION_WITH_VERIFICATION_EVIDENCE

name: JUSTIFIES_TASK_COMPLETION_WITH_VERIFICATION_EVIDENCE

definition: An agent's completion reasoning cites a successful verification or test result as evidence that the task requirements have been satisfied, grounding its decision to finish the task.

source_description: A successful verification or test result confirming that the task objective has been met.

target_description: The agent's reasoning that cites that verification result as justification for completing the task.

### EXPLAINS_MECHANISM_OF_VERIFIED_SOLUTION

name: EXPLAINS_MECHANISM_OF_VERIFIED_SOLUTION

definition: An agent's reasoning explains the technical mechanism by which a previously produced solution artifact achieves its required effect, for example why the artifact survives a filter or triggers a desired behavior.

source_description: A solution artifact produced by the agent that achieves the required effect.

target_description: The agent's explanatory reasoning describing why that artifact works or how it achieves its required effect.

### VERIFIES_PREREQUISITE_AVAILABILITY

name: VERIFIES_PREREQUISITE_AVAILABILITY

definition: A subsequent agent action probes the environment to check whether a required dependency, build tool, or other prerequisite identified during an earlier configuration inspection is actually available, before proceeding with work that depends on it.

source_description: An earlier observation of build or project configuration that identifies a required dependency, build tool, or other prerequisite.

target_description: A subsequent probe action that checks whether that previously identified prerequisite is present or available in the environment.

### SEARCHES_CODEBASE_FOR_CONSTRAINT_VIOLATIONS

name: SEARCHES_CODEBASE_FOR_CONSTRAINT_VIOLATIONS

definition: An agent action scans project sources to locate code that may violate a compatibility or environment constraint established by earlier configuration or version inspection, without requiring an observed failure.

source_description: An environment or compatibility constraint established by earlier configuration, version, or dependency inspection.

target_description: A subsequent codebase-wide search or inspection action that locates source locations potentially violating that constraint.

### VERIFIES_PRIOR_REPAIR

name: VERIFIES_PRIOR_REPAIR

definition: A subsequent agent action independently checks whether an earlier corrective action (such as a code modification, dependency installation, or rebuild) actually achieved its intended effect, for example by re-running a scan to confirm problematic patterns are gone or by executing an end-to-end usage snippet or test suite after the repair.

source_description: An earlier corrective or repair action, or a modification it produced, whose effectiveness is in question.

target_description: A subsequent verification action that checks whether the earlier repair achieved its intended effect.

## 三、本批已有类型修订

### ATTEMPTS_TO_REPAIR → ATTEMPTS_TO_REPAIR

Window：trajectory1__window_0002

修订前：

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure identified during an earlier execution step, for example by installing or otherwise providing a missing prerequisite so that the failed step can be retried successfully.

source_description: An earlier observed execution failure caused by a missing or unavailable prerequisite.

target_description: A subsequent agent action intended to resolve that failure.

修订后：

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or unmet prerequisite identified during an earlier execution step, for example by installing or otherwise providing the missing component so that the failed step can be retried successfully.

source_description: An earlier observed execution failure or a prerequisite reported as missing or unavailable.

target_description: A subsequent agent action intended to resolve that failure.

### ATTEMPTS_TO_REPAIR → ATTEMPTS_TO_REPAIR

Window：trajectory3__window_0001

修订前：

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or unmet prerequisite identified during an earlier execution step, for example by installing or otherwise providing the missing component so that the failed step can be retried successfully.

source_description: An earlier observed execution failure or a prerequisite reported as missing or unavailable.

target_description: A subsequent agent action intended to resolve that failure.

修订后：

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or unmet prerequisite identified during an earlier execution step, for example by retrying with a revised artifact or alternative approach, or by installing or otherwise providing a missing component.

source_description: An earlier observed execution failure or a prerequisite reported as missing or unavailable.

target_description: A subsequent agent action intended to resolve that failure or unmet prerequisite.

### USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION → USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

Window：trajectory4__window_0002

修订前：

### USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

name: USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

definition: A diagnostic conclusion identifying the cause of an earlier failure determines the specific corrective action the agent takes next in order to address that cause.

source_description: A diagnostic analysis identifying the root cause of an earlier failure.

target_description: A subsequent repair action selected to address the identified root cause.

修订后：

### USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

name: USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

definition: A diagnostic result — whether the analysis of an earlier failure's cause or the output of a code search or inspection that reveals a problem or incompatibility — determines the specific corrective action the agent takes next in order to address the issue it identified.

source_description: A diagnostic result identifying a problem or its cause, such as a failure-cause analysis or a code search or inspection finding of incompatible or problematic patterns.

target_description: A subsequent corrective action selected to address the problem identified by that diagnostic result.

## 四、当前完整 Registry

### USES_PREVIOUSLY_PRODUCED_ARTIFACT_AS_INPUT

name: USES_PREVIOUSLY_PRODUCED_ARTIFACT_AS_INPUT

definition: A later agent action consumes an artifact that was produced by an earlier agent action, using that previously produced artifact as an input, for example by loading, sourcing, or executing a file or module created earlier.

source_description: An agent action that creates or produces an artifact, such as writing a source file to disk.

target_description: A later agent action that loads, sources, executes, or otherwise consumes the previously produced artifact as an input.

### EXECUTION_BLOCKED_BY_PREVIOUSLY_OBSERVED_MISSING_DEPENDENCY

name: EXECUTION_BLOCKED_BY_PREVIOUSLY_OBSERVED_MISSING_DEPENDENCY

definition: A subsequent agent action is attempted even though an earlier observation already reported that a required tool, interpreter, or dependency is unavailable, and the action consequently fails on account of that missing dependency.

source_description: An observation reporting that a required tool, interpreter, or dependency is missing or unavailable in the environment.

target_description: A later agent action that requires the missing dependency and fails because of it, for example with a command-not-found error.

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or unmet prerequisite identified during an earlier execution step, for example by retrying with a revised artifact or alternative approach, or by installing or otherwise providing a missing component.

source_description: An earlier observed execution failure or a prerequisite reported as missing or unavailable.

target_description: A subsequent agent action intended to resolve that failure or unmet prerequisite.

### PLANNED_CONTINGENCY_CONFIRMED_BY_OBSERVATION

name: PLANNED_CONTINGENCY_CONFIRMED_BY_OBSERVATION

definition: An agent's plan states a contingency or explicit expectation about a possible execution condition, and a later observation confirms that the anticipated condition holds, so the planned contingency applies.

source_description: An agent plan or reasoning step that states a contingency or expectation about a possible execution condition.

target_description: A subsequent observation or execution result that confirms the anticipated condition actually holds.

### INVESTIGATES_BEFORE_REMEDIATION

name: INVESTIGATES_BEFORE_REMEDIATION

definition: An agent action gathers information about the execution environment in order to determine how to address a previously observed failure or unmet prerequisite.

source_description: A previously observed execution failure or unmet prerequisite that must be addressed.

target_description: A subsequent information-gathering action performed to select an appropriate remediation strategy.

### VERIFIES_PRODUCED_ARTIFACT

name: VERIFIES_PRODUCED_ARTIFACT

definition: A subsequent agent action independently inspects the existence or content of an artifact that an earlier agent action produced or reported producing, in order to confirm the reported result.

source_description: An earlier agent action that produced or reported creating an artifact or output.

target_description: A later action that independently inspects or validates the existence and content of that artifact.

### TERMINATES_WORKFLOW_AFTER_VERIFIED_SUCCESS

name: TERMINATES_WORKFLOW_AFTER_VERIFIED_SUCCESS

definition: The agent declares the task complete after execution results have been verified as satisfying all task requirements.

source_description: Verified successful execution results that confirm the task requirements are satisfied.

target_description: A task-completion declaration that ends the workflow.

### RESPONDS_TO_CONFIRMATION_PROMPT

name: RESPONDS_TO_CONFIRMATION_PROMPT

definition: An agent action repeats or reaffirms a previously issued decision in response to an explicit confirmation request emitted by the environment.

source_description: A confirmation request emitted by the environment in response to an earlier agent action.

target_description: A repeated agent action that reaffirms the earlier decision.

### SELECTS_ALTERNATIVE_APPROACH

name: SELECTS_ALTERNATIVE_APPROACH

definition: After an earlier intended approach or tool is observed to be blocked, unavailable, or otherwise infeasible in the environment, the agent abandons that approach and adopts a different tool or strategy to pursue the same overall goal.

source_description: An observation that an earlier intended approach or tool is blocked, unavailable, or otherwise infeasible in the environment.

target_description: A subsequent agent action that employs an alternative tool or strategy in place of the abandoned approach.

### CAPABILITY_PROBE_INFORMS_TOOL_SELECTION

name: CAPABILITY_PROBE_INFORMS_TOOL_SELECTION

definition: The result of an environment or tooling probe is used to determine which available capability or tool should be applied in a subsequent action.

source_description: An observation reporting the availability or configuration of environment capabilities, such as present interpreters, installed packages, or tool versions.

target_description: A subsequent agent action that leverages a capability revealed by that probe to carry out the task.

### MONITORS_ASYNCHRONOUS_OPERATION

name: MONITORS_ASYNCHRONOUS_OPERATION

definition: A long-running operation that an earlier action launched in the background without waiting for completion is subsequently monitored by a separate action that inspects its output or log to determine progress or outcome.

source_description: An agent action that launches a long-running operation in the background without waiting for it to finish.

target_description: A subsequent action that inspects the launched operation's output or log file to determine whether it has completed and with what result.

### RESOLVES_AMBIGUITY_IN_PRIOR_RESULT

name: RESOLVES_AMBIGUITY_IN_PRIOR_RESULT

definition: A subsequent analytical or diagnostic step is performed to investigate and disambiguate an earlier result that is ambiguous, conflicting, or inconsistent with known constraints, in order to determine which interpretation or outcome is correct.

source_description: An earlier agent result that is ambiguous, conflicting, or inconsistent with known constraints (for example, multiple analysis methods yielding different structures).

target_description: A subsequent analytical or diagnostic step performed to disambiguate or investigate that earlier result.

### SELECTS_CANDIDATE_BASED_ON_EVALUATION

name: SELECTS_CANDIDATE_BASED_ON_EVALUATION

definition: The agent selects one among several competing candidate solutions, structures, or configurations on the basis of comparative evaluation evidence, such as scores or test outcomes, produced during earlier steps.

source_description: Comparative evaluation evidence, such as scores, metrics, or statistical test outcomes, that distinguishes competing candidates.

target_description: The candidate solution, structure, or configuration selected on the basis of that comparative evaluation evidence.

### DERIVES_BYPASS_FROM_IMPLEMENTATION_OBSERVATION

name: DERIVES_BYPASS_FROM_IMPLEMENTATION_OBSERVATION

definition: An agent uses observed details of a mechanism's implementation to construct an action that exploits a discrepancy between that mechanism's behavior and the behavior of the system the mechanism is intended to model.

source_description: An observation that reveals the implementation details or parsing behavior of a mechanism, such as the source code of a filter or checker.

target_description: A subsequent agent action that constructs an artifact designed to pass or bypass that mechanism by exploiting the observed discrepancy.

### VALIDATES_CANDIDATE_AGAINST_TRANSFORMATION

name: VALIDATES_CANDIDATE_AGAINST_TRANSFORMATION

definition: An agent subjects a candidate artifact it produced to the transformation the candidate must survive, and inspects the resulting output to judge whether the candidate retained the required property.

source_description: A candidate artifact produced by the agent, such as a crafted payload written to a file.

target_description: An execution that applies the transformation to the candidate, whose resulting output is inspected to judge whether the candidate survived.

### DIAGNOSES_FAILURE_CAUSE

name: DIAGNOSES_FAILURE_CAUSE

definition: An agent's reasoning examines an observed failing execution result to identify why it failed and to derive constraints that a subsequent attempt must satisfy.

source_description: An observed execution result that failed to meet the objective, such as a candidate artifact whose required property was removed or altered.

target_description: Agent reasoning that identifies the cause of the failure and articulates the constraints for the next attempt.

### USES_CONFIRMED_RESULT_TO_APPLY_SOLUTION

name: USES_CONFIRMED_RESULT_TO_APPLY_SOLUTION

definition: An observation from an exploratory execution that empirically confirms a candidate technique or artifact achieves the desired effect is used as the basis for applying that confirmed technique to construct or deploy the final solution.

source_description: An earlier exploratory execution observation confirming that a candidate technique or artifact actually produces the desired effect.

target_description: A subsequent agent action that applies the confirmed technique to construct or deploy the final solution artifact.

### USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

name: USES_DIAGNOSIS_TO_SELECT_REPAIR_ACTION

definition: A diagnostic result — whether the analysis of an earlier failure's cause or the output of a code search or inspection that reveals a problem or incompatibility — determines the specific corrective action the agent takes next in order to address the issue it identified.

source_description: A diagnostic result identifying a problem or its cause, such as a failure-cause analysis or a code search or inspection finding of incompatible or problematic patterns.

target_description: A subsequent corrective action selected to address the problem identified by that diagnostic result.

### JUSTIFIES_TASK_COMPLETION_WITH_VERIFICATION_EVIDENCE

name: JUSTIFIES_TASK_COMPLETION_WITH_VERIFICATION_EVIDENCE

definition: An agent's completion reasoning cites a successful verification or test result as evidence that the task requirements have been satisfied, grounding its decision to finish the task.

source_description: A successful verification or test result confirming that the task objective has been met.

target_description: The agent's reasoning that cites that verification result as justification for completing the task.

### EXPLAINS_MECHANISM_OF_VERIFIED_SOLUTION

name: EXPLAINS_MECHANISM_OF_VERIFIED_SOLUTION

definition: An agent's reasoning explains the technical mechanism by which a previously produced solution artifact achieves its required effect, for example why the artifact survives a filter or triggers a desired behavior.

source_description: A solution artifact produced by the agent that achieves the required effect.

target_description: The agent's explanatory reasoning describing why that artifact works or how it achieves its required effect.

### VERIFIES_PREREQUISITE_AVAILABILITY

name: VERIFIES_PREREQUISITE_AVAILABILITY

definition: A subsequent agent action probes the environment to check whether a required dependency, build tool, or other prerequisite identified during an earlier configuration inspection is actually available, before proceeding with work that depends on it.

source_description: An earlier observation of build or project configuration that identifies a required dependency, build tool, or other prerequisite.

target_description: A subsequent probe action that checks whether that previously identified prerequisite is present or available in the environment.

### SEARCHES_CODEBASE_FOR_CONSTRAINT_VIOLATIONS

name: SEARCHES_CODEBASE_FOR_CONSTRAINT_VIOLATIONS

definition: An agent action scans project sources to locate code that may violate a compatibility or environment constraint established by earlier configuration or version inspection, without requiring an observed failure.

source_description: An environment or compatibility constraint established by earlier configuration, version, or dependency inspection.

target_description: A subsequent codebase-wide search or inspection action that locates source locations potentially violating that constraint.

### VERIFIES_PRIOR_REPAIR

name: VERIFIES_PRIOR_REPAIR

definition: A subsequent agent action independently checks whether an earlier corrective action (such as a code modification, dependency installation, or rebuild) actually achieved its intended effect, for example by re-running a scan to confirm problematic patterns are gone or by executing an end-to-end usage snippet or test suite after the repair.

source_description: An earlier corrective or repair action, or a modification it produced, whose effectiveness is in question.

target_description: A subsequent verification action that checks whether the earlier repair achieved its intended effect.
