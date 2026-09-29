# 第 2 批 Edge Type Discovery 结果

## 一、批次信息

处理 Window：11–20
Prompt 版本：v0001
本批新增边类型：17
本批已有类型修订：4
当前边类型总数：29

## 二、本批新增边类型

### PROVISIONS_MISSING_PREREQUISITE

name: PROVISIONS_MISSING_PREREQUISITE

definition: A subsequent agent action installs or otherwise obtains a prerequisite (tool, library, or package) that an earlier reconnaissance observation reported as absent, without a preceding execution failure having occurred.

source_description: An earlier observation that reports a required tool, dependency, or capability is absent from the environment.

target_description: A subsequent agent action that installs or otherwise obtains the missing prerequisite so that it becomes available.

### INVESTIGATES_FAILURE_CAUSE

name: INVESTIGATES_FAILURE_CAUSE

definition: A subsequent agent action inspects or searches the diagnostic output produced by an earlier failed execution step in order to determine the cause of that failure.

source_description: An earlier observed execution failure whose diagnostic output (log or error message) is available.

target_description: A subsequent agent action that reads or searches the failure's diagnostic output to identify its cause.

### MONITORS_LAUNCHED_ASYNC_OPERATION

name: MONITORS_LAUNCHED_ASYNC_OPERATION

definition: A subsequent agent action checks the progress or completion status of a long-running operation that was previously launched asynchronously, for example by reading its log or inspecting its job state.

source_description: A long-running operation that a previous agent action launched asynchronously (e.g., a background job).

target_description: A subsequent agent action that inspects the operation's log or job state to check its progress or completion.

### RETRIES_FAILED_OPERATION_AFTER_REMEDY

name: RETRIES_FAILED_OPERATION_AFTER_REMEDY

definition: The agent re-executes a previously failed operation after performing a corrective action intended to remove the cause of the earlier failure.

source_description: A corrective action that remedied the cause of an earlier operation failure.

target_description: A re-execution (retry) of the previously failed operation.

### USES_SUCCESSFUL_RESULT_AS_PRECONDITION

name: USES_SUCCESSFUL_RESULT_AS_PRECONDITION

definition: A subsequent agent action is initiated because an earlier step completed successfully and thereby satisfied a prerequisite that the action depends on.

source_description: An earlier step whose successful completion satisfied a prerequisite (e.g., made a required tool, library, version, or resource available).

target_description: A subsequent agent action that depends on that prerequisite being satisfied.

### REVERTS_SIDE_EFFECTS_TO_RESTORE_PRECONDITION

name: REVERTS_SIDE_EFFECTS_TO_RESTORE_PRECONDITION

definition: A subsequent agent action undoes persistent state changes left behind by an earlier test or trial run in order to restore a clean state required by the intended workflow.

source_description: An earlier test or trial action that produced persistent state changes (e.g., a created commit, a deployed artifact, or scratch files) as an unwanted side effect.

target_description: A subsequent agent action that reverts or cleans up those state changes to restore the original precondition.

### AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

name: AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

definition: After deciding to finalize the task, the agent performs an additional diagnostic examination of the environment to detect any required prerequisite or overlooked condition that could prevent the task from succeeding.

source_description: A task-completion decision or expressed intent to finalize the task.

target_description: A subsequent diagnostic probe of the environment performed to reveal overlooked prerequisites or conditions.

### CONTINUES_SETUP_AFTER_PARTIAL_ACTION_OUTCOME

name: CONTINUES_SETUP_AFTER_PARTIAL_ACTION_OUTCOME

definition: An observation revealing that an earlier agent action achieved only part of its intended state change (for example, a component was installed but its service was not started) leads the agent to perform a follow-up action that completes the remaining part of the intended configuration.

source_description: An observation showing that an earlier agent action left the system in an incomplete or not-yet-active state.

target_description: A subsequent agent action that completes the remaining portion of the intended configuration so the component becomes fully operational.

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

