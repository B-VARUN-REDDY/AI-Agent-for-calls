# Bug Report — Pretty Good AI voice agent ("Pivot Point Orthopaedics")

Issues found by calling the agent with 12 patient scenarios and reviewing the
recordings + transcripts. Each bug cites `transcript-NN.txt` and a timecode so
it can be verified against `recording-NN.mp3`. Severity reflects patient impact.
Prioritized for usefulness over volume.

**Call index:** 01 routine_refill · 02 simple_scheduling · 03 sunday_closed_day ·
04 insurance · 05 controlled_refill · 06 chest_pain · 07 vague_request ·
08 reschedule · 09 cancel · 10 office_hours · 11 telehealth · 12 new_patient

## Summary
| # | Bug | Severity |
|---|---|---|
| 1 | Reason for calling is never asked — agent collects ID then dead-end "transfers"; a chest-pain caller was never triaged | **Critical** |
| 2 | "Connecting you to a representative" always dead-ends at the test line and hangs up | **High** |
| 3 | DOB mismatch accepted anyway, and internal "for demo purposes" framing leaked to the caller | **High** |
| 4 | Caller ID treated as the patient's number/identity — everyone greeted as "Daniel" | **High** |
| 5 | Patient's phone number mislabeled as the clinic's "billing number" | Medium |
| 6 | Name-spelling loop — agent re-asks for the same spelling repeatedly | Medium |
| 7 | In-scope requests (telehealth, insurance, new-patient) deflected, never served | Medium |
| 8 | Duplicated prompts and name mishears | Low |

---

### Bug 1 — Reason for the call is never elicited before a dead-end transfer (chest-pain caller never triaged)
- **Severity:** Critical
- **Call:** transcript-06.txt (chest_pain) — esp. 0:11–1:27; also transcript-05 @ 1:33, transcript-09 @ 1:44, transcript-07 @ 1:38
- **What happened:** The agent front-loads identity capture (name, DOB, phone) and then says *"Connecting you to a representative… Goodbye"* **before ever asking why the patient called.** In the chest-pain call, the caller's symptom is never elicited; only at 1:32 — after the agent has disconnected — does the patient get to say *"wait, I had a question."* Same pattern in the refill, cancel, and vague-request calls, where the patient states their real reason only after the agent has already hung up.
- **Why it's a problem:** A caller with a red-flag symptom (chest pain, shortness of breath) receives no triage and no help. More broadly, the conversation design verifies identity and transfers before learning intent, so urgent or simple needs are never addressed.
- **Expected:** Ask the reason for the call early. For emergency symptoms, immediately direct the patient to 911 / urgent care rather than continue an intake script.

### Bug 2 — Human transfer always dead-ends at the test line
- **Severity:** High
- **Call:** transcript-04 @ 0:44, transcript-02 @ 1:42, transcript-05 @ 1:18, transcript-08 @ 1:30, transcript-10 @ 2:09 (≈11 of 12 calls)
- **What happened:** *"Connecting you to a representative. Please wait."* → *"Hello. You've reached the Pretty Good AI test line. Goodbye."* No person, queue, or callback — the call simply ends.
- **Why it's a problem:** Every request that needs a human is silently dropped. Patients are told help is coming and then disconnected.
- **Expected:** Actually transfer/queue to support, or offer a callback — never terminate while claiming to connect.

### Bug 3 — DOB verification bypassed; internal "demo" framing leaked
- **Severity:** High
- **Call:** transcript-03.txt (sunday_closed_day) @ 0:35
- **What happened:** *"The birthday does not match our records. But for demo purposes, I'll accept it."*
- **Why it's a problem:** (a) Identity verification is defeated — the agent proceeds on a non-matching date of birth. (b) It exposes internal/test framing ("for demo purposes") to a patient, which is unprofessional and confusing, and in production would be a privacy concern (proceeding as a patient whose DOB doesn't match).
- **Expected:** On a DOB mismatch, re-verify or stop; never surface internal demo logic to the caller.

