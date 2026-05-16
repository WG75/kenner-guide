import fs from "fs";
import path from "path";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({
      reply: "Method not allowed",
      actions: []
    });
  }

  try {
    const { message, image, flowState } = req.body || {};

    if (flowState?.topic === "data_flow") {
      const dataFlowReply = continueDataFlow(String(message || ""), flowState);
      return res.status(200).json(dataFlowReply);
    }

    if (flowState?.topic === "image_identified") {
      const normalisedMessage = normalise(String(message || ""));
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
        ["yes", "y", "1", "yes i have a question about this figure"].includes(normalisedMessage)
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
        if (figure === "jawa") {
          return res.status(200).json(startDataFlow("jawa.figure"));
        }

        if (figure === "luke_bespin") {
          return res.status(200).json({
            reply:
              "Luke Skywalker in Bespin Fatigues has been recognised, but the detailed variant flow is not built yet.\n\nFor now, I can:\n\n1 Tell you the accessories this figure normally came with\n2 Help with a different figure\n3 Let you upload another photo",
            flowState: null,
            actions: [
              { label: "Accessories", value: "show accessories" },
              { label: "Another figure", value: "another figure" },
              { label: "Upload another photo", value: "upload another photo" }
            ]
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
        if (figure === "jawa") {
          return res.status(200).json({
            reply:
              "A Jawa may have:\n\n1 Cloth cloak or vinyl cape\n2 Jawa blaster\n\nWhat would you like to check?",
            flowState: {
              topic: "image_identified",
              figure: "jawa",
              step: "jawa_accessory_choice"
            },
            actions: [
              { label: "Cloak / cape", value: "cloak" },
              { label: "Blaster", value: "blaster" }
            ]
          });
        }

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

      if (flowState.step === "jawa_accessory_choice") {
        if (normalisedMessage.includes("cloak") || normalisedMessage.includes("cape")) {
          return res.status(200).json(startDataFlow("jawa.cloth-cloak"));
        }

        if (normalisedMessage.includes("blaster") || normalisedMessage.includes("gun") || normalisedMessage.includes("weapon")) {
          return res.status(200).json(startDataFlow("jawa.blaster"));
        }

        return res.status(200).json({
          reply:
            "Which Jawa accessory do you want to check?\n\n1 Cloak / cape\n2 Blaster",
          flowState: {
            topic: "image_identified",
            figure: "jawa",
            step: "jawa_accessory_choice"
          },
          actions: [
            { label: "Cloak / cape", value: "cloak" },
            { label: "Blaster", value: "blaster" }
          ]
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

function startDataFlow(flowId) {
  const flow = loadFlow(flowId);

  if (!flow) {
    return {
      reply:
        `I recognised that item, but I could not find the flow file for ${flowId}.\n\nPlease check that data/flows/${flowId}.json exists.`,
      flowState: null,
      actions: []
    };
  }

  return renderFlowFromStep(flow, flow.start_step || flow.start || "entry", flowId);
}

function continueDataFlow(message, flowState) {
  const flow = loadFlow(flowState.flowId);

  if (!flow) {
    return {
      reply:
        `I could not reload the flow file for ${flowState.flowId}.\n\nPlease check that data/flows/${flowState.flowId}.json exists.`,
      flowState: null,
      actions: []
    };
  }

  const step = getStep(flow, flowState.stepId);

  if (!step) {
    return startDataFlow(flowState.flowId);
  }

  if (step.type !== "question") {
    const nextStepId = step.next;
    if (!nextStepId) {
      return {
        reply: renderStepText(step),
        images: step.images || [],
        flowState: null,
        actions: []
      };
    }

    return renderFlowFromStep(flow, nextStepId, flowState.flowId);
  }

  const match = matchStepOption(message, step);

  if (!match) {
    return {
      reply:
        step.retry ||
        `I’m not quite sure which option that matches.\n\n${renderStepText(step)}`,
      images: step.images || [],
      flowState,
      actions: optionsToActions(step.options)
    };
  }

  return renderFlowFromStep(flow, match.next, flowState.flowId);
}

function renderFlowFromStep(flow, stepId, flowId) {
  let currentStepId = stepId;
  const messages = [];
  const images = [];

  for (let guard = 0; guard < 8; guard++) {
    const step = getStep(flow, currentStepId);

    if (!step) {
      return {
        reply: "I could not find the next step in this reference flow.",
        flowState: null,
        actions: []
      };
    }

    if (step.images) images.push(...step.images);
    messages.push(renderStepText(step));

    if (step.type === "question") {
      return {
        reply: messages.filter(Boolean).join("\n\n"),
        images,
        flowState: {
          topic: "data_flow",
          flowId,
          stepId: currentStepId
        },
        actions: optionsToActions(step.options)
      };
    }

    if (step.type === "route" && step.target) {
      return startDataFlow(step.target);
    }

    if (step.end || !step.next) {
      return {
        reply: messages.filter(Boolean).join("\n\n"),
        images,
        flowState: null,
        actions: []
      };
    }

    currentStepId = step.next;
  }

  return {
    reply: "This flow has too many automatic steps. Please check the flow file.",
    flowState: null,
    actions: []
  };
}

function renderStepText(step) {
  let text = String(step.content || "").trim();

  if (step.type === "question" && Array.isArray(step.options)) {
    const optionsAlreadyRendered = step.options.some((option, index) => {
      const value = String(option.value || index + 1);
      return text.includes(`${value} `) || text.includes(`${value}.`);
    });

    if (!optionsAlreadyRendered) {
      const optionText = step.options
        .map((option, index) => {
          const value = String(option.value || index + 1);
          const label = option.label || option.text || "";
          return label ? `${value} ${label}` : value;
        })
        .join("\n");

      text = `${text}\n\n${optionText}`;
    }
  }

  return text;
}

function optionsToActions(options) {
  if (!Array.isArray(options)) return [];

  return options.map((option, index) => {
    const value = String(option.value || index + 1);
    const label = option.label || option.text || value;

    return {
      label,
      value
    };
  });
}

function matchStepOption(message, step) {
  const text = normalise(message);
  const options = Array.isArray(step.options) ? step.options : [];

  for (let i = 0; i < options.length; i++) {
    const option = options[i];
    const value = normalise(String(option.value || i + 1));
    const label = normalise(option.label || option.text || "");
    const aliases = [
      ...(Array.isArray(option.aliases) ? option.aliases : []),
      ...(Array.isArray(option.match) ? option.match : [])
    ].map(normalise);

    if (text === value) return option;
    if (label && (text === label || text.includes(label))) return option;

    for (const alias of aliases) {
      if (alias && (text === alias || text.includes(alias))) {
        return option;
      }
    }
  }

  return null;
}

function loadFlow(flowId) {
  const safeFlowId = String(flowId || "").replace(/[^a-z0-9._-]/gi, "");
  const filePath = path.join(process.cwd(), "data", "flows", `${safeFlowId}.json`);

  if (!fs.existsSync(filePath)) {
    return null;
  }

  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (err) {
    console.error("Could not parse flow file:", filePath, err);
    return null;
  }
}

function getStep(flow, stepId) {
  if (!flow || !flow.steps) return null;
  return flow.steps[stepId] || null;
}

function normalise(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[’‘]/g, "'")
    .replace(/[^a-z0-9\s\-']/g, " ")
    .replace(/\s+/g, " ")
    .trim();
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
