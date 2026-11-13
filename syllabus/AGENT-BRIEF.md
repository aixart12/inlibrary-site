# Brief for an agent drafting syllabi

You are adding syllabus files to this repository. The InLibrary study app downloads them: a
student searches for their class or exam and gets a ready-made list of subjects and chapters to
study from. A wrong or outdated chapter list misleads a student, so accuracy matters more than
coverage. A plan you leave out costs little; a wrong plan that gets published costs a student
weeks.

Your task message names one **batch**: one board's classes or one exam family. Do that batch and
nothing else.

## Before you start

1. Read [README.md](README.md) in this folder fully. It defines the file format, the slug rules
   and the build step. Follow it exactly.
2. Read two existing files in `data/` that are close to your batch, to see the shape in practice.
   For a school class, read `class-12-cbse-pcm.json`.
3. List `data/` and skip any plan in your batch that already exists. Do not edit existing plans.

## Sources

- Use only the official source: the board's, NCERT's or the exam body's own website or its
  official syllabus document. Put the exact URL in `syllabus_source_url`.
- Never write a syllabus from memory. Never use coaching sites, blogs or question-paper sites as
  the source.
- **Confirm the source is current.** Look for the session or year printed on the document itself,
  not only in its file name. If the only official document you can find is headed with an old
  session, or you cannot tell which session it is for, **do not draft from it**. Add the plan to
  "Could not verify" in the pull request and say what you found.
- If a board teaches from NCERT textbooks, say so in the pull request and name the page where the
  board states it. Do not assume it.
- If you cannot find and open an official source for a plan, do not create that file.

## What a good plan looks like

- **Topics are textbook chapters**, in the order they are taught, with the official English
  names. A broad unit that covers several chapters (for example "Reproduction and Development")
  is too coarse: list its chapters. If the official document gives only broad units and no
  chapter names, say so under "Unsure" and keep the units.
- **Include every subject the student must take**, including compulsory languages. If a
  compulsory subject has no usable official chapter list, leave the plan out and list it under
  "Could not verify"; do not publish a plan that silently lacks a compulsory subject.
- **One plan holds only what one student studies.** The app adds every subject in the file to the
  student's plan, so do not pile alternatives into one plan:
  - Class 11 and 12 Science is two plans: PCM (Physics, Chemistry, Mathematics) and PCB (Physics,
    Chemistry, Biology). Use the stream text `Science (PCM)` and `Science (PCB)` and the slugs
    `class-<n>-<board>-pcm` and `class-<n>-<board>-pcb`, as the CBSE plans do.
  - Where a stream offers a long menu of electives (Arts is the usual case), include the
    compulsory subjects and the most commonly taken electives, and list what you left out under
    "Unsure". Do not include every elective the board offers.
- **Aliases** are every word a student might type to find this plan: the number and its spoken
  forms (`12`, `12th`, `barahvi`), local words (`inter`, `intermediate`, `matric`), the board's
  short and full names, the stream and its common names, and common misspellings. Lowercase.
  Add subject names only when they tell plans apart (`maths` on PCM, `biology` on PCB).

## Every file you create

- `"verified": false` and `"is_published": false`. A person checks and publishes. Never set
  either to `true`, even if you are confident.
- `"version": 1`.
- `syllabus_cycle` states the session the source is for.
- `verification_note` says in one sentence how the plan was produced and what a person should
  check first.

## Rules

- Change files only inside `syllabus/`. Do not touch the website files.
- Never edit `v1/` or `build-state.json` by hand. Run `python syllabus/scripts/build.py` from the
  repository root. Fix every `ERROR:` line and run it again until it prints `OK`. Commit the
  `data/` files together with everything the build changed.
- Never change the slug of an existing plan, subject or topic.
- Work on a new branch. Never push to `main`. Open one pull request for the whole batch.
- Keep a batch to about ten files. If the batch is larger, do the first ten and say what is left.
- Stop when the batch is done. Do not start another board or exam.

## The pull request description

1. **A table**: file, plan name, subjects, topic count, source URL, session of the source.
2. **Could not verify**: plans you skipped, why, and what you tried.
3. **Unsure**: everything you had to guess or interpret, such as a chapter that appears in one
   official document and not another, a heading you could not read, or electives you left out.
   Be specific; this list is what the reviewer checks first.

## How your work is reviewed

A person opens each `syllabus_source_url`, compares the subject and chapter lists with the file,
and only then publishes the plan. Make that comparison easy: keep the official order and the
official names, and point out anything that will not match at a glance.