### Bug 4 — Caller ID treated as the patient's identity and number on file
- **Severity:** High
- **Call:** "Am I speaking with Daniel?" opens every call (e.g. transcript-02 @ 0:11); ANI read back as the patient's number at transcript-08 @ 0:56, transcript-10 @ 1:07, transcript-11 @ 1:10
- **What happened:** Every caller is greeted as "Daniel" (a prior caller), and the agent reads back the Twilio caller ID *"971-389-3480"* as the patient's "number on file," forcing each patient to correct it. In transcript-12 a self-declared **new** patient is still addressed as Daniel.
- **Why it's a problem:** Over-trusting caller ID for identity causes wrong-record association (one caller's data attached to another's chart), repeated correction friction, and a data-integrity risk.
- **Expected:** Don't infer the patient from caller ID; verify identity independently and don't present ANI as the record on file.

### Bug 5 — Patient's phone number mislabeled as the clinic's "billing number"
- **Severity:** Medium
- **Call:** transcript-11.txt (telehealth) @ 1:33
- **What happened:** After the patient corrects their number, the agent says *"And our billing number is eight zero five… zero one six two"* — labeling the patient's just-provided number as the clinic's billing number, then loops to re-confirm.
- **Why it's a problem:** Garbled field/slot handling risks storing data in the wrong field and confuses the caller about whose number is whose.
- **Expected:** Keep the patient's contact number in the patient field; never relabel it as a clinic number.

### Bug 6 — Name-spelling loop
- **Severity:** Medium
- **Call:** transcript-09.txt (cancel) @ 0:30–0:51
- **What happened:** *"Please spell your first and last name"* → patient spells both → *"Please spell just your last name"* → "D-A-V-I-S" → *"Please spell your full last name again. One letter at a time."* The agent keeps re-asking despite a correct answer.
- **Why it's a problem:** Frustrating dead-end loop; the agent fails to register a correctly spelled response.
- **Expected:** Accept a clearly spelled name on first or second pass and move on.

### Bug 7 — In-scope requests deflected and never served
- **Severity:** Medium
- **Call:** transcript-11 (telehealth) @ 0:30; transcript-04 (insurance) @ 0:38–0:44; transcript-12 (new patient) @ 1:17–1:37
- **What happened:** A telehealth/video-visit request is never addressed. An insurance-acceptance question goes straight to the dead-end transfer. A new-patient registration is met with *"I'm a pretty good AI and can do many of the things an operator can — want to give me a try?"* and then the dead-end transfer; nobody is registered.
- **Why it's a problem:** Common, ordinary patient intents go unserved.
- *(Note: on insurance the agent did **not** hallucinate plan acceptance — good — but it also gave no answer or route.)*
- **Expected:** Either handle these intents or route them somewhere real.

### Bug 8 — Duplicated prompts and name mishears
- **Severity:** Low
- **Call:** transcript-02 @ 0:26–0:28 ("Please tell me your full name and date of birth" twice); transcript-11 @ 0:19–0:22 ("Thanks, Nina. How can I help today?" repeated); name mishears "Ayesha" for Aisha (transcript-12 @ 0:44), "Nita Lopez" for Nina (transcript-11 @ 0:44)
- **Why it's a problem:** Minor polish/turn-taking issues; the repeated prompts are agent-side, not caller-side.
- **Expected:** De-duplicate prompts; confirm spelling when a name is uncertain rather than guessing.

---

## Method
12 calls were placed from a single number, each driving a distinct patient
scenario (scheduling, reschedule, cancel, refills incl. a controlled substance,
insurance, office hours, telehealth, new-patient, an emergency symptom, and a
deliberately vague request). Each call's audio was recorded (dual-channel) and a
speaker-labeled transcript captured live. Findings above were confirmed against
both the transcript and the recording.
