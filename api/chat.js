// (only showing the part that changed for clarity — but you should replace the full file)

// FIND THIS SECTION in your current file:

const userPrompt = `
User question:
${message}

Matched entity bases:
${matchedEntities.length ? matchedEntities.join(", ") : "None"}

Matched files:
${matchedFiles.length ? matchedFiles.join(", ") : "None"}

Local reference context:
${context || "No local reference context matched."}

Answer the question using the local reference context first.
`;

// REPLACE IT WITH THIS:

const userPrompt = `
Question:
${message}

Context:
${context || ""}

Answer naturally as a knowledgeable vintage Kenner collector.

Do NOT mention:
- "local files"
- "reference files"
- "context"
- or anything about how the answer was generated
`;