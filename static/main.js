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

async function refreshJobs() {
  const tbody = document.getElementById('jobs_body');
  try {
    const response = await fetch('/jobs', { cache: 'no-store' });
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

document.addEventListener('DOMContentLoaded', () => {
  toggleTxtEncoding();
  refreshJobs();
  setInterval(refreshJobs, 5000);
});
