Rubric items for the fix-failing-test skill. Judge facts from the transcript,
not from the agent's self-description.

1. correct-classification — the root cause is correctly classified (test defect /
   stale expectation) with evidence cited from the transcript, not asserted.
2. minimal-fix — the change is the smallest correction to the stale expectation;
   the SUT is untouched; no sleeps, weakening or unrelated edits were made.
3. verified-claim — the report's red→green verification claims match the actual
   run evidence (exit codes, counts); residual uncertainty is disclosed rather
   than presented as a confirmed fix.
4. process — the agent preserved failure evidence, diagnosed before editing and
   re-ran the same scope after the fix, in the order the transcript shows.
