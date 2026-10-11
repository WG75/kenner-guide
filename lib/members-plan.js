/* Sign-up is free. The plan name is stored so a paid gate can be added later
   without a new table. Today free, member and subscriber can save. A future
   billing change sets the plan to "lapsed", and canSave is the only check. */

const SAVING_PLANS = new Set(["free", "member", "subscriber"]);

export function normalisePlan(value) {
  const plan = String(value || "free").trim().toLowerCase();
  if (!plan) return "free";
  return plan;
}

export function canSave(plan) {
  return SAVING_PLANS.has(normalisePlan(plan));
}

export const SAVE_BLOCKED_MESSAGE = "Saving is not included on this plan.";
