# Skill: DSP Change

Use this procedure before making a meaningful change to audio-analysis mathematics.

---

# 1. State the Question

Clearly identify what is being changed.

Examples:

- frame length
- hop length
- window function
- FFT normalization
- magnitude calculation
- power calculation
- frequency-bin calculation
- frequency grouping

Do not change DSP settings simply because another library uses different defaults.

---

# 2. Create a Known Input

Whenever possible, validate the change with a controlled signal.

Useful inputs include:

    440 Hz sine
    440 Hz + 880 Hz
    silence
    impulse
    chirp

Write down what should happen before running the experiment.

---

# 3. Understand the Math

Research the relevant behavior when uncertain.

Prefer authoritative DSP references and library documentation.

Important equations should remain understandable in the implementation or documentation.

Do not hide five understandable NumPy operations behind a large abstraction merely to make them look cleaner.

---

# 4. Implement Narrowly

Change only the DSP behavior required for the experiment or approved feature.

Avoid combining a DSP change with:

- rendering redesign
- unrelated file movement
- architecture cleanup
- new UI work

Keep scientific changes easy to review.

---

# 5. Verify

Compare:

    expected result
        vs
    actual result

Use numerical tolerances where appropriate.

Run existing DSP regression tests.

Check whether the change affects deterministic output.

---

# 6. Document

If the change affects how Sound Springs measures audio, update the relevant documentation.

Record:

- what changed
- why
- expected effect
- tradeoffs
- whether the decision is experimental

Remember:

    DSP result = measurement

    measurement → visual / physical behavior = interpretation

Keep those concepts separate.