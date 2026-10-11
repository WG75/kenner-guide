import { GRADES } from "./lib/condition-grades.js";
import { applyIdentification, emptyDraft, identificationReady, STORED_PHOTO_LIMIT } from "./lib/collection-model.js";
import { preparePhotoForUpload } from "./photo-upload.js";

const CLERK_BROWSER = "https://esm.sh/@clerk/clerk-js@5.128.0";
const STORE_PHOTO = { maxSide: 960, qualities: [0.72, 0.55, 0.4], limit: STORED_PHOTO_LIMIT };

export function saveActionVisible(state) {
  return Boolean(state && state.enabled && state.signedIn && state.identified && state.canSave);
}

export function mountMembers({ bar, getPhoto }) {
  injectStyles();
  const state = {
    enabled: false,
    mode: "off",
    signedIn: false,
    canSave: false,
    email: "",
    identified: false,
    draft: emptyDraft(),
    clerk: null,
    publishableKey: ""
  };

  function noteIdentification(flowState) {
    const next = applyIdentification(state.draft, flowState);
    if (identificationReady(next)) {
      state.draft = next;
      state.identified = true;
    }
    renderBar();
  }

  renderBar();
  load().catch(() => {
    state.enabled = false;
    renderBar();
  });

  return { noteIdentification };

  async function load() {
    const config = await fetch("/api/members").then(res => res.json());
    state.enabled = Boolean(config && config.enabled);
    state.mode = config && config.mode || "off";
    state.publishableKey = config && config.publishableKey || "";
    if (!state.enabled) {
      renderBar();
      return;
    }
    if (state.mode === "clerk" && state.publishableKey) {
      state.clerk = await loadClerk(state.publishableKey);
      if (state.clerk.session) await refreshMember();
    } else if (state.mode === "dev") {
      await refreshMember().catch(() => {});
    }
    renderBar();
  }

  async function refreshMember() {
    const data = await api("me");
    state.signedIn = true;
    state.canSave = Boolean(data.member && data.member.canSave);
    state.email = data.member && data.member.email || "";
  }

  function renderBar() {
    if (!bar) return;
    bar.replaceChildren();
    if (!state.enabled) {
      bar.hidden = true;
      return;
    }
    bar.hidden = false;
    if (!state.signedIn) {
      bar.appendChild(button("Sign in", openSignIn));
      return;
    }
    const who = document.createElement("span");
    who.className = "member-who";
    who.textContent = state.email ? `Signed in as ${state.email}` : "Signed in";
    bar.appendChild(who);
    bar.appendChild(button("Collection", () => openCollection()));
    if (saveActionVisible(state)) bar.appendChild(button("Save to…", () => openSave()));
    bar.appendChild(button("Sign out", signOut));
  }

  async function api(action, body) {
    const headers = { "Content-Type": "application/json" };
    if (state.clerk && state.clerk.session) {
      const token = await state.clerk.session.getToken();
      if (token) headers.Authorization = `Bearer ${token}`;
    }
    const res = await fetch("/api/members", {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({ action, ...(body || {}) })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const error = new Error(data.message || "Something went wrong.");
      error.code = data.error;
      throw error;
    }
    return data;
  }

  async function signOut() {
    try {
      if (state.mode === "dev") await api("dev-sign-out");
      if (state.clerk) await state.clerk.signOut();
    } catch (err) {
      // The local session is cleared either way.
    }
    state.signedIn = false;
    state.canSave = false;
    state.email = "";
    renderBar();
  }

  function openSignIn() {
    const sheet = overlay();
    const title = heading("Sign in");
    sheet.appendChild(title);
    const lead = document.createElement("p");
    lead.className = "member-lead";
    lead.textContent = "Sign-up is free. You can search and identify without an account. Sign in when you want to save figures.";
    sheet.appendChild(lead);
    if (state.mode === "dev") {
      const note = document.createElement("p");
      note.className = "member-note";
      note.textContent = "Local test mode. Email, Google and Facebook sign you in on this computer only.";
      sheet.appendChild(note);
    }
    const form = document.createElement("form");
    form.className = "member-form";
    const email = field("Email", "email", "you@example.com");
    form.appendChild(email.wrap);
    const status = document.createElement("p");
    status.className = "member-status";
    form.appendChild(status);
    const codeWrap = document.createElement("div");
    codeWrap.hidden = true;
    const code = field("Email code", "text", "Code from your email");
    codeWrap.appendChild(code.wrap);
    form.appendChild(codeWrap);

    form.appendChild(button("Continue with email", (event) => {
      event.preventDefault();
      beginEmail(email.input.value, code, codeWrap, status);
    }, "submit"));
    form.appendChild(button("Continue with Google", (event) => {
      event.preventDefault();
      beginProvider("google", email.input.value, status);
    }));
    form.appendChild(button("Continue with Facebook", (event) => {
      event.preventDefault();
      beginProvider("facebook", email.input.value, status);
    }));
    form.appendChild(button("Close", (event) => {
      event.preventDefault();
      sheet.closest(".member-overlay").remove();
    }));
    sheet.appendChild(form);
  }

  async function beginEmail(value, code, codeWrap, status) {
    status.textContent = "";
    if (state.mode === "dev") {
      await devSignIn(value, "email", status);
      return;
    }
    try {
      const clerk = await clerkReady();
      const email = String(value || "").trim();
      try {
        const signIn = await clerk.client.signIn.create({ identifier: email });
        const factor = (signIn.supportedFirstFactors || []).find(item => item.strategy === "email_code");
        if (!factor) throw new Error("Email codes are not switched on for this site.");
        await signIn.prepareFirstFactor({ strategy: "email_code", emailAddressId: factor.emailAddressId });
        codeWrap.hidden = false;
        status.textContent = "Enter the code from your email.";
        code.input.onkeydown = async (event) => {
          if (event.key !== "Enter") return;
          event.preventDefault();
          const attempt = await signIn.attemptFirstFactor({ strategy: "email_code", code: code.input.value.trim() });
          await finishClerk(clerk, attempt.createdSessionId, status);
        };
      } catch (err) {
        if (!/not_found|couldn.?t find/i.test(String(err && (err.errors?.[0]?.code || err.message)))) throw err;
        await clerk.client.signUp.create({ emailAddress: email });
        await clerk.client.signUp.prepareEmailAddressVerification({ strategy: "email_code" });
        codeWrap.hidden = false;
        status.textContent = "Enter the code from your email to finish signing up.";
        code.input.onkeydown = async (event) => {
          if (event.key !== "Enter") return;
          event.preventDefault();
          const attempt = await clerk.client.signUp.attemptEmailAddressVerification({ code: code.input.value.trim() });
          await finishClerk(clerk, attempt.createdSessionId, status);
        };
      }
    } catch (err) {
      status.textContent = clerkMessage(err);
    }
  }

  async function beginProvider(provider, email, status) {
    status.textContent = "";
    if (state.mode === "dev") {
      await devSignIn(email, provider, status);
      return;
    }
    try {
      const clerk = await clerkReady();
      const strategy = provider === "facebook" ? "oauth_facebook" : "oauth_google";
      await clerk.client.signIn.authenticateWithRedirect({
        strategy,
        redirectUrl: `${location.origin}/sso-callback.html`,
        redirectUrlComplete: `${location.origin}/`
      });
    } catch (err) {
      status.textContent = clerkMessage(err);
    }
  }

  async function devSignIn(email, provider, status) {
    try {
      await api("dev-sign-in", { email, provider });
      await refreshMember();
      closeOverlays();
      renderBar();
    } catch (err) {
      status.textContent = err.message;
    }
  }

  async function finishClerk(clerk, sessionId, status) {
    if (!sessionId) {
      status.textContent = "That code was not accepted.";
      return;
    }
    await clerk.setActive({ session: sessionId });
    await refreshMember();
    closeOverlays();
    renderBar();
  }

  async function clerkReady() {
    if (state.clerk) return state.clerk;
    if (!state.publishableKey) throw new Error("Sign-in is not configured yet.");
    state.clerk = await loadClerk(state.publishableKey);
    return state.clerk;
  }

  async function openCollection() {
    const sheet = overlay();
    sheet.appendChild(heading("Collection"));
    const status = document.createElement("p");
    status.className = "member-status";
    sheet.appendChild(status);
    const layout = document.createElement("div");
    layout.className = "member-layout";
    const listsEl = document.createElement("div");
    listsEl.className = "member-lists";
    const main = document.createElement("div");
    main.className = "member-main";
    layout.appendChild(listsEl);
    layout.appendChild(main);
    sheet.appendChild(layout);
    const tools = document.createElement("div");
    tools.className = "member-tools";
    tools.appendChild(button("Save to…", () => openSave()));
    tools.appendChild(button("Checklist", () => showChecklist(main, status)));
    tools.appendChild(button("Close", () => sheet.closest(".member-overlay").remove()));
    sheet.insertBefore(tools, layout);

    let lists = [];
    try {
      lists = (await api("lists")).lists || [];
    } catch (err) {
      status.textContent = err.message;
      return;
    }
    let current = lists[0] && lists[0].id;
    drawLists();
    if (current) showItems(current);

    function drawLists() {
      listsEl.replaceChildren();
      for (const list of lists) {
        const item = button(list.name, () => {
          current = list.id;
          showItems(list.id);
        });
        if (list.id === current) item.classList.add("is-current");
        listsEl.appendChild(item);
      }
      const creator = document.createElement("form");
      creator.className = "member-form";
      const name = field("New list", "text", "Trades, Selling, Wants");
      creator.appendChild(name.wrap);
      creator.appendChild(button("Add list", async (event) => {
        event.preventDefault();
        status.textContent = "";
        try {
          await api("create-list", { name: name.input.value });
          lists = (await api("lists")).lists || [];
          const created = lists.find(list => list.name.toLowerCase() === name.input.value.trim().toLowerCase());
          if (created) current = created.id;
          drawLists();
          if (current) showItems(current);
        } catch (err) {
          status.textContent = err.message;
        }
      }, "submit"));
      listsEl.appendChild(creator);
    }

    async function showItems(listId) {
      current = listId;
      drawLists();
      main.replaceChildren();
      let payload;
      try {
        payload = await api("items", { listId });
      } catch (err) {
        status.textContent = err.message;
        return;
      }
      const list = payload.list;
      const title = document.createElement("h3");
      title.textContent = list ? list.name : "List";
      main.appendChild(title);
      if (list && !list.isDefault) {
        const row = document.createElement("div");
        row.className = "member-tools";
        const rename = field("Rename list", "text", list.name);
        rename.input.value = list.name;
        row.appendChild(rename.wrap);
        row.appendChild(button("Rename", async () => {
          try {
            await api("rename-list", { listId: list.id, name: rename.input.value });
            lists = (await api("lists")).lists || [];
            drawLists();
            showItems(list.id);
          } catch (err) {
            status.textContent = err.message;
          }
        }));
        row.appendChild(button("Delete list", async () => {
          try {
            await api("delete-list", { listId: list.id });
            lists = (await api("lists")).lists || [];
            current = lists[0] && lists[0].id;
            drawLists();
            if (current) showItems(current);
          } catch (err) {
            status.textContent = err.message;
          }
        }));
        main.appendChild(row);
      }
      if (!payload.items.length) {
        const empty = document.createElement("p");
        empty.textContent = "Nothing saved on this list yet.";
        main.appendChild(empty);
        return;
      }
      for (const item of payload.items) main.appendChild(itemCard(item, lists, () => showItems(list.id), status));
    }
  }

  function itemCard(item, lists, refresh, status) {
    const card = document.createElement("article");
    card.className = "member-card";
    const title = document.createElement("h3");
    title.textContent = item.figureName || (item.accessories[0] && item.accessories[0].name) || "Saved item";
    card.appendChild(title);
    const meta = document.createElement("p");
    const bits = [item.factory, item.mould, item.coo].filter(Boolean);
    if (item.figureGrade) bits.push(item.figureGrade);
    if (item.ownedOn) bits.push(item.ownedOn);
    meta.textContent = bits.join(" · ");
    card.appendChild(meta);
    if (item.accessories.length) {
      const list = document.createElement("ul");
      for (const accessory of item.accessories) {
        const line = document.createElement("li");
        line.textContent = [accessory.name, accessory.variant, accessory.grade].filter(Boolean).join(" · ");
        list.appendChild(line);
      }
      card.appendChild(list);
    }
    if (item.notes) {
      const notes = document.createElement("p");
      notes.textContent = item.notes;
      card.appendChild(notes);
    }
    if (item.photo) {
      const img = document.createElement("img");
      img.className = "member-photo";
      img.alt = "Saved photo";
      img.src = item.photo;
      card.appendChild(img);
    }
    const tools = document.createElement("div");
    tools.className = "member-tools";
    tools.appendChild(button("Edit", () => openSave(item)));
    const move = document.createElement("select");
    move.setAttribute("aria-label", "Move to list");
    for (const list of lists) {
      const option = document.createElement("option");
      option.value = list.id;
      option.textContent = list.name;
      if (list.id === item.listId) option.selected = true;
      move.appendChild(option);
    }
    tools.appendChild(move);
    tools.appendChild(button("Move", async () => {
      try {
        await api("move-item", { itemId: item.id, listId: move.value });
        refresh();
      } catch (err) {
        status.textContent = err.message;
      }
    }));
    tools.appendChild(button("Delete", async () => {
      try {
        await api("delete-item", { itemId: item.id });
        refresh();
      } catch (err) {
        status.textContent = err.message;
      }
    }));
    card.appendChild(tools);
    return card;
  }

  async function showChecklist(main, status) {
    main.replaceChildren();
    let data;
    try {
      data = await api("checklist");
    } catch (err) {
      status.textContent = err.message;
      return;
    }
    const title = document.createElement("h3");
    title.textContent = "Checklist";
    main.appendChild(title);
    const summary = document.createElement("p");
    summary.textContent = `${data.owned} owned, ${data.needed} needed, ${data.total} figures.`;
    main.appendChild(summary);
    const filter = field("Filter checklist", "search", "Figure name");
    main.appendChild(filter.wrap);
    const table = document.createElement("div");
    table.className = "member-checklist";
    main.appendChild(table);
    const draw = () => {
      const query = filter.input.value.trim().toLowerCase();
      table.replaceChildren();
      for (const figure of data.figures) {
        if (query && !figure.name.toLowerCase().includes(query)) continue;
        const row = document.createElement("div");
        row.className = "member-check" + (figure.owned ? " is-owned" : "");
        const name = document.createElement("span");
        name.textContent = figure.name;
        const mark = document.createElement("span");
        mark.textContent = figure.owned ? "Owned" : "Needed";
        row.appendChild(name);
        row.appendChild(mark);
        table.appendChild(row);
      }
    };
    filter.input.addEventListener("input", draw);
    draw();
  }

  function openSave(existing) {
    const sheet = overlay();
    const editing = Boolean(existing && existing.id);
    sheet.appendChild(heading(editing ? "Edit item" : "Save to…"));
    const form = document.createElement("form");
    form.className = "member-form";
    const status = document.createElement("p");
    status.className = "member-status";
    const draft = editing ? existing : state.draft;
    const listPicker = document.createElement("label");
    listPicker.className = "member-field";
    listPicker.textContent = "List";
    const listSelect = document.createElement("select");
    listSelect.setAttribute("aria-label", "List");
    listPicker.appendChild(listSelect);
    form.appendChild(listPicker);
    const newList = field("Or a new list", "text", "Trades, Selling, Wants");
    form.appendChild(newList.wrap);
    const figure = field("Figure", "text", "Luke Skywalker");
    figure.input.value = draft.figureName || "";
    const factory = field("Factory", "text", "Unitoy");
    factory.input.value = draft.factory || "";
    const mould = field("Mould", "text", "");
    mould.input.value = draft.mould || "";
    const coo = field("COO", "text", "Hong Kong");
    coo.input.value = draft.coo || "";
    form.append(figure.wrap, factory.wrap, mould.wrap, coo.wrap);
    const gradeLabel = document.createElement("label");
    gradeLabel.className = "member-field";
    gradeLabel.append("Figure grade");
    const grade = gradeSelect(draft.figureGrade || "");
    gradeLabel.appendChild(grade);
    form.appendChild(gradeLabel);
    const accessoryHost = document.createElement("div");
    form.appendChild(accessoryHost);
    const accessoryRows = [];
    const addAccessoryRow = (accessory) => {
      const row = document.createElement("div");
      row.className = "member-accessory";
      const name = field("Accessory", "text", "lightsaber");
      name.input.value = accessory && accessory.name || "";
      const variant = field("Accessory variant", "text", "Factory or mould");
      variant.input.value = accessory && accessory.variant || "";
      const accessoryGrade = gradeSelect(accessory && accessory.grade || "");
      accessoryGrade.setAttribute("aria-label", "Accessory grade");
      row.append(name.wrap, variant.wrap, accessoryGrade);
      const remove = button("Remove", () => {
        row.remove();
        const index = accessoryRows.indexOf(entry);
        if (index >= 0) accessoryRows.splice(index, 1);
      });
      row.appendChild(remove);
      accessoryHost.appendChild(row);
      const entry = { name: name.input, variant: variant.input, grade: accessoryGrade, row };
      accessoryRows.push(entry);
    };
    const starting = Array.isArray(draft.accessories) && draft.accessories.length ? draft.accessories : [{}];
    starting.forEach(addAccessoryRow);
    form.appendChild(button("Add accessory", (event) => {
      event.preventDefault();
      addAccessoryRow();
    }));
    const notes = field("Notes", "text", "");
    notes.input.value = draft.notes || "";
    const ownedOn = field("Date", "date", "");
    ownedOn.input.value = (draft.ownedOn || new Date().toISOString().slice(0, 10));
    form.append(notes.wrap, ownedOn.wrap);
    let photoData = editing ? (existing.photo || "") : (typeof getPhoto === "function" ? getPhoto() || "" : "");
    const photoLabel = document.createElement("label");
    photoLabel.className = "member-checkline";
    const photoBox = document.createElement("input");
    photoBox.type = "checkbox";
    photoBox.checked = Boolean(photoData);
    photoLabel.append(photoBox, document.createTextNode(" Save the reduced photo"));
    form.appendChild(photoLabel);
    const preview = document.createElement("img");
    preview.className = "member-photo";
    preview.alt = "Photo to save";
    if (photoData) preview.src = photoData;
    else preview.hidden = true;
    form.appendChild(preview);
    const file = document.createElement("input");
    file.type = "file";
    file.accept = "image/*";
    file.addEventListener("change", async () => {
      const picked = file.files && file.files[0];
      if (!picked) return;
      status.textContent = "";
      try {
        const dataUrl = await readFile(picked);
        const prepared = await preparePhotoForUpload(dataUrl, STORE_PHOTO);
        if (!prepared.ok) {
          status.textContent = prepared.message;
          return;
        }
        photoData = prepared.dataUrl;
        preview.src = photoData;
        preview.hidden = false;
        photoBox.checked = true;
      } catch (err) {
        status.textContent = "Sorry, there was a problem reading that photo.";
      }
    });
    form.appendChild(file);
    form.appendChild(status);
    form.appendChild(button(editing ? "Save changes" : "Save to…", async (event) => {
      event.preventDefault();
      status.textContent = "";
      try {
        let listId = listSelect.value;
        if (newList.input.value.trim()) {
          const created = await api("create-list", { name: newList.input.value });
          listId = created.list.id;
        }
        const payload = {
          listId,
          itemId: editing ? existing.id : "",
          figureName: figure.input.value,
          figureKey: editing ? existing.figureKey : state.draft.figureKey,
          factory: factory.input.value,
          mould: mould.input.value,
          coo: coo.input.value,
          figureGrade: grade.value,
          notes: notes.input.value,
          ownedOn: ownedOn.input.value,
          photo: photoBox.checked ? photoData : "",
          accessories: accessoryRows.map(row => ({
            name: row.name.value,
            variant: row.variant.value,
            grade: row.grade.value
          }))
        };
        await api(editing ? "update-item" : "save-item", payload);
        closeOverlays();
        if (!editing) {
          state.draft = emptyDraft();
          state.identified = false;
          renderBar();
        }
        openCollection();
      } catch (err) {
        status.textContent = err.message;
      }
    }, "submit"));
    form.appendChild(button("Close", (event) => {
      event.preventDefault();
      sheet.closest(".member-overlay").remove();
    }));
    sheet.appendChild(form);
    api("lists").then(data => {
      listSelect.replaceChildren();
      for (const list of data.lists || []) {
        const option = document.createElement("option");
        option.value = list.id;
        option.textContent = list.name;
        if (editing && list.id === existing.listId) option.selected = true;
        listSelect.appendChild(option);
      }
    }).catch(err => {
      status.textContent = err.message;
    });
  }
}

function gradeSelect(selected) {
  const select = document.createElement("select");
  select.setAttribute("aria-label", "Figure grade");
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = "Not graded";
  select.appendChild(blank);
  for (const grade of GRADES) {
    const option = document.createElement("option");
    option.value = grade;
    option.textContent = grade;
    if (grade === selected) option.selected = true;
    select.appendChild(option);
  }
  return select;
}

function heading(text) {
  const title = document.createElement("h2");
  title.textContent = text;
  return title;
}

function button(label, onClick, type) {
  const el = document.createElement("button");
  el.type = type || "button";
  el.className = "action-button member-button";
  el.textContent = label;
  el.addEventListener("click", onClick);
  return el;
}

function field(label, type, placeholder) {
  const wrap = document.createElement("label");
  wrap.className = "member-field";
  wrap.append(document.createTextNode(label));
  const input = document.createElement("input");
  input.type = type;
  input.placeholder = placeholder || "";
  input.setAttribute("aria-label", label);
  wrap.appendChild(input);
  return { wrap, input };
}

function overlay() {
  const root = document.createElement("div");
  root.className = "member-overlay";
  const gold = document.createElement("div");
  gold.className = "member-panel";
  const inner = document.createElement("div");
  inner.className = "member-panel-inner";
  const sheet = document.createElement("div");
  sheet.className = "member-sheet";
  inner.appendChild(sheet);
  gold.appendChild(inner);
  root.appendChild(gold);
  document.body.appendChild(root);
  return sheet;
}

function closeOverlays() {
  document.querySelectorAll(".member-overlay").forEach(node => node.remove());
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("unreadable"));
    reader.readAsDataURL(file);
  });
}

