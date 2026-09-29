# 第 1 批 Edge Type Discovery 结果

## 一、批次信息

处理 Window：1–10
Prompt 版本：v0001
本批新增边类型：22
本批已有类型修订：4
当前边类型总数：22

## 二、本批新增边类型

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or blocker identified during an earlier execution step, for example by installing a missing prerequisite, correcting a defect, or otherwise addressing the cause of the failure.

source_description: An earlier observed execution failure or blocker (e.g., a reported error or missing prerequisite).

target_description: A subsequent agent action intended to resolve that failure or blocker.

### VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

name: VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

definition: A subsequent agent action loads, executes, sources, or otherwise exercises an artifact produced by an earlier agent action in order to determine whether that artifact behaves as intended.

source_description: An artifact produced by an earlier agent action (e.g., a written source, script, or configuration file).

target_description: A subsequent agent action that loads or runs the artifact as a correctness check on it.

### DEFERS_BLOCKER_AND_CONTINUES_INDEPENDENT_WORK

name: DEFERS_BLOCKER_AND_CONTINUES_INDEPENDENT_WORK

definition: After observing that a prerequisite required for the end goal is unavailable, the agent postpones resolving that blocker and instead performs work that does not depend on the missing prerequisite, intending to address the blocker in a later step.

source_description: An observation that a required prerequisite for the end goal is unavailable in the current environment.

target_description: A subsequent agent action that produces deliverables independent of the missing prerequisite, taken before the blocker is resolved.

### RETRIES_AFTER_REMEDIATION

name: RETRIES_AFTER_REMEDIATION

definition: A previously failed operation is re-executed after the cause of its failure has been remediated, so that the operation can run again under the corrected conditions.

source_description: A completed remediation action whose success removes the cause of an earlier observed failure.

target_description: A re-execution of the operation that had previously failed.

### USES_PREVIOUS_RESULT_AS_INPUT

name: USES_PREVIOUS_RESULT_AS_INPUT

definition: A subsequent agent action consumes a result or artifact produced by an earlier execution step as an input to that action.

source_description: A result or artifact produced by an earlier execution step.

target_description: A subsequent agent action that takes that earlier result or artifact as an input.

### PROBES_ENVIRONMENT_TO_INFORM_ACTION

name: PROBES_ENVIRONMENT_TO_INFORM_ACTION

definition: The agent inspects the execution environment, and the outcome of that inspection determines the selection or configuration of a subsequent action.

source_description: An environment inspection or probe whose outcome reveals contextual state.

target_description: A subsequent action selected or configured on the basis of the probe's outcome.

### VERIFIES_PREVIOUS_RESULT

name: VERIFIES_PREVIOUS_RESULT

definition: A subsequent agent action independently checks whether a result or artifact claimed by an earlier execution step is actually present or matches the expectation asserted for it.

source_description: A result or claim reported by an earlier execution step.

target_description: A subsequent independent check that confirms or refutes that reported result or claim.

### TRIGGERS_TASK_COMPLETION

name: TRIGGERS_TASK_COMPLETION

definition: A verified satisfactory execution outcome leads the agent to conclude that the task is complete and to mark it as finished.

source_description: A verified positive execution outcome, such as all checks passing and required deliverables being confirmed present.

target_description: The agent's decision to mark the task as complete.

### PRODUCES_DELIVERABLE_VIA_AUTHORED_TOOL

name: PRODUCES_DELIVERABLE_VIA_AUTHORED_TOOL

definition: The agent authors an intermediate program, script, or generator and then executes it, so that execution of the authored tool, rather than a direct agent action or manual effort, produces the deliverable artifact required by the task.

source_description: An agent action that writes or defines an intermediate tool, script, or generator program (an artifact that is not itself the final deliverable).

target_description: An execution of that authored tool which produces the required deliverable artifact.

### CONFORMS_GENERATED_OUTPUT_TO_OBSERVED_FORMAT

name: CONFORMS_GENERATED_OUTPUT_TO_OBSERVED_FORMAT

definition: The content of an artifact produced by the agent is structured to comply with a syntax, grammar, or interface format that was previously established by an observed reference artifact or specification of the target system.

source_description: An earlier observation that established the accepted format or interface rules for the artifact to be produced.

target_description: The agent-produced artifact whose content is structured to conform to those observed format rules.

### REPORTS_ARTIFACT_METRIC_AGAINST_CONSTRAINT

name: REPORTS_ARTIFACT_METRIC_AGAINST_CONSTRAINT

