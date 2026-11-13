# InLibrary syllabus catalog

Ready-made study plans for the InLibrary app. A student searches for their class or exam in the
app, taps a result, and the app downloads that plan's subjects and chapters from this folder.

This guide is for whoever adds syllabi: a person or an AI agent. It needs no programming.

## What is in here

| Path | What it is |
|---|---|
| `data/<slug>.json` | **The source of truth.** One file per plan. Edit only these. |
| `data/chips.json` | The quick-pick chips on the app's search screen |
| `scripts/build.py` | Checks the data and regenerates everything below |
| `v1/index.json` | Generated. The list of published plans the app searches |
| `v1/plans/<slug>.json` | Generated. One published plan with its subjects and topics |
| `build-state.json` | Generated. Remembers each plan's content so its version goes up when it changes |

The app reads `https://inlibrary.in/syllabus/v1/index.json` and
`https://inlibrary.in/syllabus/v1/plans/<slug>.json`. Installed apps depend on these files, so the
`v1/` layout only ever gains fields; nothing in it is removed or renamed.

## The five rules

1. **Edit only files in `data/`.** Never edit `v1/` or `build-state.json` by hand.
2. **Never change a `slug` after it is merged.** The slug is the permanent ID of a plan, subject
   or topic. To rename something, change `name` and leave `slug` alone.
3. **A new plan starts with `"verified": false` and `"is_published": false`.** Unpublished plans
   never reach the app. Only a person who has compared the plan with the official syllabus sets
   them to `true`.
4. **Run `build.py` and commit what it generates** in the same pull request as your change.
5. **Open a pull request. Never push to `main`.** Merging to `main` makes the change live.

## What a plan is

A plan is something a student prepares for:

- a school class, for example Class 12 · Bihar Board · Science
- an exam, for example SSC CGL

Each file lists the plan's subjects, and each subject lists its topics (chapters or units) in
study order.

## Naming the file

| Kind | File name | Example |
|---|---|---|
| School, with streams | `class-<number>-<board>-<stream>.json` | `class-12-bihar-board-science.json` |
| School, no streams | `class-<number>-<board>.json` | `class-10-cbse.json` |
| Exam | `<exam>.json` | `ssc-cgl.json` |

Use lowercase letters, digits and hyphens only. The file name without `.json` must equal
`exam.slug`.

## What goes in the file

```json
{
  "exam": {
    "slug": "class-12-bihar-board-science",
    "name": "Class 12 · Bihar Board · Science",
    "short_name": "Class 12",
    "kind": "school",
    "class": "12",
    "board": "Bihar Board",
    "stream": "Science",
    "aliases": ["12", "12th", "inter", "intermediate", "bseb", "bihar board",
                "science", "barahvi", "boards"],
    "category": "school",
    "conducting_body": "Bihar School Examination Board (BSEB)",
    "official_url": "https://biharboardonline.bihar.gov.in",
    "syllabus_source_url": "https://...",
    "syllabus_cycle": "2026-27",
    "verified": false,
    "verification_note": null,
    "last_verified": null,
    "version": 1,
    "is_published": false,
    "sort_order": 300
  },
  "subjects": [
    {
      "slug": "physics",
      "name": "Physics",
      "sort_order": 10,
      "topics": [
        { "slug": "electric-charges-and-fields", "name": "Electric Charges and Fields", "sort_order": 10 },
        { "slug": "electrostatic-potential-and-capacitance", "name": "Electrostatic Potential and Capacitance", "sort_order": 20 }
      ]
    }
  ]
}
```

### Fields of `exam`