### REAFFIRMS_PRIOR_VERIFICATION

name: REAFFIRMS_PRIOR_VERIFICATION

definition: A later agent reasoning step restates and re-confirms a verification conclusion that an earlier reasoning step had already established, for example before finalizing the task after a confirmation prompt.

source_description: An earlier agent reasoning step that established a verified conclusion about the solution.

target_description: A subsequent agent reasoning step that restates and re-confirms that same verified conclusion.

### REVISES_APPROACH_BASED_ON_OBSERVED_RESULT

name: REVISES_APPROACH_BASED_ON_OBSERVED_RESULT

definition: An observed execution result reveals that an earlier assumption, interpretation, or approach was incorrect, prompting the agent to modify its plan, artifact, or parameters in order to correct the earlier approach.

source_description: An observed execution result that contradicts or invalidates an earlier assumption, interpretation, or approach.

target_description: A subsequent agent action or artifact that corrects the earlier approach in light of that observed result.

### CLASSIFIES_ITEM_FROM_OBSERVED_CONTENT

name: CLASSIFIES_ITEM_FROM_OBSERVED_CONTENT

definition: An agent decision assigns a semantic category label (e.g., invoice versus other) to an item based on content of that item obtained in an earlier reading or extraction step.

source_description: An observation containing the content of an item, produced by a prior reading or extraction step.

target_description: An agent decision that assigns a category label to that item based on its observed content.

### EXTRACTS_FIELD_VALUE_FROM_OBSERVED_CONTENT

name: EXTRACTS_FIELD_VALUE_FROM_OBSERVED_CONTENT

definition: An agent derives a specific structured attribute value (e.g., a monetary total or a named field) from content of an item observed in an earlier reading or extraction step.

source_description: An observation containing the content of an item from an earlier reading or extraction step.

target_description: The structured attribute value derived by the agent from that observed content.

### RESOLVES_CONFLICTING_VALUES_BY_PRECEDENCE

name: RESOLVES_CONFLICTING_VALUES_BY_PRECEDENCE

definition: An agent detects multiple conflicting candidate values for the same field within observed content and applies a specified precedence rule to select one of them.

source_description: An observation containing multiple conflicting candidate values for the same field.

target_description: An agent decision that selects one candidate value according to a specified precedence rule.

### PERFORMS_CLEANUP_AFTER_TASK_COMPLETION

name: PERFORMS_CLEANUP_AFTER_TASK_COMPLETION

definition: After the primary task objectives have been completed and verified, the agent removes temporary or intermediate resources that were created during the task and are no longer needed.

source_description: A point at which the agent has concluded, typically after verification, that the primary task objectives are complete.

target_description: A subsequent agent action that removes temporary or intermediate resources no longer needed.

## 三、本批已有类型修订

### ATTEMPTS_TO_REPAIR → ATTEMPTS_TO_REPAIR

Window：trajectory13__window_0001

修订前：

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure, blocker, or detected defect in an earlier execution step, including retrying an operation after remediation and correcting a verification procedure that produced a false failure.

source_description: An earlier observed failure, blocker, or detected defect (e.g., a reported error, missing prerequisite, or false-positive verification result).

target_description: A subsequent agent action intended to resolve or correct that failure, blocker, or defect.

修订后：

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure, error, or detected defect observed in an earlier execution step by removing or correcting its cause, including correcting a verification procedure that produced a spurious failure.

source_description: An earlier observed failure, error, or detected defect produced by or attributed to an execution step (e.g., a reported error or a spurious verification failure).

target_description: A subsequent agent action intended to remove or correct the cause of that failure, error, or defect.

### INVESTIGATES_FAILURE_CAUSE → INVESTIGATES_FAILURE_CAUSE

Window：trajectory13__window_0002

修订前：

### INVESTIGATES_FAILURE_CAUSE

name: INVESTIGATES_FAILURE_CAUSE

definition: A subsequent agent action inspects or searches the diagnostic output produced by an earlier failed execution step in order to determine the cause of that failure.