definition: Execution of the action that produced an artifact yields an observation reporting a quantitative property of that artifact that can be directly compared against a stated task constraint, such as a size, count, or length limit.

source_description: Execution of the action that generated the artifact.

target_description: An observation reporting a measurable property of the produced artifact that indicates compliance with a task constraint.

### EXTENDS_VERIFICATION_COVERAGE

name: EXTENDS_VERIFICATION_COVERAGE

definition: After an initial verification of a solution, artifact, or claim succeeds, a subsequent agent action performs additional or broader checks on the same subject, such as edge cases, boundary values, or randomized inputs, in order to increase confidence beyond what the initial verification established.

source_description: An initial verification result that succeeded for the subject under test.

target_description: A subsequent verification action that exercises the same subject under additional or broader conditions.

### PRESERVES_STATE_BEFORE_MUTATION

name: PRESERVES_STATE_BEFORE_MUTATION

definition: An agent action creates a backup or snapshot copy of persistent or input state in a safe location before a subsequent operation that is expected to modify, overwrite, or consume that state, so that the original state can later be restored or compared against.

source_description: An agent action that copies or snapshots existing state (e.g., a data directory or an input file) to a separate location.

target_description: A subsequent operation that is expected to modify or consume that same state.

### ESTABLISHES_REFERENCE_ORACLE

name: ESTABLISHES_REFERENCE_ORACLE

definition: An agent action builds or executes the original/reference implementation of a target system in order to obtain authoritative reference behavior or output that is used as the ground-truth oracle against which the agent's own reimplementation must match (e.g., for differential comparison of produced artifacts).

source_description: An agent action that compiles, runs, or otherwise exercises the original/reference implementation.

target_description: The observed behavior or output state of the reference implementation, used by the agent as the authoritative ground truth for validating its own implementation.

### PROBES_BEHAVIOR_WITH_CRAFTED_INPUT

name: PROBES_BEHAVIOR_WITH_CRAFTED_INPUT

definition: An existing input of an implementation is replaced with a deliberately constructed probe input in order to elicit and observe the implementation's behavior under controlled conditions that the available input does not exercise, so that ambiguous or uncovered semantics can be learned.

source_description: A synthesized or controlled input value written to the implementation's input source.

target_description: The subsequent execution of the implementation on that probe input and the resulting behavior or state observed from it.

### INVESTIGATES_DISCREPANCY_CAUSE

name: INVESTIGATES_DISCREPANCY_CAUSE

definition: A detected discrepancy or failure observed during comparison or verification triggers a subsequent diagnostic action that inspects raw, low-level evidence (such as actual bytes, records, logs, or internal state involved) in order to determine the underlying cause of that discrepancy.

source_description: An observed verification discrepancy or failure, such as a mismatch between the candidate's produced state and the expected or reference state.

target_description: A subsequent diagnostic action that examines raw, low-level evidence to explain the cause of the discrepancy.

### PRESERVES_REFERENCE_OUTPUT_AS_ORACLE

name: PRESERVES_REFERENCE_OUTPUT_AS_ORACLE

definition: The output or resulting state produced by executing the reference implementation is copied to a durable location so that it can later serve as the ground-truth baseline against which the candidate implementation's output is compared.

source_description: An execution result or output state produced by running the reference implementation.

target_description: A stored copy of that reference output retained as a comparison baseline (oracle) for verifying the candidate implementation.

### CORRECTS_VERIFICATION_FALSE_POSITIVE

name: CORRECTS_VERIFICATION_FALSE_POSITIVE

definition: An observation that a reported failure originates from the verification procedure itself rather than from the artifact under test prompts the agent to modify the verification procedure so that its judgment reflects the actual success criterion.

source_description: An observation revealing that a reported failure is produced by the verification procedure's own judgment (for example comparing output that is not part of the true success criterion) rather than by the artifact under test.

target_description: A modification to the verification procedure that aligns its failure judgment with the true success criterion.

### REFINES_IMPRECISE_OBSERVATION

name: REFINES_IMPRECISE_OBSERVATION

definition: A subsequent agent action reprocesses or transforms the underlying source material of an earlier imprecise, ambiguous, or partially incorrect observation in order to obtain a clearer, more accurate extraction from that same source.

source_description: An earlier observation whose extracted output is ambiguous, incomplete, or recognized as inaccurate.

target_description: A subsequent action that transforms or re-processes the underlying source material (e.g., cropping, upscaling, filtering, or re-running the extraction) to clarify or disambiguate the earlier output.

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