async function loadClerk(publishableKey) {
  const mod = await import(CLERK_BROWSER);
  const Clerk = mod.Clerk || mod.default;
  const clerk = new Clerk(publishableKey);
  await clerk.load();
  return clerk;
}

function clerkMessage(err) {
  const detail = err && err.errors && err.errors[0] && err.errors[0].longMessage;
  return detail || (err && err.message) || "Sign-in could not be completed. You can keep identifying figures without an account.";
}

function injectStyles() {
  if (document.getElementById("member-styles")) return;
  const style = document.createElement("style");
  style.id = "member-styles";
  style.textContent = `
    .member-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }
    .member-bar[hidden] { display: none; }
    .member-who { font-size: 14px; letter-spacing: 0.04em; }
    .member-button { min-height: 40px; padding: 8px 12px; font-size: 14px; }
    .member-overlay { position: fixed; inset: 0; z-index: 30; background: rgba(0,0,0,0.72); display: flex; justify-content: center; padding: 18px 16px; overflow: auto; }
    .member-panel { width: min(920px, 100%); background: var(--gold); padding: 3px; margin: auto; }
    .member-panel-inner { background: var(--white); padding: 3px; }
    .member-sheet { background: radial-gradient(circle at 50% 0%, #e0232a 0%, var(--window) 46%, var(--window-deep) 100%); color: var(--white); padding: 16px; }
    .member-sheet h2, .member-sheet h3 { font-weight: 700; letter-spacing: 0.04em; margin: 0 0 8px; }
    .member-lead, .member-note, .member-status { margin: 0 0 10px; }
    .member-note { color: var(--gold); }
    .member-form, .member-tools, .member-lists { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; }
    .member-form { flex-direction: column; align-items: stretch; }
    .member-field { display: flex; flex-direction: column; gap: 4px; font-size: 14px; letter-spacing: 0.04em; }
    .member-field input, .member-field select, .member-sheet select, .member-accessory select {
      font: inherit; color: var(--ink); background: var(--white); border: 1px solid var(--gold); min-height: 40px; padding: 6px 8px;
    }
    .member-layout { display: grid; grid-template-columns: minmax(160px, 220px) minmax(0, 1fr); gap: 12px; margin-top: 12px; }
    .member-lists { flex-direction: column; align-items: stretch; }
    .member-lists .is-current { outline: 2px solid var(--gold); }
    .member-card { border: 1px solid var(--gold); padding: 10px; margin: 0 0 10px; background: rgba(0,0,0,0.18); }
    .member-card p, .member-card ul { margin: 0 0 8px; }
    .member-photo { display: block; max-width: 180px; margin: 8px 0; background: #050505; }
    .member-accessory { display: grid; grid-template-columns: 1fr 1fr auto auto; gap: 8px; align-items: end; }
    .member-checklist { display: flex; flex-direction: column; gap: 4px; margin-top: 8px; }
    .member-check { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px solid rgba(230,195,92,0.35); }
    .member-check.is-owned span:last-child { color: var(--gold); }
    .member-checkline { display: flex; gap: 8px; align-items: center; }
    @media (max-width: 640px) {
      .member-layout, .member-accessory { grid-template-columns: 1fr; }
    }
  `;
  document.head.appendChild(style);
}
