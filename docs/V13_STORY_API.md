# V13 original Coast story slice

Three short original chapters reuse the existing event simulation; this is not a copied commercial-game narrative or a full campaign.

| Chapter | Event | Range | Requirement |
|---|---|---|---|
| Village Signal | Time Attack | 165–1265 m | Finish all gates before the time limit |
| Harbor Line | Coast Sprint | 2200–3350 m | Finish all gates; any finishing position qualifies |
| Last Light | Hot Pursuit | 2200–4350 m | Finish all gates and actually escape the patrol |

There is no new physics, currency, bonus award, multiplayer claim, or car-ownership change in these modules. The existing `awardResult(profile, model.result, runId)` remains the only coin award path. Replaying a completed chapter can earn the normal reward of a new race; story completion itself grants no additional coins.

## Controller API

```js
import {
  STORY_CHAPTERS, createStoryProgress, isChapterUnlocked,
  isChapterCompleted, nextStoryChapter, beginStoryRun, completeStoryRun
} from './story.js';
import {createStoryStore} from './story-store.js';

const storyStore = createStoryStore();
let storyProgress = storyStore.progress;
// The same fresh runId must be used by normal race rewards.
const admitted = beginStoryRun(storyProgress, selectedChapterId, runId, track.id);
if (admitted.ok) {
  activeStoryRun = admitted.run;
  // New GameModel(route, {...existingOptions,
  //   startS: admitted.run.startS, endS: admitted.run.endS})
  //   .start(admitted.run.scenario);
}
// Only once that selected story model has a terminal result:
const completion = completeStoryRun(storyProgress, activeStoryRun, model.result);
if (completion.ok) {
  storyProgress = completion.progress;
  storyStore.save(storyProgress);
}
```

Keep the admitted run only for its selected story model. Clear it when starting a normal event, going to the menu, or changing tracks; a restart gets a fresh run ID and fresh admission. A quick race must never be converted into a story finish merely because its scenario is the same. Finish/result camera playback must not call either reward function a second time. `completeStoryRun` is nevertheless idempotent for the first completion and for replays.

All chapter copy is exposed by `STORY_CHAPTERS`: `id`, `number`, `title`, `track`, `scenario`, `startS`, `endS`, `briefing`, `objective`, `intro`, `completion`, `shortObjective`. Unknown IDs, inherited object names, non-Coast admission, locked chapters, modified run ranges, wrong event results, non-finite values, and a pursuit without a confirmed escape are rejected.

`completeStoryRun` returns `{ok, progress, reason, newlyCompleted, nextChapter}`. `reason` is `chapter-completed`, `already-recorded`, or `replay` on success. A failed/busted/incomplete run returns `objective-not-met` without progress changes. `nextStoryChapter(progress)` is null when all three are complete.

## Storage boundary and motion preference

`createStoryStore()` returns `.progress`, `.warning`, `.persistent`, and `.save(next)`. It reads/writes only `malabar-story-v13`; it never reads/writes/deletes `malabar-garage-v12`, `malabar-garage-v1`, their backups, or other keys.

Progress schema is `{schemaVersion:1, completions:[{chapterId,runId,time,position}], reducedMotion:false}`. Completions must be an ordered prefix of the three chapters. Each first-completion run ID is immutable and unique. Missing storage starts fresh. Malformed/future progress is protected, not overwritten. Denied/quota storage or detected stale-tab writes disable persistence but retain current session progress and return false. This is optimistic conflict detection, **not cross-tab transactional locking**. The exposed progress is copied to avoid accidental mutation.

Persist a user toggle with `{...storyProgress,reducedMotion:enabled}` and use `userPreference || matchMedia('(prefers-reduced-motion: reduce)').matches` for effective motion. The user setting must not override a system request for reduced motion.

## Tests and limits

- `node tests/story.test.mjs`: strict progression and result checks; actual finite steering through all three chapters with all seven stock cars and three fully upgraded cars, real Coast route and all 1,182 static colliders.
- `node tests/story-store.test.mjs`: malformed/future data, independent namespace, duplicate completion, denied/quota storage, readback conflict, stale tab, no rollback, preferences, and old garage writers.
- Metrics: `tests/STORY_MODEL_RESULTS.json` in the project root.

These are deterministic source/model/storage checks. They do not establish GPU rendering, camera safety, browser/touch behavior, audio listening, or human driving quality; integration and actual browser acceptance are separate gates.