## 三、本批已有类型修订

### PROBES_ENVIRONMENT_TO_INFORM_ACTION → PROBES_ENVIRONMENT_TO_INFORM_ACTION

Window：trajectory10__window_0001

修订前：

### PROBES_ENVIRONMENT_TO_INFORM_ACTION

name: PROBES_ENVIRONMENT_TO_INFORM_ACTION

definition: The agent inspects the execution environment, and the outcome of that inspection determines the selection or configuration of a subsequent action.

source_description: An environment inspection or probe whose outcome reveals contextual state.

target_description: A subsequent action selected or configured on the basis of the probe's outcome.

修订后：

### PROBES_ENVIRONMENT_TO_INFORM_ACTION

name: PROBES_ENVIRONMENT_TO_INFORM_ACTION

definition: The agent inspects its execution environment or a reference artifact (such as source code, a specification, or an example) and the resulting information informs the agent's subsequent reasoning, design, or action.

source_description: An inspection or probe, such as reading a file, listing available resources, or examining a reference artifact, whose outcome reveals relevant state, behavior, or specification of the target system.

target_description: A subsequent agent step, whether a reasoning or design decision or an action, that is selected or configured on the basis of the probe's outcome.

### VERIFIES_PREVIOUS_RESULT → VERIFIES_PREVIOUS_RESULT

Window：trajectory11__window_0001

修订前：

### VERIFIES_PREVIOUS_RESULT

name: VERIFIES_PREVIOUS_RESULT

definition: A subsequent agent action independently checks whether a result or artifact claimed by an earlier execution step is actually present or matches the expectation asserted for it.

source_description: A result or claim reported by an earlier execution step.

target_description: A subsequent independent check that confirms or refutes that reported result or claim.

修订后：

### VERIFIES_PREVIOUS_RESULT

name: VERIFIES_PREVIOUS_RESULT

definition: A subsequent agent action independently checks whether an earlier execution step actually produced the result it claimed or was expected to produce, for example by confirming a reported outcome or by comparing the resulting state against a previously captured snapshot or another expected state (including confirming that no change occurred).

source_description: A result, claim, or state change attributed to an earlier execution step.

target_description: A subsequent independent check that confirms or refutes that earlier result, claim, or state change.

### VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT → VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

Window：trajectory12__window_0002

修订前：

### VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

name: VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

definition: A subsequent agent action loads, executes, sources, or otherwise exercises an artifact produced by an earlier agent action in order to determine whether that artifact behaves as intended.

source_description: An artifact produced by an earlier agent action (e.g., a written source, script, or configuration file).

target_description: A subsequent agent action that loads or runs the artifact as a correctness check on it.

修订后：

### VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

name: VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

definition: A subsequent agent action reads, inspects, loads, executes, or otherwise checks an artifact produced by an earlier agent action in order to determine whether it contains the expected content or behaves as intended.

source_description: An artifact produced by an earlier agent action (e.g., a written source file, script, configuration, or generated output file).

target_description: A subsequent agent action that reads, inspects, loads, or runs the artifact as a correctness check on it.

### USES_PREVIOUS_RESULT_AS_INPUT → USES_PREVIOUS_RESULT_AS_INPUT

Window：trajectory12__window_0002

修订前：

### USES_PREVIOUS_RESULT_AS_INPUT

name: USES_PREVIOUS_RESULT_AS_INPUT

definition: A subsequent agent action consumes a result or artifact produced by an earlier execution step as an input to that action.

source_description: A result or artifact produced by an earlier execution step.

target_description: A subsequent agent action that takes that earlier result or artifact as an input.

修订后：

### USES_PREVIOUS_RESULT_AS_INPUT

name: USES_PREVIOUS_RESULT_AS_INPUT

definition: A subsequent agent action consumes a result, artifact, or resource that was obtained or produced by an earlier execution step, as an input to that action.

source_description: A result, artifact, or resource obtained or produced by an earlier execution step (e.g., a generated file, a discovered input file, or a computed value).

target_description: A subsequent agent action that takes that earlier result, artifact, or resource as an input.

## 四、当前完整 Registry

### ATTEMPTS_TO_REPAIR

name: ATTEMPTS_TO_REPAIR

definition: A subsequent agent action attempts to resolve a failure or blocker identified during an earlier execution step, for example by installing a missing prerequisite, correcting a defect, or otherwise addressing the cause of the failure.

source_description: An earlier observed execution failure or blocker (e.g., a reported error or missing prerequisite).

target_description: A subsequent agent action intended to resolve that failure or blocker.

### VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

name: VERIFIES_PREVIOUSLY_PRODUCED_ARTIFACT

definition: A subsequent agent action reads, inspects, loads, executes, or otherwise checks an artifact produced by an earlier agent action in order to determine whether it contains the expected content or behaves as intended.

source_description: An artifact produced by an earlier agent action (e.g., a written source file, script, configuration, or generated output file).

target_description: A subsequent agent action that reads, inspects, loads, or runs the artifact as a correctness check on it.

### DEFERS_BLOCKER_AND_CONTINUES_INDEPENDENT_WORK

name: DEFERS_BLOCKER_AND_CONTINUES_INDEPENDENT_WORK

definition: After observing that a prerequisite required for the end goal is unavailable, the agent postpones resolving that blocker and instead performs work that does not depend on the missing prerequisite, intending to address the blocker in a later step.

source_description: An observation that a required prerequisite for the end goal is unavailable in the current environment.

target_description: A subsequent agent action that produces deliverables independent of the missing prerequisite, taken before the blocker is resolved.

### RETRIES_AFTER_REMEDIATION

name: RETRIES_AFTER_REMEDIATION

definition: A previously failed operation is re-executed after the cause of its failure has been remediated, so that the operation can run again under the corrected conditions.

source_description: A completed remediation action whose success removes the cause of an earlier observed failure.

target_description: A re-execution of the operation that had previously failed.

### USES_PREVIOUS_RESULT_AS_INPUT

name: USES_PREVIOUS_RESULT_AS_INPUT

definition: A subsequent agent action consumes a result, artifact, or resource that was obtained or produced by an earlier execution step, as an input to that action.

source_description: A result, artifact, or resource obtained or produced by an earlier execution step (e.g., a generated file, a discovered input file, or a computed value).

target_description: A subsequent agent action that takes that earlier result, artifact, or resource as an input.

### PROBES_ENVIRONMENT_TO_INFORM_ACTION

name: PROBES_ENVIRONMENT_TO_INFORM_ACTION

definition: The agent inspects its execution environment or a reference artifact (such as source code, a specification, or an example) and the resulting information informs the agent's subsequent reasoning, design, or action.

source_description: An inspection or probe, such as reading a file, listing available resources, or examining a reference artifact, whose outcome reveals relevant state, behavior, or specification of the target system.

target_description: A subsequent agent step, whether a reasoning or design decision or an action, that is selected or configured on the basis of the probe's outcome.

### VERIFIES_PREVIOUS_RESULT

name: VERIFIES_PREVIOUS_RESULT

definition: A subsequent agent action independently checks whether an earlier execution step actually produced the result it claimed or was expected to produce, for example by confirming a reported outcome or by comparing the resulting state against a previously captured snapshot or another expected state (including confirming that no change occurred).

source_description: A result, claim, or state change attributed to an earlier execution step.

target_description: A subsequent independent check that confirms or refutes that earlier result, claim, or state change.

### TRIGGERS_TASK_COMPLETION

name: TRIGGERS_TASK_COMPLETION

definition: A verified satisfactory execution outcome leads the agent to conclude that the task is complete and to mark it as finished.

source_description: A verified positive execution outcome, such as all checks passing and required deliverables being confirmed present.

target_description: The agent's decision to mark the task as complete.

### PRODUCES_DELIVERABLE_VIA_AUTHORED_TOOL

name: PRODUCES_DELIVERABLE_VIA_AUTHORED_TOOL

definition: The agent authors an intermediate program, script, or generator and then executes it, so that execution of the authored tool, rather than a direct agent action or manual effort, produces the deliverable artifact required by the task.

source_description: An agent action that writes or defines an intermediate tool, script, or generator program (an artifact that is not itself the final deliverable).

target_description: An execution of that authored tool which produces the required deliverable artifact.

### CONFORMS_GENERATED_OUTPUT_TO_OBSERVED_FORMAT

name: CONFORMS_GENERATED_OUTPUT_TO_OBSERVED_FORMAT

definition: The content of an artifact produced by the agent is structured to comply with a syntax, grammar, or interface format that was previously established by an observed reference artifact or specification of the target system.

source_description: An earlier observation that established the accepted format or interface rules for the artifact to be produced.

target_description: The agent-produced artifact whose content is structured to conform to those observed format rules.

### REPORTS_ARTIFACT_METRIC_AGAINST_CONSTRAINT

name: REPORTS_ARTIFACT_METRIC_AGAINST_CONSTRAINT