source_description: An earlier observed execution failure whose diagnostic output (log or error message) is available.

target_description: A subsequent agent action that reads or searches the failure's diagnostic output to identify its cause.

修订后：

### INVESTIGATES_FAILURE_CAUSE

name: INVESTIGATES_FAILURE_CAUSE

definition: A subsequent agent action inspects or searches the diagnostic output produced by an earlier observed failure, or related environment/state evidence relevant to diagnosing it, in order to determine the cause of that failure.

source_description: An earlier observed execution failure or error whose diagnostic output or related state evidence is available.

target_description: A subsequent agent action that examines the failure's diagnostic output or related environment state to identify the cause of the failure.

### PROVISIONS_MISSING_PREREQUISITE → PROVISIONS_MISSING_PREREQUISITE

Window：trajectory14__window_0001

修订前：

### PROVISIONS_MISSING_PREREQUISITE

name: PROVISIONS_MISSING_PREREQUISITE

definition: A subsequent agent action installs or otherwise obtains a prerequisite (tool, library, or package) that an earlier reconnaissance observation reported as absent, without a preceding execution failure having occurred.

source_description: An earlier observation that reports a required tool, dependency, or capability is absent from the environment.

target_description: A subsequent agent action that installs or otherwise obtains the missing prerequisite so that it becomes available.

修订后：

### PROVISIONS_MISSING_PREREQUISITE

name: PROVISIONS_MISSING_PREREQUISITE

definition: A subsequent agent action installs, creates, or otherwise obtains a prerequisite (such as a tool, library, package, account, or service) that an earlier reconnaissance observation reported as absent, without a preceding execution failure having occurred.

source_description: An earlier observation that reports a required tool, dependency, account, service, or capability is absent from the environment.

target_description: A subsequent agent action that installs, creates, or otherwise obtains the missing prerequisite so that it becomes available.

### AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT → AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

Window：trajectory14__window_0002

修订前：

### AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

name: AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

definition: After deciding to finalize the task, the agent performs an additional diagnostic examination of the environment to detect any required prerequisite or overlooked condition that could prevent the task from succeeding.

source_description: A task-completion decision or expressed intent to finalize the task.

target_description: A subsequent diagnostic probe of the environment performed to reveal overlooked prerequisites or conditions.

修订后：

### AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

name: AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

definition: After expressing intent to finalize the task (for example by requesting completion, which may return a confirmation prompt), the agent reopens its analysis and performs an additional diagnostic examination of the environment to detect a required prerequisite or overlooked condition that could prevent the task from succeeding.

source_description: A task-completion decision or request expressing the agent's intent to finalize the task, which may be gated by an environment confirmation prompt returned before final grading.

target_description: A subsequent diagnostic probe or re-examination of the environment performed to reveal overlooked prerequisites or conditions before finalizing.

## 四、当前完整 Registry

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure, error, or detected defect observed in an earlier execution step by removing or correcting its cause, including correcting a verification procedure that produced a spurious failure.

source_description: An earlier observed failure, error, or detected defect produced by or attributed to an execution step (e.g., a reported error or a spurious verification failure).

target_description: A subsequent agent action intended to remove or correct the cause of that failure, error, or defect.

### USES_PREVIOUS_RESULT_AS_INPUT

name: USES_PREVIOUS_RESULT_AS_INPUT

definition: A subsequent agent action consumes a result, artifact, or resource that was obtained or produced by an earlier execution step, as an input to that action.

source_description: A result, artifact, or resource obtained or produced by an earlier execution step (e.g., a generated file, a discovered input file, or a computed value).

target_description: A subsequent agent action that takes that earlier result, artifact, or resource as an input.

### PROBES_ENVIRONMENT_TO_INFORM_ACTION

name: PROBES_ENVIRONMENT_TO_INFORM_ACTION

definition: The agent obtains information about its execution environment, a reference artifact, or an implementation's behavior, including by supplying a controlled probe input, and the resulting information informs subsequent reasoning, design, or action.

