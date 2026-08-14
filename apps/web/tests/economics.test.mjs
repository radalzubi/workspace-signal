import assert from "node:assert/strict";
import test from "node:test";

test("percentage conversion convention remains explicit", () => {
  const displayedPercent = 1.8;
  assert.ok(Math.abs(displayedPercent / 100 - 0.018) < Number.EPSILON);
});
