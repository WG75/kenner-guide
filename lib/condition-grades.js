/* Condition scale for a saved figure and for each accessory.
   Near Mint is the top grade. Mint is not a grade on this scale. */

export const GRADES = Object.freeze([
  "Near Mint",
  "Very Fine",
  "Fine",
  "Very Good",
  "Good",
  "Fair",
  "Poor"
]);

export function normaliseGrade(value) {
  const grade = String(value || "").trim();
  if (!grade) return { ok: true, grade: "" };
  if (/^mint$/i.test(grade)) {
    return {
      ok: false,
      error: "mint_not_a_grade",
      message: "Near Mint is the top grade. Mint is not used."
    };
  }
  const found = GRADES.find(item => item.toLowerCase() === grade.toLowerCase());
  if (!found) {
    return {
      ok: false,
      error: "bad_grade",
      message: "Choose a grade from Near Mint down to Poor."
    };
  }
  return { ok: true, grade: found };
}
