export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({
      reply: "Method not allowed",
      actions: []
    });
  }

  try {
    const { message, image, flowState } = req.body || {};

    if (flowState?.topic === "image_identified") {
      const normalisedMessage = String(message || "").toLowerCase().trim();
      const figure = flowState.figure || "unknown";

      if (
        flowState.step === "post_identification" &&
        ["no", "n", "no thanks", "2"].includes(normalisedMessage)
      ) {
        return res.status(200).json({
          reply: "Thanks, let me know if I can help you with anything else.",
          flowState: null,
          actions: []
        });
      }

      if (
        flowState.step === "post_identification" &&
        ["yes", "y", "1", "yes, i have a question about this figure"].includes(normalisedMessage)
      ) {
        return res.status(200).json({
          reply:
            "What would you like help with?\n\nA Identify the figure variant\nB Tell me what accessories came with this figure\n\nOr type your question below.",
          flowState: {
            topic: "image_identified",
            figure,
            step: "choose_help"
          },
          actions: [
            { label: "A Identify the figure variant", value: "identify variant" },
            { label: "B Accessories", value: "show accessories" }
          ]
        });
      }

      if (
        flowState.step === "choose_help" &&
        (
          normalisedMessage.includes("identify") ||
          normalisedMessage.includes("variant") ||
          normalisedMessage === "a"
        )
      ) {
        if (figure === "luke_bespin") {
          return res.status(200).json({
            reply:
              "Let’s start with the broad checks for Luke Skywalker in Bespin Fatigues.\n\nCheck the Country of Origin marking on the leg.\n\n1 Hong Kong\n2 No COO / removed COO\n3 Taiwan\n4 Not sure\n\nReply with a number or describe what you can see.",
            flowState: {
              topic: "luke_bespin_variant",
              step: "coo"
            },
            actions: []
          });
        }

        return res.status(200).json({
          reply:
            "Variant identification for this figure type is not fully built yet.\n\nFor now, describe the COO marking, paint details and accessories and I’ll help as best I can.",
          flowState: null,
          actions: []
        });
      }

      if (
        flowState.step === "choose_help" &&
        (
          normalisedMessage.includes("accessor") ||
          normalisedMessage.includes("weapon") ||
          normalisedMessage === "b"
        )
      ) {
        if (figure === "luke_bespin") {
          return res.status(200).json({
            reply:
              "Luke Skywalker in Bespin Fatigues is commonly associated with:\n\n1 Yellow lightsaber\n2 Rebel blaster / pistol\n\nAccessory image cards are not connected for this figure yet. The next proper step is adding a Luke Bespin accessory reference file and images.",
            flowState: null,
            actions: []
          });
        }

        return res.status(200).json({
          reply:
            "Accessory lookup for this figure type is not fully built yet.\n\nIf you describe the weapon or accessory, I’ll help as best I can.",
          flowState: null,
          actions: []
        });
      }
    }

    if (flowState?.topic === "luke_bespin_variant") {
      if (flowState.step === "coo") {
        return res.status(200).json({
          reply:
            "Good. Next check the hair colour and face paint.\n\n1 Blonde / yellow hair\n2 Brown hair\n3 Orange / ginger hair\n4 Not sure\n\nReply with a number or describe it.",
          flowState: {
            topic: "luke_bespin_variant",
            step: "hair"
          },
          actions: []
        });
      }

      if (flowState.step === "hair") {
        return res.status(200).json({
          reply:
            "That gives a basic starting point.\n\nLuke Bespin variant narrowing needs the dedicated Bespin reference flow next, including COO family, hair paint, boot colour, belt paint and accessory pairing.\n\nFor now, use this as a broad ID, not final authentication.",
          flowState: null,
          actions: []
        });
      }
    }

    if (image) {
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            {
              role: "system",
              content: `
You are VF-CB, a Vintage Kenner Star Wars figure identification assistant.

Your job:
- identify the broad figure family only
- do not authenticate exact variants
- detect if the item appears modern, fake, bootleg or unrelated
- return ONLY compact JSON with these keys:
  "figure_key": a stable snake_case key
  "display_name": the best broad figure name
  "confidence": "high", "medium", or "low"
  "is_vintage_star_wars": true or false

Use collector-friendly naming.

Examples:
- Luke Skywalker in Bespin Fatigues
- Luke Skywalker (Original / Tatooine / Farm boy)
- Luke Skywalker (X-Wing Pilot)
- Luke Skywalker (Hoth)
- Luke Skywalker (Jedi Knight)
- Luke Skywalker (Endor / Poncho)
- Luke Skywalker (Stormtrooper)
- Jawa
- Darth Vader
- Stormtrooper
- Princess Leia Organa
- Han Solo
- Chewbacca
- C-3PO
- R2-D2

If uncertain, use:
figure_key: "uncertain"
display_name: "uncertain vintage Star Wars figure"
confidence: "low"
`
            },
            {
              role: "user",
              content: [
                {
                  type: "text",
                  text: "Identify this vintage Kenner Star Wars figure at broad figure-family level only."
                },
                {
                  type: "image_url",
                  image_url: {
                    url: image
                  }
                }
              ]
            }
          ],
          max_tokens: 220
        })
      });

      const data = await response.json();

      console.log("OPENAI RESPONSE:", JSON.stringify(data, null, 2));

      const rawReply = data?.choices?.[0]?.message?.content || "";

      let parsed = null;

      try {
        parsed = JSON.parse(rawReply.replace(/```json|```/g, "").trim());
      } catch (err) {
        parsed = null;
      }

      const displayName = parsed?.display_name || rawReply || "uncertain vintage Star Wars figure";
      const confidence = parsed?.confidence || "low";
      const isVintage = parsed?.is_vintage_star_wars !== false;
      const figureKey = parsed?.figure_key || normaliseFigureKey(displayName);

      if (!isVintage || figureKey === "uncertain") {
        return res.status(200).json({
          reply:
            `I’m not fully confident this is a vintage Kenner Star Wars figure.\n\nClosest broad match: ${displayName}\nConfidence: ${confidence}\n\nWould you like to try another photo or describe the figure instead?`,
          flowState: null,
          actions: [
            { label: "Try another photo", value: "upload another photo" },
            { label: "Describe it", value: "describe figure" }
          ]
        });
      }

      return res.status(200).json({
        reply:
          `This figure appears to be ${displayName}.\n\nConfidence: ${confidence}\n\nDid you have any questions about this figure or would you like to look up another?`,
        flowState: {
          topic: "image_identified",
          figure: figureKey,
          step: "post_identification"
        },
        actions: [
          { label: "Yes", value: "yes" },
          { label: "No", value: "no" }
        ]
      });
    }

    return res.status(200).json({
      reply:
        "Photo upload is connected. Text-only collector chat still needs reconnecting.",
      actions: []
    });

  } catch (error) {
    console.error(error);

    return res.status(500).json({
      reply: "Something went wrong analysing the image.",
      actions: []
    });
  }
}

function normaliseFigureKey(value) {
  const text = String(value || "").toLowerCase();

  if (text.includes("bespin") && text.includes("luke")) return "luke_bespin";
  if ((text.includes("farm") || text.includes("tatooine") || text.includes("original")) && text.includes("luke")) return "luke_original_tatooine_farmboy";
  if ((text.includes("x-wing") || text.includes("x wing")) && text.includes("luke")) return "luke_xwing";
  if (text.includes("hoth") && text.includes("luke")) return "luke_hoth";
  if (text.includes("jedi") && text.includes("luke")) return "luke_jedi";
  if (text.includes("endor") && text.includes("luke")) return "luke_endor";
  if (text.includes("stormtrooper") && text.includes("luke")) return "luke_stormtrooper";
  if (text.includes("jawa")) return "jawa";

  return text
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}
