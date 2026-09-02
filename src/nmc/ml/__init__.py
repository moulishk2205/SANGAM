"""
The learned layer.

Everything else in this engine is deterministic: a gazetteer, a set of regexes,
a unit-aware comparison table and two hand-chosen weights. That was the right
place to start, because a rule you can read is a rule a procurement officer can
argue with. But it left three numbers unjustified —

  * the 0.85 / 0.15 split between attribute agreement and text corroboration,
    chosen because it felt right;
  * the thresholds 0.86 / 0.70 / 0.45, chosen the same way;
  * and the claim that the resulting score means anything on a 0-1 scale, which
    the code has always denied by stamping `calibrated: False` on every payload.

This package replaces all three with parameters fitted on labelled data, and
keeps the veto exactly where it was.
"""
from .features import FEATURE_NAMES, featurise                      # noqa: F401
from .model import LearnedScorer, load_scorer, SCORER_VERSION       # noqa: F401
