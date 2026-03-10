async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

let notesPage = 1;
let actionsPage = 1;
const pageSize = 10;

async function loadNotes() {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  const data = await fetchJSON(`/notes/?page=${notesPage}&page_size=${pageSize}`);
  
  for (const n of data.items) {
    const li = document.createElement('li');
    li.textContent = `${n.title}: ${n.content}`;
    list.appendChild(li);
  }
  
  // Update pagination info
  const info = document.getElementById('notes-info');
  info.textContent = `Page ${data.page} of ${Math.ceil(data.total / data.page_size)} (${data.total} total)`;
  
  // Update button states
  document.getElementById('notes-prev').disabled = notesPage <= 1;
  document.getElementById('notes-next').disabled = notesPage >= Math.ceil(data.total / data.page_size);
}

async function loadActions() {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  const data = await fetchJSON(`/action-items/?page=${actionsPage}&page_size=${pageSize}`);
  
  for (const a of data.items) {
    const li = document.createElement('li');
    li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions();
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
  
  // Update pagination info
  const info = document.getElementById('actions-info');
  info.textContent = `Page ${data.page} of ${Math.ceil(data.total / data.page_size)} (${data.total} total)`;
  
  // Update button states
  document.getElementById('actions-prev').disabled = actionsPage <= 1;
  document.getElementById('actions-next').disabled = actionsPage >= Math.ceil(data.total / data.page_size);
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    notesPage = 1;
    loadNotes();
  });

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    actionsPage = 1;
    loadActions();
  });

  // Notes pagination
  document.getElementById('notes-prev').addEventListener('click', () => {
    if (notesPage > 1) {
      notesPage--;
      loadNotes();
    }
  });

  document.getElementById('notes-next').addEventListener('click', () => {
    notesPage++;
    loadNotes();
  });

  // Actions pagination
  document.getElementById('actions-prev').addEventListener('click', () => {
    if (actionsPage > 1) {
      actionsPage--;
      loadActions();
    }
  });

  document.getElementById('actions-next').addEventListener('click', () => {
    actionsPage++;
    loadActions();
  });

  loadNotes();
  loadActions();
});