| Field | Required | Notes |
|---|---|---|
| `slug` | yes | Same as the file name. Permanent. |
| `name` | yes | What the student sees in results. School plans: `Class 12 · Board · Stream`. |
| `short_name` | yes | Short label, for example `Class 12` or `SSC CGL`. |
| `kind` | yes | `school` or `exam`. |
| `class`, `board` | school only | Text, for example `"12"` and `"CBSE"`. |
| `stream` | school, when the class has streams | For example `Science`, `Arts`, `Commerce`. |
| `aliases` | yes | The words students type. See below. |
| `category` | yes | One of `school`, `entrance`, `central-govt`, `railways`, `banking`, `state-bihar`, `state-other`, `defence`, `teaching`. |
| `version` | yes | Use `1` for a new plan. `build.py` raises it when content changes. |
| `verified` | yes | `true` only after a person has checked the plan against the official source. |
| `is_published` | yes | `true` makes the plan visible in the app. |
| `syllabus_source_url` | strongly advised | The exact official page or PDF the plan was taken from. |
| `syllabus_cycle` | advised | The session or notification the syllabus belongs to, for example `2026-27`. |
| `name_hi` | no | Hindi name. Reserved for a later app version. |
| `sort_order` | no | Position in the list; a new plan can use the highest existing number plus 10. |

Subjects and topics each need `slug`, `name` and `sort_order`. Topic slugs must be unique within
the whole plan, not just within a subject. Optional extras used by a future scheduler
(`est_hours`, `priority`, `stage`, `prereq`, and a `templates` section) are checked when present;
new plans may leave them out.

Use a plain hyphen `-` in text. En dashes and em dashes are rejected.

### Aliases decide whether students find the plan

The app's search matches the start of each word in `name`, `short_name`, `class`, `board`,
`stream` and `aliases`. A plan with poor aliases is invisible. For every plan, include:

- the number and its spoken forms: `12`, `12th`, `twelfth`, `barahvi`
- local words for the level: `inter`, `intermediate`, `matric`, `boards`
- the board's or exam body's short and full names: `bseb`, `bihar board`
- the stream and its common names: `science`, `pcm`, `non medical`
- common misspellings you have seen

Everything in lowercase.

### Topics

- One topic is roughly one chapter or unit.
- Put topics in the order they are taught. `sort_order` goes 10, 20, 30, so a new topic can go in
  between as 25.
- Take names from the official syllabus of the board or exam body.

## Sources

Use only the official source: the board's, NCERT's or the exam body's own website or its official
syllabus PDF. Do not write a syllabus from memory, and do not use coaching sites or blogs as the
source. If no official source can be found and opened, do not add the plan.

## Steps to add a plan

1. Copy an existing file in `data/` that is close to the new one, and rename it.
2. Change the slug, names, aliases and the subject and topic lists. Set `"version": 1`,
   `"verified": false` and `"is_published": false`.
3. Run the build from the repository root:
   ```
   python syllabus/scripts/build.py
   ```
   It checks every file and regenerates `v1/` and `build-state.json`. Fix each `ERROR:` line and
   run it again until it prints `OK`.
4. Commit the `data/` file together with everything the build changed, on a new branch.
5. Open a pull request. The automatic check must be green.

## Publishing a plan

1. Open the plan's `syllabus_source_url` and compare the subject and chapter lists with the file.
2. Set `"verified": true`, today's date in `"last_verified"`, and `"is_published": true`.
3. Run `build.py`, commit, and merge the pull request.

The plan appears in the app within a few minutes of the merge. No app update is needed.

## Changing a plan that is already live

| You want to | Do this |
|---|---|
| Rename a subject or topic | Change `name`. Do not touch `slug`. |
| Add a topic | Add a new entry with a new slug. |
| Remove a topic | Delete the entry. Never reuse its slug for something else. |
| Take a plan down | Set `"is_published": false`. |
| Fix search | Add words to `aliases`. |

Students who already created the plan keep their copy as it was. Changes reach only plans created
afterwards.

## The chips on the search screen

`data/chips.json` has two lists, `school` and `exams`. Each chip has a `label` (what the student
sees) and a `query` (what tapping it searches for). Keep each list short enough for a small phone:
about five to seven chips. The build rejects a chip whose query finds no published plan.

## What the check rejects

- a file that is not valid JSON (usually a missing comma or quote)
- a file name that differs from `exam.slug`, or a slug with capitals, spaces or symbols
- two plans with the same slug, two subjects in a plan with the same slug, or two topics in a plan
  with the same slug
- a missing `name`, `short_name`, `kind`, `category`, `aliases`, `version`, `verified` or
  `is_published`
- a school plan without `class` and `board`
- a subject with no topics, or a plan with no subjects
- an alias that is not lowercase
- generated files that were not rebuilt and committed
