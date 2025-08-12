(function(){
  function showMsg(ok, msg){
	const el = document.getElementById('dialSaveMsg');
	if(!el) return;
	el.textContent = ok ? (msg || '✔ Saved!') : (msg || 'Save failed');
	el.classList.remove('hidden');
	setTimeout(()=>el.classList.add('hidden'), 2000);
  }

  function parseVal(v){
	if(v === '' || v === null || v === undefined) return null;
	const n = Number(v);
	return Number.isFinite(n) ? n : NaN;
  }

  let inFlight = false;

  async function handleManualDialSave(evt){
	evt.preventDefault();
	if(inFlight) return false;

	const btn = document.getElementById('saveDialBtn');
	const input1 = document.getElementById('dial1');
	const input2 = document.getElementById('dial2');

	input1.classList.remove('error');
	input2.classList.remove('error');

	const v1raw = (input1.value || '').trim();
	const v2raw = (input2.value || '').trim();
	const v1 = parseVal(v1raw);
	const v2 = parseVal(v2raw);

	const v1ok = (v1 === null) || !Number.isNaN(v1);
	const v2ok = (v2 === null) || !Number.isNaN(v2);
	if(!v1ok) input1.classList.add('error');
	if(!v2ok) input2.classList.add('error');

	const provided = (v1 !== null ? 1 : 0) + (v2 !== null ? 1 : 0);
	if(!v1ok || !v2ok || provided === 0){
	  showMsg(false, 'Enter a valid number in at least one field');
	  return false;
	}

	const payload = {};
	if(v1 !== null) payload.dial_1 = v1;
	if(v2 !== null) payload.dial_2 = v2;

	try{
	  inFlight = true;
	  btn.disabled = true;
	  const res = await fetch('/manual_dial_input', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	  });
	  if(!res.ok){
		showMsg(false, await res.text());
		return false;
	  }
	  const data = await res.json();
	  if(data && data.ok){
		input1.value = '';
		input2.value = '';
		showMsg(true, '✔ Saved');
		if(typeof window.reloadDialPlot === 'function'){
		  window.reloadDialPlot();
		} else {
		  const img = document.querySelector('#plot-container img');
		  if(img){ img.src = img.src.split('?')[0] + `?t=${Date.now()}`; }
		}
	  } else {
		showMsg(false, (data && data.error) || 'Save failed');
	  }
	}catch(err){
	  showMsg(false, err && err.message || 'Network error');
	}finally{
	  inFlight = false;
	  btn.disabled = false;
	}
	return false;
  }

  // Expose handler
  window.handleManualDialSave = handleManualDialSave;
})();