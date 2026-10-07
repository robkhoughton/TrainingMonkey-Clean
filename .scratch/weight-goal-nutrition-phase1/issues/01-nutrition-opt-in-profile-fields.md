# 01 — Nutrition opt-in + profile fields

**What to build:** A user can opt into the nutrition module from Settings. Opting
in (or reaching it for the first time) captures height, a sex-for-formula field
defaulted from the existing gender field but independently editable, and a
fueling-strategy field defaulting to conventional. A user who reaches any
nutrition-related surface without height on file is prompted for it in place,
without being blocked from anything else.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] User can toggle the nutrition module on/off from Settings; off is the default for every existing and new user.
- [ ] Height, sex-for-formula, and fueling-strategy fields are captured and persisted; sex-for-formula defaults from the existing gender field but can be changed independently.
- [ ] Fueling-strategy defaults to conventional and only changes on explicit user action.
- [ ] A user who reaches a nutrition-related surface without height on file is prompted for it in place, without being blocked from anything else in the app.
- [ ] Turning the module off does not delete any previously entered values (goal, height, fueling strategy, test history) — it only hides the surfaces.
- [ ] The existing weight-trend-based safety check's behavior is unaffected by opt-in state, on or off.
