// Inline editing: Edit swaps the title for a small form, Cancel swaps back.
// Without JavaScript the page still works for everything except editing.
document.querySelectorAll(".tasks li").forEach((li) => {
  const title = li.querySelector(".title");
  const actions = li.querySelector(".actions");
  const form = li.querySelector(".edit-form");
  const editBtn = li.querySelector("[data-edit]");
  const cancelBtn = li.querySelector("[data-cancel]");
  if (!form) return;

  const setEditing = (editing) => {
    title.hidden = editing;
    actions.hidden = editing;
    form.hidden = !editing;
    if (editing) {
      const input = form.querySelector("input");
      input.focus();
      input.select();
    }
  };

  editBtn.addEventListener("click", () => setEditing(true));
  cancelBtn.addEventListener("click", () => setEditing(false));
  form.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setEditing(false);
  });
});
