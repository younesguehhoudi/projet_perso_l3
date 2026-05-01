function badgeForStatus(status) {
  if (status === 'termine') return 'success';
  if (status === 'en_cours') return 'primary';
  if (status === 'en_attente') return 'secondary';
  return 'danger';
}

function toggleTxtEncoding() {
  const targetFormat = document.getElementById('target_format');
  const txtEncodingGroup = document.getElementById('txt_encoding_group');
  if (!targetFormat || !txtEncodingGroup) {
    return;
  }
  txtEncodingGroup.style.display = targetFormat.value === 'txt' ? 'block' : 'none';
}

/**
 * Display an error message with details
 * @param {string} title - Error title
 * @param {string|array} details - Error details (string or array of strings)
 * @param {string} elementId - ID of element to insert alert into (or prepend to body)
 */
function showErrorAlert(title, details, elementId = null) {
  const alert = document.createElement('div');
  alert.className = 'alert alert-danger alert-dismissible fade show';
  alert.setAttribute('role', 'alert');
  
  let detailsHtml = '';
  if (Array.isArray(details)) {
    detailsHtml = details.length > 1 
      ? `<ul>${details.map(d => `<li>${escapeHtml(d)}</li>`).join('')}</ul>`
      : `<p>${escapeHtml(details[0])}</p>`;
  } else {
    detailsHtml = `<p>${escapeHtml(details)}</p>`;
  }
  
  alert.innerHTML = `
    <strong>${escapeHtml(title)}</strong>
    ${detailsHtml}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  if (elementId) {
    const container = document.getElementById(elementId);
    if (container) {
      container.insertAdjacentElement('beforebegin', alert);
    }
  } else {
    document.querySelector('.container')?.insertAdjacentElement('afterbegin', alert);
  }
}

/**
 * Display a success message
 * @param {string} message - Success message
 * @param {number} count - Number of successful conversions (optional)
 */
function showSuccessAlert(message, count = null) {
  const alert = document.createElement('div');
  alert.className = 'alert alert-success alert-dismissible fade show';
  alert.setAttribute('role', 'alert');
  
  let content = message;
  if (count !== null) {
    content = `${message} <span class="summary-count">(${count} fichier${count > 1 ? 's' : ''})</span>`;
  }
  
  alert.innerHTML = `
    ${content}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  document.querySelector('.container')?.insertAdjacentElement('afterbegin', alert);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Validate file type and size
 */
function validateFiles(files, allowedExtensions, maxSizeMb = 10) {
  const errors = [];
  const maxSizeBytes = maxSizeMb * 1024 * 1024;
  
  Array.from(files).forEach(file => {
    // Check extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (allowedExtensions && !allowedExtensions.includes(ext)) {
      errors.push(`${file.name}: format non autorisé (${ext})`);
    }
    
    // Check size
    if (file.size > maxSizeBytes) {
      errors.push(`${file.name}: dépasse la taille limite (${(file.size / 1024 / 1024).toFixed(2)} MB > ${maxSizeMb} MB)`);
    }
  });
  
  return errors;
}

/**
 * Validate form before submission
 */