source_description: An inspection, probe, or controlled experiment (e.g., reading a file, listing resources, examining a reference, or supplying a synthesized input to elicit behavior) whose outcome reveals relevant state, behavior, or specification.

target_description: A subsequent agent step, whether reasoning, design decision, or action, that is selected or configured based on the probe's outcome.

### VERIFIES_PREVIOUS_RESULT

name: VERIFIES_PREVIOUS_RESULT

definition: A subsequent agent action checks, confirms, or broadens confidence in a result, artifact, claim, or state change attributed to an earlier execution step, including reading or running a produced artifact and performing additional checks after an initial verification succeeded.

source_description: An earlier result, artifact, claim, or state change attributed to an execution step (e.g., a produced file, a reported outcome, or an initial verification success).

target_description: A subsequent independent check that confirms, refutes, or further exercises that earlier result, artifact, claim, or state change.

### TRIGGERS_TASK_COMPLETION

name: TRIGGERS_TASK_COMPLETION

definition: A verified satisfactory execution outcome leads the agent to conclude that the task is complete and to mark it as finished.

source_description: A verified positive execution outcome, such as all checks passing and required deliverables being confirmed present.

target_description: The agent's decision to mark the task as complete.

### CONFORMS_GENERATED_OUTPUT_TO_OBSERVED_FORMAT

name: CONFORMS_GENERATED_OUTPUT_TO_OBSERVED_FORMAT

definition: The content of an artifact produced by the agent is structured to comply with a syntax, grammar, or interface format that was previously established by an observed reference artifact or specification of the target system.

source_description: An earlier observation that established the accepted format or interface rules for the artifact to be produced.

target_description: The agent-produced artifact whose content is structured to conform to those observed format rules.

### PRESERVES_STATE_BEFORE_MUTATION

name: PRESERVES_STATE_BEFORE_MUTATION

definition: An agent action creates a backup or snapshot copy of persistent or input state in a safe location before a subsequent operation that is expected to modify, overwrite, or consume that state, so that the original state can later be restored or compared against.

source_description: An agent action that copies or snapshots existing state (e.g., a data directory or an input file) to a separate location.

target_description: A subsequent operation that is expected to modify or consume that same state.

### ESTABLISHES_REFERENCE_ORACLE

name: ESTABLISHES_REFERENCE_ORACLE

definition: An agent action builds, executes, or captures the output of the original/reference implementation in order to obtain and retain authoritative reference behavior or output that is used as the ground-truth oracle against which the agent's own reimplementation is validated.

source_description: An agent action that compiles, runs, or otherwise exercises the original/reference implementation and captures its output.

target_description: The observed or stored reference behavior/output retained as the authoritative ground truth (oracle) for validating the agent's implementation.

### INVESTIGATES_DISCREPANCY_CAUSE

name: INVESTIGATES_DISCREPANCY_CAUSE

definition: A detected discrepancy or failure observed during comparison or verification triggers a subsequent diagnostic action that inspects raw, low-level evidence (such as actual bytes, records, logs, or internal state involved) in order to determine the underlying cause of that discrepancy.

source_description: An observed verification discrepancy or failure, such as a mismatch between the candidate's produced state and the expected or reference state.

target_description: A subsequent diagnostic action that examines raw, low-level evidence to explain the cause of the discrepancy.

### VALIDATES_CANDIDATES_AGAINST_EXPECTED_OUTCOME

name: VALIDATES_CANDIDATES_AGAINST_EXPECTED_OUTCOME

definition: An agent action evaluates multiple candidate interpretations or solutions against a known expected outcome or success constraint, in order to identify and select the candidate that satisfies it.

source_description: A known expected result or success criterion derived from the task specification (e.g., a required output prefix or value) that constrains which candidate interpretation can be correct.

target_description: A subsequent agent action or script that tests candidate interpretations against that expected result and selects the one that matches.

