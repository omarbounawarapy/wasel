// Paste into the browser console (or run through the Chrome extension) on a built direction page.
// Reports phone-screen controls shorter than 44px. Replace the selector prefix (.rd-) per direction.
(() => {
  const out = [];
  document.querySelectorAll('#phone a, #phone button, #phone [class*="-more"], #phone [class*="-pq"], #phone [class*="-pill"]').forEach(e => {
    const h = e.offsetHeight, w = e.offsetWidth;
    if (h && h < 44) out.push((e.className || e.tagName) + ':' + (e.textContent || '').trim().slice(0, 18) + ':' + w + 'x' + h);
  });
  return JSON.stringify({ controls: document.querySelectorAll('#phone a').length, under44: out });
})()