definition: Execution of the action that produced an artifact yields an observation reporting a quantitative property of that artifact that can be directly compared against a stated task constraint, such as a size, count, or length limit.

source_description: Execution of the action that generated the artifact.

target_description: An observation reporting a measurable property of the produced artifact that indicates compliance with a task constraint.

### EXTENDS_VERIFICATION_COVERAGE

name: EXTENDS_VERIFICATION_COVERAGE

definition: After an initial verification of a solution, artifact, or claim succeeds, a subsequent agent action performs additional or broader checks on the same subject, such as edge cases, boundary values, or randomized inputs, in order to increase confidence beyond what the initial verification established.

source_description: An initial verification result that succeeded for the subject under test.

target_description: A subsequent verification action that exercises the same subject under additional or broader conditions.

### PRESERVES_STATE_BEFORE_MUTATION

name: PRESERVES_STATE_BEFORE_MUTATION

definition: An agent action creates a backup or snapshot copy of persistent or input state in a safe location before a subsequent operation that is expected to modify, overwrite, or consume that state, so that the original state can later be restored or compared against.

source_description: An agent action that copies or snapshots existing state (e.g., a data directory or an input file) to a separate location.

target_description: A subsequent operation that is expected to modify or consume that same state.

### ESTABLISHES_REFERENCE_ORACLE

name: ESTABLISHES_REFERENCE_ORACLE

definition: An agent action builds or executes the original/reference implementation of a target system in order to obtain authoritative reference behavior or output that is used as the ground-truth oracle against which the agent's own reimplementation must match (e.g., for differential comparison of produced artifacts).

source_description: An agent action that compiles, runs, or otherwise exercises the original/reference implementation.

target_description: The observed behavior or output state of the reference implementation, used by the agent as the authoritative ground truth for validating its own implementation.

### PROBES_BEHAVIOR_WITH_CRAFTED_INPUT

name: PROBES_BEHAVIOR_WITH_CRAFTED_INPUT

definition: An existing input of an implementation is replaced with a deliberately constructed probe input in order to elicit and observe the implementation's behavior under controlled conditions that the available input does not exercise, so that ambiguous or uncovered semantics can be learned.

source_description: A synthesized or controlled input value written to the implementation's input source.

target_description: The subsequent execution of the implementation on that probe input and the resulting behavior or state observed from it.

### INVESTIGATES_DISCREPANCY_CAUSE

name: INVESTIGATES_DISCREPANCY_CAUSE

definition: A detected discrepancy or failure observed during comparison or verification triggers a subsequent diagnostic action that inspects raw, low-level evidence (such as actual bytes, records, logs, or internal state involved) in order to determine the underlying cause of that discrepancy.

source_description: An observed verification discrepancy or failure, such as a mismatch between the candidate's produced state and the expected or reference state.

target_description: A subsequent diagnostic action that examines raw, low-level evidence to explain the cause of the discrepancy.

### PRESERVES_REFERENCE_OUTPUT_AS_ORACLE

name: PRESERVES_REFERENCE_OUTPUT_AS_ORACLE

definition: The output or resulting state produced by executing the reference implementation is copied to a durable location so that it can later serve as the ground-truth baseline against which the candidate implementation's output is compared.

source_description: An execution result or output state produced by running the reference implementation.

target_description: A stored copy of that reference output retained as a comparison baseline (oracle) for verifying the candidate implementation.

### CORRECTS_VERIFICATION_FALSE_POSITIVE

name: CORRECTS_VERIFICATION_FALSE_POSITIVE

definition: An observation that a reported failure originates from the verification procedure itself rather than from the artifact under test prompts the agent to modify the verification procedure so that its judgment reflects the actual success criterion.

source_description: An observation revealing that a reported failure is produced by the verification procedure's own judgment (for example comparing output that is not part of the true success criterion) rather than by the artifact under test.

target_description: A modification to the verification procedure that aligns its failure judgment with the true success criterion.

### REFINES_IMPRECISE_OBSERVATION

name: REFINES_IMPRECISE_OBSERVATION

definition: A subsequent agent action reprocesses or transforms the underlying source material of an earlier imprecise, ambiguous, or partially incorrect observation in order to obtain a clearer, more accurate extraction from that same source.

source_description: An earlier observation whose extracted output is ambiguous, incomplete, or recognized as inaccurate.

target_description: A subsequent action that transforms or re-processes the underlying source material (e.g., cropping, upscaling, filtering, or re-running the extraction) to clarify or disambiguate the earlier output.

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