### PIVOTS_TO_ALTERNATIVE_APPROACH_AFTER_REPEATED_FAILURE

name: PIVOTS_TO_ALTERNATIVE_APPROACH_AFTER_REPEATED_FAILURE

definition: After an initial approach repeatedly produces unreliable, ambiguous, or unsuccessful results, the agent stops using that approach and adopts a fundamentally different strategy that does not depend on the failing approach, in order to make progress on the task.

source_description: A sequence of unreliable, ambiguous, or unsuccessful results repeatedly produced by an initial approach.

target_description: A subsequent agent action that implements a different approach to accomplish the task instead of continuing with the failing approach.

### PRODUCES_DELIVERABLE_ON_VALIDATED_CANDIDATE

name: PRODUCES_DELIVERABLE_ON_VALIDATED_CANDIDATE

definition: An agent action produces the required output artifact when a candidate interpretation or solution satisfies the expected validation criterion, so that the deliverable is written only upon successful validation.

source_description: A candidate interpretation or solution that satisfies the expected validation criterion.

target_description: The required output artifact produced as a result of that successful validation.

### PROVISIONS_MISSING_PREREQUISITE

name: PROVISIONS_MISSING_PREREQUISITE

definition: A subsequent agent action installs, creates, or otherwise obtains a prerequisite (such as a tool, library, package, account, or service) that an earlier reconnaissance observation reported as absent, without a preceding execution failure having occurred.

source_description: An earlier observation that reports a required tool, dependency, account, service, or capability is absent from the environment.

target_description: A subsequent agent action that installs, creates, or otherwise obtains the missing prerequisite so that it becomes available.

### INVESTIGATES_FAILURE_CAUSE

name: INVESTIGATES_FAILURE_CAUSE

definition: A subsequent agent action inspects or searches the diagnostic output produced by an earlier observed failure, or related environment/state evidence relevant to diagnosing it, in order to determine the cause of that failure.

source_description: An earlier observed execution failure or error whose diagnostic output or related state evidence is available.

target_description: A subsequent agent action that examines the failure's diagnostic output or related environment state to identify the cause of the failure.

### MONITORS_LAUNCHED_ASYNC_OPERATION

name: MONITORS_LAUNCHED_ASYNC_OPERATION

definition: A subsequent agent action checks the progress or completion status of a long-running operation that was previously launched asynchronously, for example by reading its log or inspecting its job state.

source_description: A long-running operation that a previous agent action launched asynchronously (e.g., a background job).

target_description: A subsequent agent action that inspects the operation's log or job state to check its progress or completion.

### RETRIES_FAILED_OPERATION_AFTER_REMEDY

name: RETRIES_FAILED_OPERATION_AFTER_REMEDY

definition: The agent re-executes a previously failed operation after performing a corrective action intended to remove the cause of the earlier failure.

source_description: A corrective action that remedied the cause of an earlier operation failure.

target_description: A re-execution (retry) of the previously failed operation.

### USES_SUCCESSFUL_RESULT_AS_PRECONDITION

name: USES_SUCCESSFUL_RESULT_AS_PRECONDITION

definition: A subsequent agent action is initiated because an earlier step completed successfully and thereby satisfied a prerequisite that the action depends on.

source_description: An earlier step whose successful completion satisfied a prerequisite (e.g., made a required tool, library, version, or resource available).

target_description: A subsequent agent action that depends on that prerequisite being satisfied.

### REVERTS_SIDE_EFFECTS_TO_RESTORE_PRECONDITION

name: REVERTS_SIDE_EFFECTS_TO_RESTORE_PRECONDITION

definition: A subsequent agent action undoes persistent state changes left behind by an earlier test or trial run in order to restore a clean state required by the intended workflow.

source_description: An earlier test or trial action that produced persistent state changes (e.g., a created commit, a deployed artifact, or scratch files) as an unwanted side effect.

target_description: A subsequent agent action that reverts or cleans up those state changes to restore the original precondition.

### AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

name: AUDITS_FOR_OVERLOOKED_PREREQUISITE_AFTER_COMPLETION_INTENT

definition: After expressing intent to finalize the task (for example by requesting completion, which may return a confirmation prompt), the agent reopens its analysis and performs an additional diagnostic examination of the environment to detect a required prerequisite or overlooked condition that could prevent the task from succeeding.

source_description: A task-completion decision or request expressing the agent's intent to finalize the task, which may be gated by an environment confirmation prompt returned before final grading.

target_description: A subsequent diagnostic probe or re-examination of the environment performed to reveal overlooked prerequisites or conditions before finalizing.

### CONTINUES_SETUP_AFTER_PARTIAL_ACTION_OUTCOME

name: CONTINUES_SETUP_AFTER_PARTIAL_ACTION_OUTCOME

definition: An observation revealing that an earlier agent action achieved only part of its intended state change (for example, a component was installed but its service was not started) leads the agent to perform a follow-up action that completes the remaining part of the intended configuration.

source_description: An observation showing that an earlier agent action left the system in an incomplete or not-yet-active state.

target_description: A subsequent agent action that completes the remaining portion of the intended configuration so the component becomes fully operational.

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

### REAFFIRMS_PRIOR_VERIFICATION

name: REAFFIRMS_PRIOR_VERIFICATION

definition: A later agent reasoning step restates and re-confirms a verification conclusion that an earlier reasoning step had already established, for example before finalizing the task after a confirmation prompt.

source_description: An earlier agent reasoning step that established a verified conclusion about the solution.

target_description: A subsequent agent reasoning step that restates and re-confirms that same verified conclusion.

### REVISES_APPROACH_BASED_ON_OBSERVED_RESULT

name: REVISES_APPROACH_BASED_ON_OBSERVED_RESULT

definition: An observed execution result reveals that an earlier assumption, interpretation, or approach was incorrect, prompting the agent to modify its plan, artifact, or parameters in order to correct the earlier approach.

source_description: An observed execution result that contradicts or invalidates an earlier assumption, interpretation, or approach.

target_description: A subsequent agent action or artifact that corrects the earlier approach in light of that observed result.

### CLASSIFIES_ITEM_FROM_OBSERVED_CONTENT

name: CLASSIFIES_ITEM_FROM_OBSERVED_CONTENT

definition: An agent decision assigns a semantic category label (e.g., invoice versus other) to an item based on content of that item obtained in an earlier reading or extraction step.

source_description: An observation containing the content of an item, produced by a prior reading or extraction step.

target_description: An agent decision that assigns a category label to that item based on its observed content.

### EXTRACTS_FIELD_VALUE_FROM_OBSERVED_CONTENT

name: EXTRACTS_FIELD_VALUE_FROM_OBSERVED_CONTENT

definition: An agent derives a specific structured attribute value (e.g., a monetary total or a named field) from content of an item observed in an earlier reading or extraction step.

source_description: An observation containing the content of an item from an earlier reading or extraction step.

target_description: The structured attribute value derived by the agent from that observed content.

### RESOLVES_CONFLICTING_VALUES_BY_PRECEDENCE

name: RESOLVES_CONFLICTING_VALUES_BY_PRECEDENCE

definition: An agent detects multiple conflicting candidate values for the same field within observed content and applies a specified precedence rule to select one of them.

source_description: An observation containing multiple conflicting candidate values for the same field.

target_description: An agent decision that selects one candidate value according to a specified precedence rule.

### PERFORMS_CLEANUP_AFTER_TASK_COMPLETION

name: PERFORMS_CLEANUP_AFTER_TASK_COMPLETION

definition: After the primary task objectives have been completed and verified, the agent removes temporary or intermediate resources that were created during the task and are no longer needed.

source_description: A point at which the agent has concluded, typically after verification, that the primary task objectives are complete.

target_description: A subsequent agent action that removes temporary or intermediate resources no longer needed.