function validateConversionForm() {
  const files = document.getElementById('file')?.files;
  if (!files || files.length === 0) {
    showErrorAlert('Erreur de validation', 'Veuillez sélectionner au least un fichier.');
    return false;
  }
  return true;
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(i === 0 ? 0 : 1)} ${sizes[i]}`;
}

function getFileExtension(name) {
  const parts = name.split('.');
  return parts.length > 1 ? parts.pop().toLowerCase() : '';
}

function clearPreview(container) {
  const previousUrl = container.dataset.objectUrl;
  if (previousUrl) {
    URL.revokeObjectURL(previousUrl);
    delete container.dataset.objectUrl;
  }
  const body = container.querySelector('.file-preview-body');
  if (body) {
    body.innerHTML = '';
  }
}

async function renderPreviewForFile(file, container) {
  const body = container.querySelector('.file-preview-body');
  if (!body) return;

  const ext = getFileExtension(file.name);
  const imageExt = new Set(['png', 'jpg', 'jpeg', 'webp', 'svg']);
  const textExt = new Set(['txt', 'json', 'yaml', 'yml', 'csv', 'md', 'log', 'conf']);
  const audioExt = new Set(['mp3', 'wav', 'mp4', 'm4a', 'ogg']);

  const meta = document.createElement('div');
  meta.className = 'file-meta mb-2';
  meta.textContent = `${file.name} (${formatBytes(file.size)})`;
  body.appendChild(meta);

  if (imageExt.has(ext)) {
    const url = URL.createObjectURL(file);
    container.dataset.objectUrl = url;
    const img = document.createElement('img');
    img.src = url;
    img.alt = file.name;
    img.className = 'file-preview-image';
    body.appendChild(img);
    return;
  }

  if (audioExt.has(ext)) {
    const url = URL.createObjectURL(file);
    container.dataset.objectUrl = url;
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = url;
    audio.className = 'w-100';
    body.appendChild(audio);
    return;
  }

  if (ext === 'pdf') {
    const url = URL.createObjectURL(file);
    container.dataset.objectUrl = url;
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = 'Ouvrir le PDF dans un nouvel onglet';
    body.appendChild(link);
    return;
  }

  if (textExt.has(ext)) {
    const text = await file.slice(0, 4000).text();
    const pre = document.createElement('pre');
    pre.className = 'file-preview-text';
    pre.textContent = text.length ? text : '(fichier vide)';
    body.appendChild(pre);
    return;
  }

  const info = document.createElement('div');
  info.className = 'text-muted';
  info.textContent = 'Apercu non disponible pour ce format.';
  body.appendChild(info);
}

async function updateFilePreview(input) {
  const targetId = input.dataset.previewTarget;
  if (!targetId) return;
  const container = document.getElementById(targetId);
  if (!container) return;

  clearPreview(container);

  const files = Array.from(input.files || []);
  if (files.length === 0) {
    container.style.display = 'none';
    return;
  }

  container.style.display = 'block';
  const body = container.querySelector('.file-preview-body');
  if (!body) return;

  if (files.length > 1) {
    const list = document.createElement('ul');
    list.className = 'file-preview-list';
    files.forEach(file => {
      const item = document.createElement('li');
      item.textContent = `${file.name} (${formatBytes(file.size)})`;
      list.appendChild(item);
    });
    body.appendChild(list);
  }

  await renderPreviewForFile(files[0], container);
}

async function refreshJobs() {
  const tbody = document.getElementById('jobs_body');
  try {
    const response = await fetch('/api/jobs', { cache: 'no-store' });
    const jobs = await response.json();
    if (!Array.isArray(jobs) || jobs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted">Aucun job pour le moment.</td></tr>';
      return;
    }

    tbody.innerHTML = jobs.map(job => {
      const badge = badgeForStatus(job.status);
      return `
        <tr>
          <td>${job.id.slice(0, 8)}</td>
          <td>${job.type}</td>
          <td>${job.target_format}</td>
          <td><span class="badge status-pill text-bg-${badge}">${job.status}</span></td>
          <td>${job.success_count ?? 0}/${job.files_count ?? 0}</td>
          <td>${job.error_count ?? 0}</td>
        </tr>
      `;
    }).join('');
  } catch (_err) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-danger">Impossible de charger les jobs.</td></tr>';
  }
}

const targetFormatSelect = document.getElementById('target_format');
if (targetFormatSelect) {
  targetFormatSelect.addEventListener('change', toggleTxtEncoding);
}

const refreshJobsButton = document.getElementById('refresh_jobs');
if (refreshJobsButton) {
  refreshJobsButton.addEventListener('click', refreshJobs);
}

// Improve form submission with better validation
document.querySelectorAll('form[enctype="multipart/form-data"]').forEach(form => {
  form.addEventListener('submit', function(e) {
    if (!validateConversionForm()) {
      e.preventDefault();
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  toggleTxtEncoding();
  refreshJobs();
  setInterval(refreshJobs, 5000);

  document.querySelectorAll('input[type="file"][data-preview-target]').forEach(input => {
    input.addEventListener('change', () => updateFilePreview(input));
  });
});
