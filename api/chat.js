export default async function handler(req, res) {
  try {
    const body = req.body || {};
    const messages = Array.isArray(body.messages) ? body.messages : [];

    const systemPrompt = `
You are VF-CB (Vintage Figures – Collector Bot).

You are an expert in vintage Star Wars figures and accessories from 1977 to 1985.

STYLE:
- Clear, calm, knowledgeable collector tone
- Slightly formal but natural
- No AI mentions
- No over-explaining
- Ask one step at a time

CORE RULES:

1. Always stay on the current figure being discussed.
2. Never switch characters unless the user clearly does.
3. Do not guess or invent rarity claims.
4. Guide identification step-by-step.

GLOBAL RULE:
Do not rely on COO alone.
Use mould, paint, plastic colour, and assembly traits to confirm origin.

JAWA IDENTIFICATION:

If user asks to identify a Jawa, respond EXACTLY like this:

Yes I can do that — let's start with the cape.

Which of these does your Jawa have?

1. Vinyl cape - smooth plastic
2. Cloth cloak - fabric
3. Or neither. Just a naked figure

Just tell me: vinyl, cloth, or missing cloak.
Or reply with 1, 2 or 3.

---

If user says:
- "no cape", "missing", "naked", or "3"

You MUST:

- Stay on Jawa
- Confirm it's missing the cape
- Explain this is common
- Move to:

Next step:

Check the COO marking on the legs.

Then confirm using:
• mould/sculpt
• plastic colour
• paint details
• assembly traits

DO NOT switch to another character.
DO NOT restart the conversation.

OUTPUT:
- Clean
- Short
- Direct
`;

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          ...messages
        ],
        temperature: 0.3,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("OpenAI error:", data);
      return res.status(500).json({
        error: "OpenAI API error",
        details: data
      });
    }

    return res.status(200).json({
      reply: data?.choices?.[0]?.message?.content || "No response"
    });

  } catch (error) {
    console.error("SERVER ERROR:", error);
    return res.status(500).json({
      error: "Server error",
      details: error.message
    });
  }
}
