# Test results (final prompt P1, P2 for regeneration)

Model: `gemini-3.6-flash` · run on 2026-11-22 15:05 · **12/12 passed**

| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail |
|---|---|---|---|---|---|
| T01 | 3 subjects, different exam dates; 4 h weekday / 6 h weekend | Normal | Valid plan, 0 violations; every subject revised; DBMS gets the most hours | Valid JSON, 0 violations; DBMS 31.5h, OS 23.5h, DM 16.0h | Pass |
| T02 | 5 subjects, limited study hours; 2 h weekday / 3 h weekend | Normal | Within 2 h / 3 h per day; all revised; Physics and Maths get more hours than English | Valid JSON, 0 violations; Physics 8.0h, Chemistry 6.5h, Maths 7.0h, English 4.0h, Biology 6.0h | Pass |
| T03 | 1 difficult subject and 2 easy subjects; 3 h weekday / 5 h weekend | Normal | Compiler Design gets more hours than each easy subject; same-day exam warning | Valid JSON, 0 violations; CD 23.5h, Ethics 11.0h, ES 13.0h; 1 warning(s) shown | Pass |
| T04 | Exams on consecutive days; 4 h weekday / 6 h weekend | Normal | Revision the day before each exam; half day on exam days; Algorithms gets more hours than SE | Valid JSON, 0 violations; CN 13.5h, SE 8.5h, Algorithms 18.0h | Pass |
| T05 | Very different weekday vs weekend availability; 1.5 h weekday / 8 h weekend | Normal | Weekdays at most 1.5 h, weekends carry the load; 0 violations | Valid JSON, 0 violations; ML 29.0h, Statistics 22.0h | Pass |
| T06 | Only 1 hour per day; 1 h weekday / 1 h weekend | Edge | Low-time + insufficient-time warnings; at most 1 h/day; every subject revised | Valid JSON, 0 violations; DBMS 3.0h, OS 2.5h, Java 2.5h; 4 warning(s) shown | Pass |
| T07 | Two exams on the same day; 4 h weekday / 5 h weekend | Edge | Same-day exam warning; Physics and Chemistry both revised before 12-02 | Valid JSON, 0 violations; Physics 13.2h, Chemistry 13.2h, Maths 17.5h; 1 warning(s) shown | Pass |
| T08 | Exam tomorrow (only one study day); 6 h weekday / 6 h weekend | Edge | One-day plan (at most 6 h) that includes revision | Valid JSON, 0 violations; Economics 6.0h | Pass |
| T09 | Exam date already passed; 4 h weekday / 6 h weekend | Invalid | Rejected: exam date already passed; no AI call | Rejected before AI call: DBMS: exam date 2026-11-10 has already passed. | Pass |
| T10 | No subjects entered; 4 h weekday / 6 h weekend | Invalid | Rejected: no subjects entered; no AI call | Rejected before AI call: No subjects entered. Add at least one subject with an exam date. | Pass |
| T11 | Negative study hours; -2 h weekday / 4 h weekend | Invalid | Rejected: negative hours; no AI call | Rejected before AI call: Weekday study hours cannot be negative (got -2). | Pass |
| T12 | Regeneration: student blocks a Sunday after the plan is made; 4 h weekday / 6 h weekend | Edge | Revised plan with no study on 11-29; 0 violations | Valid JSON, 0 violations; DBMS 28.5h, OS 22.0h, DM 14.5h (first plan: 0 violation(s)) | Pass |
